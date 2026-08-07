from __future__ import annotations
import uuid
from datetime import datetime
from functools import lru_cache
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm_provider import is_demo_mode, create_openai_chat, extract_text_content
from models.state import TravelDeskState


@lru_cache(maxsize=1)
def _get_llm():
    if is_demo_mode():
        from agents.mock_llm import MockLLM
        return MockLLM(role="escalation")
    return create_openai_chat(default_model="gpt-5.3-codex", max_tokens=512)


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
    is_zh = state.get("language", "en").lower().startswith("zh")
    intent = state.get("intent", "unknown")
    reason = state.get("escalation_reason") or f"Complex request: {intent}"
    customer_name = state.get("customer_name", "Traveler")

    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    priority, eta, team = PRIORITY_MAP.get(intent, PRIORITY_MAP["unknown"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    last_message = state["messages"][-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    if is_demo_mode() and is_zh:
        final_response = (
            f"我理解您的情况，已为您创建升级工单 {escalation_id}。"
            f"我们已转交给 {team}，预计 {eta} 内联系您并跟进处理。"
        )
    else:
        language_instruction = "Respond in Simplified Chinese." if is_zh else "Respond in English."
        response = _get_llm().invoke([
            SystemMessage(content=f"{ESCALATION_PROMPT}\n{language_instruction}"),
            HumanMessage(content=(
                f"Customer: {customer_name} | Issue: {user_text} | "
                f"Escalation ID: {escalation_id} | Team: {team} | ETA: {eta}"
            )),
        ])
        final_response = extract_text_content(response)

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
        "final_response": final_response,
        "knowledge_results": [escalation_data],
    }
