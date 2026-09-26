# Technical PRD: TicketSeed

**Event:** IBM Bob 2.0 Hackathon (Sep 25 to 27, 2026)
**Team size:** 4
**One-line pitch:** Paste a client's non-technical PRD, get a sprint plan, then turn any sprint into developer-ready tickets.

---

## 1. Problem

Developers regularly receive product requirement documents written by clients with no technical background. These documents describe what the client wants in business language ("customers should be able to order online and pay"), mix must-haves with nice-to-haves, skip edge cases, and leave out everything a developer needs to start: data, integrations, roles, error states.

Before any code gets written, someone on the team has to:

- read the whole document and figure out what is actually being asked,
- translate business language into technical work,
- decide what to build first and what depends on what,
- split the work into sprints,
- break each sprint into tickets small enough to assign and estimate,
- collect the questions the document leaves unanswered and send them back to the client.

This is slow, repeated for every new client project, inconsistent between people, and the unanswered-questions step is usually discovered too late, mid-sprint, when a developer gets blocked.

## 2. Solution

A web application with exactly two core capabilities:

```
Capability 1:  client PRD (.md)  →  LLM request  →  sprint plan + client questions
Capability 2:  one chosen sprint →  LLM request  →  tickets for that sprint
```

The user uploads the client's PRD, reviews the proposed sprints, picks a sprint, and generates its tickets. Each sprint is expanded on demand, so the user reviews the big picture before committing to detail.

**What makes it more than "PRD in, tickets out":**

1. **Traceability.** Every requirement, sprint and ticket points back to a verbatim quote from the client's document. The backend verifies these quotes exist in the PRD. A ticket with no traceable source is treated as invented and flagged.
2. **Client questions.** Gaps and ambiguities in the PRD become an explicit list of questions to send back to the client, instead of silent assumptions baked into tickets.
3. **Deterministic validation.** Coverage, dependencies and ticket structure are checked by plain code after every LLM call. The LLM proposes; the backend verifies.

## 3. Scope

**In scope (core product)**
- PRD input as Markdown: file upload or paste
- Capability 1: PRD to sprint plan, including extracted requirements and client questions
- Capability 2: one sprint to its tickets
- Review UI: view and edit sprints and tickets before exporting
- Export: download the plan and tickets as Markdown and JSON
- Validation of every LLM response (section 7)
- Provider-agnostic LLM layer (section 8), provider chosen by the team

**Out of scope for the hackathon**
- Team awareness (members, capacity, velocity): sprints are logical phases of work, not capacity-bound time boxes
- Databases, accounts, login, project history
- PDF or Word input
- Analysis of an existing codebase

**Phase 2, after the core product works end to end**
- Jira integration: create sprints and issues in Jira, and assign each ticket to a Jira team member (section 13)

## 4. User flow

1. **Upload.** The user drops a `.md` file or pastes text. The PRD is rendered as a preview so they can confirm it is the right document.
2. **Generate sprint plan.** One click. The app shows:
   - a short project summary,
   - the requirements extracted from the PRD, each with its source quote,
   - the sprints, in order, each with a goal, the requirements it covers and its deliverables,
   - the list of client questions.
3. **Review sprints.** The user can rename sprints, edit goals, and move requirements between sprints. The validation panel updates immediately.
4. **Generate tickets.** The user clicks "Generate tickets" on a specific sprint. The app shows that sprint's tickets.
5. **Review tickets.** Inline editing of every field. Tickets flagged `needs_clarification` are shown at the top.
6. **Export.** Download the full plan and all generated tickets as Markdown (for humans) or JSON (for tools, and for the future Jira integration).

## 5. Architecture

```
┌─────────────────────────────┐
│  Frontend (React + Vite)    │  holds all state in the browser session
└──────────────┬──────────────┘
               │ HTTPS, JSON
┌──────────────▼──────────────┐
│  Backend (FastAPI)          │
│  ├─ /api/plan/sprints       │
│  ├─ /api/plan/tickets       │
│  ├─ validators (plain code) │
│  └─ LLM provider adapter    │
└──────────────┬──────────────┘
               │
        ┌──────▼──────┐
        │  LLM API    │  provider chosen by the team
        └─────────────┘
```

