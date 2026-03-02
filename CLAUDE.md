# Autonomous Resume–Job Matching Agent

Author: Rishigesh Rajendrakumar
Stack: Python, FastAPI, Pydantic, Anthropic Claude API, React, Vite, TailwindCSS

---

# 1. Project Purpose

This project is a production-structured AI full-stack system that:

1. Accepts plain-text resume and job description inputs
2. Converts them into strict structured JSON contracts via LLM parsing
3. Computes a deterministic weighted match score (0–100)
4. Returns an explainable match report
5. Generates structured LLM-powered improvement feedback
6. Displays results in a React frontend with real-time API calls

This is NOT a simple GPT wrapper. The system is intentionally designed with:

- Strict schema enforcement
- Deterministic scoring logic (no LLM in scoring)
- Clear separation of concerns
- Production-style backend + frontend structure

---

# 2. Current Development Status

Phase 1 — Specification & Contracts ✅
- docs/PHASE_1_SPEC.md defines full system behavior
- Strict Pydantic models in schemas/models.py
- Example fixtures in /examples
- Weighted scoring rubric defined

Phase 2 — Backend Infrastructure ✅
- FastAPI app (main.py)
- Typed endpoints in api/routes.py
- Request/response models in api/request_models.py, api/response_models.py
- Centralized error handling (core/errors.py)
- Config management (core/config.py)
- Swagger docs at /docs (disabled in prod)

Phase 3 — LLM Parsing ✅
- Anthropic Claude SDK integrated (core/llm.py)
- JSON extraction helper with markdown fence stripping (core/llm_json.py)
- /api/parse-resume and /api/parse-jd use real LLM parsing
- Strict Pydantic validation with one retry on failure
- ANTHROPIC_API_KEY loaded from .env via pydantic-settings
- Model: claude-sonnet-4-6 (configurable via LLM_MODEL env var)

Phase 4 — Deterministic Scoring Engine ✅
- core/scoring.py implements all 5 component scorers (LLM-free, pure Python)
- build_match_report() is the single public entry point
- /api/match returns real computed MatchReportJSON
- Fixture removed; scores are reproducible: same inputs → same outputs
- Rubric: required(35) + experience(25) + preferred(15) + responsibilities(15) + education(10)

Phase 5 — Feedback Generation Layer ✅
- core/feedback.py implements generate_feedback() using Anthropic Claude
- Prompt enforces: max 6 suggestions, no redundancy, one suggestion per skill gap
- Suggestions follow priority order: required gaps → preferred gaps → experience → phrasing → impact
- Up to 2 retries with stricter prompt on bad JSON output
- /api/feedback returns suggestions (≤6, distinct) and rewritten_bullets (3–6)
- scripts/smoke_feedback.py validates the full pipeline end-to-end

Phase 6 — React Frontend ✅
- Vite + React + TypeScript + TailwindCSS
- src/api/client.ts — Axios, runs full pipeline: parse → match → feedback
- src/types/api.ts — TypeScript types matching all Pydantic models
- src/components/InputSection.tsx — dual textarea + submit button with spinner
- src/components/ScoreCard.tsx — animated SVG score ring, component bars, skill tags
- src/components/SuggestionsList.tsx — numbered, scannable, divider-separated list
- src/components/RewrittenBullets.tsx — card grid with hover effects
- src/pages/Home.tsx — main layout, state management, fade-in results
- Score color thresholds: green ≥80, yellow ≥60, red <60
- VITE_API_BASE_URL configurable via frontend/.env
- Production build: zero TypeScript errors

Phase 7 — Production Deployment Prep ✅
- Dockerfile.backend — Python 3.11-slim, uvicorn
- Dockerfile.frontend — multi-stage Node build → nginx serve
- docker-compose.yml — backend:8000, frontend:3000 (nginx proxies /api/ to backend)
- nginx.conf — SPA routing + /api/ reverse proxy
- .dockerignore — keeps images clean
- core/config.py — ENV and CORS_ORIGINS are env-var driven
- main.py — /docs hidden in prod, static files served from frontend/dist in prod
- ANTHROPIC_API_KEY is server-side only, never exposed to frontend bundle

Phase 8 — PDF Upload ✅
- POST /api/parse-resume-pdf — multipart upload, validates PDF, max 5MB
- core/pdf.py — extract_pdf_text_bytes() using pypdf (primary) + pdfplumber (fallback)
- Frontend: uploadResumePdf() in client.ts, file input in InputSection.tsx
- Auto-analyze checkbox: triggers analysis after PDF extraction if JD is present
- Clear button, filename display, extraction loading state

