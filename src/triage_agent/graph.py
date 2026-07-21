import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from ..shared import llm

from pydantic import ValidationError
from ..shared.models import TicketClassification

class TicketState(TypedDict):
    text: str          # input: the raw ticket
    category: str
    urgency: str
    sentiment: str
    confidence: float
    draft_reply: str

CATEGORIES = ["billing", "refund_request", "account_access", "fraud_dispute",
              "technical_issue", "complaint", "general_inquiry", "feature_request"]
URGENCIES = ["low", "medium", "high"]
SENTIMENTS = ["positive", "neutral", "negative"]
MAX_ATTEMPTS = 3

def classify_ticket(state: TicketState) -> dict:
    # system prompt
    system_prompt = f"""
    You are a support-ticket triage classifier. Classify the ticket and respond only as a JSON object with the following fields:
    - category: the category of the ticket, one of {CATEGORIES}
    - urgency: the urgency of the ticket, one of {URGENCIES}
    - sentiment: the sentiment of the ticket, one of {SENTIMENTS}
    - confidence: the confidence in the classification, a float between 0 and 1
    """

    # messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["text"]}
    ]

    for attempt in range(MAX_ATTEMPTS):
        response = llm.chat(messages, response_format={"type": "json_object"})
        try:
            data = json.loads(response)
            result = TicketClassification(**data)
            return result.model_dump()

        except (json.JSONDecodeError, ValidationError) as e:
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"That was invalid: {e}. Return correct JSON. only."})
    
    raise RuntimeError(f"Failed to classify ticket after {MAX_ATTEMPTS} attempts")

def draft_reply(state: TicketState) -> dict:
    system_prompt = (
        "You are a customer-support agent for a financial services company. "
        "Write a short, professional, empathetic reply to the customer's ticket. "
        "Do not invent specific facts (amounts, dates, policy details) you weren't given. "
        "Return only the reply text."
    )

    user_prompt = (
        f"Ticket: {state['text']}\n\n"
        f"Classification/category: {state['category']}, "
        f"urgency: {state['urgency']}, sentiment: {state['sentiment']}.\n"
        "Write the reply."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    reply = llm.chat(messages, temperature=0.4)  
    return {"draft_reply": reply}


def build_graph():
    g = StateGraph(TicketState)
    g.add_node("classify", classify_ticket)
    g.add_node("draft", draft_reply)
    g.set_entry_point("classify")
    g.add_edge("classify", "draft")
    g.add_edge("draft", END)
    return g.compile()

app = build_graph()

def run_triage(text: str) -> dict:
    return app.invoke({"text": text})