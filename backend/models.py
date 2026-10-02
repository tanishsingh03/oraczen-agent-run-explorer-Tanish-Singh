

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
    steps: list[Step] = []



class RunsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RunSummary]



class OverallStats(BaseModel):
    total_runs: int
    success_rate: float
    median_duration_ms: Optional[float] = None
    p95_duration_ms: Optional[float] = None


class AgentStats(BaseModel):
    agent: str
    total_runs: int
    success_rate: float
    total_cost_usd: Optional[float] = None
    cost_usd_is_partial: bool = False


class DailyCount(BaseModel):
    date: str
    count: int


class StatsResponse(BaseModel):
    overall: OverallStats
    per_agent: list[AgentStats]
    daily_counts: list[DailyCount]
