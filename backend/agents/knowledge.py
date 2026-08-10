from __future__ import annotations
from functools import lru_cache
from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm_provider import is_demo_mode, create_openai_chat, extract_text_content
from tools.knowledge_base import search_faqs, search_policies
from models.state import TravelDeskState


@lru_cache(maxsize=1)
def _get_llm():
    if is_demo_mode():
        from agents.mock_llm import MockLLM
        return MockLLM(role="knowledge")
    return create_openai_chat(default_model="gpt-5.3-codex", max_tokens=1024)


SYSTEM_PROMPT = """You are the Knowledge Agent for a corporate Travel Desk.
Answer using ONLY the provided context. Never invent policy details."""


def _is_zh(state: TravelDeskState) -> bool:
    return str(state.get("language") or "zh").lower().startswith("zh")


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
        if _is_zh(state):
            no_result_message = (
                "我暂时没有在知识库中找到与此问题完全匹配的信息。"
                "我会为您转接人工差旅专员，工作时间内预计 30 分钟内回复。"
            )
        else:
            no_result_message = (
                "I don't have specific information on this in my knowledge base. "
                "Let me connect you with a human travel specialist — "
                "expect a response within 30 minutes during business hours."
            )
        return {
            "knowledge_results": [],
            "response_type": "text",
            "final_response": no_result_message,
            "escalated": True,
            "escalation_reason": "Knowledge not found in base",
        }

    # Build context for LLM (or mock)
    context_parts = []
    for item in knowledge_results:
        if "question" in item:
            if _is_zh(state) and item.get("question_zh") and item.get("answer_zh"):
                context_parts.append(f"Q: {item['question_zh']}\nA: {item['answer_zh']}")
            else:
                context_parts.append(f"Q: {item['question']}\nA: {item['answer']}")
        elif "title" in item:
            desc = item.get("description_zh", "") if _is_zh(state) else item.get("description", "")
            exceptions = item.get("exceptions", [])
            exc_text = "\nExceptions: " + "; ".join(exceptions) if exceptions else ""
            title = item.get("title_zh", item["title"]) if _is_zh(state) else item["title"]
            context_parts.append(f"Policy — {title}: {desc}{exc_text}")
    context = "\n\n---\n\n".join(context_parts)

    language_instruction = (
        "Respond in Simplified Chinese."
        if _is_zh(state)
        else "Respond in English."
    )

    response = _get_llm().invoke([
        SystemMessage(content=f"{SYSTEM_PROMPT}\n{language_instruction}"),
        HumanMessage(content=f"CONTEXT:\n{context}\n\nQUESTION: {user_text}"),
    ])

    return {
        "knowledge_results": knowledge_results,
        "response_type": "policy" if intent == "policy_query" else "text",
        "final_response": extract_text_content(response),
    }
