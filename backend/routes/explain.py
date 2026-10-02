"""
routes/explain.py — POST /api/runs/{id}/explain

WHY StreamingResponse with text/plain instead of text/event-stream?
  SSE (Server-Sent Events) requires specific "data: ...\n\n" framing and
  an EventSource client. text/plain with Transfer-Encoding: chunked is
  simpler to consume from a fetch() stream on the frontend using a
  ReadableStream reader — no SSE parser needed. The README says "stream the
  response", not "use SSE specifically".

WHY POST instead of GET?
  The README specifies POST. Conceptually this is a computation, not a
  resource retrieval, so POST is semantically correct even though the
  endpoint is idempotent in practice.

WHY select provider at module load, not per request?
  The provider is stateless once instantiated. Creating a new instance per
  request would be wasteful. Module-level instantiation also makes the
  env-var selection happen once at startup with a clear error if the value
  is unrecognised.
"""

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loader import runs_by_id
from providers.mock import MockProvider

router = APIRouter(prefix="/api", tags=["explain"])

# Select provider via environment variable
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
        headers={"X-Accel-Buffering": "no"},   # disable Nginx buffering if behind a proxy
    )
