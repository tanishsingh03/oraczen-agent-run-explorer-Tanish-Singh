# TASKS.md — Agent Run Explorer

Personal task tracker. Check off items as you go. Each section maps to one commit.

---

## Commit Flow Overview

```
[✅] 1. chore: audit dataset – null costs, running runs, broken record identified
[ ]  2. chore: project scaffold – backend/frontend dirs, .env.example, .gitignore
[ ]  3. feat(backend): validated JSONL loader – skip/flag malformed records, handle nulls
[ ]  4. feat(backend): GET /api/runs – pagination, composable filters, sort
[ ]  5. feat(backend): GET /api/runs/{id} – full steps, proper 404
[ ]  6. feat(backend): GET /api/stats – success rate, p95, cost per agent, daily counts
[ ]  7. feat(backend): POST /api/runs/{id}/explain – streaming mock LLM provider
[ ]  8. test(backend): filter composition + hand-verified stat assertions
[ ]  9. feat(frontend): Next.js scaffold – App Router, TypeScript, API client
[ ] 10. feat(frontend): /runs list – server render, URL param state, loading/empty/error
[ ] 11. feat(frontend): /runs/[id] detail – steps, streaming explain control
[ ] 12. feat(frontend): /dashboard – stats charts
[ ] 13. test(frontend): component test or DECISIONS.md note
[ ] 14. docs: DECISIONS.md – all 4 decisions + data irregularity notes
[ ] 15. docs: README – clean setup steps, env vars, run instructions for reviewer
[ ] 16. feat(optional): tool filter / deep-link steps / keyboard nav / Docker Compose
```

---

## Commit 1 — Dataset Audit ✅ DONE

**Branch point:** initial commit on `main`

- [x] Read `DATA.md` — understand all fields and their nullable/optional nature
- [x] Scan `data/runs.jsonl` for irregularities
- [x] Identify: 3 runs with `cost_usd: null`
- [x] Identify: 1 run with **negative** `duration_ms` (ended_at < started_at)
- [x] Identify: 1 run with empty `steps: []`
- [x] Identify: 1 **duplicate `id`** — two records with same id, different status
- [x] Identify: 9 runs with `status: "running"` — no `ended_at`, no `duration_ms`
- [x] Identify: 1 French prompt + 1 prompt with leading/trailing whitespace

---

## Commit 2 — Project Scaffold

**Commit message:** `chore: project scaffold – backend/frontend dirs, .env.example, .gitignore`

### Backend setup
- [ ] Create `backend/` directory
- [ ] Create `backend/main.py` (empty FastAPI app)
- [ ] Create `backend/requirements.txt`
  - `fastapi`, `uvicorn[standard]`, `pytest`, `httpx`
- [ ] Create `backend/.env` (local only, gitignored)

### Frontend setup
- [ ] Scaffold Next.js app in `frontend/` with App Router + TypeScript
  ```bash
  npx create-next-app@latest frontend --typescript --app --no-tailwind --eslint
  ```
- [ ] Install chart library (e.g. `recharts` or `chart.js`)

### Root config
- [ ] Create `.env.example` with all env vars listed:
  ```
  LLM_PROVIDER=mock
  OPENAI_API_KEY=     # optional, only if using real provider
  BACKEND_PORT=8000
  FRONTEND_PORT=3000
  ```
- [ ] Create `.gitignore` — cover `__pycache__`, `.env`, `node_modules`, `.next`
- [ ] Confirm `data/runs.jsonl` is NOT gitignored (it needs to ship with the repo)

---

## Commit 3 — Validated JSONL Loader

**Commit message:** `feat(backend): validated JSONL loader – skip/flag malformed records, handle nulls`

- [ ] Create `backend/loader.py`
- [ ] Parse all 201 lines; wrap each in try/except
- [ ] **Duplicate ID handling:** keep the record whose status is NOT `running`
  (or document your choice in DECISIONS.md — either is fine, just defend it)
- [ ] **Negative duration_ms:** treat as `None` / unknown — do NOT surface it as a real value
- [ ] **cost_usd: null:** store as `None`; never coerce to 0
- [ ] **status: "running":** keep the record; `ended_at` and `duration_ms` stay `None`
- [ ] **Whitespace prompt:** strip on load so text search works correctly
- [ ] Load into memory at startup (a simple module-level list is fine for 201 records)
- [ ] Log a warning for every skipped or repaired record
- [ ] Write a quick sanity check: `assert len(runs) == 200` (201 lines - 1 duplicate)

