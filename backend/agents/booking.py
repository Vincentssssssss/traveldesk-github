from tools.flight_search import search_flights
from tools.hotel_search import search_hotels
from models.state import TravelDeskState


def _coalesce_text(value, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coalesce_int(value, default: int) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def booking_agent_node(state: TravelDeskState) -> dict:
    """Searches for flights or hotels based on extracted entities."""
    intent = state.get("intent", "")
    entities = {}
    if state.get("search_results"):
        entities = state["search_results"][0].get("entities", {})

    if intent == "flight_search":
        origin = _coalesce_text(entities.get("origin"), "New York")
        destination = _coalesce_text(entities.get("destination"), "Los Angeles")
        date = entities.get("date")
        passengers = _coalesce_int(entities.get("passengers"), 1)

        results = search_flights(
            origin=origin,
            destination=destination,
            date=date,
            passengers=passengers,
        )

        return {
            "search_results": results,
            "response_type": "flights",
        }

    elif intent == "hotel_search":
        city = _coalesce_text(entities.get("destination") or entities.get("city"), "Los Angeles")
        check_in = entities.get("check_in") or entities.get("date")
        check_out = entities.get("check_out")
        guests = _coalesce_int(entities.get("guests"), 1)

        results = search_hotels(
            city=city,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
        )

        return {
            "search_results": results,
            "response_type": "hotels",
        }

    # Fallback for cab/other transport
    return {
        "search_results": [],
        "response_type": "text",
        "final_response": (
            "For ground transportation, I can arrange a corporate cab or rideshare. "
            "Our preferred providers are Uber for Business and our contracted cab vendors. "
            "Please provide your pickup location, destination, and required time, and I'll book it for you."
        ),
    }