**The backend is stateless.** It never stores a PRD or a plan. Every request carries everything it needs. The frontend keeps the current session in memory.

**Single deployment on Vercel.** Frontend and backend live on the same Vercel project and the same domain, so there is one URL and no CORS configuration. This also gives the submission its Application URL. Details in 5.1.

### 5.1 Deployment: Vercel

**Why Vercel and not Netlify.** Both were suggested by the organisers. Netlify Functions run JavaScript/TypeScript and Go, not Python, so our FastAPI backend could not run there without rewriting it or hosting it somewhere else. Vercel runs Python functions natively. If the team strongly prefers Netlify, the backend must be rewritten in TypeScript (with Zod replacing Pydantic). Decide this on Saturday morning, not later.

**How the app runs on Vercel**
- Vite builds the frontend into static files, served from Vercel's CDN.
- The FastAPI app runs as one Vercel Python Function. Every `/api/*` request is routed to it.
- Every push to `main` redeploys production. Every branch and pull request gets its own preview URL.
- The backend is stateless and has no database, which is exactly what serverless functions expect. No design changes are needed.

**Illustrative configuration** (confirm against the current Vercel Python and FastAPI documentation at build time, do not copy blindly):

`api/index.py`
```python
from backend.app.main import app  # Vercel serves this ASGI app
```

`vercel.json`
```json
{
  "buildCommand": "cd frontend && npm ci && npm run build",
  "outputDirectory": "frontend/dist",
  "functions": { "api/index.py": { "maxDuration": 120 } },
  "rewrites": [{ "source": "/api/(.*)", "destination": "/api/index" }]
}
```

**Function time limit: the main deployment risk.** LLM calls can take tens of seconds. Vercel's documentation gives the Hobby plan 300 seconds as default and maximum with Fluid compute, but community threads show projects still being cut off at 10 or 60 seconds when settings differ. Therefore:
- confirm Fluid compute is enabled in the project settings,
- set `maxDuration` explicitly,
- test a real LLM call on the **deployed** URL, not only locally, by Saturday afternoon,
- keep calls short by design (tickets are generated one sprint at a time), and give the frontend a clear timeout message.

**Secrets.** LLM API keys go into Vercel environment variables, for both Production and Preview. Never commit them. The repo contains a `.env.example` listing variable names only.

**Bundle size.** Keep Python dependencies minimal: `fastapi`, `pydantic`, `httpx`, plus the provider SDK only if it is lightweight. If the chosen provider's SDK is heavy, call its REST API with `httpx` instead.

**Local development mirrors production.** Run the backend with `uvicorn` on port 8000 and the frontend with `vite dev`, with a Vite proxy sending `/api` to port 8000. The frontend always calls relative `/api/...` paths, so the same code works locally and on Vercel.

## 6. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend language | Python 3.11+ | Every major LLM provider ships a first-class Python SDK |
| Backend framework | FastAPI | Async, fast to write, generates API docs automatically |
| Schemas and validation | Pydantic v2 | The same models validate LLM output, define API contracts, and generate the JSON schema we put in the prompt |
| HTTP client | httpx | For providers used via REST rather than SDK |
| Tests | pytest | Validators must be tested; they are the credibility of the product |
| Frontend | React + TypeScript + Vite | Fast setup, typed contracts with the backend |
| Styling | Tailwind CSS | No design system to build in 48 hours |
| Markdown rendering | react-markdown | PRD preview and exported-ticket preview |
| Hosting | Vercel (Hobby plan) | Static frontend on the CDN, FastAPI as a Python Function, one URL, preview deploy per branch (section 5.1) |

**Why not a single full-stack JavaScript framework:** it would work, but Pydantic validation of LLM output is the heart of this product, and Python is where the LLM SDKs are most mature. The frontend stays thin.

## 7. Data model

These models are the contract between frontend, backend and prompts. Agree them in the first hour. They live in `backend/app/models.py` and the frontend mirrors them as TypeScript types.

