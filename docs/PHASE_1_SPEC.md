# Phase 1 Specification — Autonomous Resume–Job Matching Agent

**Version:** 1.0  
**Date:** 2026-02-10  
**Status:** Draft  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Inputs and Assumptions](#2-inputs-and-assumptions)
3. [Data Contracts](#3-data-contracts)
4. [Example JSON Objects](#4-example-json-objects)
5. [Scoring Rubric (v1)](#5-scoring-rubric-v1)
6. [Non-Goals for v1](#6-non-goals-for-v1)

---

## 1. Project Overview

### What It Does

The Autonomous Resume–Job Matching Agent accepts two plain-text inputs — a candidate resume and a job description — and produces an explainable match report. The system:

1. **Parses** each input into a structured JSON representation using LLM APIs (no model training).
2. **Compares** the structured resume against the structured job description using a deterministic, weighted scoring rubric.
3. **Generates** a match report containing a numerical score (0–100), lists of matched and missing skills, strengths, weak areas, and a short human-readable rationale with actionable improvement suggestions.

### What It Does NOT Do (v1)

- Does not train, fine-tune, or host any machine-learning models.
- Does not provide a user interface or web frontend.
- Does not simulate Applicant Tracking Systems (ATS).
- Does not support batch or multi-JD comparisons in a single run.
- Does not use vector embeddings or semantic similarity search.
- Does not persist data to a database.
- Does not handle file uploads (PDF, DOCX); inputs are plain text only.

---

## 2. Inputs and Assumptions

### Inputs

| Input               | Type   | Description                                          |
|---------------------|--------|------------------------------------------------------|
| `resume_text`       | string | The full plain-text content of a candidate's resume. |
| `job_description_text` | string | The full plain-text content of a single job posting. |

### Assumptions

1. **Language:** Both inputs are in English.
2. **Encoding:** UTF-8 plain text. No markup, HTML, or binary content.
3. **Length:** Each input is between 100 and 15,000 characters. Inputs outside this range are rejected before processing.
4. **Content quality:** Inputs are assumed to be real-world resumes and job descriptions, not adversarial or nonsensical text. The system does not validate truthfulness.
5. **Single candidate, single job:** Each invocation compares exactly one resume against exactly one job description.
6. **LLM availability:** An external LLM API (e.g., OpenAI GPT-4 class) is available and reachable at runtime for parsing inputs into structured JSON.
7. **Determinism:** Given identical inputs and identical LLM responses, the scoring rubric produces identical output. The LLM parsing step may introduce variance, but the scoring logic itself is deterministic.

---

## 3. Data Contracts

All field names use `snake_case`. All schemas are strict — every field is **required** unless explicitly noted. No additional properties are allowed.

---

### 3.1 ResumeJSON Schema

Structured representation of a parsed candidate resume.

| Field                      | Type                        | Description                                                                                              |
|----------------------------|-----------------------------|----------------------------------------------------------------------------------------------------------|
| `candidate_name`           | string                      | Full name of the candidate.                                                                              |
| `email`                    | string                      | Contact email address. Empty string `""` if not found.                                                   |
| `phone`                    | string                      | Contact phone number. Empty string `""` if not found.                                                    |
| `summary`                  | string                      | Professional summary or objective statement extracted from the resume. Empty string `""` if not present.  |
| `skills`                   | array of string             | Flat list of distinct technical and professional skills mentioned in the resume. Normalized to lowercase. |
| `experience`               | array of ExperienceEntry    | Work experience entries, ordered from most recent to oldest.                                             |
| `education`                | array of EducationEntry     | Education entries, ordered from most recent to oldest.                                                   |
| `certifications`           | array of string             | List of certifications or licenses mentioned. Empty array `[]` if none.                                  |
| `total_years_experience`   | number                      | Estimated total years of professional experience. `0` if not determinable.                               |

#### ExperienceEntry

| Field              | Type            | Description                                                                                       |
|--------------------|-----------------|---------------------------------------------------------------------------------------------------|
| `job_title`        | string          | Title held in this position.                                                                      |
| `company`          | string          | Name of the employer.                                                                             |
| `start_date`       | string          | Start date in `"YYYY-MM"` format. `"unknown"` if not determinable.                               |
| `end_date`         | string          | End date in `"YYYY-MM"` format, or `"present"` if current role. `"unknown"` if not determinable.  |
| `responsibilities` | array of string | Key responsibilities and accomplishments described for this role. At least one entry expected.     |

#### EducationEntry

| Field        | Type   | Description                                                              |
|--------------|--------|--------------------------------------------------------------------------|
| `degree`     | string | Degree obtained (e.g., "Bachelor of Science in Computer Science").        |
| `institution`| string | Name of the educational institution.                                      |
| `end_date`   | string | Graduation date in `"YYYY-MM"` format. `"unknown"` if not determinable.  |

---

### 3.2 JDJSON Schema

Structured representation of a parsed job description.

| Field                    | Type                          | Description                                                                                          |
|--------------------------|-------------------------------|------------------------------------------------------------------------------------------------------|
| `job_title`              | string                        | Title of the open position.                                                                          |
| `company`                | string                        | Name of the hiring company. Empty string `""` if not stated.                                         |
| `location`               | string                        | Job location or `"remote"` or `"not_specified"`.                                                     |
| `summary`                | string                        | Brief summary of the role and its purpose.                                                           |
| `required_skills`        | array of string               | Skills explicitly marked as required. Normalized to lowercase.                                       |
| `preferred_skills`       | array of string               | Skills listed as preferred, nice-to-have, or bonus. Normalized to lowercase.                         |
| `minimum_experience_years` | number                      | Minimum years of experience required. `0` if not specified.                                          |
| `responsibilities`       | array of string               | Key responsibilities and duties of the role.                                                         |
| `education_requirements` | array of string               | Required or preferred degrees/certifications (e.g., "Bachelor's in Computer Science"). Empty array `[]` if none stated. |

---

### 3.3 MatchReportJSON Schema

The output produced after comparing a ResumeJSON against a JDJSON.

| Field                          | Type                          | Description                                                                                                 |
|--------------------------------|-------------------------------|-------------------------------------------------------------------------------------------------------------|
| `overall_score`                | number                        | Final weighted match score, integer from 0 to 100 inclusive.                                                |
| `component_scores`             | ComponentScores               | Breakdown of the score by rubric category.                                                                  |
| `matched_skills`               | array of string               | Skills from the JD (required + preferred) that were found in the resume. Lowercase.                         |
| `missing_skills`               | array of string               | Required skills from the JD that were NOT found in the resume. Lowercase.                                   |
| `strengths`                    | array of string               | Human-readable bullet points highlighting the candidate's strongest alignments with the JD.                 |
| `weak_areas`                   | array of string               | Human-readable bullet points highlighting gaps or misalignments with the JD.                                |
| `improvement_suggestions`      | array of string               | Actionable recommendations for the candidate to improve their match for this role.                          |
| `rationale`                    | string                        | A short paragraph (2–5 sentences) explaining the overall score in plain language.                           |
| `resume_name`                  | string                        | `candidate_name` from the ResumeJSON, echoed for traceability.                                              |
| `job_title`                    | string                        | `job_title` from the JDJSON, echoed for traceability.                                                       |

#### ComponentScores

| Field                          | Type   | Description                                                                                    |
|--------------------------------|--------|------------------------------------------------------------------------------------------------|
| `required_skills_score`        | number | Score (0–100) for coverage of required skills.                                                 |
| `preferred_skills_score`       | number | Score (0–100) for coverage of preferred skills.                                                |
| `experience_score`             | number | Score (0–100) for alignment of years and relevance of experience.                              |
| `responsibilities_score`       | number | Score (0–100) for evidence that past responsibilities align with JD responsibilities.          |
| `education_score`              | number | Score (0–100) for match of education against JD education requirements.                        |

---

## 4. Example JSON Objects

### 4.1 Example ResumeJSON

```json
{
  "candidate_name": "Priya Sharma",
  "email": "priya.sharma@email.com",
  "phone": "+1-555-204-8831",
  "summary": "Backend engineer with 6 years of experience building scalable microservices in Python and Go. Passionate about clean architecture and observability.",
  "skills": [
    "python",
    "go",
    "postgresql",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "terraform",
    "ci/cd",
    "rest apis",
    "grpc",
    "prometheus",
    "grafana"
  ],
  "experience": [
    {
      "job_title": "Senior Backend Engineer",
      "company": "Cloudtask Inc.",
      "start_date": "2022-03",
      "end_date": "present",
      "responsibilities": [
        "Designed and maintained 12 microservices handling 50k requests per second.",
        "Led migration from monolith to event-driven architecture using Kafka.",
        "Reduced P99 API latency by 40% through caching and query optimization."
      ]
    },
    {
      "job_title": "Backend Developer",
      "company": "DataNova",
      "start_date": "2019-06",
      "end_date": "2022-02",
      "responsibilities": [
        "Built RESTful APIs in Python (FastAPI) serving a B2B analytics platform.",
        "Implemented CI/CD pipelines with GitHub Actions and Docker.",
        "Wrote integration and load tests; improved test coverage from 45% to 88%."
      ]
    }
  ],
  "education": [
    {
      "degree": "Bachelor of Technology in Computer Science",
      "institution": "Indian Institute of Technology, Hyderabad",
      "end_date": "2019-05"
    }
  ],
  "certifications": [
    "AWS Certified Solutions Architect – Associate"
  ],
  "total_years_experience": 6
}
```

### 4.2 Example JDJSON

```json
{
  "job_title": "Senior Backend Engineer",
  "company": "Finova Technologies",
  "location": "New York, NY (Hybrid)",
  "summary": "We are looking for a Senior Backend Engineer to design, build, and scale our core payment processing services. You will work closely with product and infrastructure teams to deliver reliable, low-latency systems.",
  "required_skills": [
    "python",
    "postgresql",
    "docker",
    "kubernetes",
    "rest apis",
    "aws"
  ],
  "preferred_skills": [
    "go",
    "kafka",
    "terraform",
    "grpc",
    "redis"
  ],
  "minimum_experience_years": 5,
  "responsibilities": [
    "Design and implement scalable backend services for payment processing.",
    "Collaborate with DevOps to manage CI/CD pipelines and infrastructure-as-code.",
    "Monitor system health using observability tools and maintain SLA targets.",
    "Mentor junior engineers through code reviews and design discussions."
  ],
  "education_requirements": [
    "Bachelor's degree in Computer Science or related field"
  ]
}
```

### 4.3 Example MatchReportJSON

```json
{
  "overall_score": 82,
  "component_scores": {
    "required_skills_score": 100,
    "preferred_skills_score": 80,
    "experience_score": 90,
    "responsibilities_score": 70,
    "education_score": 100
  },
  "matched_skills": [
    "python",
    "postgresql",
    "docker",
    "kubernetes",
    "rest apis",
    "aws",
    "go",
    "terraform",
    "grpc",
    "redis"
  ],
  "missing_skills": [],
  "strengths": [
    "Covers all 6 required skills listed in the job description.",
    "Has 6 years of experience, exceeding the 5-year minimum requirement.",
    "Demonstrated experience with microservices architecture and high-throughput systems directly relevant to payment processing.",
    "Holds an AWS certification aligning with the cloud infrastructure needs."
  ],
  "weak_areas": [
    "No direct experience in payment processing or financial services domain.",
    "Resume does not mention mentoring or leadership activities despite the JD requiring mentoring of junior engineers.",
    "Kafka is listed as preferred and appears in experience context but not in the explicit skills list — match was inferred from responsibilities."
  ],
  "improvement_suggestions": [
    "Add a bullet point about mentoring or leading junior team members if applicable.",
    "Highlight any experience with financial systems, compliance, or transaction processing.",
    "Explicitly list Kafka in the skills section since it appears in your work history."
  ],
  "rationale": "Priya is a strong technical match for this role, covering all required skills and most preferred skills. Her 6 years of backend experience with microservices at scale aligns well with the JD's demands. The main gaps are the absence of domain experience in financial services and no explicit mention of mentoring activities, which the role calls for. Addressing these gaps in the resume would strengthen the application.",
  "resume_name": "Priya Sharma",
  "job_title": "Senior Backend Engineer"
}
```

---

## 5. Scoring Rubric (v1)

### 5.1 Score Components and Default Weights

The overall score is a weighted sum of five component scores. Each component is scored independently on a 0–100 scale, then combined using the weights below.

| Component                  | Weight | Description                                                                                     |
|----------------------------|--------|-------------------------------------------------------------------------------------------------|
| `required_skills_score`    | 35     | Percentage of JD required skills found in the resume skills list.                               |
| `preferred_skills_score`   | 15     | Percentage of JD preferred skills found in the resume skills list.                              |
| `experience_score`         | 25     | How well the candidate's total years and relevance of experience match the JD requirements.     |
| `responsibilities_score`   | 15     | Degree of overlap between the candidate's past responsibilities and the JD's listed duties.     |
| `education_score`          | 10     | Whether the candidate's education meets the JD's education requirements.                        |
| **Total**                  | **100**|                                                                                                 |

**Formula:**

```
overall_score = round(
    (required_skills_score    * 0.35) +
    (preferred_skills_score   * 0.15) +
    (experience_score         * 0.25) +
    (responsibilities_score   * 0.15) +
    (education_score          * 0.10)
)
```

The result is clamped to the integer range [0, 100].

### 5.2 Component Scoring Rules

#### Required Skills Score (weight: 35)

```
required_skills_score = (number of matched required skills / total required skills) * 100
```

- Matching is case-insensitive, exact string match after lowercase normalization.
- If the JD lists zero required skills, this component scores 100 (no requirements to miss).

#### Preferred Skills Score (weight: 15)

```
preferred_skills_score = (number of matched preferred skills / total preferred skills) * 100
```

- Same matching rules as required skills.
- If the JD lists zero preferred skills, this component scores 100.

#### Experience Score (weight: 25)

| Condition                                                    | Score |
|--------------------------------------------------------------|-------|
| Candidate years >= JD minimum and relevant experience found  | 100   |
| Candidate years >= JD minimum but low relevance              | 70    |
| Candidate years within 1 year below JD minimum               | 50    |
| Candidate years more than 1 year below JD minimum            | 20    |
| JD minimum is 0 (not specified)                              | 80    |

- "Relevant experience" is determined by checking if any `experience[].responsibilities` entries semantically relate to the JD responsibilities. This assessment is performed by the LLM during the comparison step.

#### Responsibilities Score (weight: 15)

```
responsibilities_score = (number of JD responsibilities with evidence / total JD responsibilities) * 100
```

- For each JD responsibility, the system checks whether the candidate's combined experience responsibilities provide evidence of capability. This is a binary yes/no per JD responsibility, assessed by the LLM.
- If the JD lists zero responsibilities, this component scores 50 (neutral).

#### Education Score (weight: 10)

| Condition                                              | Score |
|--------------------------------------------------------|-------|
| Candidate education meets or exceeds JD requirements   | 100   |
| Candidate education partially meets JD requirements    | 50    |
| Candidate education does not meet JD requirements      | 10    |
| JD has no education requirements                       | 100   |

- "Meets" means the candidate holds a degree at or above the requested level in a relevant field.
- "Partially meets" means the candidate has a degree but in a different field, or at a lower level.

### 5.3 Handling Missing Sections

| Scenario                                   | Behavior                                                                                              |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------|
| Resume has empty `skills` array            | All required and preferred skills are treated as missing. Skill scores become 0.                      |
| Resume has empty `experience` array        | `experience_score` = 10. `responsibilities_score` = 0.                                                |
| Resume has empty `education` array         | If JD has education requirements, `education_score` = 10. If JD has none, `education_score` = 100.    |
| JD has empty `required_skills` array       | `required_skills_score` = 100 (nothing to miss).                                                      |
| JD has empty `preferred_skills` array      | `preferred_skills_score` = 100 (nothing to miss).                                                     |
| JD has empty `responsibilities` array      | `responsibilities_score` = 50 (neutral).                                                              |
| JD has empty `education_requirements`      | `education_score` = 100 (nothing to miss).                                                            |
| Resume `total_years_experience` is 0       | Treated as unknown experience; `experience_score` = 20 unless JD minimum is also 0 (then score = 80).|

### 5.4 Handling Ambiguous Matches

- **Skill synonyms:** In v1, skill matching is strict lowercase string equality. Synonyms (e.g., "js" vs "javascript") are NOT automatically resolved. The LLM is instructed during parsing to normalize common aliases to canonical forms (a normalization guide will be provided in Phase 2).
- **Partial experience overlap:** If a candidate's responsibility partially relates to a JD responsibility, the LLM must make a binary call (match or no match). No partial credit per responsibility.
- **Conflicting information:** If the resume contains contradictory dates or claims, the system uses the most recent or most favorable interpretation and flags the conflict in `weak_areas`.

### 5.5 Required Output Fields

Every MatchReportJSON must contain all of the following populated arrays/fields:

| Field                      | Minimum Entries | Notes                                                        |
|----------------------------|-----------------|--------------------------------------------------------------|
| `matched_skills`           | 0               | May be empty if no skills matched.                           |
| `missing_skills`           | 0               | May be empty if all required skills matched.                 |
| `strengths`                | 1               | At least one strength must be identified, even for low scores.|
| `weak_areas`               | 1               | At least one weak area must be identified, even for high scores.|
| `improvement_suggestions`  | 1               | At least one actionable suggestion must be provided.         |
| `rationale`                | —               | Must be 2–5 sentences. Must reference the overall score.     |

---

## 6. Non-Goals for v1

The following are explicitly out of scope for version 1 of this system:

| Non-Goal                            | Reason                                                                                      |
|-------------------------------------|---------------------------------------------------------------------------------------------|
| ATS simulation or keyword stuffing  | v1 focuses on genuine skill matching, not gaming ATS parsers.                               |
| Vector embeddings / semantic search | v1 uses LLM-based parsing and deterministic scoring, not embedding similarity.              |
| Multi-JD comparison                 | v1 compares one resume against one JD per invocation. Batch comparison is a future feature. |
| Model fine-tuning                   | v1 relies on general-purpose LLM APIs with prompt engineering only.                         |
| File upload / parsing (PDF, DOCX)   | v1 accepts plain text only. Document parsing is a future integration.                       |
| User accounts or authentication     | No user management in v1.                                                                   |
| Data persistence or history         | v1 is stateless. No database, no run history.                                               |
| Multi-language support              | v1 supports English-only inputs.                                                            |
| Salary or compensation analysis     | Out of scope for match scoring.                                                             |
| Cultural fit or soft-skill scoring  | v1 scores only on explicit skills, experience, responsibilities, and education.             |
| Confidence intervals or uncertainty | v1 produces a single deterministic score, not a range.                                      |

---

*End of Phase 1 Specification.*
