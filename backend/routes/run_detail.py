"""
routes/run_detail.py — GET /api/runs/{id}

WHY raise 404 instead of returning an empty body?
  HTTP semantics: 200 with empty body means "found nothing", which is ambiguous.
  404 means "this resource does not exist", which is unambiguous and lets the
  frontend render a proper "not found" page without inspecting the body.

WHY sort steps by index?
  The JSONL steps array is already ordered, but we sort defensively because
  a naive shuffle in the loader would silently break the detail view.
"""

from fastapi import APIRouter, HTTPException
from loader import runs_by_id
from models import RunDetail

router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    run = runs_by_id.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    # Sort steps by index defensively
    run_copy = {**run, "steps": sorted(run.get("steps", []), key=lambda s: s.get("index", 0))}
    return RunDetail(**run_copy)