### 7.1 Sprint plan (output of capability 1)

```json
{
  "project": {
    "name": "string",
    "summary": "string, 2 to 4 sentences in technical language",
    "assumptions": ["string"]
  },
  "requirements": [
    {
      "id": "R1",
      "text": "string, restated in technical language",
      "source_quote": "string, verbatim excerpt from the PRD",
      "kind": "functional | non_functional"
    }
  ],
  "sprints": [
    {
      "id": "S1",
      "order": 1,
      "name": "string",
      "goal": "string, one sentence describing the outcome",
      "requirement_ids": ["R1", "R2"],
      "deliverables": ["string"],
      "depends_on": ["S0"],
      "rationale": "string, why this work belongs here and in this order"
    }
  ],
  "client_questions": [
    {
      "id": "Q1",
      "question": "string, written for a non-technical reader",
      "why_it_matters": "string",
      "requirement_ids": ["R3"]
    }
  ]
}
```

### 7.2 Ticket list (output of capability 2)

```json
{
  "sprint_id": "S2",
  "tickets": [
    {
      "id": "S2-T1",
      "title": "string, imperative, max 100 characters",
      "type": "feature | task | chore | spike",
      "description": "string, markdown",
      "acceptance_criteria": ["string"],
      "technical_notes": "string",
      "areas": ["frontend | backend | database | devops | design | qa"],
      "size": "XS | S | M | L | XL",
      "priority": "high | medium | low",
      "depends_on": ["S2-T0"],
      "requirement_ids": ["R4"],
      "needs_clarification": false,
      "clarification_note": "string | null"
    }
  ]
}
```

### 7.3 Size scale

Relative size, not hours, since the app knows nothing about the team:

| Size | Meaning |
|---|---|
| XS | Trivial change, one file, no new logic |
| S | Small, contained change with tests |
| M | Several files or one new component |
| L | New subsystem or integration |
| XL | Too big for one ticket. Always flagged for splitting |

### 7.4 Validation rules

Run by the backend on every LLM response, before anything is returned to the frontend.

**Capability 1**
- Response parses and conforms to the Pydantic model.
- Every `source_quote` appears in the PRD. Matching is normalised (whitespace, case, punctuation) and tolerant of small differences; quotes that fail are flagged, not silently dropped.
- Every requirement is assigned to at least one sprint (coverage).
- Every `requirement_ids` entry in sprints and questions refers to an existing requirement.
- Sprint `depends_on` references exist and contain no cycle; no sprint depends on a sprint with a higher `order`.

**Capability 2**
- Response parses and conforms to the model.
- Every ticket's `requirement_ids` belongs to the chosen sprint.
- Every requirement of the sprint is covered by at least one ticket.
- Ticket ids are unique; `depends_on` references exist within the sprint and contain no cycle.
- Any `XL` ticket is automatically marked `needs_clarification` with a note to split it.

**On failure:** if the response does not parse or does not match the schema, the backend retries once, sending the validation errors back to the model. If it still fails, the user sees a clear error. Semantic issues (an unverified quote, an uncovered requirement) do not trigger a retry; they are returned as a validation report alongside the result and shown in the UI.

## 8. LLM layer

### 8.1 Provider adapter

The team picks the provider. The code must not care which one. A single interface:

```python
class LLMProvider(Protocol):
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str: ...
```

One implementation for the chosen provider, selected by the `LLM_PROVIDER` environment variable. API keys come only from environment variables and are never committed.

**Note for the choice:** IBM watsonx.ai is offered to participants for this hackathon, and the guide suggests it as an option once Bobcoins run out. Using it strengthens the IBM story in the pitch. Whatever the choice, test that the provider returns valid JSON for our schemas in the first hours.

### 8.2 Prompts

Stored as versioned files, not strings buried in code:

```
backend/prompts/
├── prd_to_sprints.md
└── sprint_to_tickets.md
```

