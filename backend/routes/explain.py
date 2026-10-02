import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loader import runs_by_id
from providers.mock import MockProvider

router = APIRouter(prefix="/api", tags=["explain"])

_provider_name = os.getenv("LLM_PROVIDER", "mock").lower()

if _provider_name == "mock":
    _provider = MockProvider()
else:
    raise RuntimeError(
        f"Unknown LLM_PROVIDER='{_provider_name}'. "
        "Supported values: 'mock'. "
        "Add a real provider in backend/providers/ to extend."
    )

@router.post("/runs/{run_id}/explain")
async def explain_run(run_id: str):
    run = runs_by_id.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    async def _stream():
        async for chunk in _provider.explain(run):
            yield chunk

    return StreamingResponse(
        _stream(),
        media_type="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )
