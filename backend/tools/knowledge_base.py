import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def _split_query_tokens(query: str) -> tuple[set[str], set[str]]:
    # English-like words
    latin_tokens = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_]+", query)
        if len(token) > 2
    }
    # Chinese text segments
    cjk_tokens = {
        token
        for token in re.findall(r"[\u4e00-\u9fff]+", query)
        if len(token) >= 2
    }
    return latin_tokens, cjk_tokens


def _score_text(query: str, text: str, keywords: list[str] | None = None) -> int:
    query_lower = query.lower()
    text_lower = text.lower()
    latin_tokens, cjk_tokens = _split_query_tokens(query)

    score = 0
    for token in latin_tokens:
        if token in text_lower:
            score += 1

    # CJK matching is substring-based because whitespace tokenization doesn't apply.
    for token in cjk_tokens:
        if token in text:
            score += 2

    for kw in keywords or []:
        if not kw:
            continue
        kw_lower = kw.lower()
        if kw_lower in query_lower:
            score += 3
        elif kw in query:
            score += 3

    return score


def search_faqs(query: str) -> list[dict]:
    """Keyword-based FAQ search. Returns top matching FAQs."""
    data = _load_json("faqs.json")

    scored = []
    for faq in data["faqs"]:
        keywords = faq.get("keywords", []) + faq.get("keywords_zh", [])
        text = " ".join([
            faq.get("question", ""),
            faq.get("answer", ""),
            faq.get("question_zh", ""),
            faq.get("answer_zh", ""),
            " ".join(keywords),
        ])
        score = _score_text(query, text, keywords=keywords)
        if score > 0:
            scored.append((score, faq))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:3]]


def search_policies(query: str, category: str = None) -> list[dict]:
    """Search travel policies by query and optional category."""
    data = _load_json("policies.json")

    results = []
    for policy in data["policies"]:
        if category and policy["category"] != category:
            continue
        keywords = policy.get("keywords", []) + policy.get("keywords_zh", [])
        text = " ".join([
            policy.get("title", ""),
            policy.get("description", ""),
            policy.get("title_zh", ""),
            policy.get("description_zh", ""),
            policy.get("category", ""),
            " ".join(keywords),
        ])
        score = _score_text(query, text, keywords=keywords)
        if score > 0:
            results.append((score, policy))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results[:3]]


def get_all_policies() -> list[dict]:
    return _load_json("policies.json")["policies"]


def get_all_faqs() -> list[dict]:
    return _load_json("faqs.json")["faqs"]