**Rules both prompts enforce:**
- Role: a senior tech lead translating a non-technical client's document into an engineering plan.
- Never invent features the PRD does not ask for.
- Every requirement and ticket must trace to a verbatim quote from the PRD.
- When the PRD is ambiguous or silent on something a developer would need, write a client question instead of assuming.
- Output JSON only, matching the provided schema, generated from the Pydantic model.
- Low temperature, for consistent output between runs.

**`prd_to_sprints.md` specific:** extract requirements first, then group them into sprints ordered by dependency: foundations (setup, data, auth) before features that depend on them. Sprints are logical phases, not time boxes.

**`sprint_to_tickets.md` specific:** receives the full PRD, the full sprint plan, and the chosen sprint id. It sees the other sprints only so it does not duplicate their work. Tickets must be small enough to assign to one developer.

### 8.3 Input limits

Maximum PRD length is a configurable constant (start around 30,000 characters). Longer documents are rejected with a clear message rather than truncated silently.

## 9. API

### `POST /api/plan/sprints`

Request:
```json
{ "prd_markdown": "string" }
```

Response:
```json
{
  "plan": { "...sprint plan, section 7.1..." },
  "validation": {
    "ok": true,
    "issues": [
      { "severity": "warning | error", "target": "R3", "message": "string" }
    ]
  }
}
```

### `POST /api/plan/tickets`

Request:
```json
{
  "prd_markdown": "string",
  "plan": { "...sprint plan, possibly edited by the user..." },
  "sprint_id": "S2"
}
```

Response:
```json
{
  "tickets": { "...ticket list, section 7.2..." },
  "validation": { "ok": true, "issues": [] }
}
```

The request sends the plan as edited by the user, so tickets reflect the user's edits, not the original LLM output.

### `GET /api/health`

Returns status and the configured provider name, without secrets.

### Error responses

`400` for invalid input (empty PRD, over the length limit). `502` when the LLM fails after retry, with a message the UI can show. Never expose raw provider errors or keys.

## 10. Frontend

Three views, one page app.

**1. Input**
Drag-and-drop area for `.md`, a paste box as an alternative, rendered preview, a "Generate sprint plan" button, and a loading state that says what is happening (LLM calls can take tens of seconds).

**2. Sprint plan**
- Project summary at the top.
- Sprints as ordered cards: name, goal, covered requirements, deliverables, and a "Generate tickets" button.
- Side panel with the client questions, with a "Copy all" button so the user can paste them into an email to the client.
- Collapsible requirements list with source quotes.
- Validation panel showing warnings (unverified quotes, uncovered requirements).
- Editable sprint name, goal and requirement assignment.

**3. Sprint tickets**
- Tickets for one sprint, flagged tickets first.
- Each ticket expandable to show description, acceptance criteria, technical notes, dependencies and the linked requirements with their source quotes.
- Inline editing.
- "Regenerate" to call capability 2 again for this sprint.

**Export**, available from views 2 and 3: download Markdown (one readable document with the plan and all generated tickets) or JSON (the raw data).

**Not building:** accounts, saved projects, dark mode, a landing page.

## 11. Repository layout

```
ticketseed/
├── AGENTS.md                  # generated with /init in Bob IDE, then edited
├── docs/
│   └── PRD.md                 # this document
├── samples/
│   ├── prd-clean.md
│   ├── prd-vague.md
│   └── prd-messy.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py          # Pydantic models, section 7
│   │   ├── validators.py      # section 7.4
│   │   ├── providers/         # section 8.1
│   │   └── routes.py          # section 9
│   ├── prompts/
│   └── tests/
├── frontend/
│   └── src/
├── .bob/
│   └── skills/                # optional, section 12.3
├── api/
│   └── index.py               # Vercel entry point, imports the FastAPI app
├── requirements.txt           # Python dependencies for the Vercel function
├── vercel.json
├── .env.example               # variable names only, no secrets
└── bob_sessions/              # required submission evidence
```

## 12. How Bob 2.0 is used

### 12.1 What the rules require

Bob IDE is required for the hackathon and must be a core component of the solution. Every team member must upload Bob IDE task session summary screenshots to `bob_sessions/`.

