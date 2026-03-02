"""Smoke test — runs the full Phase 3→4→5 pipeline end-to-end.

Usage:
    python3 scripts/smoke_feedback.py

Requires the server to be running:
    uvicorn main:app --reload
"""

import json
import sys

import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

RESUME_TEXT = (
    "Jane Smith\n"
    "Email: jane@example.com\n"
    "Skills: Python, Docker, Kubernetes, PostgreSQL, REST APIs\n"
    "Experience: 4 years building backend microservices at FinTech Inc.\n"
    "Responsibilities: Designed payment processing services, "
    "maintained CI/CD pipelines, mentored junior engineers.\n"
    "Education: BS Computer Science, State University, 2020."
)

JD_TEXT = (
    "We are hiring a Backend Engineer. "
    "Required skills: Python, Docker, Kubernetes, PostgreSQL, REST APIs. "
    "Preferred: Redis, Go. "
    "Minimum 3 years experience. "
    "Responsibilities: Build scalable payment services, manage CI/CD, mentor junior engineers. "
    "Education: Bachelor's in Computer Science or related field."
)


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"  ERROR {exc.code} on {path}: {body}")
        sys.exit(1)


def main() -> None:
    print("=== Smoke Test: Full Pipeline ===\n")

    print("1. Parsing resume...")
    resume = post("/api/parse-resume", {"resume_text": RESUME_TEXT})
    print(f"   candidate_name : {resume['candidate_name']}")
    print(f"   skills         : {resume['skills']}")

    print("\n2. Parsing job description...")
    job = post("/api/parse-jd", {"job_description_text": JD_TEXT})
    print(f"   job_title      : {job['job_title']}")
    print(f"   required_skills: {job['required_skills']}")

    print("\n3. Running match...")
    match_report = post("/api/match", {
        "resume": resume,
        "job": job,
        "resume_text": RESUME_TEXT,
    })
    print(f"   overall_score  : {match_report['overall_score']}")
    print(f"   matched_skills : {json.dumps(match_report['matched_skills'][:2], indent=6)}")
    print(f"   missing_skills : {json.dumps(match_report['missing_skills'][:2], indent=6)}")

    print("\n4. Generating feedback...")
    feedback = post("/api/feedback", {
        "resume": resume,
        "job": job,
        "match_report": match_report,
    })

    print(f"\n   suggestions ({len(feedback['suggestions'])}):")
    for s in feedback["suggestions"]:
        print(f"     - {s}")

    print(f"\n   rewritten_bullets ({len(feedback['rewritten_bullets'])}):")
    for b in feedback["rewritten_bullets"]:
        print(f"     • {b}")

    # Validate non-empty per spec.
    assert len(feedback["suggestions"]) >= 1, "suggestions must not be empty"
    assert len(feedback["rewritten_bullets"]) >= 1, "rewritten_bullets must not be empty"

    print("\n=== All checks passed ===")


if __name__ == "__main__":
    main()
