def compute_score(r: dict) -> float:
    if not r["is_valid_format"]:
        return 0.0

    if not r["mx_found"]:
        return 0.05

    if r["mailbox_exists"] is False:
        return 0.05

    base = 0.45

    # DNS signals (always available, even on cloud platforms)
    if r["mx_found"]:
        base += 0.15
    if r["has_a_record"]:
        base += 0.05
    if r["has_spf"]:
        base += 0.10
    if r["has_dmarc"]:
        base += 0.05

    # SMTP signals (may be blocked on PaaS like Render)
    if r["smtp_reachable"]:
        base += 0.10
    if r["mailbox_exists"] is True:
        base += 0.10

    # Negative signals
    if r["is_greylisted"]:
        base -= 0.15
    if r["is_accept_all"]:
        base -= 0.20
    if r["is_disposable"]:
        base -= 0.35
    if r["is_role_account"]:
        base -= 0.10

    return round(max(0.0, min(1.0, base)), 2)
