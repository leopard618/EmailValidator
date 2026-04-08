from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import ValidateRequest, ValidationResult
from app.validator import validate_email_address

app = FastAPI(
    title="Email Validation Service",
    description="Truelist-style email validation with open-source tools",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/validate", response_model=ValidationResult)
async def validate(req: ValidateRequest):
    return await validate_email_address(req.email.strip())
