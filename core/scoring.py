"""Deterministic scoring engine for the Resume–Job Matching Agent.

All functions are pure and LLM-free.
Given identical inputs, outputs are always identical.

Rubric weights (must sum to 100):
    required_skills   → 35
    experience        → 25
    preferred_skills  → 15
    responsibilities  → 15
    education         → 10
"""

import re
from typing import List, Tuple

from core.evidence import extract_evidence
from schemas.models import ComponentScores, JDJSON, MatchReportJSON, ResumeJSON, SkillEvidence

# ---------------------------------------------------------------------------
# Stop-words excluded from keyword overlap matching.
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "with",
    "on", "at", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "our", "their",
    "this", "that", "it", "its", "we", "you", "they", "as", "up", "into",
    "through", "using", "via", "across", "within", "about",
}


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def normalize_skill(s: str) -> str:
    """Lowercase, strip leading/trailing whitespace, collapse internal spaces."""
    return re.sub(r"\s+", " ", s.lower().strip())


def _words(s: str) -> set:
    """Extract lowercase alphabetic tokens from a string, minus stop-words."""
    return set(re.findall(r"[a-z]+", s.lower())) - _STOP_WORDS


# ---------------------------------------------------------------------------
# Component scoring functions — each returns int 0–100
# ---------------------------------------------------------------------------

def score_required_skills(resume: ResumeJSON, job: JDJSON) -> int:
    """Percentage of JD required skills found in resume skills list.

    Spec rule: if JD has no required skills → 100 (nothing to miss).
    """
    if not job.required_skills:
        return 100

    resume_skills = {normalize_skill(s) for s in resume.skills}
    matched = sum(
        1 for s in job.required_skills if normalize_skill(s) in resume_skills
    )
    return round((matched / len(job.required_skills)) * 100)


def score_preferred_skills(resume: ResumeJSON, job: JDJSON) -> int:
    """Percentage of JD preferred skills found in resume skills list.

    Spec rule: if JD has no preferred skills → 100.
    """
    if not job.preferred_skills:
        return 100

    resume_skills = {normalize_skill(s) for s in resume.skills}
    matched = sum(
        1 for s in job.preferred_skills if normalize_skill(s) in resume_skills
    )
    return round((matched / len(job.preferred_skills)) * 100)


def score_experience_alignment(resume: ResumeJSON, job: JDJSON) -> int:
    """Tiered experience score per spec §5.2.

    Tier table:
        JD minimum == 0                               → 80
        resume years == 0 (unknown), JD minimum > 0  → 20
        resume >= minimum                             → 100
        resume within 1 year below minimum           → 50
        resume more than 1 year below minimum        → 20
    """
    min_yrs = job.minimum_experience_years
    candidate_yrs = resume.total_years_experience

    if min_yrs == 0:
        return 80

    if candidate_yrs == 0:
        return 20

    if candidate_yrs >= min_yrs:
        return 100
    elif (min_yrs - candidate_yrs) <= 1:
        return 50
    else:
        return 20


def score_responsibilities_evidence(resume: ResumeJSON, job: JDJSON) -> int:
    """Keyword-overlap evidence score between JD duties and resume history.

    A JD responsibility is considered evidenced if at least 2 of its
    significant words appear anywhere in the candidate's flattened
    experience responsibilities.

    Spec rules:
        JD has no responsibilities → 50 (neutral)
        Resume has no experience   → 0
    """
    if not job.responsibilities:
        return 50  # Spec §5.3: empty JD responsibilities → neutral

    if not resume.experience:
        return 0   # Spec §5.3: empty resume experience → 0

    # Flatten all resume responsibility text into one word set.
    combined_resume_text = " ".join(
        resp
        for exp in resume.experience
        for resp in exp.responsibilities
    )
    resume_words = _words(combined_resume_text)

    matched = 0
    for jd_resp in job.responsibilities:
        jd_significant_words = _words(jd_resp)
        if len(jd_significant_words & resume_words) >= 2:
            matched += 1

    return round((matched / len(job.responsibilities)) * 100)


