from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from loader import runs
from models import AgentStats, DailyCount, OverallStats, StatsResponse

router = APIRouter(prefix="/api", tags=["stats"])

def _percentile(sorted_vals: list[float], p: float) -> Optional[float]:
    if not sorted_vals:
        return None
    rank = int((p / 100) * len(sorted_vals))
    rank = min(rank, len(sorted_vals) - 1)
    return sorted_vals[rank]

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    total = len(runs)

    terminal = [r for r in runs if r.get("status") != "running"]
    succeeded = [r for r in terminal if r.get("status") == "succeeded"]
    success_rate = len(succeeded) / len(terminal) if terminal else 0.0

    durations = sorted(
        r["duration_ms"] for r in terminal
        if r.get("duration_ms") is not None and r["duration_ms"] >= 0
    )
    median_ms = _percentile(durations, 50)
    p95_ms = _percentile(durations, 95)

    overall = OverallStats(
        total_runs=total,
        success_rate=round(success_rate, 4),
        median_duration_ms=median_ms,
        p95_duration_ms=p95_ms,
    )

    by_agent: dict[str, list[dict]] = defaultdict(list)
    for r in runs:
        by_agent[r.get("agent", "unknown")].append(r)

    per_agent_stats: list[AgentStats] = []
    for agent_name, agent_runs in sorted(by_agent.items()):
        a_terminal = [r for r in agent_runs if r.get("status") != "running"]
        a_succeeded = [r for r in a_terminal if r.get("status") == "succeeded"]
        a_rate = len(a_succeeded) / len(a_terminal) if a_terminal else 0.0

        costs = [r.get("cost_usd") for r in agent_runs]
        non_null_costs = [c for c in costs if c is not None]
        has_null = len(non_null_costs) < len(costs)

        total_cost: Optional[float] = sum(non_null_costs) if non_null_costs else None

        per_agent_stats.append(AgentStats(
            agent=agent_name,
            total_runs=len(agent_runs),
            success_rate=round(a_rate, 4),
            total_cost_usd=round(total_cost, 6) if total_cost is not None else None,
            cost_usd_is_partial=has_null,
        ))

    counts_by_day: dict[date, int] = defaultdict(int)
    for r in runs:
        sa = r.get("started_at", "")
        if sa:
            day = datetime.fromisoformat(sa.replace("Z", "+00:00")).date()
            counts_by_day[day] += 1

    if counts_by_day:
        min_day = min(counts_by_day)
        max_day = max(counts_by_day)
        daily: list[DailyCount] = []
        current = min_day
        while current <= max_day:
            daily.append(DailyCount(date=current.isoformat(), count=counts_by_day[current]))
            current += timedelta(days=1)
    else:
        daily = []

    return StatsResponse(overall=overall, per_agent=per_agent_stats, daily_counts=daily)
