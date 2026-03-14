# RecruitIQ

An end-to-end AI hiring pipeline built with CrewAI, Groq, Supabase, and Streamlit. Takes a job description and produces a ranked shortlist, interview kits, evaluation reports, and offer letters — fully automated.

Live demo: [recruitiq-com.streamlit.app](https://recruitiq-com.streamlit.app)

---

## Why I built this

Hiring is broken in most companies. Recruiters spend 80% of their time on tasks that should take minutes — reading resumes, writing interview questions, formatting offer letters. The actual thinking — who is the right person, why, and what do we do next — gets rushed.

I wanted to build something that flips that ratio. The AI handles the repetitive parts. The recruiter focuses on the human judgment that actually matters.

RecruitIQ is the result. It's a 5-phase hiring pipeline where each phase is run by a dedicated CrewAI crew. You paste a job description at one end. You get a signed offer letter at the other.

---

## What it actually does

### Phase 1 — JD Intake
Paste any job description. Three agents work sequentially:
- Parses the raw text into structured JSON (title, level, location, responsibilities, qualifications)
- Extracts a skills taxonomy — separates must-haves from nice-to-haves, assigns importance weights, flags deal-breakers
- Audits the JD for biased language — gender-coded words, age bias, credential inflation — and suggests inclusive rewrites with a 0–10 inclusivity score

### Phase 2 — Resume Screening
Upload PDFs or DOCX files in bulk. For each resume:
- Extracts raw text using PyMuPDF (no external OCR service, runs locally)
- Runs a semantic similarity score against the JD using sentence-transformers locally (no API cost)
- Runs a deep AI screening via CrewAI — section-by-section scoring, green flags, red flags, keyword hit/gap analysis
- Ranks all candidates by AI match score with shortlist/hold/reject recommendation

### Phase 3 — Interview Prep
Select any screened candidate. Generates a complete interview kit tailored to their background and the role:
- Technical questions (role-specific, not generic)
- Behavioral questions in STAR format
- Situational and culture-fit questions
- Probing questions targeting specific gaps found in the resume
- A 1/3/5-star scoring rubric per question so any interviewer can score consistently

### Phase 4 — Evaluation
After the interview, paste your notes or transcript. The evaluation crew:
- Scores the candidate across competency dimensions
- Gives a hire/no-hire recommendation with justification
- Generates a reference check guide — claims to verify, targeted questions, call script

### Phase 5 — Offer Generator
Generates the full hiring package:
- Market salary benchmarks (P25/P50/P75/P90) for the role and location
- A personalized offer letter — not a template, actually written for this candidate
- A negotiation playbook — expected counter-offers, non-salary levers, walk-away point, closing scripts

---

## Additional features

**Candidate Comparison Dashboard** — Select 2 or 3 candidates, get a radar chart across 5 dimensions, score breakdown bars, head-to-head profile cards, and an AI recommendation with confidence level and medal ranking.

**Pipeline Kanban Board** — Visual hiring board with 6 stages (Applied → Screened → Interview → Offer → Hired → Rejected). Auto-populates from screening results. Drag candidates between stages. Shows funnel drop-off rates.

**PDF Report Export** — One-click professional PDF per candidate. Dark-themed, includes score cards, recommendation banner, skills table, keyword analysis, screening flags. Bulk export as ZIP. Shortlisted-only export.

**AI Interview Scorecard** — Live scoring tool for use during the interview. Six weighted competency sliders, real-time score calculation, open notes fields. One click generates AI final verdict with confidence level and decisive factor.

**Red Flag Explainer** — Deep-dive analysis on any candidate. Four modes: full red flag analysis, score gap analysis, skills mismatch breakdown, credibility check. Each flag shown with the specific resume evidence and score impact. Generates targeted interview questions to probe each concern.

**Hiring Analytics Dashboard** — Score distribution histogram, recommendation split, AI vs semantic score comparison, pipeline funnel visualization, top candidates leaderboard, auto-generated pipeline insights.

---

## Tech stack

Everything here is either open-source or has a free tier. Monthly cost: $0.

| Layer | Technology | Why |
|---|---|---|
| Agent framework | CrewAI | Best multi-agent orchestration in Python right now. Sequential crews, task chaining, clean abstractions. |
| LLM | Groq (LLaMA 3.3 70B) | Fastest inference available. 14,400 free requests/day. Falls back to Gemini 2.0 Flash. |
| Embeddings | sentence-transformers (BAAI/bge-small) | Runs on CPU locally. Zero API cost. Good enough for semantic resume-JD matching. |
| Vector DB | ChromaDB | In-memory, no setup, no external service. |
| Database | Supabase (PostgreSQL) | Free tier, 500MB, built-in auth and file storage. Stores every JD, candidate, kit, and offer. |
| Resume parsing | PyMuPDF | Handles PDFs cleanly without external services. python-docx for DOCX. |
| PDF generation | ReportLab | Full control over layout. Generates the candidate report PDFs. |
| Frontend | Streamlit | Right tool for an AI-heavy app — fast to iterate, no separate frontend/backend complexity. |
| Hosting | Streamlit Community Cloud | Free, deploys directly from GitHub, no server management. |

---

## Architecture

```
recruitiq/
├── app.py                          # Dashboard entry point
├── config.py                       # LLM setup, st.secrets integration
├── requirements.txt
│
├── agents/
│   ├── agents.py                   # 12 CrewAI agents (lazy-loaded for Streamlit compatibility)
│   └── tasks.py                    # Task definitions — one per agent action
│
├── crews/
│   └── crews.py                    # 5 crew orchestrators
│
├── utils/
│   ├── styles.py                   # Shared CSS + UI helper functions
│   ├── execution_log.py            # Terminal-style live execution log component
│   ├── resume_parser.py            # PDF/DOCX text extraction
│   ├── vector_store.py             # ChromaDB + sentence-transformers
│   ├── database.py                 # Supabase helpers + schema
│   └── pdf_report.py               # ReportLab PDF generation
│
└── pages/
    ├── 1_JD_Intake.py
    ├── 2_Resume_Screening.py
    ├── 3_Interview_Prep.py
    ├── 4_Evaluation.py
    ├── 5_Offer_Generator.py
    ├── 6_Compare_Candidates.py
    ├── 7_Pipeline_Board.py
    ├── 8_PDF_Export.py
    ├── 9_Interview_Scorecard.py
    ├── 10_Red_Flag_Explainer.py
    └── 11_Analytics.py
```

**12 agents across 5 crews:**

| Crew | Agents |
|---|---|
| JD Intake | JD Parser, Skills Extractor, Bias Checker |
| Resume Screening | Resume Screener, Skills Matcher |
| Interview Prep | Question Generator, Rubric Builder |
| Evaluation | Interview Analyst, Reference Checker |
| Offer Generation | Salary Benchmarker, Offer Drafter, Negotiation Advisor |

One design decision worth noting: all agents are lazy-loaded inside getter functions rather than instantiated at module level. This is necessary because Streamlit loads page modules before `st.secrets` is available — if you create agents at module level, the LLM initialization runs before your API keys are accessible and the whole app crashes. Wrapping each agent in `get_*_agent()` defers initialization to call time, when secrets are already loaded.

---

## Setup

### Clone and configure

```bash
git clone https://github.com/sihabsafincom/recruitiq.git
cd recruitiq
```

### Get API keys (all free)

| Service | URL | What you need |
|---|---|---|
| Groq | console.groq.com | API key — free, 14,400 req/day |
| Supabase | supabase.com | Project URL + anon key |
| Serper | serper.dev | API key — free, 2,500 searches/month |

### Set up the database

In your Supabase project, go to SQL Editor and run the schema from `utils/database.py` (the `SCHEMA_SQL` string). Creates 5 tables: job_descriptions, candidates, interview_kits, evaluations, offers.

### Deploy to Streamlit Cloud

1. Push to a public GitHub repo
2. Go to share.streamlit.io → New app → select your repo → main file: `app.py`
3. In Advanced settings → Secrets, add:

```toml
GROQ_API_KEY   = "gsk_..."
SUPABASE_URL   = "https://xxxx.supabase.co"
SUPABASE_KEY   = "eyJ..."
SERPER_API_KEY = "..."
```

4. Deploy. That's it.

No Docker, no server, no infra cost.

---

## Honest limitations

**Session-based state** — candidate data lives in Streamlit's session state, not persistent storage. If the app restarts, you lose your current session. Supabase stores the data permanently but the UI doesn't yet have a "load previous session" flow. This is the biggest gap for production use.

**Groq rate limits** — at 14,400 requests/day and 30 requests/minute, you can screen roughly 200-400 resumes per day before hitting limits. For a small hiring team this is fine. For high-volume recruiting you'd need a paid API tier or a queue system.

**JSON parsing robustness** — agents sometimes return JSON with markdown code fences or slightly malformed structure. The `_safe_json()` function handles most cases but edge cases exist. Real production systems would use structured outputs or a validation layer.

**No authentication** — the app has no login system. Anyone with the URL can use it. Fine for a demo or internal tool, not fine for a SaaS product with multiple clients.

---

## Things I learned building this

Multi-agent systems fail in interesting ways. Single-agent prompting is fairly predictable — you write a prompt, you get output, you iterate. When you chain 3 agents sequentially and the second agent gets malformed output from the first, the failure mode is subtle and hard to debug. I spent a lot of time on the `_safe_json()` parsing function and the task output extraction.

Streamlit has opinions about HTML rendering. `st.markdown(unsafe_allow_html=True)` works fine in most contexts but fails silently inside loops, columns, and after certain widget renders. Switching to `streamlit.components.v1.html()` for any complex HTML (the radar chart, the execution log, the histogram) was the right call — it renders in an iframe and is completely isolated from Streamlit's rendering quirks.

LLM latency is the user experience. Each crew takes 15-60 seconds. Without the terminal execution log showing exactly what's happening — which agent is running, what it's doing, elapsed time — the app feels broken. The animated log turns waiting from frustrating to transparent.

Free tier constraints force good architecture decisions. Working within Groq's rate limits pushed me to use local sentence-transformers for the initial semantic match rather than burning API calls on a rough similarity check. That's actually better architecture — fast local pre-screening, expensive LLM deep-screening only when worth it.

---

## What's next

A few things I'd build next with more time:

- Persistent session management — load any previous hiring pipeline from Supabase
- Email integration — send shortlist/rejection emails directly from the app via Resend
- ATS export — push candidate data as JSON to Greenhouse, Lever, or Workable APIs
- Candidate portal — a separate URL where candidates can submit their own resumes
- Async processing — queue-based job processing so screening 50 resumes doesn't block the UI

---

## About

Built by **Sihab Safin** — Computer Science student at BGC Trust University Bangladesh.

I built RecruitIQ to demonstrate what's actually possible with CrewAI in a real-world context — not a toy demo, but a complete workflow that solves a real problem. The hiring pipeline covers every phase from intake to offer, integrates 12 specialized agents, runs entirely on free infrastructure, and produces outputs that hiring managers can actually use.

If you're a recruiter or hiring manager reading this — the app is live, the resumes are tested, and it works. Try it.

If you're a developer — the code is clean, the architecture decisions are documented above, and I'm happy to walk through any part of it.

LinkedIn: [linkedin.com/in/sihabsafin](https://linkedin.com/in/sihabsafin)

---

*Stack: Python · CrewAI · Groq · LLaMA 3.3 70B · Supabase · sentence-transformers · ChromaDB · PyMuPDF · ReportLab · Streamlit*
