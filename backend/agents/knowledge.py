from __future__ import annotations
import os
from functools import lru_cache
from langchain_core.messages import SystemMessage, HumanMessage
from tools.knowledge_base import search_faqs, search_policies
from models.state import TravelDeskState


def _is_demo() -> bool:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return not key or key.startswith("your_") or key == "test-key"


@lru_cache(maxsize=1)
def _get_llm():
    if _is_demo():
        from agents.mock_llm import MockLLM
        return MockLLM(role="knowledge")
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        max_tokens=1024,
    )


SYSTEM_PROMPT = """You are the Knowledge Agent for a corporate Travel Desk.
Answer using ONLY the provided context. Never invent policy details."""


def knowledge_agent_node(state: TravelDeskState) -> dict:
    last_message = state["messages"][-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)
    intent = state.get("intent", "general_faq")

    category_map = {
        "visa_inquiry": "visa",
        "expense_query": "expense",
        "cancellation": "cancellation",
    }
    category = category_map.get(intent)

    faqs = search_faqs(user_text)
    policies = search_policies(user_text, category=category)
    knowledge_results = faqs + policies

    if not knowledge_results:
        return {
            "knowledge_results": [],
            "response_type": "text",
            "final_response": (
                "I don't have specific information on this in my knowledge base. "
                "Let me connect you with a human travel specialist — "
                "expect a response within 30 minutes during business hours."
            ),
            "escalated": True,
            "escalation_reason": "Knowledge not found in base",
        }

    # Build context for LLM (or mock)
    context_parts = []
    for item in knowledge_results:
        if "question" in item:
            context_parts.append(f"Q: {item['question']}\nA: {item['answer']}")
        elif "title" in item:
            desc = item.get("description", "")
            exceptions = item.get("exceptions", [])
            exc_text = "\nExceptions: " + "; ".join(exceptions) if exceptions else ""
            context_parts.append(f"Policy — {item['title']}: {desc}{exc_text}")
    context = "\n\n---\n\n".join(context_parts)

    response = _get_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"CONTEXT:\n{context}\n\nQUESTION: {user_text}"),
    ])

    return {
        "knowledge_results": knowledge_results,
        "response_type": "policy" if intent == "policy_query" else "text",
        "final_response": response.content,
    }
