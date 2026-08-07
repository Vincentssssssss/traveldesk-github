"""
Mock LLM used in DEMO_MODE (no API key required).
Provides deterministic, realistic responses for each agent role.
"""
from __future__ import annotations
import json
import re
from typing import List, Any


INTENT_KEYWORDS = {
    "flight_search":   ["flight", "fly", "plane", "airline", "departure", "arrival", "book a flight", "flying"],
    "hotel_search":    ["hotel", "accommodation", "stay", "room", "lodge", "resort", "motel", "book a hotel"],
    "cab_request":     ["cab", "taxi", "car", "uber", "lyft", "rideshare", "pickup", "ground transport"],
    "visa_inquiry":    ["visa", "passport", "immigration", "entry requirement", "work permit"],
    "cancellation":    ["cancel", "cancellation", "call off", "abort trip"],
    "refund_inquiry":  ["refund", "money back", "reimburse", "credit"],
    "policy_query":    ["policy", "rule", "allowed", "permitted", "guideline", "eligible", "business class"],
    "expense_query":   ["expense", "claim", "receipt", "concur", "reimbursement", "per diem"],
    "itinerary_query": ["itinerary", "booking status", "my trip", "pnr", "confirmation"],
    "complaint":       ["frustrated", "angry", "terrible", "horrible", "unacceptable", "complain", "disgusted"],
    "emergency":       ["emergency", "urgent", "stranded", "stuck", "help now", "missed connection", "missed my", "i am stranded", "flight was cancelled", "flight got cancelled"],
    "general_faq":     ["how", "what", "when", "where", "who", "process", "help"],
}

KNOWLEDGE_RESPONSES = {
    "policy_query": (
        "Based on our corporate travel policy:\n\n"
        "• **Flight Class**: Economy for flights under 6 hours; Business permitted for 6+ hour flights at Senior Manager level and above\n"
        "• **Advance Booking**: Domestic 7 days, International 14 days minimum\n"
        "• **Hotel Cap**: $200/night domestic, $250/night international (exceptions require manager approval)\n"
        "• **Meal Allowance**: $75/day domestic, $100/day international\n\n"
        "Would you like details on a specific policy area?"
    ),
    "expense_query": (
        "To claim travel expenses:\n\n"
        "1. Submit through **Concur Expense** within 30 days of return\n"
        "2. Attach receipts for any item over $25\n"
        "3. Select the correct cost center and project code\n"
        "4. Meals within per diem limits don't require receipts\n\n"
        "Reimbursement is processed with the next payroll cycle. Need help with a specific expense?"
    ),
    "visa_inquiry": (
        "Our travel desk handles all visa applications. Processing times:\n\n"
        "• **India**: 3–5 business days\n"
        "• **UK/Schengen**: 3–4 weeks\n"
        "• **USA (B1/B2)**: 2–8 weeks\n"
        "• **Canada**: 2–4 weeks\n\n"
        "Please initiate at least **4 weeks before travel**. I'll need your passport copy, invitation letter, and accommodation proof to get started."
    ),
    "cancellation": (
        "To cancel your trip:\n\n"
        "1. Provide your **booking reference / PNR**\n"
        "2. Our team checks refund eligibility based on fare rules\n"
        "3. Refundable tickets: processed in 5–7 business days\n"
        "4. Non-refundable tickets may qualify for airline travel credits\n\n"
        "Medical emergencies with a doctor's note qualify for full reimbursement. What's your booking reference?"
    ),
    "refund_inquiry": (
        "Refund status depends on your fare type:\n\n"
        "• **Refundable fares**: 5–7 business days to original payment method\n"
        "• **Non-refundable**: Travel credit issued by the airline (valid 12 months)\n"
        "• **Carrier-initiated cancellations**: Full refund regardless of fare class\n\n"
        "Please share your PNR or booking reference and I'll check the specific status for you."
    ),
    "itinerary_query": (
        "I can pull up your itinerary details. Please provide your:\n\n"
        "• **Booking reference / PNR** (e.g., DL4821, LH7X3K)\n"
        "• Or your **trip dates and destination**\n\n"
        "Your itinerary is also available in the TravelDesk portal under 'My Trips'."
    ),
    "general_faq": (
        "I'm happy to help! Our Travel Desk supports:\n\n"
        "• Flight, hotel, and ground transport bookings\n"
        "• Visa and documentation assistance\n"
        "• Travel policy guidance\n"
        "• Expense and reimbursement queries\n"
        "• Cancellations and refunds\n\n"
        "What would you like help with today?"
    ),
}

