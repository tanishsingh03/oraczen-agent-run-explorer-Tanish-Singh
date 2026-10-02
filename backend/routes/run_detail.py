from fastapi import APIRouter, HTTPException
from loader import runs_by_id
from models import RunDetail

router = APIRouter(prefix="/api", tags=["runs"])

@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    run = runs_by_id.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    run_copy = {**run, "steps": sorted(run.get("steps", []), key=lambda s: s.get("index", 0))}
    return RunDetail(**run_copy)
