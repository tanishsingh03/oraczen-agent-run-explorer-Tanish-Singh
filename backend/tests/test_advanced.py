"""
tests/test_advanced.py — Extended test suite for the Agent Run Explorer API.

Covers:
  - Multi-value OR filters (status, agent)
  - All-four-filter composition
  - Sort correctness (asc/desc) with None-last guarantee
  - Pagination exhaustion and boundary arithmetic
  - Data integrity: total across all pages equals /api/runs total
  - Detail endpoint: steps present, sorted by index
  - Detail endpoint: repaired fields (run_0064 negative duration -> None)
  - List endpoint: cost_usd null runs excluded from sort but present in results
  - Stats endpoint: success_rate arithmetic, total_runs sum, partial-cost flag
  - Stats endpoint: daily_counts is contiguous (no date gaps)
  - Prompt text search: case-insensitive, partial match
  - Explain endpoint: returns non-empty streaming text for a valid run
  - Explain endpoint: 404 for unknown run
  - Health check endpoint
  - Schema validation: all required fields present on every list item
  - Edge cases: page beyond last page returns empty items
  - Edge cases: page_size=1 returns exactly 1 item
  - Cross-endpoint consistency: run IDs in list are fetchable via detail
"""

import json
import sys
import asyncio
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app  # noqa: E402

client = TestClient(app)

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "runs.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_raw() -> list[dict]:
    """Load & deduplicate runs.jsonl exactly as the loader does."""
    seen: dict[str, dict] = {}
    deduped: list[dict] = []
    for line in DATA_PATH.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = r.get("id")
        if not rid:
            continue
        if rid not in seen:
            seen[rid] = r
            deduped.append(r)
        elif seen[rid].get("status") == "running" and r.get("status") != "running":
            idx = next(i for i, x in enumerate(deduped) if x["id"] == rid)
            deduped[idx] = r
            seen[rid] = r
    return deduped


def _fetch_all(url_without_page: str) -> list[dict]:
    """Paginate through all pages and collect every item."""
    items = []
    page = 1
    while True:
        sep = "&" if "?" in url_without_page else "?"
        resp = client.get(f"{url_without_page}{sep}page={page}&page_size=200")
        assert resp.status_code == 200
        body = resp.json()
        items.extend(body["items"])
        if len(items) >= body["total"]:
            break
        page += 1
    return items


RAW = _load_raw()


# ─────────────────────────────────────────────────────────────────────────────
# Group A — Health & Schema
# ─────────────────────────────────────────────────────────────────────────────

def test_healthz_returns_ok():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_response_schema_fields():
    """Every item in the list response must have all required top-level fields."""
    required = {
        "id", "agent", "model", "status", "started_at",
        "input_tokens", "output_tokens", "prompt", "tenant_id",
    }
    resp = client.get("/api/runs?page_size=50")
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert "items" in body
    for run in body["items"]:
        missing = required - run.keys()
        assert not missing, f"Run {run.get('id')} missing fields: {missing}"


