import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def search_faqs(query: str) -> list[dict]:
    """Keyword-based FAQ search. Returns top matching FAQs."""
    data = _load_json("faqs.json")
    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored = []
    for faq in data["faqs"]:
        score = 0
        text = f"{faq['question']} {faq['answer']} {' '.join(faq.get('keywords', []))}".lower()
        for word in query_words:
            if len(word) > 2 and word in text:
                score += 1
        # Boost for keyword list matches
        for kw in faq.get("keywords", []):
            if kw.lower() in query_lower:
                score += 3
        if score > 0:
            scored.append((score, faq))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:3]]


def search_policies(query: str, category: str = None) -> list[dict]:
    """Search travel policies by query and optional category."""
    data = _load_json("policies.json")
    query_lower = query.lower()
    query_words = set(query_lower.split())

    results = []
    for policy in data["policies"]:
        if category and policy["category"] != category:
            continue
        text = f"{policy['title']} {policy['description']} {policy['category']}".lower()
        score = sum(1 for w in query_words if len(w) > 2 and w in text)
        if score > 0:
            results.append((score, policy))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results[:3]]


def get_all_policies() -> list[dict]:
    return _load_json("policies.json")["policies"]


def get_all_faqs() -> list[dict]:
    return _load_json("faqs.json")["faqs"]
