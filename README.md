# Autonomous Resume–Job Matching Agent

A production-structured AI backend that parses resumes and job descriptions,
computes an explainable match score, and generates improvement feedback.

---

## Stack

Python · FastAPI · Pydantic v2 · Anthropic Claude API

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Specification & contracts | ✅ Complete |
| 2 | Backend infrastructure | ✅ Complete |
| 3 | LLM parsing (Anthropic) | ✅ Complete |
| 4 | Deterministic scoring engine | ✅ Complete |
| 5 | Feedback generation layer | ✅ Complete |

---

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

Create a `.env` file in the project root (never commit this file):

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Optional overrides:

```
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=2000
```

### 3. Run the server

```bash
uvicorn main:app --reload
```

### 4. Open Swagger docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| POST | `/api/parse-resume` | Parse raw resume text → ResumeJSON |
| POST | `/api/parse-resume-pdf` | Upload a PDF resume → extract plain text |
| POST | `/api/parse-jd` | Parse raw job description → JDJSON |
| POST | `/api/match` | Match resume vs JD → MatchReportJSON (deterministic, no LLM) |
| POST | `/api/feedback` | LLM-generated suggestions + rewritten resume bullets |

---

## Testing via Swagger (/docs)

**Full pipeline:**

1. `POST /api/parse-resume` → paste plain resume text into `resume_text` → copy the JSON response
2. `POST /api/parse-jd` → paste job description text into `job_description_text` → copy the JSON response
3. `POST /api/match` → body: `{"resume": <step 1 output>, "job": <step 2 output>}` → copy the JSON response
4. `POST /api/feedback` → body:
```json
{
  "resume": <ResumeJSON from step 1>,
  "job": <JDJSON from step 2>,
  "match_report": <MatchReportJSON from step 3>
}
```
Expect HTTP 200 with `suggestions` (5–8 items) and `rewritten_bullets` (3–6 items).

**Smoke test (command line):**
```bash
python3 scripts/smoke_feedback.py
```

**PDF upload test:**
```bash
curl -F "file=@resume.pdf" http://127.0.0.1:8000/api/parse-resume-pdf
```
