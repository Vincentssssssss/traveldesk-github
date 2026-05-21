from __future__ import annotations
import json
import os
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
        return MockLLM(role="supervisor")
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        max_tokens=512,
    )


SYSTEM_PROMPT = """You are the Supervisor Agent for a corporate Travel Desk AI system.
Your ONLY job is to classify the customer's intent and extract key entities.

Classify the intent into exactly one of:
- flight_search, hotel_search, cab_request, visa_inquiry, itinerary_query,
  cancellation, refund_inquiry, policy_query, expense_query, general_faq,
  complaint, emergency, unknown

Respond ONLY with a JSON object:
{
  "intent": "<intent>",
  "sub_intent": null,
  "confidence": 0.95,
  "entities": { "origin": "...", "destination": "...", "passengers": 1 },
  "needs_escalation": false,
  "escalation_reason": null
}"""


def supervisor_node(state: TravelDeskState) -> dict:
    last_message = state["messages"][-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    response = _get_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Customer message: {user_text}"),
    ])

    try:
        parsed = json.loads(response.content)
    except (json.JSONDecodeError, AttributeError):
        parsed = {
            "intent": "general_faq",
            "sub_intent": None,
            "confidence": 0.5,
            "entities": {},
            "needs_escalation": False,
            "escalation_reason": None,
        }

    escalate = parsed.get("needs_escalation", False)
    if parsed.get("intent") in ("complaint", "emergency"):
        escalate = True

    return {
        "intent": parsed.get("intent", "unknown"),
        "sub_intent": parsed.get("sub_intent"),
        "confidence": parsed.get("confidence", 0.5),
        "escalated": escalate,
        "escalation_reason": parsed.get("escalation_reason"),
        "search_results": [{"entities": parsed.get("entities", {})}],
    }