The judging criterion **Application of Technology** asks how clearly Bob 2.0 is applied, and the theme asks teams to use Bob across multiple steps, not only as a coding assistant. Our answer must be concrete, which is why this section exists.

### 12.2 Bob in the development workflow

| Step | Bob feature | Who |
|---|---|---|
| Project context from this PRD | `/init` to generate `AGENTS.md`, then point Bob at `docs/PRD.md` | Everyone, first hour |
| Architecture and endpoint design | Plan mode, then Code mode to implement | Backend owner |
| Pydantic models and validators | Agent mode, with `@docs/PRD.md` section 7 as context | Backend owner |
| Validator test suite | Agent mode generating pytest cases, including cycle and coverage edge cases | Backend owner |
| React views | Agent mode per view | Frontend owner |
| Pre-merge checks | Bob's built-in code review on each branch | Whoever merges |
| Commits and pull requests | Generated commit messages and PR descriptions | Everyone |
| Safe experimentation | Rollback when an AI change goes wrong | Everyone |

Every member must run and screenshot real tasks, since evidence is required per person.

### 12.3 Optional: the planner as Bob skills (recommended if time allows)

The two prompts from section 8.2 can also ship as Bob skills, so a developer can run the same planning directly inside Bob IDE on a PRD in their repo, without the web app:

```
.bob/skills/
├── prd-to-sprints/
│   ├── SKILL.md           # instructions, points to the prompt and schema
│   └── sprint-plan.schema.json
└── sprint-to-tickets/
    ├── SKILL.md
    └── ticket-list.schema.json
```

The skills reuse the same prompt text and the same schemas, so there is one source of truth. This costs a few hours and gives the pitch a direct answer to "where is Bob in the product": the planner is available both as a web app and as a Bob-native workflow. Do this only after the core product works end to end.

### 12.4 Bobcoin budget

40 Bobcoins per member, 160 total, no top-ups.
- Do not use Bob to iterate on prompt wording; test prompts through the app itself, which uses the team's LLM provider.
- Use Bob for building code, tests and reviews.
- Check usage on Saturday afternoon.

## 13. Phase 2: Jira integration

Start only when the core product is complete and demo-ready.

**Goal:** export a sprint and its tickets into Jira, and assign each ticket to a member of the Jira project.

**Mapping from our model:**

| Our field | Jira |
|---|---|
| Sprint | Jira sprint on a Scrum board |
| `type` | Issue type (Story, Task, Spike as Task with label) |
| `title` | Summary |
| `description` + `acceptance_criteria` + `technical_notes` | Description |
| `areas` | Labels or components |
| `size` | Story points via a fixed mapping (XS=1, S=2, M=3, L=5, XL=8) |
| `priority` | Priority |
| `depends_on` | Issue links ("is blocked by") |
| `requirement_ids` + source quote | Included in the description for traceability |

**Assignment:** requires knowing the team, which the core product deliberately does not. Phase 2 therefore adds reading the Jira project's members and letting the user pick an assignee per ticket (or accept a suggestion based on `areas`).

**Rules for building it:** Jira Cloud with an API token, a throwaway free-tier project, a dry-run mode that shows exactly what would be created before calling Jira, and reporting of created versus failed issues on partial failure. Confirm endpoints against current Jira Cloud documentation at build time rather than from memory. As an alternative worth testing, Bob IDE supports MCP servers, so a Jira MCP server could be used during development to inspect or create issues from inside Bob.

## 14. Sample data

Real client PRDs are not allowed: the hackathon forbids client data and personal information. The team writes three realistic, fictional client PRDs in `samples/`:

- **`prd-clean.md`**: well structured, clear requirements. Shows the happy path.
- **`prd-vague.md`**: short, business-only language ("an app like Uber but for dog walkers"). Should produce many client questions.
- **`prd-messy.md`**: long, repetitive, mixes must-haves with wishes and contradicts itself once. Shows traceability and question generation under stress.

The demo uses the messy one. It is the most convincing, because it is what developers actually receive.

## 15. Suggested team workflow

