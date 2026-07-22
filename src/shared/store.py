"""Approval-queue store with two interchangeable backends (same function API):

- local: a JSON file under data/runtime/ — $0, no AWS, used for the local demo.
- aws:   DynamoDB — selected via TICKETPILOT_BACKEND=aws.

Each record is a triage result plus its escalation decision and human-review
status, keyed by record["id"].
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

_AWS = config.BACKEND == "aws"


# --- local JSON backend -----------------------------------------------------
def _load() -> dict:
    if QUEUE_PATH.exists():
        return json.loads(QUEUE_PATH.read_text())
    return {}


def _write(data: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(data, indent=2))


# --- DynamoDB backend (lazy so boto3/network aren't touched locally) --------
_table = None


def _ddb():
    global _table
    if _table is None:
        import boto3
        _table = boto3.resource("dynamodb", region_name=config.AWS_REGION) \
                      .Table(config.DDB_TICKETS_TABLE)
    return _table


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(record: dict) -> dict:
    """Insert or update a record (keyed by record['id'])."""
    if _AWS:
        # DynamoDB rejects Python floats; store numbers as strings (parse_float=str).
        _ddb().put_item(Item=json.loads(json.dumps(record), parse_float=str))
        return record
    data = _load()
    data[record["id"]] = record
    _write(data)
    return record


def get(ticket_id: str) -> dict | None:
    if _AWS:
        return _ddb().get_item(Key={"id": ticket_id}).get("Item")
    return _load().get(ticket_id)


def all_records() -> list[dict]:
    if _AWS:
        return _ddb().scan().get("Items", [])   # fine at demo scale
    return list(_load().values())


def list_pending() -> list[dict]:
    return [r for r in all_records() if r.get("status") == PENDING]


def set_status(ticket_id: str, status: str, decided_by: str = "human") -> dict:
    """Flip a record's status and log who decided and when."""
    if _AWS:
        _ddb().update_item(
            Key={"id": ticket_id},
            UpdateExpression="SET #s = :s, decided_by = :b, decided_at = :t",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status, ":b": decided_by, ":t": _now()},
        )
        return get(ticket_id)
    data = _load()
    rec = data.get(ticket_id)
    if rec is None:
        raise KeyError(f"No ticket {ticket_id!r} in queue")
    rec["status"] = status
    rec["decided_by"] = decided_by
    rec["decided_at"] = _now()
    _write(data)
    return rec
