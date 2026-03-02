"""Pydantic request-body models for the Resume–Job Matching Agent API.

Each model defines the exact payload a caller must provide when hitting an
endpoint.  Contract types (ResumeJSON, JDJSON, MatchReportJSON) are imported
directly from the shared schemas package so the request/response surface stays
in sync with the Phase 1 data contracts at all times.
"""

from pydantic import BaseModel

from api.response_models import FeedbackResponse
from schemas.models import JDJSON, MatchReportJSON, ResumeJSON


class ParseResumeRequest(BaseModel):
    """Payload for POST /api/parse-resume."""

    resume_text: str
    """Raw plain-text content of the candidate's resume."""


class ParseJDRequest(BaseModel):
    """Payload for POST /api/parse-jd."""

    job_description_text: str
    """Raw plain-text content of the job description."""


class MatchRequest(BaseModel):
    """Payload for POST /api/match."""

    resume: ResumeJSON
    """Structured resume produced by the parse-resume step."""

    job: JDJSON
    """Structured job description produced by the parse-jd step."""

    resume_text: str = ""
    """Original plain-text resume for evidence extraction. Optional for backward compatibility."""


class FeedbackRequest(BaseModel):
    """Payload for POST /api/feedback."""

    resume: ResumeJSON
    """Structured resume produced by the parse-resume step."""

    job: JDJSON
    """Structured job description produced by the parse-jd step."""

    match_report: MatchReportJSON
    """Match report produced by the match step."""


class PdfReportRequest(BaseModel):
    """Payload for POST /api/report/pdf."""

    match_report: MatchReportJSON
    """Match report with skill evidence."""

    feedback: FeedbackResponse
    """Feedback with suggestions and rewritten bullets."""