This is a suggestion, not a fixed assignment. Swap roles to match each person's strengths; what matters is that every area has exactly one owner and that the handoffs below are respected.

### 15.1 Roles at a glance

| Person | Role | Owns | Main Bob usage |
|---|---|---|---|
| **A** | Backend | FastAPI app, Pydantic models, validators and their tests, provider adapter, API routes | Plan mode for the API design, Agent mode for models and validators, generated pytest suite |
| **B** | Prompts and quality | Both prompt files, the three sample PRDs, example JSON fixtures, running samples and measuring metrics | Reviewing prompt outputs against the schema, analysing validator reports, writing the metrics script |
| **C** | Frontend | All three views, editing, validation panel, export to Markdown and JSON | Agent mode per view, TypeScript types mirrored from the models |
| **D** | Delivery | Vercel deployment, README, optional Bob skills (12.3), video, slides, both 500-word statements, `bob_sessions/` collection | Vercel config and entry point, README generation, packaging the Bob skills |

### 15.2 What each person delivers, by checkpoint

**Person A: Backend**

| Checkpoint | Deliverable |
|---|---|
| Saturday morning | `models.py` with all Pydantic models from section 7, committed **first**, since B and C depend on it. One successful JSON call to the chosen LLM provider from Python. `/api/health` running. |
| Saturday afternoon | `POST /api/plan/sprints` working end to end, including capability 1 validators and the retry-once logic. |
| Saturday night | `POST /api/plan/tickets` working end to end, including capability 2 validators. Validator tests passing. |
| Sunday midday | Error handling finished (400, 502), input length limit, code frozen except bug fixes. |

Depends on: B for prompt files. Hands off to: C (API contract), D (FastAPI app importable from the Vercel entry point).

**Person B: Prompts and quality**

| Checkpoint | Deliverable |
|---|---|
| Saturday morning | One hand-written example response per capability in `samples/fixtures/` (`sprint-plan.example.json`, `tickets.example.json`) that passes the Pydantic models. Do this first, C is waiting for it. Then `prd-messy.md` drafted. |
| Saturday afternoon | First working version of `prd_to_sprints.md`, tested with a direct provider script until A's endpoint is ready. `prd-clean.md` and `prd-vague.md` written. |
| Saturday night | First working version of `sprint_to_tickets.md`. All three samples run through both capabilities at least once. |
| Sunday midday | Prompts tuned until validator warnings are rare. Metrics from section 18 captured in `docs/metrics.md`. |

Depends on: A for a working endpoint to test prompts through (until then, B tests prompts by calling the provider directly with a small script). Hands off to: A (prompt files), C (fixtures), D (metrics for slides and video).

**Person C: Frontend**

| Checkpoint | Deliverable |
|---|---|
| Saturday morning | Vite + React + Tailwind scaffold. TypeScript types mirroring `models.py`. Upload view with Markdown preview. |
| Saturday afternoon | Sprint plan view rendering B's fixture: sprint cards, requirements with quotes, client questions panel with "Copy all". |
| Saturday night | Connected to the real backend. Tickets view working. Editing of sprints and tickets. |
| Sunday midday | Validation panel, loading states, export to Markdown and JSON. UI frozen except bug fixes. |

Depends on: B's fixtures (until the backend works), then A's endpoints. Hands off to: D (frontend build that Vercel serves).

**Person D: Delivery**

| Checkpoint | Deliverable |
|---|---|
| Saturday morning | Repo created, this PRD committed, `/init` run. Vercel project connected to the repo. Hello-world deploy live: placeholder frontend plus `/api/health` answering from the Python function. Fluid compute enabled, `maxDuration` set. |
| Saturday afternoon | LLM API key set as a Vercel environment variable. One real LLM call tested on the deployed URL, not only locally. README structure. Collects everyone's Bob session screenshots taken so far. |
| Saturday night | Full app deployed and reachable at the Application URL. Demo script drafted from section 17. |
| Sunday midday | Optional Bob skills (12.3) if the core is solid. Both 500-word statements drafted. Slides drafted. |
| Sunday afternoon | Video recorded, plus a backup take. Submission assembled. |

