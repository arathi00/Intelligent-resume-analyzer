import re
from fastapi import FastAPI, UploadFile
import pdfplumber
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_text(text):

    score = 0
    suggestions = []

    text_lower = text.lower()

    # ✅ Skill keywords
    skills = ["python", "java", "javascript", "react", "sql", "api", "fastapi"]
    skill_count = sum(1 for skill in skills if skill in text_lower)
    score += skill_count * 10

    if skill_count < 3:
        suggestions.append("Add more technical skills (e.g., React, APIs, SQL).")

    # ✅ Projects section
    if "project" in text_lower:
        score += 15
    else:
        suggestions.append("Include a projects section.")

    # ✅ Experience
    if "experience" in text_lower or "intern" in text_lower:
        score += 15
    else:
        suggestions.append("Add internship or experience.")

    # ✅ Education
    if "education" in text_lower:
        score += 10

    # ✅ Numbers / achievements (AI-like check)
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

    return score, suggestions


@app.post("/analyze")
async def analyze_resume(file: UploadFile):

    text = ""

    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    score, suggestions = analyze_text(text)

    return {
        "score": min(score, 100),
        "suggestions": suggestions
    }