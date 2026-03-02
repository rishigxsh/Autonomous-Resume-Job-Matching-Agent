"""API route definitions for the Resume–Job Matching Agent.

Phase status:
- /api/parse-resume  → real LLM parsing via Anthropic (with one retry).
- /api/parse-jd      → real LLM parsing via Anthropic (with one retry).
- /api/match         → deterministic rule-based scoring (no LLM).
- /api/feedback      → LLM-powered suggestions + rewritten bullets.
"""

from __future__ import annotations

import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from core.errors import internal_error
from core.feedback import generate_feedback
from core.llm import llm_client
from core.llm_json import extract_json
from core.pdf import extract_pdf_text_bytes
from core.report import generate_pdf_report
from core.scoring import build_match_report
from schemas.models import JDJSON, MatchReportJSON, ResumeJSON

from .request_models import (
    FeedbackRequest,
    MatchRequest,
    ParseJDRequest,
    ParseResumeRequest,
    PdfReportRequest,
)
from .response_models import FeedbackResponse

router = APIRouter(prefix="/api", tags=["matching"])

_PDF_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


# ---------------------------------------------------------------------------
# PDF resume upload — Phase 8
# ---------------------------------------------------------------------------


@router.post("/parse-resume-pdf")
async def parse_resume_pdf(file: UploadFile = File(...)) -> dict[str, str]:
    """Extract plain text from an uploaded PDF resume.

    Accepts multipart/form-data with a single field named ``file``.
    Returns ``{"resume_text": "<extracted text>"}`` on success.
    """
    # --- Validate content type / extension ---
    is_pdf_mime = file.content_type == "application/pdf"
    is_pdf_ext = (file.filename or "").lower().endswith(".pdf")
    if not (is_pdf_mime or is_pdf_ext):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted.",
        )

    # --- Read and enforce size limit ---
    pdf_bytes = await file.read()
    if len(pdf_bytes) > _PDF_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum allowed size is 5 MB.",
        )
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Extract text ---
    try:
        resume_text = extract_pdf_text_bytes(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error(f"PDF extraction failed: {exc}") from exc

    return {"resume_text": resume_text}

# ---------------------------------------------------------------------------
# System prompt shared across all parsing calls.
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a precise data-extraction assistant. "
    "You always respond with a single, valid JSON object — no markdown, "
    "no code fences, no commentary, no extra keys. "
    "Every field must be present. Use snake_case keys."
)

# ---------------------------------------------------------------------------
# Resume parsing — Phase 3
# ---------------------------------------------------------------------------

_RESUME_USER_PROMPT = """\
Extract the resume below into a JSON object that matches this schema exactly:

{{
  "candidate_name": string,
  "email": string,
  "phone": string,
  "summary": string,
  "skills": [string, ...],          // lowercase, deduplicated
  "experience": [
    {{
      "job_title": string,
      "company": string,
      "start_date": string,         // YYYY-MM or "unknown"
      "end_date": string,           // YYYY-MM, "present", or "unknown"
      "responsibilities": [string, ...]
    }},
    ...
  ],
  "education": [
    {{
      "degree": string,
      "institution": string,
      "end_date": string            // YYYY-MM or "unknown"
    }},
    ...
  ],
  "certifications": [string, ...],  // empty list if none
  "total_years_experience": integer // 0 if unknown
}}

Rules:
- Return JSON only. No markdown. No extra keys. No commentary.
- All string lists may be empty but must be present.
- Normalise all skills to lowercase.

RESUME TEXT:
{resume_text}
"""

_RESUME_RETRY_PROMPT = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Return ONLY the corrected JSON object. No markdown. No commentary. No extra keys."
)


@router.post("/parse-resume", response_model=ResumeJSON)
async def parse_resume(body: ParseResumeRequest) -> ResumeJSON:
    """Parse raw resume text into a validated ResumeJSON using the LLM."""
    user_prompt = _RESUME_USER_PROMPT.format(resume_text=body.resume_text)

    # First attempt.
    raw = llm_client.generate_text(_SYSTEM_PROMPT, user_prompt)
    result = _validate_resume(raw)

    if result is None:
        # Single retry with corrective instruction.
        raw = llm_client.generate_text(_SYSTEM_PROMPT, _RESUME_RETRY_PROMPT)
        result = _validate_resume(raw)

    if result is None:
        raise internal_error("LLM returned invalid JSON for resume after retry.")

    return result


