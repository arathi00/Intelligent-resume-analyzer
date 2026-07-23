"""
Basic unit tests for resume_parser.py.
Run with: pytest tests/
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from resume_parser import looks_like_resume, analyze_text


SAMPLE_RESUME = """
John Doe
john.doe@email.com | +1 234 567 8901

Objective
Motivated fresher seeking an entry-level software engineering role.

Education
B.Tech in Computer Science, XYZ University, 2026

Projects
Built a resume analyzer using Python and FastAPI.
Developed a chat application using React and Node.

Skills
Python, JavaScript, React, SQL, Git

Certifications
AWS Cloud Practitioner
"""

SAMPLE_INVOICE = """
INVOICE #4521
Bill To: Acme Corp
Subtotal: $1,200.00
Tax: $96.00
Total: $1,296.00
Terms and Conditions apply. Payment due within 30 days.
This invoice was generated automatically by our billing system for
services rendered during the month of June. Please remit payment to
the address listed above before the due date to avoid late fees.
"""

SAMPLE_EXPERIENCED_RESUME = """
Jane Smith
jane.smith@email.com | +1 987 654 3210

Experience
Software Engineer at TechCorp (2020-2024)
Built scalable APIs serving 1 million+ requests/day.

Education
B.Sc Computer Science

Skills
Python, AWS, Docker, Kubernetes, SQL
"""


def test_looks_like_resume_accepts_real_resume():
    is_resume, reason = looks_like_resume(SAMPLE_RESUME)
    assert is_resume is True


def test_looks_like_resume_rejects_invoice():
    is_resume, reason = looks_like_resume(SAMPLE_INVOICE)
    assert is_resume is False


def test_looks_like_resume_rejects_empty_text():
    is_resume, reason = looks_like_resume("")
    assert is_resume is False


def test_looks_like_resume_rejects_short_text():
    is_resume, reason = looks_like_resume("Hi there, just a short note.")
    assert is_resume is False


def test_analyze_text_fresher_not_penalized_for_missing_experience():
    result = analyze_text(SAMPLE_RESUME)
    assert result["is_fresher"] is True
    # Should not tell a fresher to simply "add experience"
    assert not any(s == "Add internship or experience." for s in result["suggestions"])


def test_analyze_text_experienced_candidate_scored_normally():
    result = analyze_text(SAMPLE_EXPERIENCED_RESUME)
    assert result["is_fresher"] is False
    assert result["sections_detected"]["experience"] is True


def test_analyze_text_score_within_bounds():
    result = analyze_text(SAMPLE_RESUME)
    assert 0 <= result["score"] <= 100