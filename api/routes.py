"""API route definitions for the Resume–Job Matching Agent.

All endpoints currently return example fixtures so the API surface can be
explored and integration-tested before any AI or scoring logic is wired in.
Real LLM parsing and scoring will replace the fixture responses in later phases.
"""

from fastapi import APIRouter

from schemas.models import JDJSON, MatchReportJSON, ResumeJSON

from .request_models import FeedbackRequest, MatchRequest, ParseJDRequest, ParseResumeRequest
from .response_models import FeedbackResponse
from .utils import load_example

router = APIRouter(prefix="/api", tags=["matching"])


@router.post("/parse-resume", response_model=ResumeJSON)
async def parse_resume(body: ParseResumeRequest) -> ResumeJSON:
    """Parse raw resume text into a structured ResumeJSON.

    Placeholder: returns the bundled resume fixture.
    LLM-based parsing will replace this in Phase 3.
    """
    return ResumeJSON(**load_example("resume_example.json"))


@router.post("/parse-jd", response_model=JDJSON)
async def parse_jd(body: ParseJDRequest) -> JDJSON:
    """Parse raw job-description text into a structured JDJSON.

    Placeholder: returns the bundled JD fixture.
    LLM-based parsing will replace this in Phase 3.
    """
    return JDJSON(**load_example("jd_example.json"))


@router.post("/match", response_model=MatchReportJSON)
async def match(body: MatchRequest) -> MatchReportJSON:
    """Compare a ResumeJSON against a JDJSON and return a MatchReportJSON.

    Placeholder: returns the bundled match-report fixture.
    Deterministic scoring logic will replace this in Phase 3.
    """
    return MatchReportJSON(**load_example("match_report_example.json"))


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(body: FeedbackRequest) -> FeedbackResponse:
    """Return improvement suggestions and rewritten resume bullets.

    Placeholder: returns empty lists.
    LLM-driven feedback generation will replace this in Phase 4.
    """
    return FeedbackResponse(suggestions=[], rewritten_bullets=[])
