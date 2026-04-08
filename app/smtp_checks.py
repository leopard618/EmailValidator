import asyncio
import random
import string
import aiosmtplib

SMTP_PER_HOST_TIMEOUT = 8
SMTP_TOTAL_TIMEOUT = 20
SENDER_DOMAIN = "verify.local"
SENDER_EMAIL = f"check@{SENDER_DOMAIN}"

PORTS_TO_TRY = [
    (25,  False),   # plain SMTP
    (587, False),   # submission (STARTTLS)
    (465, True),    # implicit TLS (SMTPS)
]


async def _try_one_mx_port(mx: str, port: int, use_tls: bool, email: str) -> dict | None:
    try:
        client = aiosmtplib.SMTP(
            hostname=mx,
            port=port,
            timeout=SMTP_PER_HOST_TIMEOUT,
            use_tls=use_tls,
            start_tls=False,
        )
        await client.connect()

        try:
            await client.ehlo(SENDER_DOMAIN)
        except aiosmtplib.SMTPException:
            await client.helo(SENDER_DOMAIN)

        if port == 587 and not use_tls:
            try:
                await client.starttls()
                await client.ehlo(SENDER_DOMAIN)
            except aiosmtplib.SMTPException:
                pass

        mail_code, _ = await client.mail(SENDER_EMAIL)
        if mail_code >= 400:
            try:
                await client.quit()
            except Exception:
                pass
            return None

        rcpt_code, rcpt_msg = await client.rcpt(email)

        result = {
            "smtp_reachable": True,
            "mailbox_exists": None,
            "is_greylisted": False,
            "smtp_code": rcpt_code,
            "smtp_message": rcpt_msg,
        }

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

    except (aiosmtplib.SMTPException, asyncio.TimeoutError,
            OSError, ConnectionError):
        return None


async def _try_one_mx(mx: str, email: str) -> dict | None:
    for port, use_tls in PORTS_TO_TRY:
        hit = await _try_one_mx_port(mx, port, use_tls, email)
        if hit:
            return hit
    return None


async def smtp_check_mailbox(mx_hosts: list[str], email: str) -> dict:
    default = {
        "smtp_reachable": False,
        "mailbox_exists": None,
        "is_greylisted": False,
        "smtp_code": None,
        "smtp_message": None,
    }

    async def _run():
        for mx in mx_hosts[:3]:
            hit = await _try_one_mx(mx, email)
            if hit:
                return hit
        return default

    try:
        return await asyncio.wait_for(_run(), timeout=SMTP_TOTAL_TIMEOUT)
    except asyncio.TimeoutError:
        return default


async def detect_catch_all(mx_hosts: list[str], domain: str) -> bool | None:
    fake_local = "".join(random.choices(string.ascii_lowercase + string.digits, k=20))
    fake_email = f"{fake_local}@{domain}"
    result = await smtp_check_mailbox(mx_hosts, fake_email)

    if result["mailbox_exists"] is True:
        return True
    if result["mailbox_exists"] is False:
        return False
    return None
