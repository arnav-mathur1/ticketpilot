"""The escalation gate is pure logic — cheap, deterministic, high-value to lock down."""
from src.triage_agent.escalation import should_escalate


def test_low_confidence_escalates():
    esc, reason = should_escalate("general_inquiry", 0.40, "just a question")
    assert esc and "confidence" in reason


def test_sensitive_category_escalates_even_when_confident():
    esc, reason = should_escalate("billing", 0.99, "quick question about my plan")
    assert esc and "category" in reason


def test_sensitive_keyword_escalates():
    esc, reason = should_escalate("general_inquiry", 0.99, "I will be contacting my lawyer")
    assert esc and "keyword" in reason


def test_safe_ticket_auto_releases():
    esc, _ = should_escalate("general_inquiry", 0.99, "how do I change the app theme?")
    assert not esc
