from __future__ import annotations
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
        return MockLLM(role="customer_interaction")
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        max_tokens=1024,
    )


SYSTEM_PROMPT = """You are the Customer Interaction Agent for a corporate Travel Desk.
Warm, professional, and concise. For flight/hotel results: write a 2-3 sentence intro only —
the UI renders the cards separately. End every response with an offer to help further."""


def customer_interaction_node(state: TravelDeskState) -> dict:
    # Upstream agent already produced a complete response
    if state.get("final_response") and state.get("response_type") in ("text", "escalation"):
        return {}

    response_type = state.get("response_type", "text")
    customer_name = state.get("customer_name", "there")

    last_message = state["messages"][-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    if response_type in ("flights", "hotels"):
        results = state.get("search_results", [])
        count = len(results)
        item_type = "flight options" if response_type == "flights" else "hotel options"
        non_compliant = [r for r in results if not r.get("policy_compliant", True)]
        compliant_count = count - len(non_compliant)

        if _is_demo():
            # Fast deterministic response for demo
            approval_note = (
                f" {len(non_compliant)} option(s) exceed policy limits and will need manager approval."
                if non_compliant else ""
            )
            return {
                "final_response": (
                    f"I found {count} {item_type} for you, {customer_name}. "
                    f"{compliant_count} are fully within corporate travel policy.{approval_note} "
                    f"Please review the options below and click **Select** on your preferred choice."
                )
            }

        response = _get_llm().invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Customer ({customer_name}) asked: {user_text}\n\n"
                f"Found {count} {item_type}, {compliant_count} policy-compliant, "
                f"{len(non_compliant)} need approval.\n\n"
                f"Write a brief 2-3 sentence intro."
            )),
        ])
        return {"final_response": response.content}

    # Knowledge/FAQ path
    if state.get("final_response"):
        return {}

    response = _get_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Customer asked: {user_text}\nPlease help them."),
    ])
    return {"final_response": response.content}
