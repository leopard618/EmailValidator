from rapidfuzz import process, fuzz

COMMON_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "zoho.com", "yandex.com",
    "gmx.com", "live.com", "msn.com", "me.com", "mac.com",
    "comcast.net", "verizon.net", "att.net", "sbcglobal.net",
    "cox.net", "charter.net", "earthlink.net",
    "yahoo.co.uk", "yahoo.co.in", "yahoo.co.jp",
    "hotmail.co.uk", "outlook.co.uk",
    "googlemail.com", "fastmail.com", "tutanota.com",
]

_THRESHOLD = 80


def suggest_domain(domain: str) -> str | None:
    domain_lower = domain.lower()
    if domain_lower in COMMON_DOMAINS:
        return None

    match = process.extractOne(
        domain_lower,
        COMMON_DOMAINS,
        scorer=fuzz.ratio,
        score_cutoff=_THRESHOLD,
    )
    if match:
        suggested, score, _ = match
        if suggested != domain_lower:
            return suggested
    return None


def suggest_email(email: str) -> str | None:
    if "@" not in email:
        return None
    local, domain = email.rsplit("@", 1)
    suggestion = suggest_domain(domain)
    if suggestion:
        return f"{local}@{suggestion}"
    return None