Depends on: everyone, for a working app and for screenshots. Hands off to: the submission.

### 15.3 Contracts between people

These are the only things people depend on from each other. Changing one requires telling everyone affected.

| Contract | Owner | Used by |
|---|---|---|
| `backend/app/models.py` | A | B (fixtures must pass it), C (TypeScript types mirror it) |
| `samples/fixtures/*.json` | B | C (builds the UI before the backend works) |
| `backend/prompts/*.md` | B | A (loads them), D (reuses them in the Bob skills) |
| API request and response shapes, section 9 | A | C |

**Rule:** if A changes a model, A updates the fixture that breaks and tells C the same hour. A silent schema change is the most likely way to lose half a day.

### 15.4 Git workflow

- `main` always runs. Nobody pushes broken code to it.
- One branch per person per piece of work: `backend/sprints-endpoint`, `frontend/tickets-view`, `prompts/v2-tickets`, `delivery/vercel-setup`.
- Small pull requests, merged often. Aim for merging at least every few hours, not once at the end of the day.
- Before merging, run Bob's code review on the branch. This is useful and it produces Bob evidence.
- Use Bob to generate commit messages and PR descriptions.
- Every pull request gets a Vercel preview URL. Check the change on the preview before merging, not only locally, so deployment problems show up early.
- Do not edit files in another person's area without telling them. If you must, do it in your own branch and ask them to review.

### 15.5 Sync points

Short check-ins, 10 to 15 minutes, everyone present. Each person answers three questions: what is done, what is next, what is blocking me.

| When | Purpose |
|---|---|
| Saturday morning, start | Agree the models in section 7. Assign roles. Everyone confirms Bob access and the hackathon instance. |
| Saturday, late morning | Check the morning deliverables. Confirm the provider returns valid JSON. Fix the schema now if anything feels wrong, later it costs hours. |
| Saturday afternoon | Bobcoin checkpoint for everyone. Connect frontend to real backend. Real LLM call confirmed on the deployed URL. |
| Saturday night | **Go/no-go:** does the full flow work end to end on one sample? If not, cut scope before sleeping. |
| Sunday midday | **Feature freeze.** From here on: bugs, polish, recording, submission only. |
| Sunday, before recording | Walk through the demo script once together. |

### 15.6 Bob evidence, per person

The rules require task session summary screenshots from every team member, so this is not only D's job.

- Take the screenshot **right after finishing each task**, not on Sunday afternoon. Tasks from Saturday morning are easy to lose track of by Sunday.
- Name files consistently: `teamname_personA_task01_sprints_endpoint.png`.
- Give each Bob task a clear first message so its title in the Tasks panel is recognisable later.
- Push screenshots into `bob_sessions/` in your own branch as you go. D checks on Saturday afternoon and Sunday midday that everyone has some.
- Target: at least 3 meaningful tasks per person by the end.

### 15.7 When someone is blocked or finishes early

**If A's backend is late:** B keeps testing prompts with a direct provider script, C keeps building on fixtures. Nobody waits.

**If C's frontend is late:** D takes over the export feature, since it is self-contained.

**If B's prompts produce bad output:** A helps by tightening validators and retry feedback. Better validation often fixes more than better wording.

**If someone finishes early, the backlog in order of value:**
1. Help whoever is furthest behind the Saturday night go/no-go.
2. Bob skills (section 12.3), if D has not started them.
3. "Regenerate tickets" button on the tickets view.
4. More edge-case tests for the validators.
5. A fourth sample PRD in a different domain.

Never start Jira (section 13) before the Sunday midday feature freeze has shown that the core is demo-ready.

## 16. Timeline

Work starts Saturday morning. Because Friday evening is not used, there is no slack: the Saturday night go/no-go is strict.

**Optional tonight, 10 minutes each:** accept the Bob invite email, install Bob IDE, log in and select the hackathon instance. This avoids losing Saturday morning to account problems.

