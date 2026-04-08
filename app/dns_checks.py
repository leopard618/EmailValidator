import dns.resolver

_RESOLVER = dns.resolver.Resolver()
_RESOLVER.timeout = 10
_RESOLVER.lifetime = 10


def lookup_mx(domain: str) -> list[str]:
    """Return MX hosts sorted by preference (lowest first)."""
    try:
        answers = _RESOLVER.resolve(domain, "MX")
        mx_records = [
            (r.preference, str(r.exchange).rstrip("."))
            for r in answers
        ]
        mx_records.sort(key=lambda x: x[0])
        return [host for _, host in mx_records]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers, dns.exception.Timeout):
        return []


def has_a_record(domain: str) -> bool:
    try:
        _RESOLVER.resolve(domain, "A")
        return True
    except Exception:
        return False


def lookup_spf(domain: str) -> str | None:
    try:
        answers = _RESOLVER.resolve(domain, "TXT")
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=spf1"):
                return txt
    except Exception:
        pass
    return None


def lookup_dmarc(domain: str) -> str | None:
    try:
        answers = _RESOLVER.resolve(f"_dmarc.{domain}", "TXT")
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith("v=DMARC1"):
                return txt
    except Exception:
        pass
    return None
