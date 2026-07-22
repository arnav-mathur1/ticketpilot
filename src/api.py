"""API Gateway (HTTP API) handlers for the serverless deployment.

- intake_handler:    POST /tickets                          -> enqueue to SQS (async, burst-safe)
- approvals_handler: GET  /approvals                         -> list pending records
                     POST /approvals/{ticket_id}/{decision}  -> approve | reject
"""
import json
import os
import uuid

from .triage_agent.handler import approve_ticket, reject_ticket
from .shared import store

_CORS = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}


def intake_handler(event, context):
    """Accept a ticket and hand it to SQS so triage runs asynchronously."""
    import boto3
    body = json.loads(event.get("body") or "{}")
    text = (body.get("text") or "").strip()
    if not text:
        return {"statusCode": 400, "headers": _CORS,
                "body": json.dumps({"error": "text required"})}
    ticket_id = body.get("id") or f"T-{uuid.uuid4().hex[:8]}"
    boto3.client("sqs").send_message(
        QueueUrl=os.environ["QUEUE_URL"],
        MessageBody=json.dumps({"ticket_id": ticket_id, "text": text}),
    )
    return {"statusCode": 202, "headers": _CORS,
            "body": json.dumps({"ticket_id": ticket_id, "status": "queued"})}


def approvals_handler(event, context):
    """List the human-review queue, or apply an approve/reject decision."""
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    if method == "GET":
        return {"statusCode": 200, "headers": _CORS,
                "body": json.dumps({"pending": store.list_pending()}, default=str)}

    params = event.get("pathParameters") or {}
    ticket_id = params.get("ticket_id")
    decision = (params.get("decision") or "").lower()
    try:
        if decision == "approve":
            rec = approve_ticket(ticket_id)
        elif decision == "reject":
            rec = reject_ticket(ticket_id)
        else:
            return {"statusCode": 400, "headers": _CORS,
                    "body": json.dumps({"error": "decision must be approve|reject"})}
    except KeyError:
        return {"statusCode": 404, "headers": _CORS,
                "body": json.dumps({"error": f"ticket {ticket_id} not found"})}
    return {"statusCode": 200, "headers": _CORS, "body": json.dumps(rec, default=str)}
