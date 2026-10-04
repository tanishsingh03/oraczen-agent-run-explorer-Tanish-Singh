# Agent Run Explorer

A web tool for browsing and understanding agent execution traces.

## Prerequisites

- Python 3.10+
- Node.js 18+


---

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd oraczen-agent-run-explorer
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload
```

Backend runs at **http://localhost:8000**  
API docs at **http://localhost:8000/docs**

### 3. Frontend

Open a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local      # sets NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Frontend runs at **http://localhost:3000**

---

## Pages

| URL | What it does |
|-----|-------------|
| `http://localhost:3000/runs` | Filterable, sortable, paginated run list |
| `http://localhost:3000/runs/{id}` | Full run detail: metadata, steps, streaming explain |
| `http://localhost:3000/dashboard` | Stats charts: daily volume, success rate, cost per agent |

---

## Running tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

59 tests, all passing.

---

## Environment variables

All variables are in `.env.example`. The only one you need to change for local dev is:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `mock` | Use `mock` (no key needed) or `openai` |
| `OPENAI_API_KEY` | _(empty)_ | Only needed when `LLM_PROVIDER=openai` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → backend URL |

The grading mock provider works with `LLM_PROVIDER=mock` and no API key.

---

## What the loader does

- Loads `data/runs.jsonl` into memory at startup (200 unique runs after dedup)
- Deduplicates `run_0031` (duplicate ID, different statuses — keeps `succeeded`)
- Repairs `run_0064` (negative `duration_ms` → set to `None`)
- Strips prompt whitespace from `run_0172`
- Logs every repair; nothing is silent

See `DECISIONS.md` for the full reasoning on each data decision.
