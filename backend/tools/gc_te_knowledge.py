"""
GC TE Policy keyword retrieval for the Knowledge Agent.
Reads structured JSON from knowledge-base/gc-te-policy/data/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

KB_DATA_DIR = Path(__file__).parent.parent.parent / "knowledge-base" / "gc-te-policy" / "data"
CHAPTERS_DIR = KB_DATA_DIR / "chapters"

INTENT_CATEGORY_MAP = {
    "policy_query": None,
    "expense_query": {"expense", "submission", "china"},
    "visa_inquiry": {"general", "travel"},
    "cancellation": {"travel", "expense", "compliance"},
    "refund_inquiry": {"expense", "compliance"},
    "general_faq": None,
}


def _tokenize_query(query: str) -> list[str]:
    """Split query into keyword tokens; handle CJK without whitespace."""
    query_lower = query.lower().strip()
    tokens = [w for w in re.split(r"[\s,，。！？；;]+", query_lower) if len(w) > 1]

    if re.search(r"[\u4e00-\u9fff]", query):
        if query_lower not in tokens:
            tokens.append(query_lower)
        cn = re.findall(r"[\u4e00-\u9fff]+", query)
        for segment in cn:
            if len(segment) >= 2:
                tokens.append(segment)
            for i in range(len(segment) - 1):
                tokens.append(segment[i : i + 2])

    return list(dict.fromkeys(tokens))


def _score_text(query_tokens: list[str], text: str) -> int:
    text_lower = text.lower()
    score = 0
    for token in query_tokens:
        if len(token) <= 1:
            continue
        if token in text_lower:
            score += 1
            if len(token) >= 4 or re.search(r"[\u4e00-\u9fff]", token):
                score += 1
    return score


def _load_chapters() -> list[dict]:
    chapters = []
    if not CHAPTERS_DIR.exists():
        return chapters
    for path in sorted(CHAPTERS_DIR.glob("ch*.json")):
        with open(path, encoding="utf-8") as f:
            chapters.append(json.load(f))
    return chapters


def search_gc_te_policy(query: str, intent: str | None = None, limit: int = 3) -> list[dict]:
    """
    Keyword search across GC TE chapters (sections + rules).
    Returns normalized dicts for the Knowledge Agent context builder.
    """
    if not query or not query.strip():
        return []

    query_tokens = _tokenize_query(query)
    if not query_tokens:
        return []

    allowed_categories = INTENT_CATEGORY_MAP.get(intent) if intent else None
    scored: list[tuple[int, dict]] = []

    for chapter in _load_chapters():
        if allowed_categories and chapter.get("category") not in allowed_categories:
            continue

        chapter_prefix = f"{chapter.get('title', '')} ({chapter.get('title_en', '')})"

        for section in chapter.get("sections", []):
            searchable = " ".join([
                chapter.get("title", ""),
                chapter.get("summary", ""),
                section.get("title", ""),
                section.get("content", ""),
                " ".join(section.get("key_points", [])),
                " ".join(chapter.get("keywords", [])),
            ])
            score = _score_text(query_tokens, searchable)
            if score > 0:
                scored.append((score, {
                    "source": "gc_te",
                    "type": "section",
                    "id": section.get("id", ""),
                    "chapter_id": chapter.get("id", ""),
                    "category": chapter.get("category", ""),
                    "title": f"{chapter_prefix} — {section.get('title', '')}",
                    "content": section.get("content", ""),
                    "key_points": section.get("key_points", []),
                    "related_rules": section.get("related_rules", []),
                }))

        for rule in chapter.get("rules", []):
            searchable = " ".join([
                chapter.get("title", ""),
                rule.get("id", ""),
                rule.get("title", ""),
                rule.get("description", ""),
                rule.get("severity", ""),
            ])
            score = _score_text(query_tokens, searchable)
            if score > 0:
                score += 1 if rule.get("severity") == "critical" else 0
                scored.append((score, {
                    "source": "gc_te",
                    "type": "rule",
                    "id": rule.get("id", ""),
                    "chapter_id": chapter.get("id", ""),
                    "category": chapter.get("category", ""),
                    "title": f"[{rule.get('id', '')}] {rule.get('title', '')}",
                    "content": rule.get("description", ""),
                    "severity": rule.get("severity", "info"),
                }))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen_ids: set[str] = set()
    results: list[dict] = []
    for _, item in scored:
        uid = f"{item['type']}:{item['id']}"
        if uid in seen_ids:
            continue
        seen_ids.add(uid)
        results.append(item)
        if len(results) >= limit:
            break

    return results


def format_gc_te_context(items: list[dict]) -> str:
    """Format GC TE hits as LLM context blocks."""
    parts = []
    for item in items:
        header = f"GC TE Policy — {item['title']}"
        body = item.get("content", "")
        if item.get("key_points"):
            body += "\n要点: " + "; ".join(item["key_points"])
        if item.get("severity"):
            body += f"\n(严重级别: {item['severity']})"
        parts.append(f"{header}\n{body}")
    return "\n\n---\n\n".join(parts)
