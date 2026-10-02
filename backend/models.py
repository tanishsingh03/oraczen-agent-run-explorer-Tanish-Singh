"""
models.py — Pydantic v2 response models.

WHY separate RunSummary from RunDetail?
  The README explicitly forbids returning steps from the list endpoint.
  Separating models enforces this at the type level — you cannot
  accidentally serialise steps in a list response.

WHY Optional[float] for cost_usd and duration_ms?
  Three runs have cost_usd=null and one has a repaired duration_ms=None.
  Pydantic will serialise None → null in JSON, which is honest.
  Coercing to 0 would be silently wrong (0 cost ≠ unknown cost).

WHY datetime instead of str for timestamps?
  Parsing to datetime lets the sort logic use native comparison rather
  than string comparison (which only works when ISO strings are zero-padded,
  which ours are, but relying on that is fragile).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class StepTokens(BaseModel):
    input: int
    output: int


class Step(BaseModel):
    index: int
    name: str
    tool: str
    status: str
    started_at: datetime
    duration_ms: Optional[int] = None
    input: str
    output: Optional[str] = None
    tokens: StepTokens


class RunError(BaseModel):
    type: str
    message: str
    step_index: int


class RunSummary(BaseModel):
    """Returned by GET /api/runs — NO steps field."""
    id: str
    agent: str
    model: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_tokens: int
    output_tokens: int
    cost_usd: Optional[float] = None
    prompt: str
    error: Optional[RunError] = None
    tenant_id: str


class RunDetail(RunSummary):
    """Returned by GET /api/runs/{id} — extends summary with steps."""
    steps: list[Step] = []


# ── List endpoint response ─────────────────────────────────────────────────────

class RunsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RunSummary]


# ── Stats endpoint response ────────────────────────────────────────────────────

class OverallStats(BaseModel):
    total_runs: int
    success_rate: float                   # 0.0–1.0
    median_duration_ms: Optional[float] = None
    p95_duration_ms: Optional[float] = None


class AgentStats(BaseModel):
    agent: str
    total_runs: int
    success_rate: float
    total_cost_usd: Optional[float] = None   # None when ALL runs have null cost
    cost_usd_is_partial: bool = False         # True when SOME runs have null cost


class DailyCount(BaseModel):
    date: str   # "YYYY-MM-DD"
    count: int


class StatsResponse(BaseModel):
    overall: OverallStats
    per_agent: list[AgentStats]
    daily_counts: list[DailyCount]
