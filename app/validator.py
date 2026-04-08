import os

from email_validator import validate_email, EmailNotValidError

from app.dns_checks import lookup_mx, has_a_record, lookup_spf, lookup_dmarc
from app.smtp_checks import smtp_check_mailbox, detect_catch_all
from app.disposable import is_disposable_domain
from app.role_accounts import is_role_account
from app.typo_suggest import suggest_email
from app.scoring import compute_score
from app.schemas import ValidationResult

SKIP_SMTP = os.environ.get("SKIP_SMTP", "").lower() in ("1", "true", "yes")


async def validate_email_address(email: str) -> ValidationResult:
    result = ValidationResult(email=email)

    # --- 1) Syntax validation & normalization ---
    try:
        v = validate_email(email, check_deliverability=False)
        normalized = v.normalized
        local_part, domain = normalized.rsplit("@", 1)

        result.normalized_email = normalized
        result.local_part = local_part
        result.domain = domain
        result.is_valid_format = True
    except EmailNotValidError as e:
        result.status = "invalid"
        result.sub_status = "bad_syntax"
        result.message = str(e)
        result.score = 0.0
        return result

    # --- 2) Role account detection ---
    result.is_role_account = is_role_account(local_part)

    # --- 3) Disposable domain detection ---
    result.is_disposable = is_disposable_domain(domain)

    # --- 4) "Did you mean" typo suggestion ---
    suggestion = suggest_email(email)
    if suggestion:
        result.did_you_mean = suggestion

    # --- 5) MX record lookup ---
    mx_hosts = lookup_mx(domain)
    result.mx_found = len(mx_hosts) > 0

    # --- 6) Additional DNS signals ---
    result.has_a_record = has_a_record(domain)
    spf_record = lookup_spf(domain)
    dmarc_record = lookup_dmarc(domain)
    result.has_spf = spf_record is not None
    result.has_dmarc = dmarc_record is not None

    if not result.mx_found:
        result.status = "invalid"
        result.sub_status = "no_mx"
        result.message = "No MX records found for domain"
        result.score = 0.05
        if result.is_disposable:
            result.status = "disposable"
            result.sub_status = "disposable_no_mx"
        return result

    # --- 7) SMTP mailbox verification ---
    if not SKIP_SMTP:
        smtp_info = await smtp_check_mailbox(
            mx_hosts=mx_hosts,
            email=result.normalized_email,
        )
        result.smtp_reachable = smtp_info["smtp_reachable"]
        result.mailbox_exists = smtp_info["mailbox_exists"]
        result.is_greylisted = smtp_info["is_greylisted"]
        result.smtp_code = smtp_info.get("smtp_code")
        result.smtp_message = smtp_info.get("smtp_message")

        # --- 8) Catch-all / accept-all detection ---
        if result.smtp_reachable and result.mailbox_exists is True:
            catch_all = await detect_catch_all(mx_hosts=mx_hosts, domain=domain)
            result.is_accept_all = catch_all
        else:
            result.is_accept_all = None

    # --- 9) Final classification ---
    _classify(result)

    # --- 10) Confidence score ---
    result.score = compute_score(result.model_dump())

    return result


def _classify(r: ValidationResult) -> None:
    if r.mailbox_exists is True:
        if r.is_accept_all:
            r.status = "risky"
            r.sub_status = "accept_all"
            r.message = "Domain appears to accept all recipients"
        elif r.is_disposable:
            r.status = "disposable"
            r.sub_status = "disposable"
            r.message = "Disposable / temporary email domain"
        elif r.is_role_account:
            r.status = "risky"
            r.sub_status = "role_account"
            r.message = "Role-based email address"
        else:
            r.status = "ok"
            r.sub_status = "deliverable"
            r.message = "Mailbox accepted by remote server"
    elif r.mailbox_exists is False:
        r.status = "invalid"
        r.sub_status = "mailbox_not_found"
        r.message = "Mailbox rejected by remote server"
    elif r.is_greylisted:
        r.status = "risky"
        r.sub_status = "greylisted"
        r.message = "Server returned temporary failure (greylisting)"
    elif not r.smtp_reachable:
        if r.is_disposable:
            r.status = "disposable"
            r.sub_status = "disposable"
            r.message = "Disposable / temporary email domain"
        elif r.is_role_account:
            r.status = "risky"
            r.sub_status = "role_account"
            r.message = "Role-based email address (SMTP not verified)"
        elif r.mx_found and r.has_spf and r.has_dmarc:
            r.status = "ok"
            r.sub_status = "dns_verified"
            r.message = "Domain has valid MX, SPF and DMARC — likely deliverable"
        elif r.mx_found and (r.has_spf or r.has_dmarc):
            r.status = "ok"
            r.sub_status = "dns_partial"
            r.message = "Domain has valid MX and partial email authentication"
        elif r.mx_found:
            r.status = "unknown"
            r.sub_status = "smtp_blocked"
            r.message = "MX exists but SMTP verification was not possible"
        else:
            r.status = "unknown"
            r.sub_status = "smtp_unreachable"
            r.message = "Could not connect to mail server"
    else:
        r.status = "unknown"
        r.sub_status = "inconclusive"
        r.message = "Server did not provide a definitive answer"