BOOKING_INTROS = {
    "flights": (
        "I found {count} flight options for your route. "
        "{compliant} are fully policy-compliant and ready to book. "
        "Please review the options below and select your preferred flight."
    ),
    "hotels": (
        "Here are {count} hotel options for your stay. "
        "{compliant} fall within the corporate per diem cap. "
        "Select your preferred option and I'll proceed with the booking request."
    ),
}


class MockMessage:
    """Minimal message object that mimics langchain_core AIMessage."""
    def __init__(self, content: str):
        self.content = content


class MockLLM:
    """
    Keyword-driven mock LLM. Used when OPENAI_API_KEY is absent.
    Supports the same .invoke() interface as ChatOpenAI.
    """

    def __init__(self, role: str = "general"):
        self.role = role  # supervisor | knowledge | escalation | customer_interaction

    def invoke(self, messages: List[Any], **kwargs) -> MockMessage:
        # Extract user text from the last HumanMessage
        user_text = ""
        for msg in reversed(messages):
            content = msg.content if hasattr(msg, "content") else str(msg)
            if content and not content.startswith("You are"):
                user_text = content.lower()
                break

        if self.role == "supervisor":
            return MockMessage(self._classify(user_text))
        elif self.role == "knowledge":
            return MockMessage(self._knowledge_answer(user_text))
        elif self.role == "escalation":
            return MockMessage(self._escalation_message(messages))
        else:
            return MockMessage(self._interaction_response(user_text))

    # ------------------------------------------------------------------

    def _classify(self, text: str) -> str:
        text_lower = text.lower()

        # High-priority intents checked first — these override generic booking keywords
        PRIORITY_INTENTS = ["emergency", "complaint", "cancellation", "refund_inquiry"]
        for intent in PRIORITY_INTENTS:
            keywords = INTENT_KEYWORDS.get(intent, [])
            if any(kw in text_lower for kw in keywords):
                best_intent = intent
                best_score = 1
                break
        else:
            best_intent = "general_faq"
            best_score = 0
            for intent, keywords in INTENT_KEYWORDS.items():
                if intent in PRIORITY_INTENTS:
                    continue
                score = sum(1 for kw in keywords if kw in text_lower)
                if score > best_score:
                    best_score = score
                    best_intent = intent

        # Entity extraction (very basic)
        entities: dict = {}

        # Origin / destination
        route = re.search(r'from\s+([a-z\s]+)\s+to\s+([a-z\s]+)', text_lower)
        if route:
            entities["origin"] = route.group(1).strip().title()
            entities["destination"] = route.group(2).strip().title()

        city_match = re.search(r'in\s+([a-z\s]+?)(?:\s+for|\s+next|\s+on|$)', text_lower)
        if city_match and best_intent == "hotel_search":
            entities["destination"] = city_match.group(1).strip().title()

        nights = re.search(r'(\d+)\s+nights?', text_lower)
        if nights:
            entities["nights"] = int(nights.group(1))

        passengers = re.search(r'(\d+)\s+(?:passenger|person|people|travell?er)', text_lower)
        if passengers:
            entities["passengers"] = int(passengers.group(1))

        result = {
            "intent": best_intent,
            "sub_intent": None,
            "confidence": 0.85 if best_score > 0 else 0.50,
            "entities": entities,
            "needs_escalation": best_intent in ("complaint", "emergency"),
            "escalation_reason": "Customer expressed frustration" if best_intent == "complaint" else (
                "Emergency travel situation" if best_intent == "emergency" else None
            ),
        }
        return json.dumps(result)

    def _knowledge_answer(self, text: str) -> str:
        text_lower = text.lower()
        # Pick best matching canned response
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                if intent in KNOWLEDGE_RESPONSES:
                    return KNOWLEDGE_RESPONSES[intent]
        return KNOWLEDGE_RESPONSES["general_faq"]

    def _escalation_message(self, messages: List[Any]) -> str:
        # Extract escalation_id from last human message context
        esc_id = "ESC-DEMO001"
        for msg in messages:
            content = msg.content if hasattr(msg, "content") else ""
            match = re.search(r'ESC-[A-Z0-9]+', content)
            if match:
                esc_id = match.group(0)
                break
        return (
            f"I completely understand your concern, and I want to make sure you get the right help. "
            f"I'm connecting you with a specialist who can resolve this personally. "
            f"Your escalation ticket **{esc_id}** has been created and our team will be in touch shortly. "
            f"Thank you for your patience."
        )

    def _interaction_response(self, text: str) -> str:
        return (
            "Thank you for reaching out to TravelDesk AI. "
            "I'm here to help with all your corporate travel needs — "
            "from flights and hotels to policies and visa assistance. "
            "How can I assist you today?"
        )