---

## Commit 4 — GET /api/runs

**Commit message:** `feat(backend): GET /api/runs – pagination, composable filters, sort`

### Endpoint spec
```
GET /api/runs
  ?page=1&page_size=25
  &status=succeeded&status=failed     ← multi-value
  &agent=kpi-analyst&agent=email-drafter
  &started_after=2026-07-01
  &started_before=2026-08-31
  &q=invoice                          ← prompt text search
  &sort_by=started_at|duration_ms|cost_usd
  &sort_dir=asc|desc
```

### Tasks
- [ ] Create `backend/models.py` — Pydantic models for `RunSummary` (no `steps` field)
- [ ] Create `backend/routes/runs.py`
- [ ] Implement filter pipeline (all filters compose via AND logic):
  - [ ] Status filter (multi-value)
  - [ ] Agent filter (multi-value)
  - [ ] `started_after` / `started_before` date range
  - [ ] Text search on `prompt` (case-insensitive substring match)
- [ ] Implement sort:
  - [ ] `started_at` — default, desc
  - [ ] `duration_ms` — runs with `None` duration sort last
  - [ ] `cost_usd` — runs with `None` cost sort last
- [ ] Implement pagination — return `{ total, page, page_size, items: [...] }`
- [ ] **Do NOT include `steps` in list response** — only summary fields
- [ ] Add CORS middleware so frontend can call the API

---

## Commit 5 — GET /api/runs/{id}

**Commit message:** `feat(backend): GET /api/runs/{id} – full steps, proper 404`

- [ ] Create `backend/routes/run_detail.py`
- [ ] Create `RunDetail` Pydantic model (includes `steps` array)
- [ ] Return full run with all steps in index order
- [ ] Return HTTP 404 with `{ "detail": "Run not found" }` for unknown IDs
- [ ] Handle the duplicate-ID case consistently (whichever record you kept in the loader)

---

## Commit 6 — GET /api/stats

**Commit message:** `feat(backend): GET /api/stats – success rate, p95, cost per agent, daily counts`

### Response shape
```json
{
  "overall": {
    "total_runs": 201,
    "success_rate": 0.62,
    "median_duration_ms": 21000,
    "p95_duration_ms": 47000
  },
  "per_agent": [
    {
      "agent": "kpi-analyst",
      "total_runs": 42,
      "success_rate": 0.57,
      "total_cost_usd": 2.31,
      "cost_usd_is_partial": true
    }
  ],
  "daily_counts": [
    { "date": "2026-07-20", "count": 5 }
  ]
}
```

### Tasks
- [ ] Compute overall run count and success rate
  - Decision needed: does `running` count toward success rate? → DECISIONS.md
- [ ] Compute median and p95 duration over **completed** runs only (exclude `running` and negative duration)
- [ ] Compute total cost per agent
  - Exclude `null` costs from the sum; surface `cost_usd_is_partial: true` if any are missing
- [ ] Compute run counts per day across the full date range (include days with 0 runs)
- [ ] Stats are **global** (not filter-aware) — document this in DECISIONS.md

---

## Commit 7 — POST /api/runs/{id}/explain (Streaming)

**Commit message:** `feat(backend): POST /api/runs/{id}/explain – streaming mock LLM provider`

### Architecture
```
backend/providers/
  __init__.py
  base.py          ← abstract ExplainProvider class
  mock.py          ← returns deterministic canned text with artificial delay
  openai.py        ← (optional) real OpenAI provider behind same interface
```

### Tasks
- [ ] Define `ExplainProvider` abstract base class with `async def explain(run) -> AsyncIterator[str]`
- [ ] Implement `MockProvider`:
  - [ ] Reads the run's status, agent, prompt, and error (if any)
  - [ ] Returns a canned multi-sentence explanation (not just "hello world")
  - [ ] Streams word-by-word or chunk-by-chunk with `asyncio.sleep(0.05)` between chunks
  - [ ] Response is **deterministic** — same run always gives same explanation
