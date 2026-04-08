from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DISPOSABLE_FILE = _DATA_DIR / "disposable_domains.txt"

_DISPOSABLE_DOMAINS: set[str] = set()

if _DISPOSABLE_FILE.exists():
    with _DISPOSABLE_FILE.open() as f:
        _DISPOSABLE_DOMAINS = {line.strip().lower() for line in f if line.strip()}


def is_disposable_domain(domain: str) -> bool:
    return domain.lower() in _DISPOSABLE_DOMAINS