def score_education_match(resume: ResumeJSON, job: JDJSON) -> int:
    """Keyword-overlap education score per spec §5.2 tier table.

    Tiers:
        JD has no education requirements → 100
        Resume has no education + JD has requirements → 10
        All requirements keyword-matched → 100
        Some requirements matched → 50
        None matched → 10
    """
    if not job.education_requirements:
        return 100  # Spec §5.3: no JD education requirements → 100

    if not resume.education:
        return 10   # Spec §5.3: empty resume education + JD has requirements → 10

    resume_edu_words = _words(" ".join(e.degree for e in resume.education))

    total_matched = 0
    for req in job.education_requirements:
        req_words = _words(req)
        if not req_words:
            continue
        overlap_ratio = len(req_words & resume_edu_words) / len(req_words)
        if overlap_ratio >= 0.4:  # ≥40% keyword overlap → requirement met
            total_matched += 1

    if total_matched == len(job.education_requirements):
        return 100
    elif total_matched > 0:
        return 50
    else:
        return 10


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def compute_component_scores(resume: ResumeJSON, job: JDJSON) -> ComponentScores:
    """Compute all five component scores and return a ComponentScores object."""
    return ComponentScores(
        required_skills_score=score_required_skills(resume, job),
        preferred_skills_score=score_preferred_skills(resume, job),
        experience_score=score_experience_alignment(resume, job),
        responsibilities_score=score_responsibilities_evidence(resume, job),
        education_score=score_education_match(resume, job),
    )


def compute_overall_score(cs: ComponentScores) -> int:
    """Weighted sum per spec rubric, rounded and clamped to [0, 100].

    Formula:
        overall = round(
            required * 0.35 + preferred * 0.15 +
            experience * 0.25 + responsibilities * 0.15 + education * 0.10
        )
    """
    raw = (
        cs.required_skills_score  * 0.35
        + cs.preferred_skills_score * 0.15
        + cs.experience_score       * 0.25
        + cs.responsibilities_score * 0.15
        + cs.education_score        * 0.10
    )
    return max(0, min(100, round(raw)))


# ---------------------------------------------------------------------------
# Matched / missing skill lists
# ---------------------------------------------------------------------------

def compute_matched_skills(resume: ResumeJSON, job: JDJSON) -> List[str]:
    """JD skills (required + preferred) found in resume skills, order preserved."""
    resume_skills = {normalize_skill(s) for s in resume.skills}
    seen: set = set()
    result: List[str] = []
    for s in job.required_skills + job.preferred_skills:
        norm = normalize_skill(s)
        if norm in resume_skills and norm not in seen:
            result.append(norm)
            seen.add(norm)
    return result


def compute_missing_skills(resume: ResumeJSON, job: JDJSON) -> List[str]:
    """Required JD skills NOT found in resume skills."""
    resume_skills = {normalize_skill(s) for s in resume.skills}
    return [
        normalize_skill(s)
        for s in job.required_skills
        if normalize_skill(s) not in resume_skills
    ]


# ---------------------------------------------------------------------------
# Deterministic narrative generation
# ---------------------------------------------------------------------------

