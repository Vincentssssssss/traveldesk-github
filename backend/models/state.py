from __future__ import annotations
from typing import TypedDict, Annotated, Optional, List, Dict, Any
from langgraph.graph.message import add_messages


class TravelDeskState(TypedDict):
    messages: Annotated[list, add_messages]
    conversation_id: str
    customer_name: str

    # Intent classification
    intent: Optional[str]
    sub_intent: Optional[str]
    confidence: float

    # Agent outputs
    search_results: Optional[List[Dict[str, Any]]]
    knowledge_results: Optional[List[Dict[str, Any]]]
    policy_result: Optional[Dict[str, Any]]

    # Escalation
    escalated: bool
    escalation_id: Optional[str]
    escalation_reason: Optional[str]

    # Final formatted response
    final_response: Optional[str]
    response_type: Optional[str]  # text | flights | hotels | policy | escalation
