import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path(__file__).parent.parent / "data" / "runs.jsonl"
DATA_PATH = Path(os.getenv("DATA_PATH", str(_DEFAULT_PATH)))


def _load() -> list[dict]:
    raw: list[dict] = []
    seen_ids: dict[str, dict] = {}
    skipped = 0

    with open(DATA_PATH, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue

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

            if run_id in seen_ids:
                existing = seen_ids[run_id]
                if existing.get("status") == "running" and record.get("status") != "running":
                    logger.warning(
                        "Duplicate id %s – replacing running record with %s",
                        run_id, record["status"],
                    )
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
    run_id = record.get("id", "?")

    if record.get("duration_ms") is not None and record["duration_ms"] < 0:
        logger.warning(
            "Run %s has negative duration_ms=%d (clock skew) → set to None",
            run_id, record["duration_ms"],
        )
        record["duration_ms"] = None

    if isinstance(record.get("prompt"), str):
        stripped = record["prompt"].strip()
        if stripped != record["prompt"]:
            logger.warning("Run %s: prompt had leading/trailing whitespace – stripped", run_id)
            record["prompt"] = stripped

    if "steps" not in record or record["steps"] is None:
        record["steps"] = []


    return record


runs: list[dict] = _load()

runs_by_id: dict[str, dict] = {r["id"]: r for r in runs}
