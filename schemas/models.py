"""Pydantic models defining the data contracts for the Resume–Job Matching Agent.

Every model here mirrors the schemas documented in docs/PHASE_1_SPEC.md.
All fields are required. Field names use snake_case. No additional properties
are allowed (model_config forbids extras).
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Resume sub-models
# ---------------------------------------------------------------------------


class ExperienceEntry(BaseModel):
    """A single work-experience block from a candidate's resume."""

    model_config = {"extra": "forbid"}

    job_title: str
    """Title held in this position."""

    company: str
    """Name of the employer."""

    start_date: str
    """Start date in YYYY-MM format. 'unknown' if not determinable."""

    end_date: str
    """End date in YYYY-MM format, 'present' if current, or 'unknown'."""

    responsibilities: List[str]
    """Key responsibilities and accomplishments for this role."""


class EducationEntry(BaseModel):
    """A single education block from a candidate's resume."""

    model_config = {"extra": "forbid"}

    degree: str
    """Degree obtained (e.g. 'Bachelor of Science in Computer Science')."""

    institution: str
    """Name of the educational institution."""

    end_date: str
    """Graduation date in YYYY-MM format. 'unknown' if not determinable."""


# ---------------------------------------------------------------------------
# Top-level schemas
# ---------------------------------------------------------------------------


class ResumeJSON(BaseModel):
    """Structured representation of a parsed candidate resume.

    Produced by the LLM parsing step from raw resume text.
    """

    model_config = {"extra": "forbid"}

    candidate_name: str
    """Full name of the candidate."""

    email: str
    """Contact email address. Empty string if not found."""

    phone: str
    """Contact phone number. Empty string if not found."""

    summary: str
    """Professional summary or objective statement. Empty string if absent."""

    skills: List[str]
    """Distinct technical and professional skills, normalized to lowercase."""

    experience: List[ExperienceEntry]
    """Work experience entries ordered from most recent to oldest."""

    education: List[EducationEntry]
    """Education entries ordered from most recent to oldest."""

    certifications: List[str]
    """Certifications or licenses mentioned. Empty list if none."""

    total_years_experience: int
    """Estimated total years of professional experience. 0 if unknown."""


class JDJSON(BaseModel):
    """Structured representation of a parsed job description.

    Produced by the LLM parsing step from raw job-description text.
    """

    model_config = {"extra": "forbid"}

    job_title: str
    """Title of the open position."""

    company: str
    """Hiring company name. Empty string if not stated."""

    location: str
    """Job location, 'remote', or 'not_specified'."""

    summary: str
    """Brief summary of the role and its purpose."""

    required_skills: List[str]
    """Skills explicitly marked as required. Normalized to lowercase."""

    preferred_skills: List[str]
    """Skills listed as preferred / nice-to-have. Normalized to lowercase."""

    minimum_experience_years: int
    """Minimum years of experience required. 0 if not specified."""

    responsibilities: List[str]
    """Key responsibilities and duties of the role."""

    education_requirements: List[str]
    """Required or preferred degrees/certifications. Empty list if none."""


# ---------------------------------------------------------------------------
# Match report sub-model
# ---------------------------------------------------------------------------


class ComponentScores(BaseModel):
    """Breakdown of the match score by rubric category (each 0–100)."""

    model_config = {"extra": "forbid"}

    required_skills_score: int
    """Score for coverage of required skills."""

    preferred_skills_score: int
    """Score for coverage of preferred skills."""

    experience_score: int
    """Score for alignment of years and relevance of experience."""

    responsibilities_score: int
    """Score for evidence that past work aligns with JD duties."""

    education_score: int
    """Score for match of education against JD requirements."""


# ---------------------------------------------------------------------------
# Match report top-level
# ---------------------------------------------------------------------------


class MatchReportJSON(BaseModel):
    """Output produced after comparing a ResumeJSON against a JDJSON.

    Contains the overall score, component breakdown, skill lists,
    qualitative feedback, and a human-readable rationale.
    """

    model_config = {"extra": "forbid"}

    overall_score: int
    """Final weighted match score, integer 0–100 inclusive."""

    component_scores: ComponentScores
    """Per-category score breakdown."""

    matched_skills: List[str]
    """JD skills (required + preferred) found in the resume. Lowercase."""

    missing_skills: List[str]
    """Required JD skills NOT found in the resume. Lowercase."""

    strengths: List[str]
    """Bullet points highlighting the candidate's strongest alignments."""

    weak_areas: List[str]
    """Bullet points highlighting gaps or misalignments with the JD."""

    improvement_suggestions: List[str]
    """Actionable recommendations to improve the candidate's match."""

    rationale: str
    """Short paragraph (2–5 sentences) explaining the overall score."""

    resume_name: str
    """candidate_name echoed from the ResumeJSON for traceability."""

    job_title: str
    """job_title echoed from the JDJSON for traceability."""
