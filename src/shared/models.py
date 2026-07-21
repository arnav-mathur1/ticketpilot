#  Literal[...] means Pydantic rejects any category not in the list (raises ValidationError)

from typing import Literal
from pydantic import BaseModel, Field

class TicketClassification(BaseModel):
    category: Literal["billing", "refund_request", "account_access", "fraud_dispute",
                      "technical_issue", "complaint", "general_inquiry", "feature_request"]
    urgency: Literal["low", "medium", "high"]
    sentiment: Literal["positive", "neutral", "negative"]
    confidence: float = Field(ge=0.0, le=1.0)