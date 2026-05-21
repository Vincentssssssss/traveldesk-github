from tools.flight_search import search_flights
from tools.hotel_search import search_hotels
from models.state import TravelDeskState


def booking_agent_node(state: TravelDeskState) -> dict:
    """Searches for flights or hotels based on extracted entities."""
    intent = state.get("intent", "")
    entities = {}
    if state.get("search_results"):
        entities = state["search_results"][0].get("entities", {})

    if intent == "flight_search":
        origin = entities.get("origin", "New York")
        destination = entities.get("destination", "Los Angeles")
        date = entities.get("date")
        passengers = int(entities.get("passengers", 1))

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
        city = entities.get("destination") or entities.get("city", "Los Angeles")
        check_in = entities.get("check_in") or entities.get("date")
        check_out = entities.get("check_out")
        guests = int(entities.get("guests", 1))

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
