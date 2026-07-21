"""Approval-queue store: a tiny JSON-file-backed record store.

Stands in for DynamoDB. Each record is a triage result plus its
escalation decision and human-review status, persisted to data/runtime/queue.json.
Records are keyed by id; the file is a JSON object {id: record}.
"""

import json
from datetime import datetime, timezone

from . import config

QUEUE_PATH = config.DATA_DIR / "runtime" / "queue.json"

# status lifecycle
PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
AUTO_RELEASED = "auto_released"


def _load() -> dict:
    if QUEUE_PATH.exists():
        return json.loads(QUEUE_PATH.read_text())
    return {}


def _write(data: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(data, indent=2))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(record: dict) -> dict:
    """Insert or update a record (keyed by record['id'])."""
    data = _load()
    data[record["id"]] = record
    _write(data)
    return record


def get(ticket_id: str) -> dict | None:
    return _load().get(ticket_id)


def all_records() -> list[dict]:
    return list(_load().values())


def list_pending() -> list[dict]:
    return [r for r in _load().values() if r.get("status") == PENDING]


def set_status(ticket_id: str, status: str, decided_by: str = "human") -> dict:
    """Flip a record's status and log who decided and when."""
    data = _load()
    rec = data.get(ticket_id)
    if rec is None:
        raise KeyError(f"No ticket {ticket_id!r} in queue")
    rec["status"] = status
    rec["decided_by"] = decided_by
    rec["decided_at"] = _now()
    _write(data)
    return rec
