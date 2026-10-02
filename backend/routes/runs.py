"""
routes/runs.py — GET /api/runs

WHY composable filter pipeline instead of separate endpoints?
  The README requirement is explicit: "Filters must compose. Two agents plus
  one status plus a date range plus a sort is a single valid request."
  A single function that reduces through all active filters is the cleanest
  implementation: each filter is an independent predicate and they AND together.

WHY sort None values last?
  Runs with status "running" have no duration_ms. Runs with unknown cost have
  no cost_usd. Sorting them as 0 would put them at the top for ascending sorts,
  which is misleading. Sorting them last is the least surprising behaviour for
  an engineer scanning the list.

WHY parse date params as date not datetime?
  started_after=2026-07-20 should match runs starting on that day, not just
  runs starting after midnight. Comparing date(started_at) >= started_after
  is more intuitive than requiring the user to pass a full ISO timestamp.
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
from loader import runs
from models import RunSummary, RunsResponse

router = APIRouter(prefix="/api", tags=["runs"])

_VALID_SORT_FIELDS = {"started_at", "duration_ms", "cost_usd"}
_VALID_SORT_DIRS = {"asc", "desc"}


def _sort_key(run: dict, sort_by: str, sort_dir: str):
    """
    Returns a tuple (has_value, value) so None sorts last regardless of direction.
    has_value=0 means the field is None → always sorts after real values.
    """
    raw = run.get(sort_by)
    if raw is None:
        return (0, None)
    if isinstance(raw, str):
        # started_at is an ISO string in the raw dict
        raw = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return (1, raw)


@router.get("/runs", response_model=RunsResponse)
def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    status: list[str] = Query(default=[]),
    agent: list[str] = Query(default=[]),
    tool: list[str] = Query(default=[]),
    started_after: Optional[date] = Query(default=None),
    started_before: Optional[date] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Case-insensitive prompt text search"),
    sort_by: str = Query(default="started_at", pattern="^(started_at|duration_ms|cost_usd)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    filtered = runs  # start with full list

    # ── Filter: status (multi-value OR) ───────────────────────────────────────
    if status:
        status_set = set(s.lower() for s in status)
        filtered = [r for r in filtered if r.get("status", "").lower() in status_set]

    # ── Filter: agent (multi-value OR) ────────────────────────────────────────
    if agent:
        agent_set = set(a.lower() for a in agent)
        filtered = [r for r in filtered if r.get("agent", "").lower() in agent_set]

    # ── Filter: tool (matches runs containing a step using that tool) ──────────
    if tool:
        tool_set = set(t.lower() for t in tool)
        filtered = [
            r for r in filtered
            if any(s.get("tool", "").lower() in tool_set for s in r.get("steps", []))
        ]

    # ── Filter: date range ────────────────────────────────────────────────────
    if started_after or started_before:
        def in_range(r: dict) -> bool:
            sa = r.get("started_at", "")
            if not sa:
                return False
            run_date = datetime.fromisoformat(sa.replace("Z", "+00:00")).date()
            if started_after and run_date < started_after:
                return False
            if started_before and run_date > started_before:
                return False
            return True
        filtered = [r for r in filtered if in_range(r)]

    # ── Filter: text search on prompt ─────────────────────────────────────────
    if q:
        q_lower = q.lower()
        filtered = [r for r in filtered if q_lower in r.get("prompt", "").lower()]

    # ── Sort ───────────────────────────────────────────────────────────────────
    reverse = sort_dir == "desc"
    filtered = sorted(
        filtered,
        key=lambda r: _sort_key(r, sort_by, sort_dir),
        reverse=reverse,
    )

    # ── Paginate ───────────────────────────────────────────────────────────────
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return RunsResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[RunSummary(**r) for r in page_items],
    )
