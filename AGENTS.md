# AGENTS.md — Ticket Planner

> This file is the Bob IDE project context. Read it at the start of every session.
> Source of truth: `docs/PRD-ticket-planner.md`. When in doubt, consult the PRD.

---

## Project summary

**Ticket Planner** converts a non-technical client PRD (Markdown) into an ordered sprint plan and developer-ready tickets, with full traceability back to the client's own words.

Two capabilities:
1. `POST /api/plan/sprints` — PRD → sprint plan + extracted requirements + client questions
2. `POST /api/plan/tickets` — one sprint → its tickets

Deployed as a single Vercel project: static React frontend on the CDN, FastAPI backend as a Python Function.

---

## Repository layout

```
ticket-planner/
├── AGENTS.md                  ← this file
├── docs/
│   └── PRD-ticket-planner.md  ← full spec, read before coding anything
├── samples/
│   ├── prd-clean.md
│   ├── prd-vague.md
│   ├── prd-messy.md
│   └── fixtures/
│       ├── sprint-plan.example.json
│       └── tickets.example.json
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI app entry point
│   │   ├── models.py          ← Pydantic v2 models (source of truth for all data shapes)
│   │   ├── validators.py      ← deterministic post-LLM validation
│   │   ├── routes.py          ← API route handlers
│   │   └── providers/         ← LLM provider adapter (one impl per provider)
│   ├── prompts/
│   │   ├── prd_to_sprints.md
│   │   └── sprint_to_tickets.md
│   └── tests/                 ← pytest; validators must be fully tested
├── frontend/
│   └── src/                   ← React + TypeScript + Vite + Tailwind
├── .bob/
│   └── skills/                ← optional Bob skills (section 12.3 of PRD)
├── api/
│   └── index.py               ← Vercel entry point: imports the FastAPI app
├── bob_sessions/              ← task session screenshots, one subfolder per person
│   ├── abdullah/
│   ├── ali/
│   ├── najmi/
│   └── sergiu/
├── requirements.txt
├── vercel.json
└── .env.example               ← variable names only, never secrets
```

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| HTTP client | httpx |
| Tests | pytest |
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Markdown rendering | react-markdown |
| Hosting | Vercel (Hobby plan) |

---

## Data models (source of truth: `backend/app/models.py`)

### Sprint plan (Capability 1 output)
- `project`: `name`, `summary`, `assumptions[]`
- `requirements[]`: `id` (R1…), `text`, `source_quote`, `kind` (functional | non_functional)
- `sprints[]`: `id` (S1…), `order`, `name`, `goal`, `requirement_ids[]`, `deliverables[]`, `depends_on[]`, `rationale`
- `client_questions[]`: `id` (Q1…), `question`, `why_it_matters`, `requirement_ids[]`

### Ticket list (Capability 2 output)
- `sprint_id`
- `tickets[]`: `id` (S2-T1…), `title`, `type` (feature|task|chore|spike), `description`, `acceptance_criteria[]`, `technical_notes`, `areas[]`, `size` (XS|S|M|L|XL), `priority` (high|medium|low), `depends_on[]`, `requirement_ids[]`, `needs_clarification`, `clarification_note`

**Size scale:** XS = trivial, S = small with tests, M = several files, L = new subsystem, XL = too big (always flagged).

---

## API contract

### `POST /api/plan/sprints`
- Request: `{ "prd_markdown": "string" }`
- Response: `{ "plan": {...}, "validation": { "ok": bool, "issues": [...] } }`

### `POST /api/plan/tickets`
- Request: `{ "prd_markdown": "string", "plan": {...}, "sprint_id": "S2" }`
- Response: `{ "tickets": {...}, "validation": { "ok": bool, "issues": [...] } }`

### `GET /api/health`
- Returns status and configured provider name (no secrets).

### Errors
- `400` — invalid input (empty PRD, over length limit ~30,000 chars)
- `502` — LLM failed after one retry

---

## LLM layer

- Provider-agnostic. One `LLMProvider` Protocol: `async generate_json(system_prompt, user_prompt, json_schema) -> str`
- Provider selected by `LLM_PROVIDER` environment variable. API keys from env vars only — never committed.
- IBM watsonx.ai is the recommended provider (available to hackathon participants).
- On invalid JSON response: retry once, sending validation errors back to the model. If still failing, return `502`.

---

## Validation rules (run on every LLM response before returning to frontend)

**Capability 1:**
- Response parses against the Pydantic model
- Every `source_quote` exists in the PRD (normalised match; failures flagged, not dropped)
- Every requirement assigned to at least one sprint
- All `requirement_ids` in sprints/questions reference existing requirements
- Sprint `depends_on` is acyclic; no sprint depends on a higher-`order` sprint

**Capability 2:**
- Response parses against the Pydantic model
- Every ticket's `requirement_ids` belongs to the chosen sprint
- Every sprint requirement covered by at least one ticket
- Ticket IDs unique; `depends_on` acyclic within the sprint
- Any XL ticket automatically marked `needs_clarification`

---

## Coding conventions

- All Python in `backend/`. All frontend in `frontend/src/`.
- Pydantic models in `models.py` are the single source of truth — frontend TypeScript types must mirror them exactly.
- Prompts live as files in `backend/prompts/`, never as inline strings.
- Frontend calls relative `/api/...` paths only (works locally via Vite proxy and on Vercel without CORS config).
- No secrets in code or committed files. Use `.env.example` for variable names.
- Backend is stateless — no file I/O, no database, no session storage.

---

## Team roles

| Person | Role | Primary files |
|---|---|---|
| Abdullah | Backend (Person A) | `backend/app/` |
| Sergiu | Prompts & Quality (Person B) | `backend/prompts/`, `samples/` |
| TBA | Frontend (Person C) | `frontend/src/` |
| TBA | Delivery (Person D) | `vercel.json`, `api/index.py`, `README.md`, `bob_sessions/` |

**Critical handoff rule:** if `models.py` changes, the owner (Abdullah) updates any broken fixture and notifies Person C (frontend) the same hour. A silent schema change is the most likely way to lose half a day.

---

## Bob IDE usage guidelines

- Use **Plan mode** for API design and architecture decisions.
- Use **Agent mode** for implementing models, validators, routes, views, and tests.
- Always pass `@docs/PRD-ticket-planner.md` as context when starting a new task.
- Run Bob's built-in code review before merging any branch to `main`.
- Use Bob to generate commit messages and PR descriptions.
- **Do not** use Bob to iterate on prompt wording — test prompts through the running app.
- Each team member must capture **at least 3 task session summary screenshots** and push them to `bob_sessions/<name>/`.
- File naming: `teamname_personA_task01_description.png`

---

## Git workflow

- `main` always runs. Never push broken code to it.
- Branch naming: `backend/feature-name`, `frontend/feature-name`, `prompts/v2-tickets`, `delivery/vercel-setup`
- Small PRs, merged often (at least every few hours).
- Every PR gets a Vercel preview URL — check the change on the preview before merging.
- Do not edit files in another person's area without telling them.

---

## Key risks to keep in mind

- **LLM slow responses** — tickets generated one sprint at a time; show clear loading states.
- **Function timeout on Vercel** — Fluid compute must be enabled, `maxDuration` set explicitly, real LLM call tested on the deployed URL by Saturday afternoon.
- **Invalid JSON from LLM** — schema in prompt, provider JSON mode if available, one retry with errors fed back.
- **Invented requirements** — mandatory source quotes, verified by validators.
