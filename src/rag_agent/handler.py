"""Lambda handler: API Gateway POST /ask -> grounded policy answer."""
import json

from .answer import answer_question

_CORS = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}


def handler(event, context):
    body = json.loads(event.get("body") or "{}")
    question = (body.get("question") or "").strip()
    if not question:
        return {"statusCode": 400, "headers": _CORS,
                "body": json.dumps({"error": "question required"})}
    result = answer_question(question)
    return {"statusCode": 200, "headers": _CORS, "body": json.dumps(result)}
