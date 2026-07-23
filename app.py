import os
import logging

import uvicorn
from fastapi import FastAPI, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from resume_parser import extract_text, looks_like_resume, analyze_text

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resume_analyzer")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = (".pdf", ".docx")

# In production, set this env var, e.g.:
#   ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
# Falls back to "*" for local development only.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AI Resume Analyzer")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_resume(request: Request, file: UploadFile):
    filename = (file.filename or "").lower()

    if not filename.endswith(ALLOWED_EXTENSIONS):
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unsupported file type. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}"
            },
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=400,
            content={"error": f"File too large. Max size is {MAX_FILE_SIZE_MB}MB."},
        )

    try:
        text = extract_text(filename, file_bytes)
    except Exception as exc:
        logger.warning("Extraction failed for %s: %s", filename, exc)
        return JSONResponse(
            status_code=400,
            content={"error": "Could not read this file. It may be corrupted or an unsupported format."},
        )

    is_resume, reason = looks_like_resume(text)
    if not is_resume:
        logger.info("Rejected non-resume upload (%s): %s", filename, reason)
        return JSONResponse(
            status_code=400,
            content={"error": f"This doesn't look like a resume/CV. {reason}"},
        )

    result = analyze_text(text)
    logger.info("Analyzed %s — score=%s fresher=%s", filename, result["score"], result["is_fresher"])
    return result


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port)