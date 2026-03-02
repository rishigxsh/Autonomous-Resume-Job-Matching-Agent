"""LLM-powered feedback generator for the Resume–Job Matching Agent.

Responsibilities:
- Build a compact, structured prompt from ResumeJSON + JDJSON + MatchReportJSON.
- Call the LLM and extract a JSON response with keys: suggestions, rewritten_bullets.
- Validate against FeedbackResponse with up to 2 retries.
- Raise a clean 500 on persistent failure.

The scoring logic (core/scoring.py) is never called here.
This module is LLM-only, feedback-only.
"""

import logging
from typing import Optional

from pydantic import ValidationError

from api.response_models import FeedbackResponse
from core.errors import internal_error
from core.llm import llm_client
from core.llm_json import extract_json
from schemas.models import JDJSON, MatchReportJSON, ResumeJSON

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an expert resume coach and technical recruiter. "
    "You give precise, actionable, role-specific feedback. "
    "You always respond with a single valid JSON object — no markdown, "
    "no code fences, no commentary, no extra keys."
)

_FEEDBACK_USER_PROMPT = """\
You are reviewing a candidate's resume against a job description.
Use the match report to understand where the candidate is weak.

=== CANDIDATE SUMMARY ===
Name: {candidate_name}
Skills: {skills}
Total experience: {total_years} year(s)
Education: {education}
Experience highlights:
{responsibilities}

=== JOB DESCRIPTION ===
Role: {job_title} at {company}
Required skills: {required_skills}
Preferred skills: {preferred_skills}
Min experience: {min_exp} year(s)
Key responsibilities: {jd_responsibilities}
Education requirements: {edu_requirements}

=== MATCH REPORT ===
Overall score: {overall_score}/100
Required skills score: {req_score}
Experience score: {exp_score}
Responsibilities score: {resp_score}
Missing required skills: {missing_skills}
Weak areas: {weak_areas}

=== YOUR TASK ===
Return a JSON object with EXACTLY these two keys:

{{
  "suggestions": [...],
  "rewritten_bullets": [...]
}}

SUGGESTIONS — strict rules:

NON-REDUNDANCY (most important rule):
- Every suggestion must address a DISTINCT topic.
- If multiple issues relate to the same skill, merge them into ONE suggestion.
- ONE suggestion per missing skill maximum — never split a single skill gap across two suggestions.
- Scan your list before finalising: if two suggestions share the same subject, delete one and merge the key idea into the other.
- Bad (redundant): "Add Redis to your skills section." + "Mention Redis usage in a project."
- Good (merged): "Add Redis and demonstrate usage in a caching or session-store project."

PRIORITY ORDER — produce suggestions in this order:
1. Required skill gaps (one per missing skill, merged)
2. Preferred skill gaps (one per cluster, merged)
3. Experience alignment (if exp_score < 80)
4. Resume phrasing / responsibilities language
5. Impact quantification

HARD CAP: maximum 6 suggestions total.

FORMAT per suggestion:
- ONE sentence only.
- Maximum 20 words.
- Start with a strong action verb (Add, Quantify, Highlight, Rewrite, Tailor, Demonstrate, etc.).
- No filler: never use "consider", "you may want to", "it would be beneficial", "in order to", "to close the gap".
- No explanations or context. Direct and specific only.

REWRITTEN BULLETS — strict rules:
- 3 to 6 items.
- Each bullet is a maximum of 2 lines.
- Start every bullet with a strong action verb (Built, Designed, Led, Reduced, Implemented, Optimized, Delivered, Architected, etc.).
- Never use weak phrases like "worked on", "responsible for", "assisted with", "helped with".
- Include impact or outcome if it exists in the candidate's resume. Do NOT invent metrics.
- Keep each bullet tight, specific, and ATS-friendly.

OUTPUT FORMAT:
- Return JSON only.
- No markdown fences.
- No commentary.
- No extra keys.
"""

_RETRY_PROMPT = (
    "Your previous response was not valid JSON or was missing required keys. "
    "Return ONLY a JSON object with exactly two keys: "
    "\"suggestions\" (list of 3–6 strings, maximum 6, no two addressing the same topic) and "
    "\"rewritten_bullets\" (list of 3–6 strings). "
    "No markdown. No code fences. No extra keys. No commentary."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MAX_RETRIES = 2


def _build_prompt(
    resume: ResumeJSON,
    job: JDJSON,
    match_report: MatchReportJSON,
) -> str:
    """Build the user prompt from structured inputs."""

    # Flatten resume experience responsibilities (first 6 bullets to stay compact).
    resp_lines = [
        f"  - {r}"
        for exp in resume.experience
        for r in exp.responsibilities
    ][:6]
    responsibilities_text = "\n".join(resp_lines) if resp_lines else "  - (none listed)"

    # Education summary.
    edu_text = (
        ", ".join(f"{e.degree} ({e.institution})" for e in resume.education)
        or "(none listed)"
    )

    return _FEEDBACK_USER_PROMPT.format(
        candidate_name=resume.candidate_name,
        skills=", ".join(resume.skills) or "(none)",
        total_years=resume.total_years_experience,
        education=edu_text,
        responsibilities=responsibilities_text,
        job_title=job.job_title,
        company=job.company or "unknown company",
        required_skills=", ".join(job.required_skills) or "(none)",
        preferred_skills=", ".join(job.preferred_skills) or "(none)",
        min_exp=job.minimum_experience_years,
        jd_responsibilities="; ".join(job.responsibilities) or "(none)",
        edu_requirements=", ".join(job.education_requirements) or "(none)",
        overall_score=match_report.overall_score,
        req_score=match_report.component_scores.required_skills_score,
        exp_score=match_report.component_scores.experience_score,
        resp_score=match_report.component_scores.responsibilities_score,
        missing_skills=", ".join(s.skill for s in match_report.missing_skills) or "none",
        weak_areas="; ".join(match_report.weak_areas),
    )


def _parse_feedback(raw: str) -> Optional[FeedbackResponse]:
    """Extract JSON and validate as FeedbackResponse. Returns None on failure."""
    try:
        data = extract_json(raw)
        return FeedbackResponse.model_validate(data)
    except (ValueError, ValidationError) as exc:
        logger.warning("Feedback validation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_feedback(
    resume: ResumeJSON,
    job: JDJSON,
    match_report: MatchReportJSON,
) -> FeedbackResponse:
    """Generate LLM-powered suggestions and rewritten bullets.

    Retries up to _MAX_RETRIES times with a stricter prompt on failure.

    Raises:
        HTTPException(500): If the LLM returns unusable output after all retries.
    """
    user_prompt = _build_prompt(resume, job, match_report)

    for attempt in range(1, _MAX_RETRIES + 1):
        prompt = user_prompt if attempt == 1 else _RETRY_PROMPT
        raw = llm_client.generate_text(_SYSTEM_PROMPT, prompt)
        logger.debug(
            "Feedback attempt %d — raw output (first 500 chars): %s",
            attempt, raw[:500],
        )
        result = _parse_feedback(raw)
        if result is not None:
            return result
        logger.warning("Feedback attempt %d/%d failed validation.", attempt, _MAX_RETRIES)

    raise internal_error(
        f"LLM returned unusable feedback JSON after {_MAX_RETRIES} attempts."
    )