Phase 9 — Evidence Highlighting ✅
- SkillEvidence model in schemas/models.py (skill + up to 2 evidence snippets)
- matched_skills/missing_skills changed from List[str] to List[SkillEvidence]
- core/evidence.py — extract_evidence() deterministic sentence-level extraction
  - Case-insensitive, word-boundary regex, handles c++/c#, multi-word skills
  - Max 2 snippets per skill, truncated at 200 chars
- MatchRequest accepts optional resume_text for evidence extraction
- Frontend: evidence snippets displayed as bullets under matched skill chips
- Missing skills show "No direct evidence found" italic text
- scripts/test_evidence.py — 8 unit tests for edge cases

Phase 10 — PDF Report Export ✅
- POST /api/report/pdf — stateless, receives match_report + feedback in body
- core/report.py — generate_pdf_report() using reportlab
  - Sections: title, candidate/score, component table, matched skills with evidence, missing skills, suggestions, rewritten bullets
  - Helvetica, white PDF, wrapped text, HRFlowable dividers
- PdfReportRequest model in api/request_models.py
- Frontend: downloadPdfReport() in client.ts (blob download)
- "Download PDF Report" button in Home.tsx — always visible, disabled until analysis runs
  - Tooltip on disabled: "Run analysis first to generate report"
  - Loading spinner during generation, aria-labels for accessibility

---

# 3. Architecture Overview

```
Plain Text Input (resume + JD) or PDF Upload
        ↓
  React Frontend (Vite)
        ↓ HTTP
  FastAPI Backend
        ↓
  LLM Parsing Layer — Anthropic Claude (probabilistic)
        ↓
  Strict JSON Validation — Pydantic (extra="forbid")
        ↓
  Deterministic Scoring Engine — pure Python (reproducible)
  + Evidence Extraction — regex sentence matching (deterministic)
        ↓
  Match Report Output (with skill evidence snippets)
        ↓
  LLM Feedback Agent — Anthropic Claude (structured prompt)
        ↓
  React Results UI + PDF Report Export (reportlab)
```

Key Principle:
Parsing may be probabilistic. Scoring must be deterministic and reproducible.

---

# 4. Core Contracts (Do Not Modify Without Instruction)

Located in: schemas/models.py

Models:
- ExperienceEntry
- EducationEntry
- ResumeJSON
- JDJSON
- SkillEvidence (skill + evidence snippets)
- ComponentScores
- MatchReportJSON (matched_skills/missing_skills are List[SkillEvidence])

Rules:
- snake_case fields only
- extra="forbid"
- No optional fields unless explicitly defined
- All outputs must validate against these schemas

Claude must never loosen schema strictness.

---

# 5. Deterministic Scoring Rubric

Weighted Components:

- Required skills coverage → 35
- Experience alignment → 25
- Preferred skills coverage → 15
- Responsibilities evidence → 15
- Education match → 10

Total = 100

Scoring must:
- Be reproducible
- Be purely rule-based
- Never depend on LLM randomness

LLM must NOT compute the weighted score.

---

# 6. API Endpoints (Current — All Live)

GET  /health                → liveness check, returns env mode
POST /api/parse-resume      → LLM parsing → ResumeJSON
POST /api/parse-jd          → LLM parsing → JDJSON
POST /api/parse-resume-pdf  → PDF text extraction → { resume_text }
POST /api/match             → deterministic scoring → MatchReportJSON (with skill evidence)
POST /api/feedback          → LLM feedback → FeedbackResponse
POST /api/report/pdf        → PDF report generation → StreamingResponse (application/pdf)

Swagger: http://localhost:8000/docs (dev only, disabled in prod)

---

# 7. LLM Integration Rules

Parsing (Phase 3):
- Structured output prompting, pure JSON, no markdown
- Validate immediately with Pydantic
- If validation fails → retry once
- If retry fails → raise standardized 500

Feedback (Phase 5):
- Max 6 suggestions, distinct topics, one per skill gap
- Priority: required gaps → preferred gaps → experience → phrasing → impact
- Up to 2 retries with stricter prompt
- Rewritten bullets: 3–6, strong action verbs, no hallucinated metrics

LLM must never:
- Compute weighted scores
- Modify schema definitions
- Change scoring logic

---

# 8. Directory Structure

