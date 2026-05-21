from __future__ import annotations
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"

CITY_HOTEL_MAP = {
    "los angeles": ["HTL-001", "HTL-002", "HTL-003", "HTL-004"],
    "la": ["HTL-001", "HTL-002", "HTL-003", "HTL-004"],
    "lax": ["HTL-002"],
    "frankfurt": ["HTL-005"],
    "fra": ["HTL-005"],
    "singapore": ["HTL-006"],
    "sin": ["HTL-006"],
}


def _load_hotels() -> list[dict]:
    with open(DATA_DIR / "mock_hotels.json") as f:
        return json.load(f)["hotels"]


def search_hotels(city: str, check_in: str = None, check_out: str = None, guests: int = 1) -> List[Dict]:
    """
    Search for available hotels in a city. Returns mock data with policy compliance flags.
    """
    all_hotels = _load_hotels()
    city_lower = city.lower().strip()

    hotel_ids = None
    for key, ids in CITY_HOTEL_MAP.items():
        if key in city_lower or city_lower in key:
            hotel_ids = ids
            break

    if hotel_ids:
        matches = [h for h in all_hotels if h["id"] in hotel_ids]
    else:
        matches = all_hotels[:3]

    today = datetime.now()
    result = []
    for hotel in matches:
        h = hotel.copy()
        h["check_in_date"] = check_in or (today + timedelta(days=7)).strftime("%Y-%m-%d")
        h["check_out_date"] = check_out or (today + timedelta(days=10)).strftime("%Y-%m-%d")
        h["guests"] = guests
        # Calculate total stay
        try:
            ci = datetime.strptime(h["check_in_date"], "%Y-%m-%d")
            co = datetime.strptime(h["check_out_date"], "%Y-%m-%d")
            nights = max((co - ci).days, 1)
        except ValueError:
            nights = 3
        h["nights"] = nights
        h["total_price"] = round(h["nightly_rate"] * nights * random.uniform(0.97, 1.03))
        result.append(h)

    return result
