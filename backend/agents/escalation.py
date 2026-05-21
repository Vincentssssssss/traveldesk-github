from __future__ import annotations
import uuid
import os
from datetime import datetime
from functools import lru_cache
from langchain_core.messages import SystemMessage, HumanMessage
from models.state import TravelDeskState


def _is_demo() -> bool:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return not key or key.startswith("your_") or key == "test-key"


@lru_cache(maxsize=1)
def _get_llm():
    if _is_demo():
        from agents.mock_llm import MockLLM
        return MockLLM(role="escalation")
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        max_tokens=512,
    )


ESCALATION_PROMPT = """Write a brief, empathetic escalation notice to the customer.
Cover: understanding their concern, connecting to a specialist, expected time, ticket ID.
Under 80 words. Warm and professional."""

PRIORITY_MAP = {
    "emergency":      ("P0", "15 minutes", "Emergency Response Team"),
    "complaint":      ("P1", "30 minutes", "Senior Travel Specialist"),
    "refund_inquiry": ("P2", "1 hour",     "Billing Specialist"),
    "visa_inquiry":   ("P2", "2 hours",    "Visa & Documentation Specialist"),
    "unknown":        ("P3", "4 hours",    "Travel Specialist"),
}


def escalation_agent_node(state: TravelDeskState) -> dict:
    intent = state.get("intent", "unknown")
    reason = state.get("escalation_reason") or f"Complex request: {intent}"
    customer_name = state.get("customer_name", "Traveler")

    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    priority, eta, team = PRIORITY_MAP.get(intent, PRIORITY_MAP["unknown"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    last_message = state["messages"][-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    response = _get_llm().invoke([
        SystemMessage(content=ESCALATION_PROMPT),
        HumanMessage(content=(
            f"Customer: {customer_name} | Issue: {user_text} | "
            f"Escalation ID: {escalation_id} | Team: {team} | ETA: {eta}"
        )),
    ])

    escalation_data = {
        "id": escalation_id,
        "priority": priority,
        "eta": eta,
        "team": team,
        "reason": reason,
        "timestamp": timestamp,
        "customer": customer_name,
        "summary": user_text[:200],
    }

    return {
        "escalated": True,
        "escalation_id": escalation_id,
        "response_type": "escalation",
        "final_response": response.content,
        "knowledge_results": [escalation_data],
    }
