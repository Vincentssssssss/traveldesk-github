#!/usr/bin/env python3
"""
Build/refresh study materials from chapter data.
Generates additional flashcards from rules and cross-references.
"""

import json
from pathlib import Path

KB_ROOT = Path(__file__).parent.parent
DATA_DIR = KB_ROOT / "data"
CHAPTERS_DIR = DATA_DIR / "chapters"


def load_all_chapters() -> list[dict]:
    chapters = []
    for path in sorted(CHAPTERS_DIR.glob("ch*.json")):
        with open(path, encoding="utf-8") as f:
            chapters.append(json.load(f))
    return chapters


def generate_rule_flashcards(chapters: list[dict]) -> list[dict]:
    """Auto-generate flashcards from chapter rules."""
    cards = []
    counter = 100
    for ch in chapters:
        for rule in ch.get("rules", []):
            counter += 1
            cards.append({
                "id": f"fc-auto-{counter}",
                "category": ch.get("category", "general"),
                "front": f"[{rule['id']}] {rule['title']}",
                "back": rule["description"],
                "chapter": ch["id"],
                "difficulty": "hard" if rule.get("severity") == "critical" else "medium",
                "auto_generated": True,
            })
    return cards


def update_index_stats(chapters: list[dict]):
    index_path = DATA_DIR / "index.json"
    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    total_rules = sum(len(ch.get("rules", [])) for ch in chapters)

    with open(DATA_DIR / "flashcards.json", encoding="utf-8") as f:
        flashcards = json.load(f)

    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        glossary = json.load(f)

    with open(DATA_DIR / "scenarios.json", encoding="utf-8") as f:
        scenarios = json.load(f)

    index["meta"]["total_chapters"] = len(chapters)
    index["meta"]["total_rules"] = total_rules
    index["meta"]["total_flashcards"] = len(flashcards["flashcards"])
    index["meta"]["total_glossary_terms"] = len(glossary["terms"])
    index["meta"]["total_scenarios"] = len(scenarios["scenarios"])

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def merge_auto_flashcards():
    """Add auto-generated rule flashcards to existing deck."""
    chapters = load_all_chapters()
    auto_cards = generate_rule_flashcards(chapters)

    flashcards_path = DATA_DIR / "flashcards.json"
    with open(flashcards_path, encoding="utf-8") as f:
        data = json.load(f)

    existing_ids = {c["id"] for c in data["flashcards"]}
    new_cards = [c for c in auto_cards if c["id"] not in existing_ids]
    data["flashcards"].extend(new_cards)

    with open(flashcards_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Added {len(new_cards)} auto-generated flashcards")
    update_index_stats(chapters)
    print("  Index stats updated")


if __name__ == "__main__":
    print("Building study materials...")
    merge_auto_flashcards()
    print("Done.")