**Saturday morning**
- Everyone: Bob access confirmed, hackathon instance selected.
- D: repo created, this PRD committed, `/init` run, `AGENTS.md` reviewed. Vercel hello-world deploy live.
- All together: models agreed. A commits `models.py`, B commits the fixtures right after.
- A: provider chosen, one successful JSON call from Python.
- C: project scaffold, upload view.

**Saturday afternoon**
- A: capability 1 end to end in the backend, with validators.
- B: first sprint prompt working, remaining samples written.
- C: sprint plan view on fixtures, then on the real backend.
- D: real LLM call tested on the deployed URL.
- Bobcoin checkpoint.

**Saturday night**
- Capability 2 end to end. Tickets view. Editing.
- **Go/no-go: upload a PRD, see sprints, generate tickets for one sprint.** Rough is fine. If it does not work, cut scope before sleeping, do not add anything.

**Sunday**
- Morning: prompt tuning on the three samples, capture metrics, export finished, redeploy.
- Midday: everyone uploads their Bob session screenshots. Optional Bob skills if the core is solid.
- Afternoon: record the demo and a backup take, write the statements, build slides.
- Final hours: submit. Confirm the exact deadline on the lablab platform.

## 17. Demo (3 minutes or less, at least 90 seconds of the product in action)

1. **The problem (~20s):** a messy client PRD on screen. "This is what developers get. Turning it into sprints and tickets takes a tech lead hours, and the gaps show up mid-sprint."
2. **Sprint plan (~45s):** upload, generate, show the sprints in dependency order and the extracted requirements with their source quotes.
3. **Client questions (~25s):** the list of questions the PRD left unanswered, copied in one click. Frame it as the feature that saves a blocked sprint.
4. **Tickets (~45s):** pick one sprint, generate tickets, open one to show acceptance criteria and its link back to the client's own words.
5. **Export (~15s):** download Markdown.
6. **Bob (~20s):** how the product was built with Bob IDE (Plan mode, code review, generated tests), plus the Bob skills if built.
7. **Numbers (~10s):** metrics below.

Record a full backup run before judging.

## 18. Metrics

- **Traceability:** percentage of requirements and tickets whose source quote was verified in the PRD. Target above 95%.
- **Coverage:** percentage of requirements covered by sprints, and of sprint requirements covered by tickets. Target 100%.
- **Client questions:** number generated per sample, especially for `prd-vague.md`.
- **Time:** PRD to full ticket set, compared with one team member writing tickets for one sprint by hand, measured, then extrapolated and stated as an extrapolation.

## 19. Risks

| Risk | Mitigation |
|---|---|
| LLM returns invalid JSON | Schema in the prompt, provider JSON mode if available, one retry with errors fed back |
| Invented requirements or tickets | Mandatory source quotes, verified by the backend and shown to the user |
| Slow LLM responses make the UI feel broken | Clear loading states; tickets generated per sprint, never all at once |
| Judges see Bob as "only used to write code" | Section 12: concrete Bob workflow, evidence from every member, optional Bob skills |
| Theme-fit questions (planning is not in the theme's examples) | Frame it as the first step of the development workflow: getting from a client document to work a developer can start on |
| Deployment breaks late | Hello-world deploy on Saturday morning; every merge to `main` redeploys automatically; preview URL checked on every PR |
| LLM call cut off by the function time limit | Fluid compute on, explicit `maxDuration`, real call tested on the deployed URL by Saturday afternoon, tickets generated one sprint at a time, clear timeout message in the UI |
| Provider SDK too heavy for the function bundle | Call the provider's REST API with `httpx` instead of the SDK |
| Jira eats time before the core is done | Jira is Phase 2 and does not start until the core flow is demo-ready |

## 20. Submission checklist

- [ ] Public code repository
- [ ] `bob_sessions/` with task session summary screenshots from every team member
- [ ] Problem and Solution Statement, 500 words or less
- [ ] IBM Bob Usage Statement, 500 words or less
- [ ] Cover image
- [ ] Video demo, 3 minutes or less, at least 90 seconds showing the product in action
- [ ] Slide presentation
- [ ] Application URL (the Vercel production URL) and demo platform
- [ ] Technology and category tags
