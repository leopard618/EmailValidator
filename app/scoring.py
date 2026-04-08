def compute_score(result: dict) -> float:
    if not result["is_valid_format"]:
        return 0.0

    if not result["mx_found"]:
        return 0.05

    if result["mailbox_exists"] is False:
        return 0.05

    base = 0.50

    if result["smtp_reachable"]:
        base += 0.20

    if result["mailbox_exists"] is True:
        base += 0.26

    if result["is_greylisted"]:
        base -= 0.15

    if result["is_accept_all"]:
        base -= 0.20

    if result["is_disposable"]:
        base -= 0.30

    if result["is_role_account"]:
        base -= 0.10

    return round(max(0.0, min(1.0, base)), 2)
