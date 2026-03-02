# Autonomous Resume-Job Matching Agent

An AI-powered full-stack application that analyzes how well a resume matches a job description. It computes an explainable weighted match score, highlights skill evidence with sentence-level snippets, and generates actionable feedback with rewritten resume bullets — all in seconds.

**[Live Demo](https://autonomous-resume-job-matching-agen.vercel.app/)**

---

## Features

- **Intelligent Resume Parsing** — Upload a PDF or paste text. The LLM extracts structured data (skills, experience, education, certifications) into a clean JSON schema.
- **Job Description Parsing** — Extracts required/preferred skills, responsibilities, experience requirements, and education from any JD.
- **Deterministic Match Scoring** — A weighted rubric (no LLM randomness) scores 5 components: Required Skills (35%), Experience (25%), Preferred Skills (15%), Responsibilities (15%), Education (10%).
- **Evidence Highlighting** — For every matched skill, the system finds the exact sentences in your resume where that skill appears (up to 2 snippets per skill).
- **Strengths & Gap Analysis** — Surfaces what's strong in your resume and where the gaps are relative to the job requirements.
- **AI Feedback & Rewritten Bullets** — Claude generates 3-6 targeted suggestions and rewrites your resume bullets with stronger action verbs and quantified impact.
- **PDF Report Export** — Download a formatted PDF report with scores, evidence, suggestions, and rewritten bullets.
- **Real-Time Pipeline UI** — Visual step indicator shows progress through parsing, scoring, and feedback generation.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS 4 |
| **Backend** | Python, FastAPI, Pydantic v2 |
| **AI/LLM** | Anthropic Claude API (claude-sonnet-4-6) |
| **PDF Processing** | pypdf + pdfplumber (extraction), reportlab (generation) |
| **Deployment** | Vercel (frontend), Railway (backend) |
| **Containerization** | Docker, Docker Compose, nginx |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│  InputSection → StepIndicator → ScoreCard → Export   │
└──────────────────────┬──────────────────────────────┘
                       │ REST API (axios)
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│                                                      │
│  /api/parse-resume ──→ LLM Parser ──→ ResumeJSON    │
│  /api/parse-jd     ──→ LLM Parser ──→ JDJSON        │
│  /api/match        ──→ Scoring Engine (no LLM)      │
│                        + Evidence Extraction          │
│  /api/feedback     ──→ LLM Feedback ──→ Suggestions │
│  /api/report/pdf   ──→ reportlab   ──→ PDF bytes    │
└─────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Scoring is deterministic** — no LLM calls in the scoring engine. Results are reproducible and fast.
- **Evidence is extracted at the sentence level** using regex with word-boundary support (handles `c++`, `c#`, multi-word skills).
- **Stateless API** — no server-side sessions. PDF reports are generated on-demand from the request payload.
- **Full-stack type safety** — Pydantic models (backend) mirror TypeScript interfaces (frontend).

---

## Project Structure

```
├── api/                    # FastAPI route handlers & request/response models
│   ├── routes.py           # All endpoint definitions
│   ├── request_models.py   # Pydantic request bodies
│   └── response_models.py  # Pydantic response schemas
├── core/                   # Business logic
│   ├── scoring.py          # Deterministic weighted scoring engine
│   ├── feedback.py         # LLM-powered feedback generation
│   ├── evidence.py         # Sentence-level skill evidence extraction
│   ├── report.py           # PDF report generation (reportlab)
│   ├── pdf.py              # PDF text extraction (pypdf + pdfplumber)
│   ├── llm.py              # Anthropic client wrapper
│   ├── llm_json.py         # JSON extraction from LLM output
│   ├── config.py           # Environment & settings management
│   └── errors.py           # Centralized error handling
├── schemas/                # Shared data contracts
│   └── models.py           # ResumeJSON, JDJSON, MatchReportJSON, SkillEvidence, etc.
├── frontend/               # React + TypeScript SPA
│   └── src/
│       ├── pages/Home.tsx           # Main page orchestrating the pipeline
│       ├── components/
│       │   ├── InputSection.tsx     # Resume/JD input + PDF upload
│       │   ├── ScoreCard.tsx        # Score ring + breakdown + skills + evidence
│       │   ├── StepIndicator.tsx    # Pipeline progress indicator
│       │   ├── SuggestionsList.tsx  # AI suggestions display
│       │   └── RewrittenBullets.tsx # Rewritten resume bullets
│       ├── api/client.ts           # API client + pipeline orchestration
│       └── types/api.ts            # TypeScript interfaces (mirrors Pydantic models)
├── examples/               # Sample JSON data for testing
├── scripts/                # Smoke tests & utilities
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Multi-service container orchestration
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container (build → nginx)
├── vercel.json             # Vercel deployment config
├── railway.json            # Railway deployment config
└── Procfile                # Process file for Railway/Heroku
```

---

## API Endpoints

| Method | Path | Description | LLM |
|--------|------|-------------|-----|
| `GET` | `/health` | Liveness check | No |
| `POST` | `/api/parse-resume` | Parse resume text → structured JSON | Yes |
| `POST` | `/api/parse-resume-pdf` | Upload PDF → extract plain text | No |
| `POST` | `/api/parse-jd` | Parse job description → structured JSON | Yes |
| `POST` | `/api/match` | Compute match score + evidence | No |
| `POST` | `/api/feedback` | Generate suggestions + rewritten bullets | Yes |
| `POST` | `/api/report/pdf` | Generate downloadable PDF report | No |

---

## Scoring Rubric

The match score is computed deterministically (no LLM) using a weighted rubric:

| Component | Weight | How it's scored |
|-----------|--------|----------------|
| Required Skills | 35% | % of required skills found in resume |
| Experience | 25% | Tiered scoring based on years vs. requirement |
| Preferred Skills | 15% | % of preferred skills found in resume |
| Responsibilities | 15% | Keyword overlap between JD responsibilities and resume |
| Education | 10% | Keyword overlap with education requirements |

Each component produces a 0-100 score. The overall score is the weighted average.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Docker (both services)

```bash
docker-compose up --build
```

This starts the backend on port `8000` and the frontend on port `3000` with nginx routing.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `APP_ENV` | No | `dev` | `dev` or `prod` |
| `LLM_MODEL` | No | `claude-sonnet-4-6` | Claude model ID |
| `LLM_TEMPERATURE` | No | `0.0` | Sampling temperature |
| `LLM_MAX_TOKENS` | No | `2000` | Max tokens per LLM response |
| `CORS_ORIGINS` | No | `localhost:5173,5174` | Comma-separated allowed origins |
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | Backend URL for frontend |

---

## How It Works

1. **Input** — Paste your resume (or upload a PDF) and a job description.
2. **Parse** — The LLM extracts structured data from both documents in parallel.
3. **Score** — A deterministic engine computes component scores and finds sentence-level evidence for each matched skill.
4. **Feedback** — The LLM generates targeted suggestions and rewrites your weakest resume bullets with stronger phrasing.
5. **Export** — Download a formatted PDF report with everything.

---

## License

MIT
