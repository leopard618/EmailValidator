ROLE_NAMES = {
    "admin", "administrator", "support", "sales", "info", "contact",
    "billing", "help", "team", "hello", "office", "careers", "jobs",
    "marketing", "enquiries", "noreply", "no-reply", "postmaster",
    "webmaster", "hostmaster", "abuse", "security", "mailer-daemon",
    "root", "ftp", "www", "uucp", "news", "usenet", "nobody",
    "operator", "list", "listserv", "majordomo", "subscribe",
    "unsubscribe", "bounce", "owner", "request", "feedback",
    "newsletter", "alerts", "notifications", "updates", "press",
    "media", "hr", "finance", "legal", "compliance", "operations",
    "devops", "engineering", "design", "product", "ceo", "cfo",
    "cto", "coo", "founder", "partners", "investors", "board",
    "reception", "frontdesk", "concierge", "bookings", "reservations",
}


def is_role_account(local_part: str) -> bool:
    return local_part.lower() in ROLE_NAMES
