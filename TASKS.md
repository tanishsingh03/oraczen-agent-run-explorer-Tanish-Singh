# TASKS.md — Agent Run Explorer

Personal task tracker. Check off items as you go. Each section maps to one commit.

---

## Commit Flow Overview

```
[✅] 1. chore: audit dataset – null costs, running runs, broken record identified
[✅] 2. chore: project scaffold – .gitignore, .env.example, TASKS.md, DECISIONS.md
[✅] 3. feat(backend): validated JSONL loader – dedup run_0031, repair negative duration, strip whitespace
[✅] 4. feat(backend): GET /api/runs – pagination, composable filters, None-last sort, tool filter
[✅] 5. feat(backend): GET /api/runs/{id} – full steps, 404 for unknown IDs
[✅] 6. feat(backend): GET /api/stats – success rate, p95 duration, partial-cost flag, daily counts
[✅] 7. feat(backend): POST /api/runs/{id}/explain – streaming mock provider, word-by-word
[✅] 8. test(backend): 6 tests – filter composition, hand-verified stat, 404, no-steps, pagination
[ ]  9. feat(frontend): Next.js scaffold – App Router, TypeScript, API client
[ ] 10. feat(frontend): /runs list – server render, URL param state, loading/empty/error
[ ] 11. feat(frontend): /runs/[id] detail – steps, streaming explain control
[ ] 12. feat(frontend): /dashboard – stats charts
[ ] 13. test(frontend): component test or DECISIONS.md note
[ ] 14. docs: DECISIONS.md – already written ✅, update after frontend complete
[ ] 15. docs: README – clean setup steps, env vars, run instructions for reviewer
[ ] 16. feat(optional): tool filter ✅ already in /api/runs – deep-link, keyboard nav
```

---

## Commit 1 — Dataset Audit ✅ DONE

**Commit:** `5d1b696` · pushed ✅

- [x] Read `DATA.md` — understand all fields and their nullable/optional nature
- [x] Scan `data/runs.jsonl` for irregularities
- [x] Identify: 3 runs with `cost_usd: null` → `run_0008`, `run_0042`, `run_0153`
- [x] Identify: 1 run with **negative** `duration_ms` → `run_0064` (-4000ms, clock skew)
- [x] Identify: 1 run with empty `steps: []` → `run_0089`
- [x] Identify: 1 **duplicate `id`** → `run_0031` (one succeeded, one running)
- [x] Identify: 9 runs with `status: "running"` — no `ended_at`, no `duration_ms`
- [x] Identify: 1 French prompt → `run_0121` + 1 prompt with leading/trailing whitespace → `run_0172`

---

## Commit 2 — Project Scaffold ✅ DONE

**Commit:** `ae323f1` · pushed ✅

- [x] `backend/` directory created with all subdirs
- [x] `backend/main.py` — FastAPI app with CORS
- [x] `backend/requirements.txt` — fastapi, uvicorn, pytest, httpx
- [x] `backend/providers/` — base.py + mock.py
- [x] `backend/routes/` — runs.py, run_detail.py, stats.py, explain.py
- [x] `backend/tests/` — test_runs.py
- [x] `.env.example` — all env vars listed
- [x] `.gitignore` — covers __pycache__, .env, node_modules, .next, venv
- [x] `TASKS.md` — task tracker
- [x] `DECISIONS.md` — all 4 required decisions answered
- [ ] **PENDING:** `frontend/` scaffold (Commit 9)

---

## Commit 3 — Validated JSONL Loader ✅ DONE

**Commit:** `24f8ee0` · pushed ✅

- [x] `backend/loader.py` — full implementation
- [x] Try/except around every line
- [x] **Duplicate ID `run_0031`:** kept `succeeded`, discarded `running`
- [x] **Negative `duration_ms` on `run_0064`:** set to `None`, warned
- [x] **`cost_usd: null`:** stored as `None`, never coerced to 0
- [x] **`status: "running"`:** kept, `ended_at` and `duration_ms` stay `None`
- [x] **Whitespace prompt `run_0172`:** stripped on load
- [x] Module-level `runs: list[dict]` + `runs_by_id: dict` for O(1) lookup
- [x] Every repair is logged → nothing is silent
- [x] Loads 200 unique runs (201 lines − 1 duplicate)

---

## Commit 4 — GET /api/runs ✅ DONE

**Commit:** `6f08ecd` · pushed ✅

- [x] `backend/models.py` — RunSummary (no steps), RunDetail, RunsResponse, StatsResponse
- [x] `backend/routes/runs.py` — full implementation
- [x] Status filter (multi-value OR)
- [x] Agent filter (multi-value OR)
- [x] `started_after` / `started_before` date range
- [x] Text search on prompt (case-insensitive)
- [x] **Tool filter** (bonus should-build feature — already included)
- [x] Sort by `started_at` / `duration_ms` / `cost_usd` — None values sort last
- [x] Pagination — returns `{ total, page, page_size, items }`
- [x] Steps excluded from list response ✅
- [x] CORS middleware in main.py

---

## Commit 5 — GET /api/runs/{id} ✅ DONE

**Commit:** `e4032ea` · pushed ✅

- [x] `backend/routes/run_detail.py` — full implementation
- [x] `RunDetail` model includes steps array
- [x] Steps sorted by index defensively
- [x] HTTP 404 with `{ "detail": "Run 'X' not found" }` for unknown IDs
- [x] Uses `runs_by_id` dict → O(1) lookup

---

## Commit 6 — GET /api/stats ✅ DONE

**Commit:** `8cb164c` · pushed ✅

- [x] `backend/routes/stats.py` — full implementation
- [x] Overall: total runs, success rate (running excluded from denominator)
- [x] Median + p95 duration — completed runs only, negative durations excluded
- [x] Per-agent: success rate, total cost, `cost_usd_is_partial` flag
- [x] Daily counts — fills ALL days in range, including zero-count days
- [x] Stats are global (documented in DECISIONS.md §4)

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

## Commit 8 — Backend Tests ✅ DONE

**Commit:** `c24f1ef` · pushed ✅  **6/6 PASS ✅**

- [x] `test_two_filters_compose_status_and_agent` — status=failed AND agent=kpi-analyst
- [x] `test_stats_succeeded_email_drafter_matches_raw` — hand-verified against raw JSONL
- [x] `test_three_filters_compose_status_agent_date` — 3 simultaneous filters
- [x] `test_get_unknown_run_returns_404` — unknown ID → 404
- [x] `test_list_endpoint_omits_steps` — no steps key in list response
- [x] `test_pagination_total_and_pages` — pages don't overlap, totals consistent

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
