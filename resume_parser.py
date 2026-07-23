"""
resume_parser.py

Handles text extraction from uploaded resume/CV files (PDF, DOCX, and
scanned/image-based PDFs via OCR fallback), validates that the extracted
content actually looks like a resume, and scores it.
"""

import re
import logging
from io import BytesIO

import pdfplumber
from docx import Document

logger = logging.getLogger("resume_analyzer")


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_obj) -> str:
    """Extract text from a PDF file-like object using pdfplumber."""
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_obj) -> str:
    """Extract text from a DOCX file-like object using python-docx."""
    document = Document(file_obj)
    return "\n".join(p.text for p in document.paragraphs)


def extract_text_from_pdf_ocr(file_bytes: bytes) -> str:
    """
    Fallback extraction for scanned/photographed PDFs with no selectable
    text. Requires the optional packages `pytesseract` + `pdf2image`, and
    the system binaries `tesseract-ocr` and `poppler-utils`.

    On Ubuntu/Debian:
        sudo apt-get install tesseract-ocr poppler-utils
    On Mac:
        brew install tesseract poppler

    If these aren't installed, this silently returns "" and the file will
    correctly fail the "looks like a resume" check with a clear message,
    rather than crashing the request.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except ImportError:
        logger.warning("OCR libraries not installed; skipping OCR fallback.")
        return ""

    text = ""
    try:
        images = convert_from_bytes(file_bytes)
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
    except Exception as exc:
        logger.warning("OCR extraction failed: %s", exc)
        return ""
    return text


def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Dispatch extraction based on file extension. For PDFs with no
    selectable text (i.e. a scanned image saved as PDF), falls back to OCR.
    Raises ValueError for unsupported extensions.
    """
    filename = filename.lower()
    buffer = BytesIO(file_bytes)

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(buffer)
        if not text.strip():
            logger.info("No selectable text found in PDF, attempting OCR fallback.")
            text = extract_text_from_pdf_ocr(file_bytes)
        return text

    if filename.endswith(".docx"):
        return extract_text_from_docx(buffer)

    raise ValueError(f"Unsupported file type: {filename}")


# ---------------------------------------------------------------------------
# Validation — is this actually a resume/CV?
# ---------------------------------------------------------------------------

RESUME_SECTION_KEYWORDS = [
    "experience", "work experience", "employment history",
    "education", "academic background",
    "skills", "technical skills", "core competencies",
    "projects", "personal projects",
    "certification", "certifications", "certificate",
    "objective", "career objective", "professional summary", "summary",
    "internship", "achievements", "awards",
    "references", "contact",
]

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\-\s()]{8,}\d)")

# Soft signals that the document is something else entirely
# (invoice, book, contract, etc). Not required — just tips the scale.
NON_RESUME_HINTS = [
    "invoice", "purchase order", "subtotal", "tax invoice",
    "chapter 1", "table of contents", "abstract", "isbn",
    "terms and conditions", "privacy policy", "lorem ipsum",
]

MIN_WORD_COUNT = 50
MIN_SIGNAL_SCORE = 2


def looks_like_resume(text: str):
    """
    Heuristic check to decide whether extracted text is actually a resume/CV.
    Returns (is_resume: bool, reason: str).
    """
    if not text or not text.strip():
        return False, "No readable text could be extracted from this file."

    text_lower = text.lower()
    word_count = len(text.split())

    if word_count < MIN_WORD_COUNT:
        return False, "Document is too short to be a resume."

    section_hits = sum(1 for kw in RESUME_SECTION_KEYWORDS if kw in text_lower)
    has_email = bool(EMAIL_PATTERN.search(text))
    has_phone = bool(PHONE_PATTERN.search(text))
    non_resume_hits = sum(1 for kw in NON_RESUME_HINTS if kw in text_lower)

    signal_score = section_hits + int(has_email) + int(has_phone)

    if non_resume_hits >= 2 and signal_score < 3:
        return False, "This looks like a different type of document (not a resume/CV)."

    if signal_score < MIN_SIGNAL_SCORE:
        return False, (
            "This document doesn't appear to contain resume sections "
            "(e.g. Experience, Education, Skills) or contact details."
        )

    return True, "OK"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

SKILL_CATEGORIES = {
    "programming": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust"],
    "web": ["react", "angular", "vue", "node", "fastapi", "django", "flask", "html", "css"],
    "data": ["sql", "mongodb", "postgresql", "mysql", "pandas", "numpy", "spark"],
    "cloud_devops": ["aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins"],
    "general": ["api", "rest", "git", "agile", "testing"],
}

FRESHER_HINTS = [
    "fresher", "entry level", "entry-level", "recent graduate",
    "final year", "b.tech", "b.e.", "bachelor of", "pursuing",
    "graduating", "looking for an opportunity", "seeking an internship",
]

MAX_SKILL_SCORE = 30  # caps keyword-stuffing from dominating the score


def _detect_sections(text_lower: str) -> dict:
    return {
        "experience": "experience" in text_lower or "intern" in text_lower,
        "projects": "project" in text_lower,
        "education": "education" in text_lower,
        "skills": "skills" in text_lower,
        "certifications": "certification" in text_lower or "certificate" in text_lower,
        "summary": "summary" in text_lower or "objective" in text_lower,
    }


def analyze_text(text: str) -> dict:
    """
    Scores resume text out of 100 and returns suggestions plus which
    sections were detected. Freshers (no work experience) aren't penalized
    as long as they show projects, certifications, or education instead.
    """
    score = 0
    suggestions = []
    text_lower = text.lower()
    sections = _detect_sections(text_lower)

    is_fresher = (not sections["experience"]) and (
        sections["education"] or sections["projects"] or sections["certifications"]
        or any(hint in text_lower for hint in FRESHER_HINTS)
    )

    # ✅ Skills — capped so a giant keyword list can't dominate the score
    matched_skills = [
        skill
        for skills in SKILL_CATEGORIES.values()
        for skill in skills
        if skill in text_lower
    ]
    score += min(len(matched_skills) * 5, MAX_SKILL_SCORE)
    if len(matched_skills) < 3:
        suggestions.append("Add more technical skills (e.g., React, APIs, SQL).")

    # ✅ Projects
    if sections["projects"]:
        score += 15
    else:
        suggestions.append("Include a projects section.")

    # ✅ Experience (relaxed for freshers)
    if sections["experience"]:
        score += 15
    elif is_fresher:
        if sections["projects"] or sections["certifications"]:
            score += 10
        suggestions.append(
            "No work experience found — that's expected for freshers. "
            "Make sure your Projects and Certifications sections are detailed "
            "and highlight any internships, if you have them."
        )
    else:
        suggestions.append("Add internship or experience.")

    # ✅ Education
    if sections["education"]:
        score += 10
    else:
        suggestions.append("Include an education section.")

    # ✅ Certifications (small bonus — especially useful for freshers)
    if sections["certifications"]:
        score += 5

    # ✅ Numbers / measurable achievements
    if re.search(r"\d+", text):
        score += 10
    else:
        suggestions.append("Add measurable achievements (numbers, impact).")

    # ✅ Length check
    word_count = len(text.split())
    if word_count < 200:
        suggestions.append("Resume is too short. Add more details.")
    elif word_count > 800:
        suggestions.append("Resume is too long. Keep it concise.")
    else:
        score += 10

    return {
        "score": min(score, 100),
        "suggestions": suggestions,
        "is_fresher": is_fresher,
        "sections_detected": sections,
    }