```
/
├── api/
│   ├── request_models.py
│   ├── response_models.py
│   ├── routes.py
│   └── utils.py
├── core/
│   ├── config.py          ← ENV, CORS_ORIGINS, LLM settings
│   ├── errors.py          ← standardized HTTP errors
│   ├── evidence.py        ← deterministic skill evidence extraction
│   ├── feedback.py        ← Phase 5 LLM feedback
│   ├── llm.py             ← Anthropic client wrapper
│   ├── llm_json.py        ← JSON extraction from LLM output
│   ├── pdf.py             ← PDF text extraction (pypdf + pdfplumber)
│   ├── report.py          ← PDF report generation (reportlab)
│   └── scoring.py         ← Phase 4 deterministic engine
├── docs/
│   └── PHASE_1_SPEC.md    ← authoritative specification
├── examples/              ← fixture JSON files
├── frontend/
│   ├── src/
│   │   ├── api/client.ts
│   │   ├── components/
│   │   ├── pages/Home.tsx
│   │   └── types/api.ts
│   ├── .env               ← VITE_API_BASE_URL
│   └── vite.config.ts
├── schemas/
│   └── models.py          ← strict Pydantic contracts
├── scripts/
│   ├── smoke_feedback.py  ← end-to-end pipeline test
│   └── test_evidence.py   ← unit tests for evidence extraction
├── .dockerignore
├── .env                   ← ANTHROPIC_API_KEY (never committed)
├── .gitignore
├── CLAUDE.md
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── main.py
├── nginx.conf
├── README.md
└── requirements.txt
```

---

# 9. Environment Variables

Backend (.env):
- ANTHROPIC_API_KEY — required, never expose to frontend
- ENV — "dev" or "prod" (default: dev)
- CORS_ORIGINS — comma-separated allowed origins
- LLM_MODEL — default: claude-sonnet-4-6
- LLM_TEMPERATURE — default: 0.0
- LLM_MAX_TOKENS — default: 2000

Frontend (frontend/.env):
- VITE_API_BASE_URL — backend URL (empty string = same origin in prod)

---

# 10. Running the Project

Dev mode (two terminals):
```
# Terminal 1 — backend
cd <project-root>
uvicorn main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

Docker (full stack):
```
export ANTHROPIC_API_KEY=sk-ant-...
docker compose up --build
# Open http://localhost:3000
```

Smoke test:
```
python3 scripts/smoke_feedback.py
```

Evidence extraction tests (no server needed):
```
python3 scripts/test_evidence.py
```

---

# 11. Coding Standards

- Use Python type hints everywhere
- Keep functions modular and single-purpose
- Avoid global state
- Centralize error handling via core/errors.py
- Keep API layer thin — business logic lives in core/
- Avoid unnecessary abstraction
- Avoid premature optimization
- Avoid architectural changes unless explicitly instructed
- Frontend: typed props on every component, no any

---

# 12. Explicit Non-Goals (v1)

Do NOT implement:
- Embeddings or vector databases
- Semantic search
- Batch comparisons or multi-JD ranking
- Authentication or user accounts
- Database persistence
- Multi-language support

---

# 13. Development Philosophy

This project is portfolio-focused for AI/backend internship roles.

Priorities:
- Reliability
- Schema enforcement
- Guardrails around LLM
- Clean architecture
- Separation of probabilistic and deterministic components

Code clarity > cleverness.
Correctness > feature volume.
Maintainability > complexity.

---

# 14. When Unsure

Claude should:
- Ask before modifying architecture
- Never remove schema strictness
- Never merge scoring into LLM
- Never expand scope without instruction

If unclear, request clarification instead of refactoring.

---

# 15. Session Log

## Session: 2026-03-01
- CLAUDE.md initialized
- Phase 3: LLM parsing — core/llm.py, core/llm_json.py
- Phase 3 debug: fixed model ID (claude-3-5-sonnet → claude-sonnet-4-6), added API error handling
- Phase 4: Deterministic scoring — core/scoring.py, /api/match live
- Phase 5: Feedback generation — core/feedback.py, scripts/smoke_feedback.py
- Phase 5 prompt tuning: output quality pass (concise, action-verb led)
- Phase 5 prompt tuning: non-redundancy pass (max 6, one per skill gap, merged suggestions)
- Phase 6: React frontend — Vite + TypeScript + TailwindCSS, full component set
- Phase 6 UI polish: animated SVG score ring, stagger fade-in, score color thresholds, accessibility
- Phase 7: Production deployment prep — Dockerfiles, docker-compose, nginx, env-driven CORS
- Step indicator (StepIndicator.tsx) added — shows live parse → match → feedback progress
- Phase 8: PDF upload — core/pdf.py, /api/parse-resume-pdf, frontend file input + auto-analyze
- Phase 9: Evidence highlighting — core/evidence.py, SkillEvidence model, frontend evidence display
- Phase 10: PDF report export — core/report.py, POST /api/report/pdf, frontend download button
- PDF download UX: button always visible, disabled until analysis, tooltip + accessibility

---

End of CLAUDE.md
