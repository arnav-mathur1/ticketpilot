"""Lambda handler: API Gateway POST /ask -> grounded policy answer."""
import json

from .answer import answer_question
from ..shared.logging_utils import get_logger, log_event

_CORS = {"Content-Type": "application/json"}   # CORS handled at the HTTP API level
logger = get_logger("rag.handler")


def handler(event, context):
    body = json.loads(event.get("body") or "{}")
    question = (body.get("question") or "").strip()
    if not question:
        return {"statusCode": 400, "headers": _CORS,
                "body": json.dumps({"error": "question required"})}
    result = answer_question(question)
    log_event(logger, "question_answered", refused=result["refused"],
              cache=result.get("cache"), n_citations=len(result.get("citations", [])))
    return {"statusCode": 200, "headers": _CORS, "body": json.dumps(result)}
