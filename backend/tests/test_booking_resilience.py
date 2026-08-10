import unittest

from agents.booking import booking_agent_node
from tools.flight_search import search_flights


class BookingResilienceTests(unittest.TestCase):
    def test_search_flights_handles_missing_origin(self):
        results = search_flights(origin=None, destination="LAX", passengers=1)
        self.assertTrue(isinstance(results, list))
        self.assertGreater(len(results), 0)

    def test_booking_flight_uses_defaults_when_entities_are_none(self):
        state = {
            "intent": "flight_search",
            "search_results": [{"entities": {"origin": None, "destination": None, "passengers": None}}],
        }
        out = booking_agent_node(state)
        self.assertEqual(out.get("response_type"), "flights")
        self.assertTrue(isinstance(out.get("search_results"), list))
        self.assertGreater(len(out.get("search_results", [])), 0)

    def test_booking_hotel_uses_defaults_when_city_is_none(self):
        state = {
            "intent": "hotel_search",
            "search_results": [{"entities": {"destination": None, "city": None, "guests": None}}],
        }
        out = booking_agent_node(state)
        self.assertEqual(out.get("response_type"), "hotels")
        self.assertTrue(isinstance(out.get("search_results"), list))
        self.assertGreater(len(out.get("search_results", [])), 0)


if __name__ == "__main__":
    unittest.main()
