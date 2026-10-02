from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
from loader import runs
from models import RunSummary, RunsResponse

router = APIRouter(prefix="/api", tags=["runs"])

_VALID_SORT_FIELDS = {"started_at", "duration_ms", "cost_usd"}
_VALID_SORT_DIRS = {"asc", "desc"}

def _sort_value(run: dict, sort_by: str):
    raw = run.get(sort_by)
    if raw is None:
        return None
    if isinstance(raw, str):
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return raw

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
    filtered = runs

    if status:
        status_set = set(s.lower() for s in status)
        filtered = [r for r in filtered if r.get("status", "").lower() in status_set]

    if agent:
        agent_set = set(a.lower() for a in agent)
        filtered = [r for r in filtered if r.get("agent", "").lower() in agent_set]

    if tool:
        tool_set = set(t.lower() for t in tool)
        filtered = [
            r for r in filtered
            if any(s.get("tool", "").lower() in tool_set for s in r.get("steps", []))
        ]

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

    if q:
        q_lower = q.lower()
        filtered = [r for r in filtered if q_lower in r.get("prompt", "").lower()]

    reverse = sort_dir == "desc"
    has_value = [r for r in filtered if _sort_value(r, sort_by) is not None]
    no_value  = [r for r in filtered if _sort_value(r, sort_by) is None]
    filtered = sorted(has_value, key=lambda r: _sort_value(r, sort_by), reverse=reverse) + no_value

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
