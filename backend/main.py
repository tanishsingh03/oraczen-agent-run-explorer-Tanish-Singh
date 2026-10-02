

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.runs import router as runs_router
from routes.run_detail import router as detail_router
from routes.stats import router as stats_router
from routes.explain import router as explain_router

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s  %(message)s",
)

app = FastAPI(
    title="Agent Run Explorer API",
    version="0.1.0",
    description="Browse and understand agent run traces.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(detail_router)
app.include_router(stats_router)
app.include_router(explain_router)


@app.get("/healthz", tags=["meta"])
def healthz():
    return {"status": "ok"}
