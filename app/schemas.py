from pydantic import BaseModel, Field


class ValidateRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=320)


class ValidationResult(BaseModel):
    email: str
    normalized_email: str | None = None
    local_part: str | None = None
    domain: str | None = None

    is_valid_format: bool = False
    mx_found: bool = False
    has_a_record: bool = False
    has_spf: bool = False
    has_dmarc: bool = False
    smtp_reachable: bool = False
    mailbox_exists: bool | None = None
    is_role_account: bool = False
    is_disposable: bool = False
    is_accept_all: bool | None = None
    is_greylisted: bool = False

    did_you_mean: str | None = None

    status: str = "unknown"
    sub_status: str | None = None
    score: float = 0.0
    message: str | None = None

    smtp_code: int | None = None
    smtp_message: str | None = None
