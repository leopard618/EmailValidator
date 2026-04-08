import asyncio
import random
import string
import aiosmtplib

SMTP_TIMEOUT = 15
SENDER_DOMAIN = "verify.local"
SENDER_EMAIL = f"check@{SENDER_DOMAIN}"


async def smtp_check_mailbox(
    mx_hosts: list[str],
    email: str,
) -> dict:
    result = {
        "smtp_reachable": False,
        "mailbox_exists": None,
        "is_greylisted": False,
        "smtp_code": None,
        "smtp_message": None,
    }

    for mx in mx_hosts:
        try:
            client = aiosmtplib.SMTP(
                hostname=mx,
                port=25,
                timeout=SMTP_TIMEOUT,
                start_tls=False,
                use_tls=False,
            )
            await client.connect()
            await client.ehlo(SENDER_DOMAIN)

            mail_code, _ = await client.mail(SENDER_EMAIL)
            if mail_code >= 400:
                try:
                    await client.quit()
                except Exception:
                    pass
                continue

            rcpt_code, rcpt_msg = await client.rcpt(email)
            result["smtp_reachable"] = True
            result["smtp_code"] = rcpt_code
            result["smtp_message"] = rcpt_msg

            if 200 <= rcpt_code < 300:
                result["mailbox_exists"] = True
            elif 500 <= rcpt_code < 600:
                result["mailbox_exists"] = False
            elif 400 <= rcpt_code < 500:
                result["mailbox_exists"] = None
                result["is_greylisted"] = True

            try:
                await client.quit()
            except Exception:
                pass
            return result

        except (aiosmtplib.SMTPException, asyncio.TimeoutError, OSError):
            try:
                await client.quit()
            except Exception:
                pass
            continue

    return result


async def detect_catch_all(mx_hosts: list[str], domain: str) -> bool | None:
    fake_local = "".join(random.choices(string.ascii_lowercase + string.digits, k=20))
    fake_email = f"{fake_local}@{domain}"
    result = await smtp_check_mailbox(mx_hosts, fake_email)

    if result["mailbox_exists"] is True:
        return True
    if result["mailbox_exists"] is False:
        return False
    return None
