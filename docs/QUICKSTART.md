# Local Development Quickstart

Get the backend and frontend running on your machine.

---

## Prerequisites

| Tool | Minimum version | Check |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Git | any | `git --version` |

---

## 1 — Clone & enter the repo

```bash
git clone https://github.com/AbdullahKhetran/TicketSeed.git
cd ticket-planner
```

---

## 2 — Environment variables

Copy the example file and fill in your watsonx credentials:

```bash
cp .env.example .env
```

Open `.env` and set these values:

```env
# Required — IBM watsonx.ai credentials
WATSONX_API_KEY=<your-ibm-cloud-api-key>
WATSONX_PROJECT_ID=<your-watsonx-project-id>

# Optional — defaults shown
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
LLM_PROVIDER=watsonx
MAX_PRD_CHARS=30000
```

> **Never commit `.env`.** It is already in `.gitignore`.

Where to get the values:
- **`WATSONX_API_KEY`** — IBM Cloud console → Manage → Access (IAM) → API keys
- **`WATSONX_PROJECT_ID`** — watsonx.ai console → your project → Manage tab → Project ID
- **`WATSONX_URL`** — leave as default unless your region is different (e.g. `https://eu-de.ml.cloud.ibm.com`)

---

## 3 — Backend

### 3a. Create a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3b. Install dependencies

```bash
pip install -r requirements.txt
```

### 3c. Start the FastAPI server

```bash
uvicorn backend.app.main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**.

| Endpoint | Description |
|---|---|
| `GET  http://localhost:8000/api/health` | Liveness check — returns `{"status":"ok","provider":"watsonx"}` |
| `POST http://localhost:8000/api/plan/sprints` | PRD → sprint plan |
| `POST http://localhost:8000/api/plan/tickets` | Sprint → tickets |
| `GET  http://localhost:8000/docs` | Swagger UI (auto-generated) |

**Verify the backend is working:**

```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok","provider":"watsonx"}
```

---

## 4 — Frontend

> ⚠️ The `frontend/` directory does not exist yet — this section is ready for Person C to fill in once the scaffold is created. The steps below follow the expected Vite + React + Tailwind setup from the PRD.

### 4a. Install dependencies

```bash
cd frontend
npm install
```

### 4b. Start the Vite dev server

```bash
npm run dev
```

The frontend is now live at **http://localhost:5173**.

All `/api` requests from the browser are **automatically proxied** to `http://localhost:8000` by the Vite dev server — no CORS issues, no environment variable needed in the frontend.

---

## 5 — Running both at the same time

Open **two terminals** side by side:

**Terminal 1 — backend**
```bash
# From repo root, with .venv active
uvicorn backend.app.main:app --reload --port 8000
```

**Terminal 2 — frontend**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## 6 — Running the tests

```bash
# From repo root, with .venv active
pytest backend/tests/ -v
```

---

## 7 — Trying the API directly (no frontend)

Use the auto-generated Swagger UI at **http://localhost:8000/docs**, or curl:

```bash
# Capability 1 — PRD to sprint plan
curl -X POST http://localhost:8000/api/plan/sprints \
  -H "Content-Type: application/json" \
  -d '{"prd_markdown": "## My App\nUsers can sign up and log in."}'

# Capability 2 — sprint to tickets (replace S1 with the sprint id from the plan above)
curl -X POST http://localhost:8000/api/plan/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "prd_markdown": "## My App\nUsers can sign up and log in.",
    "plan": { ... },
    "sprint_id": "S1"
  }'
```

Sample PRDs are available in [`samples/`](../samples/) — use them as realistic test inputs.

---

## 8 — Common issues

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Run `uvicorn` from the repo root, not from inside `backend/` |
| `KeyError: 'WATSONX_API_KEY'` | `.env` file is missing or the variable name is wrong — check against section 2 above |
| `401 Unauthorized` from watsonx | API key is invalid or expired — regenerate it in IBM Cloud console |
| `502` from `/api/plan/sprints` | The LLM returned invalid JSON twice. Check `uvicorn` logs for the raw response |
| Frontend shows blank page or CORS error | Make sure both servers are running and the Vite proxy is configured (`/api` → `localhost:8000`) |
| `pytest` not found | Virtual environment is not activated — run `.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (macOS/Linux) |
