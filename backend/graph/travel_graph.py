from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from models.state import TravelDeskState
from agents.supervisor import supervisor_node
from agents.booking import booking_agent_node
from agents.knowledge import knowledge_agent_node
from agents.escalation import escalation_agent_node
from agents.customer_interaction import customer_interaction_node


# ---------------------------------------------------------------------------
# Routing function — determines which agent handles the request post-supervisor
# ---------------------------------------------------------------------------

def route_from_supervisor(state: TravelDeskState) -> Literal[
    "booking", "knowledge", "escalation", "customer_interaction"
]:
    intent = state.get("intent", "unknown")
    escalated = state.get("escalated", False)

    if escalated:
        return "escalation"

    booking_intents = {
        "flight_search",
        "hotel_search",
        "cab_request",
    }
    knowledge_intents = {
        "policy_query",
        "general_faq",
        "expense_query",
        "visa_inquiry",
        "cancellation",
        "refund_inquiry",
        "itinerary_query",
    }

    if intent in booking_intents:
        return "booking"
    elif intent in knowledge_intents:
        return "knowledge"
    elif intent in ("complaint", "emergency"):
        return "escalation"
    else:
        return "customer_interaction"


def route_after_booking(state: TravelDeskState) -> Literal["customer_interaction", END]:
    # If booking agent already set a direct text response (e.g., cab), skip CI agent
    if state.get("final_response") and state.get("response_type") == "text":
        return END
    return "customer_interaction"


def route_after_escalation(state: TravelDeskState) -> Literal[END]:
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    builder = StateGraph(TravelDeskState)

    # Register nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("booking", booking_agent_node)
    builder.add_node("knowledge", knowledge_agent_node)
    builder.add_node("escalation", escalation_agent_node)
    builder.add_node("customer_interaction", customer_interaction_node)

    # Entry point
    builder.add_edge(START, "supervisor")

    # Supervisor → conditional routing
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "booking": "booking",
            "knowledge": "knowledge",
            "escalation": "escalation",
            "customer_interaction": "customer_interaction",
        },
    )

    # Booking → customer_interaction (or END if response already set)
    builder.add_conditional_edges(
        "booking",
        route_after_booking,
        {
            "customer_interaction": "customer_interaction",
            END: END,
        },
    )

    # Knowledge → customer_interaction
    builder.add_edge("knowledge", "customer_interaction")

    # Escalation → END (response already fully set)
    builder.add_edge("escalation", END)

    # Customer interaction → END
    builder.add_edge("customer_interaction", END)

    return builder


# Compile with in-memory checkpointer (swap for PostgresSaver in production)
_checkpointer = MemorySaver()

def get_compiled_graph():
    graph = build_graph()
    return graph.compile(checkpointer=_checkpointer)