def _validate_resume(raw: str) -> ResumeJSON | None:
    """Extract JSON from raw LLM text and validate against ResumeJSON.

    Returns the validated model on success, None on any failure.
    """
    try:
        data = extract_json(raw)
        return ResumeJSON.model_validate(data)
    except (ValueError, ValidationError):
        return None


# ---------------------------------------------------------------------------
# JD parsing — Phase 3
# ---------------------------------------------------------------------------

_JD_USER_PROMPT = """\
Extract the job description below into a JSON object that matches this schema exactly:

{{
  "job_title": string,
  "company": string,                  // empty string if not stated
  "location": string,                 // actual location, "remote", or "not_specified"
  "summary": string,
  "required_skills": [string, ...],   // lowercase, deduplicated
  "preferred_skills": [string, ...],  // lowercase, deduplicated
  "minimum_experience_years": integer,// 0 if not specified
  "responsibilities": [string, ...],
  "education_requirements": [string, ...]  // empty list if none
}}

Rules:
- Return JSON only. No markdown. No extra keys. No commentary.
- Normalise all skills to lowercase.

JOB DESCRIPTION TEXT:
{jd_text}
"""

_JD_RETRY_PROMPT = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Return ONLY the corrected JSON object. No markdown. No commentary. No extra keys."
)


@router.post("/parse-jd", response_model=JDJSON)
async def parse_jd(body: ParseJDRequest) -> JDJSON:
    """Parse raw job-description text into a validated JDJSON using the LLM."""
    user_prompt = _JD_USER_PROMPT.format(jd_text=body.job_description_text)

    # First attempt.
    raw = llm_client.generate_text(_SYSTEM_PROMPT, user_prompt)
    result = _validate_jd(raw)

    if result is None:
        # Single retry with corrective instruction.
        raw = llm_client.generate_text(_SYSTEM_PROMPT, _JD_RETRY_PROMPT)
        result = _validate_jd(raw)

    if result is None:
        raise internal_error("LLM returned invalid JSON for job description after retry.")

    return result


def _validate_jd(raw: str) -> JDJSON | None:
    """Extract JSON from raw LLM text and validate against JDJSON.

    Returns the validated model on success, None on any failure.
    """
    try:
        data = extract_json(raw)
        return JDJSON.model_validate(data)
    except (ValueError, ValidationError):
        return None


# ---------------------------------------------------------------------------
# Match — Phase 4 (fixture placeholder)
# ---------------------------------------------------------------------------


@router.post("/match", response_model=MatchReportJSON)
async def match(body: MatchRequest) -> MatchReportJSON:
    """Compare a ResumeJSON against a JDJSON and return a MatchReportJSON.

    Phase 4: deterministic, rule-based scoring. No LLM calls.
    """
    return build_match_report(body.resume, body.job, body.resume_text)


# ---------------------------------------------------------------------------
# Feedback — Phase 5 (placeholder)
# ---------------------------------------------------------------------------


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(body: FeedbackRequest) -> FeedbackResponse:
    """Return LLM-generated improvement suggestions and rewritten resume bullets.

    Phase 5: powered by Anthropic Claude. Retries up to 2 times on bad output.
    """
    return generate_feedback(body.resume, body.job, body.match_report)


# ---------------------------------------------------------------------------
# PDF report export
# ---------------------------------------------------------------------------


@router.post("/report/pdf")
async def report_pdf(body: PdfReportRequest) -> StreamingResponse:
    """Generate and return a PDF match report from the provided analysis data.

    Stateless — receives the full payload, generates PDF, returns it.
    """
    pdf_bytes = generate_pdf_report(body.match_report, body.feedback)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="resume_match_report.pdf"'
        },
    )
