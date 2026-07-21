CONFIDENCE_THRESHOLD = 0.7
SENSITIVE_CATEGORIES = {"billing", "refund_request", "account_access", "fraud_dispute"}
SENSITIVE_KEYWORDS = ["lawyer", "attorney", "legal", "sue", "fraud",
                      "unauthorized", "hacked", "stolen", "chargeback",
                      "privacy", "data problem", "breach", "leak"]

def should_escalate(category: str, confidence: float, text: str) -> tuple[bool, str]:
    if confidence < CONFIDENCE_THRESHOLD:
        return True, f"low confidence ({confidence:.2f} < {CONFIDENCE_THRESHOLD})"
    if category in SENSITIVE_CATEGORIES:
        return True, f"sensitive category ({category})"
    hit = next((kw for kw in SENSITIVE_KEYWORDS if kw in text.lower()), None)
    if hit:
        return True, f"sensitive keyword ('{hit}')"
    return False, "auto-release"