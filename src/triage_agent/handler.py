import json

from ..shared import store
from .graph import run_triage
from .escalation import should_escalate
#
# store gives: store.save(record), store.set_status(id, status), and the status constants store.PENDING, store.APPROVED, store.REJECTED, store.AUTO_RELEASED

def process_ticket(ticket_id: str, text: str) -> dict:
    result = run_triage(text)
    escalate, reason = should_escalate(result["category"], result["confidence"], text)
    record = {
        "id": ticket_id,
        "text": text,
        "category": result["category"],
        "urgency": result["urgency"],
        "sentiment": result["sentiment"],
        "confidence": result["confidence"],
        "draft_reply": result["draft_reply"],
        "escalated": escalate,
        "reason": reason,
        "status": store.PENDING if escalate else store.AUTO_RELEASED
    }

    return store.save(record)

def approve_ticket(ticket_id: str) -> dict:
    return store.set_status(ticket_id, store.APPROVED)

def reject_ticket(ticket_id: str) -> dict:
    return store.set_status(ticket_id, store.REJECTED)


def handler(event, context):
    """SQS-triggered Lambda entrypoint (Phase 6).

    Each SQS record is {"ticket_id": ..., "text": ...}. Raising on failure lets
    SQS redeliver the message (at-least-once, retry-safe processing).
    """
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        process_ticket(body["ticket_id"], body["text"])
    return {"statusCode": 200}