- [ ] Select provider via `LLM_PROVIDER` env var (`mock` | `openai`)
- [ ] Use `StreamingResponse` from FastAPI with `text/event-stream` content type
- [ ] Return 404 if run ID not found

---

## Commit 8 — Backend Tests

**Commit message:** `test(backend): filter composition + hand-verified stat assertions`

- [ ] Create `backend/tests/test_runs.py`
- [ ] **Test 1: Filter composition** — query `status=failed&agent=kpi-analyst`, assert all returned runs match BOTH filters
- [ ] **Test 2: Filter composition (3 filters)** — add a date range on top, assert count is correct
- [ ] **Test 3: Hand-verified stat** — compute a statistic by hand from the raw JSONL (e.g., total succeeded runs for `email-drafter`), assert `/api/stats` matches
- [ ] **Test 4: 404** — GET `/api/runs/run_9999` returns 404
- [ ] **Test 5: No steps in list** — verify `steps` key is absent from `/api/runs` items
- [ ] Run all tests: `pytest backend/tests/ -v`

---

## Commit 9 — Next.js Frontend Scaffold

**Commit message:** `feat(frontend): Next.js scaffold – App Router, TypeScript, API client`

- [ ] Create `frontend/lib/api.ts` — typed fetch wrapper for all backend endpoints
  ```ts
  export async function getRuns(params: RunsParams): Promise<RunsResponse>
  export async function getRun(id: string): Promise<RunDetail>
  export async function getStats(): Promise<StatsResponse>
  ```
- [ ] Create `frontend/types/index.ts` — TypeScript types matching backend Pydantic models
- [ ] Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`
- [ ] Confirm dev server starts: `npm run dev` in `frontend/`
- [ ] Set up basic layout (`app/layout.tsx`) with fonts + global styles

---

## Commit 10 — /runs List Page

**Commit message:** `feat(frontend): /runs list – server render, URL param state, loading/empty/error`

### Requirements
- [ ] Create `app/runs/page.tsx` as a **Server Component** (fetch on server)
- [ ] All filter/sort/page state lives in **URL search params** (shareable links)
- [ ] Implement filter controls:
  - [ ] Status multi-select (succeeded / failed / cancelled / running)
  - [ ] Agent multi-select
  - [ ] Date range pickers (started_after / started_before)
  - [ ] Text search input
  - [ ] Sort by + direction dropdowns
- [ ] Render "Showing X–Y of Z runs" using `total` from the API
- [ ] Implement pagination controls (prev / next, page numbers)
- [ ] Handle three states visibly:
  - [ ] **Loading** — skeleton or spinner
  - [ ] **Empty** — "No runs match your filters" message
  - [ ] **Error** — "Could not load runs" with retry option
- [ ] Each row links to `/runs/[id]`

---

## Commit 11 — /runs/[id] Detail Page

**Commit message:** `feat(frontend): /runs/[id] detail – steps, streaming explain control`

### Requirements
- [ ] Create `app/runs/[id]/page.tsx`
- [ ] Show run metadata: ID, agent, model, status, started_at, duration, cost, tenant
- [ ] Show error block (if `error` is not null): type, message, which step failed
- [ ] Show steps list in index order:
  - [ ] Step name, tool, status, duration_ms, input_tokens, output_tokens
  - [ ] Step input and output **readable without leaving the page** (expand/collapse or inline)
- [ ] "Explain this run" button:
  - [ ] Calls `POST /api/runs/{id}/explain` and reads the streaming response
  - [ ] Renders text **as it streams in**, not after completion (use `ReadableStream`)
  - [ ] Show a loading indicator while streaming
- [ ] Return 404 page if run not found (use Next.js `notFound()`)

**Should-build (if time):**
- [ ] Deep-link to specific step: `/runs/run_0042#step-3` opens with that step expanded

---

## Commit 12 — /dashboard Page

**Commit message:** `feat(frontend): /dashboard – stats charts`

- [ ] Create `app/dashboard/page.tsx`
- [ ] Fetch from `GET /api/stats`
- [ ] Render at least 2–3 charts:
  - [ ] **Run counts per day** — line or bar chart (show the date range)
  - [ ] **Success rate per agent** — bar or grouped bar chart
  - [ ] **Total cost per agent** — bar chart; flag partial costs visually (e.g. asterisk + note)
