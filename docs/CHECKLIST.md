# Project Checklist — Ticket Planner

> Status key: ✅ Done · ⬜ Remaining · 🔲 Blocked (needs something else first)
>
> Last updated: see git log. Cross-reference with [`docs/PRD-ticket-planner.md`](PRD-ticket-planner.md) §15.2 for the full deliverables table.

---

## Person A — Backend (Abdullah)

### Models & core structure
- [x] `backend/app/models.py` — all Pydantic v2 models matching PRD §7 (SprintPlan, TicketList, enums, API envelopes)
- [x] `backend/app/__init__.py` created
- [x] `backend/app/providers/base.py` — `LLMProvider` Protocol
- [x] `backend/app/providers/__init__.py`
- [x] `backend/app/providers/watsonx.py` — IBM watsonx.ai adapter with IAM token exchange

### API & application
- [x] `backend/app/main.py` — FastAPI app, CORS middleware, router mounted at `/api`
- [x] `backend/app/routes.py` — `GET /api/health`, `POST /api/plan/sprints`, `POST /api/plan/tickets`
- [x] Input validation — 400 on empty PRD, 400 on PRD over 30 000 chars
- [x] LLM retry logic — retry once on bad JSON, return 502 after second failure
- [x] Prompt files loaded from `backend/prompts/` (not inlined as strings)

### Validators
- [x] `backend/app/validators.py` — `validate_sprint_plan()` (Capability 1, all 4 rules)
- [x] `backend/app/validators.py` — `validate_ticket_list()` (Capability 2, all 5 rules)
- [x] Cycle-detection helper `_has_cycle()`
- [x] Normalised quote matching `_normalise()`

### Tests
- [ ] `backend/tests/test_validators.py` — pytest suite covering Capability 1 validation rules
- [ ] `backend/tests/test_validators.py` — pytest suite covering Capability 2 validation rules
- [ ] `backend/tests/test_routes.py` — route-level tests (happy path + error cases)
- [ ] All tests passing (`pytest backend/tests/`)

### Remaining / in-progress
- [ ] Notify Person C whenever `models.py` changes (contract per PRD §15.3)
- [ ] Error handling review — confirm 400 and 502 responses match PRD §9 spec exactly
- [ ] Code frozen (Sunday midday)

---

## Person B — Prompts & Quality (Sergiu)

### Fixtures (prerequisite for Person C)
- [x] `samples/fixtures/sprint-plan.example.json` — hand-written, passes Pydantic models
- [x] `samples/fixtures/tickets.example.json` — hand-written, passes Pydantic models

### Sample PRDs
- [x] `samples/prd-clean.md` — well-written, unambiguous sample
- [x] `samples/prd-messy.md` — realistic messy client PRD
- [x] `samples/prd-vague.md` — vague PRD that should generate client questions

### Prompts
- [x] `backend/prompts/prd_to_sprints.md` — system + user template for Capability 1
- [x] `backend/prompts/sprint_to_tickets.md` — system + user template for Capability 2

### Quality & metrics
- [ ] Run all three sample PRDs through `POST /api/plan/sprints` and check validator output
- [ ] Run all three sample PRDs through `POST /api/plan/tickets` (at least one sprint per sample)
- [ ] Tune `prd_to_sprints.md` until validator warnings are rare
- [ ] Tune `sprint_to_tickets.md` until validator warnings are rare
- [ ] `docs/metrics.md` — capture metrics from PRD §18:
  - [ ] Traceability % (source quotes verified) — target > 95 %
  - [ ] Coverage % (requirements → sprints, sprint requirements → tickets) — target 100 %
  - [ ] Client questions count per sample (especially `prd-vague.md`)
  - [ ] Time comparison (automated vs manual ticket writing)

### Bob evidence
- [x] `bob_sessions/sergiu/the_clique_personB_01_prompts_and_fixtures.png`
- [ ] At least 2 more Bob session screenshots in `bob_sessions/sergiu/`

---

## Person C — Frontend (TBA / Ali / Najmi)

### Scaffold & types
- [ ] Vite + React + TypeScript + Tailwind CSS project in `frontend/`
- [ ] TypeScript types mirroring `backend/app/models.py` exactly (update whenever A changes models)
- [ ] Vite dev-server proxy configured: `/api` → `http://localhost:8000`

### Upload view (Capability 1 — input)
- [ ] PRD text area or file-upload input
- [ ] Markdown preview of the uploaded PRD
- [ ] "Generate sprint plan" button with loading state
- [ ] Error display for 400 and 502 responses

### Sprint plan view (Capability 1 — output)
- [ ] Sprint cards rendered in dependency order
- [ ] Requirements listed per sprint with `source_quote` shown
- [ ] Client questions panel with "Copy all" button
- [ ] Validation panel showing `ValidationReport` issues (warnings and errors)
- [ ] Editable sprint / requirement fields (inline edit)