def _build_narrative(
    resume: ResumeJSON,
    job: JDJSON,
    cs: ComponentScores,
    overall: int,
    matched: List[str],
    missing: List[str],
) -> Tuple[List[str], List[str], List[str], str]:
    """Return (strengths, weak_areas, improvement_suggestions, rationale).

    All content is derived purely from component scores and skill lists.
    No randomness; no LLM calls.
    """
    strengths: List[str] = []
    weak_areas: List[str] = []
    suggestions: List[str] = []

    # --- Strengths ---
    if cs.required_skills_score == 100 and job.required_skills:
        strengths.append(
            f"Covers all {len(job.required_skills)} required skill(s): "
            f"{', '.join(normalize_skill(s) for s in job.required_skills)}."
        )
    elif cs.required_skills_score >= 70:
        strengths.append(
            f"Covers {cs.required_skills_score}% of required skills "
            f"({len(matched)} matched)."
        )

    if cs.experience_score >= 80:
        if job.minimum_experience_years == 0:
            strengths.append("Experience requirement is unspecified; candidate has relevant history.")
        else:
            strengths.append(
                f"Has {resume.total_years_experience} year(s) of experience, meeting or exceeding "
                f"the {job.minimum_experience_years}-year minimum."
            )

    if cs.preferred_skills_score >= 60 and job.preferred_skills:
        strengths.append(
            "Demonstrates coverage of multiple preferred/bonus skills from the JD."
        )

    if cs.responsibilities_score >= 60:
        strengths.append(
            "Work history shows evidence of responsibilities aligned with this role."
        )

    if cs.education_score == 100 and job.education_requirements:
        strengths.append("Education meets the requirements stated in the job description.")

    # Spec §5.5: at least 1 strength required.
    if not strengths:
        strengths.append(
            "The candidate shows some foundational alignment with this role."
            if overall >= 40
            else "The candidate has transferable skills that may be developed further."
        )

    # --- Weak areas ---
    if missing:
        weak_areas.append(f"Missing required skill(s): {', '.join(missing)}.")

    if cs.experience_score < 80:
        if resume.total_years_experience == 0:
            weak_areas.append(
                "Total years of experience could not be determined from the resume."
            )
        else:
            gap = job.minimum_experience_years - resume.total_years_experience
            weak_areas.append(
                f"Candidate has {resume.total_years_experience} year(s) of experience; "
                f"role requires {job.minimum_experience_years} (gap: {gap} year(s))."
            )

    if cs.responsibilities_score < 50:
        weak_areas.append(
            "Limited evidence in work history aligning with the JD's stated responsibilities."
        )

    if cs.preferred_skills_score < 50 and job.preferred_skills:
        resume_norm = {normalize_skill(s) for s in resume.skills}
        unmatched_pref = [
            normalize_skill(s)
            for s in job.preferred_skills
            if normalize_skill(s) not in resume_norm
        ]
        if unmatched_pref:
            weak_areas.append(
                f"Missing preferred skill(s): {', '.join(unmatched_pref[:4])}."
            )

    if cs.education_score < 100 and job.education_requirements:
        weak_areas.append(
            "Education listed may not fully satisfy the JD's education requirements."
        )

    # Spec §5.5: at least 1 weak area required.
    if not weak_areas:
        weak_areas.append(
            "Even strong matches benefit from tailoring resume language to "
            "mirror the JD's terminology more closely."
        )

    # --- Suggestions ---
    if missing:
        suggestions.append(
            f"Acquire or highlight experience with: {', '.join(missing[:3])}."
        )

    if cs.experience_score < 80 and resume.total_years_experience < job.minimum_experience_years:
        suggestions.append(
            "Add side projects, freelance work, or open-source contributions to "
            "demonstrate additional hands-on experience."
        )

    if cs.responsibilities_score < 60:
        suggestions.append(
            "Rewrite resume bullets to mirror the language used in the JD's "
            "responsibilities section."
        )

    if cs.preferred_skills_score < 60 and job.preferred_skills:
        suggestions.append(
            "Consider learning or explicitly highlighting experience with "
            "preferred skills to strengthen the application."
        )

    if cs.education_score < 100 and job.education_requirements:
        suggestions.append(
            "If you have relevant coursework or certifications, add them to "
            "strengthen the education section."
        )

    # Spec §5.5: at least 1 suggestion required.
    if not suggestions:
        suggestions.append(
            "Tailor resume bullet points to use keywords directly from the "
            "job description to improve ATS and reviewer alignment."
        )

    # --- Rationale (2–5 sentences, references overall score) ---
    score_label = "strong" if overall >= 75 else "moderate" if overall >= 50 else "weak"
    req_note = (
        "covering all required skills"
        if cs.required_skills_score == 100
        else f"covering {cs.required_skills_score}% of required skills"
    )
    exp_note = (
        "Experience alignment is strong."
        if cs.experience_score >= 80
        else "Experience falls below the minimum requirement."
    )
    missing_note = (
        f"Key gaps include: {', '.join(missing[:3])}." if missing
        else "No required skills are missing."
    )
    rationale = (
        f"{resume.candidate_name} is a {score_label} match for the "
        f"{job.job_title} role with an overall score of {overall}/100, "
        f"{req_note}. "
        f"{exp_note} "
        f"{missing_note} "
        "Addressing the weak areas identified in this report would improve the match score."
    )

    return strengths, weak_areas, suggestions, rationale


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_match_report(
    resume: ResumeJSON, job: JDJSON, resume_text: str = ""
) -> MatchReportJSON:
    """Compute and return a fully populated MatchReportJSON.

    This is the only function callers outside this module need to use.

    Args:
        resume_text: Original plain-text resume for evidence extraction.
                     If empty, evidence lists will be empty.
    """
    cs = compute_component_scores(resume, job)
    overall = compute_overall_score(cs)
    matched = compute_matched_skills(resume, job)
    missing = compute_missing_skills(resume, job)
    strengths, weak_areas, suggestions, rationale = _build_narrative(
        resume, job, cs, overall, matched, missing
    )

    # Extract sentence-level evidence for matched skills.
    all_skills = matched + missing
    evidence_map = extract_evidence(resume_text, all_skills)

    matched_evidence = [
        SkillEvidence(skill=s, evidence=evidence_map.get(s, []))
        for s in matched
    ]
    missing_evidence = [
        SkillEvidence(skill=s, evidence=[])
        for s in missing
    ]

    return MatchReportJSON(
        overall_score=overall,
        component_scores=cs,
        matched_skills=matched_evidence,
        missing_skills=missing_evidence,
        strengths=strengths,
        weak_areas=weak_areas,
        improvement_suggestions=suggestions,
        rationale=rationale,
        resume_name=resume.candidate_name,
        job_title=job.job_title,
    )
