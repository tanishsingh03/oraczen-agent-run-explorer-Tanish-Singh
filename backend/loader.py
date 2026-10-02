"""
loader.py — Loads and validates runs.jsonl into memory at startup.

WHY load into memory?
  201 records is ~300KB. A module-level list is instantaneous to query
  and eliminates any database dependency for the reviewer.
  At 20M records we'd switch to SQLite or Postgres with indexed columns.

WHY strip the prompt?
  run_0172 has leading/trailing whitespace in its prompt field.
  Text search on " DRAFT AN APOLOGY" would miss "DRAFT AN APOLOGY".
  Stripping on load is cheaper than doing it on every search query.

WHY keep run_0031 (succeeded) over run_0031 (running)?
  Both share the same id and started_at. One says succeeded, one says running.
  The succeeded record has actual meaning (the run finished); the running
  record is likely a stale snapshot. We keep the more informative one.
  Decision is documented in DECISIONS.md.

WHY treat negative duration_ms as None?
  run_0064 has ended_at < started_at → duration_ms = -4000.
  This is a clock-skew artifact in the source system. A negative duration
  is not a real measurement. Surfacing -4s would break p95 stats and mislead
  any engineer reading the detail page.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve path relative to this file so it works from any cwd
_DEFAULT_PATH = Path(__file__).parent.parent / "data" / "runs.jsonl"
DATA_PATH = Path(os.getenv("DATA_PATH", str(_DEFAULT_PATH)))


def _load() -> list[dict]:
    raw: list[dict] = []
    seen_ids: dict[str, dict] = {}  # id → already-kept record
    skipped = 0

    with open(DATA_PATH, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue

            # ── Parse JSON ──────────────────────────────────────────────────
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning("Line %d: JSON parse error – %s (skipped)", lineno, exc)
                skipped += 1
                continue

            run_id = record.get("id")
            if not run_id:
                logger.warning("Line %d: missing 'id' field (skipped)", lineno)
                skipped += 1
                continue

            # ── Duplicate ID ────────────────────────────────────────────────
            # run_0031 appears twice: one "succeeded", one "running".
            # Keep "succeeded" because it carries more information.
            if run_id in seen_ids:
                existing = seen_ids[run_id]
                # Prefer any terminal status over "running"
                if existing.get("status") == "running" and record.get("status") != "running":
                    logger.warning(
                        "Duplicate id %s – replacing running record with %s",
                        run_id, record["status"],
                    )
                    # Replace in-place so list order is stable
                    idx = next(i for i, r in enumerate(raw) if r["id"] == run_id)
                    raw[idx] = _repair(record)
                    seen_ids[run_id] = raw[idx]
                else:
                    logger.warning(
                        "Duplicate id %s – keeping existing (%s), discarding (%s)",
                        run_id, existing["status"], record.get("status"),
                    )
                skipped += 1
                continue

            repaired = _repair(record)
            raw.append(repaired)
            seen_ids[run_id] = repaired

    logger.info(
        "Loaded %d runs from %s (%d lines skipped/deduped)",
        len(raw), DATA_PATH, skipped,
    )
    return raw


def _repair(record: dict) -> dict:
    """
    Normalise edge-case fields in-place (returns the same dict).
    All repairs are logged so nothing is silent.
    """
    run_id = record.get("id", "?")

    # Negative duration_ms → treat as unknown
    if record.get("duration_ms") is not None and record["duration_ms"] < 0:
        logger.warning(
            "Run %s has negative duration_ms=%d (clock skew) → set to None",
            run_id, record["duration_ms"],
        )
        record["duration_ms"] = None

    # Strip whitespace from prompt
    if isinstance(record.get("prompt"), str):
        stripped = record["prompt"].strip()
        if stripped != record["prompt"]:
            logger.warning("Run %s: prompt had leading/trailing whitespace – stripped", run_id)
            record["prompt"] = stripped

    # Ensure steps is always a list (defensive)
    if "steps" not in record or record["steps"] is None:
        record["steps"] = []

    # cost_usd: None is valid — do NOT coerce to 0
    # status "running": valid — ended_at and duration_ms will be None

    return record


# ── Module-level singleton loaded once at import time ─────────────────────────
runs: list[dict] = _load()

# Indexed by ID for O(1) detail lookups
runs_by_id: dict[str, dict] = {r["id"]: r for r in runs}
