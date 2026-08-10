from __future__ import annotations
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"

ROUTE_MAP = {
    # (origin_keywords, dest_keywords): [flight_ids]
    "JFK-LAX": ["DL 402", "AA 100", "UA 575"],
    "NYC-LA": ["DL 402", "AA 100", "UA 575"],
    "JFK-FRA": ["LH 401"],
    "JFK-SIN": ["SQ 023"],
    "JFK-DXB": ["EK 202"],
    "JFK-LHR": ["BA 178"],
}

CITY_CODES = {
    "new york": "JFK", "nyc": "JFK", "jfk": "JFK", "lga": "JFK",
    "los angeles": "LAX", "la": "LAX", "lax": "LAX",
    "london": "LHR", "lhr": "LHR",
    "frankfurt": "FRA", "fra": "FRA",
    "singapore": "SIN", "sin": "SIN",
    "dubai": "DXB", "dxb": "DXB",
}


def _load_flights() -> list[dict]:
    with open(DATA_DIR / "mock_flights.json") as f:
        return json.load(f)["flights"]


def _resolve_city(text: Optional[str]) -> str:
    if text is None:
        return ""
    text_value = str(text).strip()
    if not text_value:
        return ""
    text_lower = text_value.lower()
    return CITY_CODES.get(text_lower, text_value.upper()[:3])


def search_flights(origin: str, destination: str, date: str = None, passengers: int = 1) -> List[Dict]:
    """
    Search for available flights. Returns matching flights with pricing.
    In MVP, returns mock data filtered by origin/destination keywords.
    """
    all_flights = _load_flights()

    origin_code = _resolve_city(origin)
    dest_code = _resolve_city(destination)
    origin_text = (origin or "").upper()
    destination_text = (destination or "").upper()

    # Filter matching flights
    matches = [
        f for f in all_flights
        if (f["origin"] == origin_code or (origin_text and origin_text in f["origin"]))
        and (f["destination"] == dest_code or (destination_text and destination_text in f["destination"]))
    ]

    # If no exact match, return a diverse subset to demonstrate the UI
    if not matches:
        matches = all_flights[:3]

    # Add minor price variation for realism
    result = []
    for flight in matches:
        f = flight.copy()
        f["price"] = round(f["price"] * random.uniform(0.95, 1.05))
        f["search_date"] = date or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        f["passengers"] = passengers
        f["total_price"] = f["price"] * passengers
        result.append(f)

    return result
