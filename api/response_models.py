"""Pydantic response-body models for the Resume–Job Matching Agent API.

Separating response models from request models keeps each concern in its own
file and makes future additions easier to locate.
"""

from typing import List

from pydantic import BaseModel


class FeedbackResponse(BaseModel):
    """Response body for POST /api/feedback."""

    suggestions: List[str]
    """Actionable recommendations to improve the resume for this role."""

    rewritten_bullets: List[str]
    """LLM-rewritten resume bullet points (populated in Phase 4)."""