- [ ] Show overall summary cards: total runs, overall success rate, median duration, p95 duration
- [ ] Handle loading and error states

---

## Commit 13 — Frontend Test

**Commit message:** `test(frontend): [component test or DECISIONS.md note]`

- [ ] Option A: Write a test with Jest + React Testing Library
  - Suggested: render the `/runs` page with mocked API response, assert filter UI renders
- [ ] Option B: Write a paragraph in `DECISIONS.md` explaining what you *would* test and why you skipped it ("No time" is an acceptable reason if the rest is solid)

---

## Commit 14 — DECISIONS.md

**Commit message:** `docs: DECISIONS.md – all 4 decisions + data irregularity notes`

Must answer all four required questions:
- [ ] **Decision 1:** `cost_usd: null` handling — what does "total cost per agent" mean when some rows are unpriced? Is the UI honest about partial sums?
- [ ] **Decision 2:** `status: "running"` — do they count toward success rate? How do they sort when sorting by `duration_ms`?
- [ ] **Decision 3:** The broken record — which one breaks a naive loader? What did you do about it?
- [ ] **Decision 4:** Does `/api/stats` respect the list-page filters, or is it always global? (Either is fine — just be consistent)

Also include:
- [ ] What you noticed about the data (irregularities beyond the 4 required decisions)
- [ ] What you would do with another day (the "should build" / "stretch" features)
- [ ] Which parts you are least happy with (honest > impressive)
- [ ] What you'd change if the file had 20 million records (loader + storage strategy)

---

## Commit 15 — README (Setup Guide for Reviewer)

**Commit message:** `docs: README – clean setup steps, env vars, run instructions for reviewer`

The reviewer will clone your repo, follow the README, and expect a **working app within 10 minutes**.

- [ ] Prerequisites section: Python 3.x, Node 18+, nothing else assumed
- [ ] Backend setup:
  ```bash
  cd backend
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  cp ../.env.example .env
  uvicorn main:app --reload
  ```
- [ ] Frontend setup:
  ```bash
  cd frontend
  npm install
  cp .env.example .env.local
  npm run dev
  ```
- [ ] How to run tests: `pytest backend/tests/ -v`
- [ ] All env variables listed and explained
- [ ] URL table: where each page lives (e.g. `http://localhost:3000/runs`)
- [ ] **Test this on a fresh clone before submitting**

---

## Commit 16 — Optional Features (if time allows)

**Commit message:** `feat(optional): tool filter, deep-link steps, keyboard nav`

- [ ] `tool` filter on `/api/runs` — matches runs containing a step using that tool
- [ ] Deep-link to specific step: `#step-3` opens with that step expanded
- [ ] Keyboard navigation in list: arrow keys move selection, Enter opens run
- [ ] Request-duration or request-count indicator visible in the UI
- [ ] Docker Compose (`docker-compose.yml`) — brings both services up with one command
- [ ] Cursor pagination alongside offset pagination (with tradeoff note in DECISIONS.md)

---

## Data Irregularities Reference

> From `DATA.md` — keep this handy while coding the loader.

| # | Irregularity | Your handling |
|---|---|---|
| 1 | 3 runs with `cost_usd: null` | Store as `None`, never sum with real values |
| 2 | 1 run with **negative** `duration_ms` | Treat as `None`, log warning |
| 3 | 1 run with empty `steps: []` | Valid — keep the run, render "no steps" in UI |
| 4 | 1 **duplicate `id`** (different statuses) | Keep one, discard other — document choice |
| 5 | 9 `running` runs (no `ended_at`, no `duration_ms`) | Keep, handle nulls, exclude from duration stats |
| 6 | 1 French prompt | No special handling needed — text search works as-is |
| 7 | 1 prompt with leading/trailing whitespace | Strip on load |

---

## Quick Reference

| Thing | Where |
|---|---|
| Raw data | `data/runs.jsonl` |
| Backend | `backend/` → runs on `http://localhost:8000` |
| Frontend | `frontend/` → runs on `http://localhost:3000` |
| API docs | `http://localhost:8000/docs` (FastAPI auto-docs) |
| Task tracker | This file (`TASKS.md`) |
| Data notes | `DATA.md` |
| Design decisions | `DECISIONS.md` (create in commit 14) |
| Env vars template | `.env.example` (create in commit 2) |
