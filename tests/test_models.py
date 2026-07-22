"""TicketClassification enforces the schema the LLM must return."""
import pytest
from pydantic import ValidationError

from src.shared.models import TicketClassification


def test_valid_classification():
    c = TicketClassification(category="billing", urgency="high",
                             sentiment="negative", confidence=0.82)
    assert c.category == "billing" and c.confidence == 0.82


def test_rejects_unknown_category():
    with pytest.raises(ValidationError):
        TicketClassification(category="not_a_category", urgency="high",
                             sentiment="negative", confidence=0.5)


def test_rejects_out_of_range_confidence():
    with pytest.raises(ValidationError):
        TicketClassification(category="billing", urgency="low",
                             sentiment="neutral", confidence=1.5)