### Tickets view (Capability 2 — output)
- [ ] Sprint selector to choose which sprint to expand
- [ ] "Generate tickets" button with loading state (per sprint, not all at once)
- [ ] Ticket cards showing title, type, size, priority, acceptance criteria
- [ ] Link from ticket back to `requirement_ids` → `source_quote`
- [ ] Editable ticket fields (inline edit)
- [ ] `needs_clarification` / `clarification_note` highlighted visually

### Export & finishing
- [ ] Export sprint plan to Markdown
- [ ] Export sprint plan to JSON
- [ ] Export tickets to Markdown
- [ ] Export tickets to JSON

### API integration
- [ ] All calls use relative `/api/...` paths (no hardcoded host)
- [ ] Connected to real backend (replaces fixture-driven state)

### Bob evidence
- [ ] At least 3 Bob session screenshots in `bob_sessions/ali/` or `bob_sessions/najmi/`

---

## Person D — Delivery (TBA / Ali / Najmi)

### Repository setup
- [x] Repository created with this PRD committed
- [x] `AGENTS.md` in place
- [ ] `README.md` — project description, local setup, env variables, how to run

### Vercel deployment
- [ ] Vercel project connected to the repo
- [ ] `vercel.json` — routes `POST /api/*` to the Python function, everything else to the frontend
- [ ] `api/index.py` — Vercel entry point importing the FastAPI `app`
- [ ] `requirements.txt` — all Python dependencies listed
- [ ] `.env.example` — variable names only, no secrets (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `WATSONX_MODEL_ID`, `LLM_PROVIDER`, `MAX_PRD_CHARS`)
- [ ] Fluid compute enabled, `maxDuration` set explicitly in `vercel.json`
- [ ] Hello-world deploy live (placeholder frontend + `/api/health` responding)
- [ ] LLM API key set as a Vercel environment variable (not committed)
- [ ] One real LLM call confirmed on the **deployed URL** (not only locally)
- [ ] Full app deployed and reachable at the production Application URL

### Bob skills (optional, PRD §12.3)
- [ ] `.bob/skills/` — skill file(s) created if time allows

### Bob session evidence collection
- [ ] Collect screenshots from all team members into `bob_sessions/`
  - [x] `bob_sessions/abdullah/` — 2 screenshots present
  - [x] `bob_sessions/sergiu/` — 1 screenshot present
  - [ ] `bob_sessions/ali/` — needs ≥ 3 screenshots
  - [ ] `bob_sessions/najmi/` — needs ≥ 3 screenshots

### Submission materials
- [ ] `docs/metrics.md` available (handed off from Person B)
- [ ] Problem & Solution Statement — 500 words or fewer
- [ ] IBM Bob Usage Statement — 500 words or fewer
- [ ] Cover image
- [ ] Demo script drafted (following PRD §17 structure)
- [ ] Video demo recorded — ≤ 3 min, ≥ 90 s of product in action
- [ ] Backup video take recorded
- [ ] Slide presentation prepared
- [ ] Submission assembled on the lablab platform

---

## Submission Checklist (PRD §20 — whole team)

- [ ] Public code repository link
- [ ] `bob_sessions/` with task session screenshots from **every** team member (A, B, C, D)
- [ ] Problem and Solution Statement (≤ 500 words)
- [ ] IBM Bob Usage Statement (≤ 500 words)
- [ ] Cover image
- [ ] Video demo (≤ 3 min, ≥ 90 s of product in action)
- [ ] Slide presentation
- [ ] Application URL (Vercel production URL) + demo platform
- [ ] Technology and category tags filled in

---

## Quick status summary

| Area | Owner | Status |
|---|---|---|
| Pydantic models | A | ✅ Complete |
| LLM provider adapter (watsonx) | A | ✅ Complete |
| FastAPI app + routes | A | ✅ Complete |
| Validators (Cap 1 + Cap 2) | A | ✅ Complete |
| Validator tests | A | ⬜ Not started |
| Route tests | A | ⬜ Not started |
| Prompts (both) | B | ✅ Complete |
| Sample PRDs (all 3) | B | ✅ Complete |
| Fixtures (both) | B | ✅ Complete |
| Prompt tuning + metrics | B | ⬜ Remaining |
| Frontend scaffold | C | ⬜ Not started |
| Frontend views + export | C | ⬜ Not started |
| Vercel deployment | D | ⬜ Not started |
| `api/index.py` + `vercel.json` | D | ⬜ Not started |
| README | D | ⬜ Not started |
| Submission materials | D | ⬜ Not started |
