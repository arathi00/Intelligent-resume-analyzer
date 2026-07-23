# Intelligent Resume Analyzer 🚀

An intelligent web application that analyzes resumes, evaluates their quality, and provides personalized improvement suggestions using rule-based NLP techniques.

## ✨ Features

- Resume scoring system (0–100)
- PDF and DOCX resume support
- OCR support for scanned/image-based PDFs
- Resume section detection (Skills, Education, Projects, Experience, Certifications)
- Fresher-aware resume analysis
- Intelligent improvement suggestions
- File size and file type validation
- Rate limiting for API protection
- Health check endpoint
- Drag-and-drop resume upload

## 🛠 Tech Stack

### Backend
- Python
- FastAPI
- PDFPlumber
- python-docx
- pytesseract
- pdf2image

### Frontend
- HTML
- CSS
- JavaScript

### Deployment
- Docker
- OpenShift

## ⚙️ Run Locally

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the application

```bash
uvicorn app:app --reload
```

Open:

```
http://localhost:8000
```

## 💡 Project Overview

The Intelligent Resume Analyzer extracts text from PDF and DOCX resumes, detects important resume sections, validates resume structure, and generates personalized improvement suggestions using rule-based NLP techniques.

The current version focuses on deterministic resume analysis without relying on external AI services or commercial APIs.

## 🚀 Future Improvements

- Integrate a local LLM (Ollama + Llama/Phi)
- ATS compatibility analysis
- Job description matching
- AI-powered resume rewriting
- Semantic skill extraction
- Multi-language resume support

## 📷 Screenshots

(Add screenshots here)

## 📄 License

MIT License
