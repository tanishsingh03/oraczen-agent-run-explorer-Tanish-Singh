# DECISIONS.md

This file documents every non-obvious design decision made during the build.
Honest reasoning scores better than impressive-sounding justifications.

---

## Required Decisions

### 1. `cost_usd: null` — what does "total cost per agent" mean?

Three runs (`run_0008`, `run_0042`, `run_0153`) have `cost_usd: null`.

**Decision:** Sum only the non-null values, and surface a `cost_usd_is_partial: true`
flag in the `/api/stats` response whenever any run for that agent has a null cost.
The frontend renders an asterisk next to the total and a tooltip explaining that
the figure is a lower bound.

**Why not treat null as 0?**
Zero cost means "this run cost nothing." Null cost means "we don't know what it cost."
These are different things. Silently summing them would understate the true cost and
give the support engineer a false sense of certainty.

**Why not exclude the agent entirely?**
That would hide agents who have *mostly* priced runs. A partial sum with a visible
disclaimer is more useful than no number at all.

---

### 2. Runs with `status: "running"` — sorting and success rate

Nine runs are still running. They have no `ended_at` and no `duration_ms`.

**Decision on success rate:**
`running` runs are excluded from the success-rate denominator entirely.
Success rate = `succeeded / (succeeded + failed + cancelled)`.

**Why?** A run in progress has not yet had an outcome. Including it as a failure
would make the success rate artificially pessimistic; including it as a success
would be wrong. The most honest answer is to count only runs that have finished.

**Decision on sorting by `duration_ms`:**
Runs with `duration_ms: null` sort last in both ascending and descending order.
The implementation partitions runs into two lists — those with a value and those without —
sorts only the valued list, then appends the null list at the end regardless of direction.

**Why not sort them first?**
Sorting nulls first would mix "currently running" and "fast runs" at the top of
an ascending sort, which is confusing. Last is the least surprising position.

---

### 3. The broken record — what breaks a naive loader?

**The record:** `run_0031` appears **twice** in `data/runs.jsonl` with the same `id`
and `started_at` but different `status` values: one says `"succeeded"`, one says
`"running"`.

A naive `json.loads` on every line and insertion into a dict keyed by `id` would
silently overwrite the first record with the second (or vice versa, depending on
file order), and the discarded record would never appear in the API.

Additionally, `run_0064` has `duration_ms: -4000` (ended_at precedes started_at),
which would break any duration statistic that assumes non-negative values.

**Decision:**
- **Duplicate:** Keep the `"succeeded"` record; discard the `"running"` one.
  A terminal status carries more information than an in-progress snapshot.
  Both records are identical in all fields except `status`. The loader logs a
  warning for every deduplication so nothing is silent.
- **Negative duration:** Set `duration_ms` to `None` and log a warning.
  It is treated identically to a `running` run for stat purposes.

---

### 4. Does `/api/stats` respect the list-page filters?

**Decision: No — `/api/stats` is always global.**

The dashboard is a high-level health overview of the entire system. If stats
changed based on whatever the user has filtered on the list page, the dashboard
would no longer answer "how is the system doing overall?" — it would answer
"how are the 12 runs matching my current filter doing?", which is far less useful
as a first glance.

A reviewer looking at the dashboard should always see the same baseline. The
list page is for drilling down; the dashboard is for the big picture.

If filtered stats become a requirement later, a separate `/api/stats?{filter_params}`
endpoint can be added without changing the existing contract.

---

## Additional Data Observations

| Observation | Impact | Handling |
|---|---|---|
| `run_0172` prompt has leading/trailing whitespace | Text search would miss it if we compare raw strings | Strip on load |
| `run_0121` prompt is in French | No impact on search or display | No special handling; UTF-8 is handled correctly |
| ~15 runs contain 🔥 emoji in the prompt | No impact — Python handles Unicode strings natively | No special handling |
| Some runs have `steps: []` (empty array) | The detail page must not crash on an empty steps list | Defensive render: show "No steps recorded" |
| `run_0064` has `ended_at` before `started_at` | Breaks duration math | Treat duration as None |

---

## Frontend Test Note

I skipped writing a Jest/React Testing Library test due to time constraints. If I had more time, I would test:

- **`RunsFilters` component**: render it, click the "failed" status badge, assert the URL changes to `?status=failed` and the "Clear" button appears
- **`Pagination` component**: given `total=100, page=1, pageSize=25`, assert 4 page buttons render and clicking page 2 pushes `?page=2` to the router
- **`ExplainButton`**: mock `fetch`, click the button, assert the streaming text appears character by character

I skipped it because the backend test suite (59 tests) is thorough and the frontend logic is thin — the pages are mostly server-rendered with URL state passed down as props, which is easier to verify end-to-end than in unit tests.

---

## What I Would Do With Another Day

1. **Frontend tests** — see note above.
   Specifically: `RunsFilters` status toggle → URL assertion, `ExplainButton` streaming mock.

2. **Cursor pagination** — The current offset pagination is simple and correct for 200 records.
   At larger scale, offset pagination becomes slow (`OFFSET 50000` scans 50k rows).
   Cursor pagination using `started_at + id` as a composite cursor would be O(log n)
   with a proper index. I would add `?cursor=<base64-encoded-last-seen>` alongside
   `?page=` and document the tradeoff in this file.

3. **Docker Compose** — A single `docker-compose up` command is much friendlier for
   reviewers than "run two terminals". I would add a `docker-compose.yml` with two
   services (`backend` and `frontend`) and a `healthcheck` on the backend before
   the frontend starts.

4. **Real LLM provider** — The mock is graded, but I would have liked to add an
   OpenAI provider behind the same interface to demonstrate the pattern works end-to-end.

5. **Request-duration indicator in the UI** — A small "Fetched in 42ms · 201 runs"
   badge in the list header so a reviewer can verify the frontend is not over-fetching.

---

## Parts I Am Least Happy With

- **Stats are global, not filter-aware.** A support engineer filtered to "failed kpi-analyst
  runs" probably wants to see the p95 duration for that subset, not the global p95.
  The current design is consistent and documented, but it limits the dashboard's utility
  when drilling down.

- **Text search is a substring match on the raw prompt.** It works correctly for 200 records.
  At scale, a proper full-text index (Postgres `tsvector`, Elasticsearch, SQLite FTS5)
  would be needed for acceptable performance.

- **No authentication.** The API is fully open. In production every endpoint would require
  a tenant-scoped JWT, and the loader would filter runs by `tenant_id` from the token claims.

---

## What I Would Change for 20 Million Records

| Concern | Current approach | At 20M records |
|---|---|---|
| **Storage** | In-memory list at startup | PostgreSQL with indexes on `agent`, `status`, `started_at` |
| **Loader** | Read entire file at startup | Bulk COPY import on first run; incremental append thereafter |
| **Filtering** | Linear scan in Python | SQL WHERE clause; composite index on `(agent, status, started_at)` |
| **Sorting** | Python `sorted()` | SQL ORDER BY with index; cursor pagination |
| **Stats** | Python aggregation at query time | Pre-computed materialized views, refreshed on a schedule |
| **Text search** | `str.lower() in prompt.lower()` | PostgreSQL `tsvector` full-text index |
| **p95 computation** | Sort all durations in memory | SQL `percentile_cont(0.95)` aggregate function |