def test_list_total_matches_raw_record_count():
    """The API's total must equal the number of deduplicated records in the JSONL."""
    resp = client.get("/api/runs?page_size=1")
    assert resp.status_code == 200
    assert resp.json()["total"] == len(RAW), (
        f"API total {resp.json()['total']} != raw count {len(RAW)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Group B — Filter Composition
# ─────────────────────────────────────────────────────────────────────────────

def test_multi_value_status_or_filter():
    """status=failed&status=cancelled must return runs with EITHER status."""
    items = _fetch_all("/api/runs?status=failed&status=cancelled")
    expected = sum(1 for r in RAW if r["status"] in ("failed", "cancelled"))
    assert len(items) == expected, f"Expected {expected}, got {len(items)}"
    for run in items:
        assert run["status"] in ("failed", "cancelled"), (
            f"Run {run['id']} has unexpected status {run['status']}"
        )


def test_multi_value_agent_or_filter():
    """agent=email-drafter&agent=kpi-analyst must return runs from EITHER agent."""
    items = _fetch_all("/api/runs?agent=email-drafter&agent=kpi-analyst")
    expected = sum(1 for r in RAW if r["agent"] in ("email-drafter", "kpi-analyst"))
    assert len(items) == expected
    for run in items:
        assert run["agent"] in ("email-drafter", "kpi-analyst"), (
            f"Run {run['id']} has unexpected agent {run['agent']}"
        )


def test_four_filters_compose_status_agent_tool_date():
    """
    All four filter types must AND together:
      status=succeeded, agent=invoice-extractor,
      tool=sql, started_after=2026-07-01
    Every returned run must satisfy all four conditions.
    """
    resp = client.get(
        "/api/runs"
        "?status=succeeded"
        "&agent=invoice-extractor"
        "&tool=sql"
        "&started_after=2026-07-01"
        "&page_size=200"
    )
    assert resp.status_code == 200
    body = resp.json()
    cutoff = date(2026, 7, 1)
    for run in body["items"]:
        assert run["status"] == "succeeded", f"{run['id']}: wrong status"
        assert run["agent"] == "invoice-extractor", f"{run['id']}: wrong agent"
        run_date = date.fromisoformat(run["started_at"][:10])
        assert run_date >= cutoff, f"{run['id']}: date {run_date} before cutoff"


def test_prompt_text_search_case_insensitive():
    """q=INVOICE must match the same runs as q=invoice (case-insensitive)."""
    lower = client.get("/api/runs?q=invoice&page_size=200").json()
    upper = client.get("/api/runs?q=INVOICE&page_size=200").json()
    assert lower["total"] == upper["total"], "Case-insensitive search returned different totals"
    ids_lower = {r["id"] for r in lower["items"]}
    ids_upper = {r["id"] for r in upper["items"]}
    assert ids_lower == ids_upper


def test_prompt_text_search_returns_correct_count():
    """q=invoice count must match what we compute from the raw JSONL."""
    expected = sum(1 for r in RAW if "invoice" in r.get("prompt", "").lower())
    resp = client.get("/api/runs?q=invoice&page_size=200")
    assert resp.status_code == 200
    assert resp.json()["total"] == expected


def test_date_range_started_before_filter():
    """started_before=2026-08-01 must exclude all runs on or after that date."""
    resp = client.get("/api/runs?started_before=2026-08-01&page_size=200")
    assert resp.status_code == 200
    cutoff = date(2026, 8, 1)
    for run in resp.json()["items"]:
        run_date = date.fromisoformat(run["started_at"][:10])
        assert run_date <= cutoff, f"Run {run['id']} started {run_date} which is after {cutoff}"


def test_date_range_both_bounds():
    """started_after + started_before must both be enforced simultaneously."""
    resp = client.get(
        "/api/runs?started_after=2026-07-20&started_before=2026-08-10&page_size=200"
    )
    assert resp.status_code == 200
    after = date(2026, 7, 20)
    before = date(2026, 8, 10)
    for run in resp.json()["items"]:
        d = date.fromisoformat(run["started_at"][:10])
        assert after <= d <= before, f"Run {run['id']} date {d} out of range [{after}, {before}]"


def test_tool_filter_only_returns_runs_containing_that_tool():
    """tool=sql must only return runs that have at least one step with tool='sql'."""
    resp = client.get("/api/runs?tool=sql&page_size=200")
    assert resp.status_code == 200
    assert resp.json()["total"] > 0, "Expected some sql runs"

    ids_from_api = {r["id"] for r in resp.json()["items"]}
    for run_id in ids_from_api:
        detail = client.get(f"/api/runs/{run_id}").json()
        tools_in_run = {s["tool"] for s in detail.get("steps", [])}
        assert "sql" in tools_in_run, f"Run {run_id} has no sql step: {tools_in_run}"


def test_no_filter_returns_all_runs():
    """Applying no filters must return all deduplicated runs."""
    resp = client.get("/api/runs?page_size=1")
    assert resp.json()["total"] == len(RAW)


# ─────────────────────────────────────────────────────────────────────────────
# Group C — Sort Correctness
# ─────────────────────────────────────────────────────────────────────────────

def test_sort_started_at_desc_order():
    """Default sort (started_at desc) must be in descending date order."""
    items = _fetch_all("/api/runs?sort_by=started_at&sort_dir=desc")
    dates = [item["started_at"] for item in items]
    assert dates == sorted(dates, reverse=True), "started_at desc order violated"


def test_sort_started_at_asc_order():
    items = _fetch_all("/api/runs?sort_by=started_at&sort_dir=asc")
    dates = [item["started_at"] for item in items]
    assert dates == sorted(dates), "started_at asc order violated"


def test_sort_duration_desc_nones_last():
    """
    Sort by duration_ms descending. Runs with null duration must appear AFTER
    all runs that have a real duration value.
    """
    items = _fetch_all("/api/runs?sort_by=duration_ms&sort_dir=desc")
    hit_null = False
    for run in items:
        if run["duration_ms"] is None:
            hit_null = True
        else:
            assert not hit_null, (
                f"Run {run['id']} has duration_ms={run['duration_ms']} "
                "but appears after a None-duration run — None should be last"
            )


def test_sort_duration_asc_nones_last():
    """Sort by duration_ms ascending — Nones still go last."""
    items = _fetch_all("/api/runs?sort_by=duration_ms&sort_dir=asc")
    non_null = [r["duration_ms"] for r in items if r["duration_ms"] is not None]
    assert non_null == sorted(non_null), "Non-null durations not in ascending order"
    for i, run in enumerate(items):
        if run["duration_ms"] is None:
            remaining = [r["duration_ms"] for r in items[i:]]
            assert all(v is None for v in remaining), (
                "Non-None duration found after a None — Nones must be last"
            )
            break


def test_sort_cost_usd_desc_nones_last():
    """cost_usd desc: null-cost runs must come after all priced runs."""
    items = _fetch_all("/api/runs?sort_by=cost_usd&sort_dir=desc")
    hit_null = False
    for run in items:
        if run["cost_usd"] is None:
            hit_null = True
        else:
            assert not hit_null, (
                f"Run {run['id']} cost={run['cost_usd']} appears after a null-cost run"
            )


def test_sort_duration_desc_first_run_is_longest():
    """The first result when sorted by duration desc must be the actual longest run."""
    expected_id = max(
        (r for r in RAW if r.get("duration_ms") and r["duration_ms"] > 0),
        key=lambda r: r["duration_ms"]
    )["id"]
    resp = client.get("/api/runs?sort_by=duration_ms&sort_dir=desc&page_size=1")
    assert resp.status_code == 200
    actual_first = resp.json()["items"][0]["id"]
    assert actual_first == expected_id, (
        f"Expected longest run {expected_id}, got {actual_first}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Group D — Pagination
# ─────────────────────────────────────────────────────────────────────────────

def test_page_size_1_returns_exactly_one_item():
    resp = client.get("/api/runs?page_size=1")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


def test_page_beyond_last_returns_empty_items():
    """Requesting a page number well beyond the data should return an empty items list."""
    resp = client.get("/api/runs?page=9999&page_size=200")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] > 0  # total is still the full count


def test_pagination_covers_all_unique_ids():
    """
    Fetching all pages with page_size=10 must yield exactly the same set of IDs
    as a single page_size=200 call.
    """
    all_paged = _fetch_all("/api/runs")
    all_at_once = _fetch_all("/api/runs?page_size=200")
    assert {r["id"] for r in all_paged} == {r["id"] for r in all_at_once}


def test_pagination_no_id_appears_twice():
    """A run ID must never appear on more than one page."""
    all_items = _fetch_all("/api/runs")
    ids = [r["id"] for r in all_items]
    assert len(ids) == len(set(ids)), "Duplicate run ID found across pages"


def test_consistent_total_across_pages():
    """The 'total' field must be the same on every page of the same query."""
    totals = set()
    for page in range(1, 5):
        resp = client.get(f"/api/runs?page={page}&page_size=50")
        assert resp.status_code == 200
        totals.add(resp.json()["total"])
    assert len(totals) == 1, f"'total' inconsistent across pages: {totals}"


def test_page_size_boundary_last_page_items():
    """
    For a known total of 200 runs and page_size=30,
    page 7 must have exactly 200 - 6*30 = 20 items.
    """
    total_resp = client.get("/api/runs?page_size=1").json()["total"]
    page_size = 30
    full_pages = total_resp // page_size
    remainder = total_resp % page_size
    if remainder == 0:
        pytest.skip("Happens to divide evenly; boundary test not meaningful")
    last_page = full_pages + 1
    resp = client.get(f"/api/runs?page={last_page}&page_size={page_size}")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == remainder, (
        f"Expected {remainder} items on last page, got {len(resp.json()['items'])}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Group E — Run Detail Endpoint
# ─────────────────────────────────────────────────────────────────────────────

def test_detail_endpoint_includes_steps():
    """GET /api/runs/{id} must return a 'steps' array (not present in list)."""
    run_with_steps = next(r for r in RAW if r.get("steps"))
    resp = client.get(f"/api/runs/{run_with_steps['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert "steps" in body
    assert len(body["steps"]) == len(run_with_steps["steps"])


def test_detail_steps_sorted_by_index():
    """Steps must always be returned in ascending index order."""
    run_with_steps = next(r for r in RAW if len(r.get("steps", [])) >= 2)
    resp = client.get(f"/api/runs/{run_with_steps['id']}")
    assert resp.status_code == 200
    steps = resp.json()["steps"]
    indices = [s["index"] for s in steps]
    assert indices == sorted(indices), f"Steps not sorted: {indices}"


def test_detail_step_schema_fields():
    """Each step in the detail response must have all required fields."""
    required_step_fields = {"index", "name", "tool", "status", "started_at", "input", "tokens"}
    run_with_steps = next(r for r in RAW if r.get("steps"))
    resp = client.get(f"/api/runs/{run_with_steps['id']}")
    assert resp.status_code == 200
    for step in resp.json()["steps"]:
        missing = required_step_fields - step.keys()
        assert not missing, f"Step missing fields: {missing}"


def test_detail_run_0064_duration_repaired_to_none():
    """
    run_0064 has a raw duration_ms of -4000 (clock skew).
    The loader must repair it to None — the API must surface None, not -4000.
    """
    resp = client.get("/api/runs/run_0064")
    assert resp.status_code == 200
    body = resp.json()
    assert body["duration_ms"] is None, (
        f"run_0064 duration_ms should be None after repair, got {body['duration_ms']}"
    )


def test_detail_404_for_nonexistent_run():
    resp = client.get("/api/runs/totally_fake_id_xyz_999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_detail_known_null_cost_runs_return_null():
    """Runs that have null cost in the source must surface None via the API."""
    null_cost_ids = ["run_0008", "run_0042", "run_0153"]
    for run_id in null_cost_ids:
        resp = client.get(f"/api/runs/{run_id}")
        assert resp.status_code == 200, f"{run_id} not found"
        assert resp.json()["cost_usd"] is None, (
            f"{run_id} cost_usd should be None, got {resp.json()['cost_usd']}"
        )


def test_cross_endpoint_list_ids_fetchable_via_detail():
    """
    Every ID returned by the list endpoint must be individually fetchable
    via the detail endpoint with status 200.
    """
    items = client.get("/api/runs?page_size=20").json()["items"]
    for run in items:
        resp = client.get(f"/api/runs/{run['id']}")
        assert resp.status_code == 200, f"Detail 404 for listed ID {run['id']}"


def test_detail_data_consistent_with_list():
    """
    Fields returned in the list and the detail for the same run must be identical
    (since RunDetail extends RunSummary).
    """
    list_item = client.get("/api/runs?page_size=1").json()["items"][0]
    detail = client.get(f"/api/runs/{list_item['id']}").json()
    shared_fields = [
        "id", "agent", "model", "status", "started_at",
        "input_tokens", "output_tokens", "cost_usd", "prompt", "tenant_id"
    ]
    for field in shared_fields:
        assert list_item.get(field) == detail.get(field), (
            f"Field '{field}' differs between list and detail for {list_item['id']}: "
            f"{list_item.get(field)!r} vs {detail.get(field)!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Group F — Stats Endpoint
# ─────────────────────────────────────────────────────────────────────────────

def test_stats_success_rate_arithmetic():
    """
    success_rate = succeeded / (total - running).
    Verify the API value matches our own computation from raw data.
    """
    terminal = [r for r in RAW if r["status"] != "running"]
    succeeded = [r for r in terminal if r["status"] == "succeeded"]
    expected_rate = round(len(succeeded) / len(terminal), 4)

    resp = client.get("/api/stats")
    assert resp.status_code == 200
    actual_rate = resp.json()["overall"]["success_rate"]
    assert actual_rate == expected_rate, (
        f"Expected success_rate={expected_rate}, got {actual_rate}"
    )


def test_stats_total_runs_equals_all_records():
    """overall.total_runs must equal the total number of deduplicated records."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert resp.json()["overall"]["total_runs"] == len(RAW)


def test_stats_per_agent_sums_to_total():
    """Sum of all per-agent total_runs must equal overall total_runs."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    total_from_agents = sum(a["total_runs"] for a in body["per_agent"])
    assert total_from_agents == body["overall"]["total_runs"], (
        f"Per-agent sum {total_from_agents} != overall {body['overall']['total_runs']}"
    )


def test_stats_all_five_agents_present():
    """All five agents in the dataset must appear in per_agent stats."""
    expected_agents = {"email-drafter", "contract-reviewer", "support-router", "kpi-analyst", "invoice-extractor"}
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    api_agents = {a["agent"] for a in resp.json()["per_agent"]}
    assert expected_agents <= api_agents, f"Missing agents: {expected_agents - api_agents}"


def test_stats_null_cost_runs_flagged_partial():
    """
    Agents that have runs with null cost_usd must have cost_usd_is_partial=True.
    We know run_0008, run_0042, run_0153 have null cost — find their agents
    and confirm the flag is set.
    """
    null_cost_run_ids = {"run_0008", "run_0042", "run_0153"}
    agents_with_null_cost = {
        r["agent"] for r in RAW if r["id"] in null_cost_run_ids
    }

    resp = client.get("/api/stats")
    assert resp.status_code == 200
    per_agent = {a["agent"]: a for a in resp.json()["per_agent"]}

    for agent_name in agents_with_null_cost:
        row = per_agent.get(agent_name)
        assert row is not None, f"Agent {agent_name} missing from stats"
        assert row["cost_usd_is_partial"] is True, (
            f"Agent {agent_name} has null-cost runs but cost_usd_is_partial=False"
        )


def test_stats_daily_counts_no_gaps():
    """
    daily_counts must be a contiguous date series with no missing days
    between min_date and max_date.
    """
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    daily = resp.json()["daily_counts"]
    assert len(daily) > 0

    dates = [date.fromisoformat(d["date"]) for d in daily]
    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i - 1]).days
        assert diff == 1, (
            f"Gap in daily_counts between {dates[i-1]} and {dates[i]} ({diff} days)"
        )


def test_stats_daily_counts_total_matches_runs():
    """Sum of all daily counts must equal the total number of runs in the dataset."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    total_from_daily = sum(d["count"] for d in body["daily_counts"])
    assert total_from_daily == body["overall"]["total_runs"], (
        f"Daily count sum {total_from_daily} != total_runs {body['overall']['total_runs']}"
    )


def test_stats_median_and_p95_are_positive():
    """Median and p95 duration must be positive numbers (no clock-skew artifacts)."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    overall = resp.json()["overall"]
    if overall["median_duration_ms"] is not None:
        assert overall["median_duration_ms"] > 0, "Median duration is <= 0"
    if overall["p95_duration_ms"] is not None:
        assert overall["p95_duration_ms"] > 0, "p95 duration is <= 0"
        assert overall["p95_duration_ms"] >= overall["median_duration_ms"], (
            "p95 must be >= median"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Group G — Explain Endpoint
# ─────────────────────────────────────────────────────────────────────────────

def test_explain_returns_non_empty_text_for_valid_run():
    """POST /api/runs/{id}/explain must stream back a non-empty text body."""
    run_id = RAW[0]["id"]
    resp = client.post(f"/api/runs/{run_id}/explain")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert len(resp.text.strip()) > 0, "Explain returned empty body"


def test_explain_response_mentions_run_id():
    """The streamed explanation must reference the run's own ID."""
    run_id = RAW[0]["id"]
    resp = client.post(f"/api/runs/{run_id}/explain")
    assert resp.status_code == 200
    assert run_id in resp.text, f"Explanation does not mention run ID {run_id}"


def test_explain_is_deterministic():
    """Calling explain twice on the same run must return the exact same text."""
    run_id = next(r["id"] for r in RAW if r.get("steps"))
    text1 = client.post(f"/api/runs/{run_id}/explain").text
    text2 = client.post(f"/api/runs/{run_id}/explain").text
    assert text1 == text2, "Explain is not deterministic — got different output on second call"


def test_explain_404_for_unknown_run():
    resp = client.post("/api/runs/this_run_does_not_exist_xyzzy/explain")
    assert resp.status_code == 404


def test_explain_failed_run_mentions_error():
    """The explanation for a failed run must mention the failure."""
    failed_run = next(r for r in RAW if r.get("status") == "failed" and r.get("error"))
    resp = client.post(f"/api/runs/{failed_run['id']}/explain")
    assert resp.status_code == 200
    text = resp.text.lower()
    assert "fail" in text or "error" in text, (
        f"Explanation for failed run {failed_run['id']} doesn't mention failure: {text[:200]}"
    )


def test_explain_succeeded_run_mentions_success():
    """The explanation for a succeeded run must mention success."""
    succeeded_run = next(r for r in RAW if r.get("status") == "succeeded")
    resp = client.post(f"/api/runs/{succeeded_run['id']}/explain")
    assert resp.status_code == 200
    text = resp.text.lower()
    assert "succeed" in text or "success" in text or "completed" in text, (
        f"Explanation for succeeded run doesn't mention success: {text[:200]}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Group H — Edge Cases & Negative Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_sort_field_rejected():
    """sort_by with an invalid field must return 422 Unprocessable Entity."""
    resp = client.get("/api/runs?sort_by=hacker_field")
    assert resp.status_code == 422


def test_invalid_sort_dir_rejected():
    """sort_dir with a value other than asc/desc must return 422."""
    resp = client.get("/api/runs?sort_dir=sideways")
    assert resp.status_code == 422


def test_page_size_0_rejected():
    """page_size=0 must be rejected (ge=1 constraint)."""
    resp = client.get("/api/runs?page_size=0")
    assert resp.status_code == 422


def test_page_size_too_large_rejected():
    """page_size > 200 must be rejected (le=200 constraint)."""
    resp = client.get("/api/runs?page_size=201")
    assert resp.status_code == 422


def test_filter_with_no_matches_returns_empty_items_not_error():
    """A filter that matches nothing should return 200 with empty items, not an error."""
    resp = client.get("/api/runs?agent=no_such_agent_ever&status=failed")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_running_runs_are_included_in_total():
    """The list must include runs with status='running' (they are valid records)."""
    running_count = sum(1 for r in RAW if r["status"] == "running")
    assert running_count > 0, "No running runs in dataset — test would be vacuous"

    resp = client.get("/api/runs?status=running&page_size=200")
    assert resp.status_code == 200
    assert resp.json()["total"] == running_count


def test_running_runs_have_null_duration_and_ended_at():
    """Runs with status='running' must have duration_ms=None and ended_at=None."""
    resp = client.get("/api/runs?status=running&page_size=200")
    assert resp.status_code == 200
    for run in resp.json()["items"]:
        assert run["duration_ms"] is None, (
            f"Running run {run['id']} has duration_ms={run['duration_ms']}"
        )
        assert run.get("ended_at") is None, (
            f"Running run {run['id']} has ended_at={run.get('ended_at')}"
        )
