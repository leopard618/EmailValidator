import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import ValidateRequest, ValidationResult
from app.validator import validate_email_address

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Email Validation Service",
    description="Truelist-style email validation with open-source tools",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.post("/api/validate", response_model=ValidationResult)
async def validate(req: ValidateRequest):
    return await validate_email_address(req.email.strip())


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
