"""
GC TE Policy Knowledge Base API Router
Provides search, chapters, flashcards, scenarios, and study endpoints.
"""

import json
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File

KB_ROOT = Path(__file__).parent.parent / "knowledge-base" / "gc-te-policy"
DATA_DIR = KB_ROOT / "data"
CHAPTERS_DIR = DATA_DIR / "chapters"

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])


def _load_json(relative_path: str) -> dict:
    path = DATA_DIR / relative_path
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Knowledge base data not found: {relative_path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_chapter(chapter_id: str) -> dict:
    path = CHAPTERS_DIR / f"{chapter_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Chapter not found: {chapter_id}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _search_text(query: str, text: str) -> int:
    query_lower = query.lower()
    words = [w for w in query_lower.split() if len(w) > 1]
    if not words:
        return 0
    text_lower = text.lower()
    return sum(1 for w in words if w in text_lower)


@router.get("/overview")
async def kb_overview():
    index = _load_json("index.json")
    return {
        "meta": index["meta"],
        "categories": index["categories"],
        "learning_paths": index["learning_paths"],
        "chapter_count": len(index["chapters"]),
    }


@router.get("/chapters")
async def list_chapters(category: Optional[str] = None):
    index = _load_json("index.json")
    chapters = index["chapters"]
    if category:
        chapters = [c for c in chapters if c["category"] == category]
    return {"chapters": chapters}


@router.get("/chapters/{chapter_id}")
async def get_chapter(chapter_id: str):
    return _load_chapter(chapter_id)


@router.get("/search")
async def search_knowledge(q: str, limit: int = 10):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    results = []

    for path in sorted(CHAPTERS_DIR.glob("ch*.json")):
        with open(path, encoding="utf-8") as f:
            chapter = json.load(f)
        searchable = f"{chapter['title']} {chapter.get('summary', '')} {' '.join(chapter.get('keywords', []))}"
        for section in chapter.get("sections", []):
            searchable += f" {section['title']} {section['content']}"
        score = _search_text(q, searchable)
        if score > 0:
            results.append({
                "type": "chapter",
                "id": chapter["id"],
                "title": chapter["title"],
                "summary": chapter.get("summary", ""),
                "category": chapter.get("category"),
                "score": score,
            })

    glossary = _load_json("glossary.json")
    for term in glossary["terms"]:
        searchable = f"{term['term']} {term.get('term_zh', '')} {term['definition']}"
        score = _search_text(q, searchable)
        if score > 0:
            results.append({
                "type": "glossary",
                "id": term["term"],
                "title": f"{term['term']} ({term.get('term_zh', '')})",
                "summary": term["definition"],
                "category": term.get("category"),
                "score": score,
            })

    for rule_result in _search_rules(q):
        results.append(rule_result)

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"query": q, "total": len(results), "results": results[:limit]}


def _search_rules(query: str) -> list[dict]:
    results = []
    for path in sorted(CHAPTERS_DIR.glob("ch*.json")):
        with open(path, encoding="utf-8") as f:
            chapter = json.load(f)
        for rule in chapter.get("rules", []):
            searchable = f"{rule['id']} {rule['title']} {rule['description']}"
            score = _search_text(query, searchable)
            if score > 0:
                results.append({
                    "type": "rule",
                    "id": rule["id"],
                    "title": rule["title"],
                    "summary": rule["description"],
                    "severity": rule.get("severity"),
                    "chapter": chapter["id"],
                    "score": score,
                })
    return results


@router.get("/glossary")
async def get_glossary(category: Optional[str] = None, q: Optional[str] = None):
    data = _load_json("glossary.json")
    terms = data["terms"]
    if category:
        terms = [t for t in terms if t.get("category") == category]
    if q:
        terms = [t for t in terms if _search_text(q, f"{t['term']} {t.get('term_zh', '')} {t['definition']}") > 0]
    return {"terms": terms, "total": len(terms)}


@router.get("/flashcards")
async def get_flashcards(
    category: Optional[str] = None,
    chapter: Optional[str] = None,
    difficulty: Optional[str] = None,
):
    data = _load_json("flashcards.json")
    cards = data["flashcards"]
    if category:
        cards = [c for c in cards if c.get("category") == category]
    if chapter:
        cards = [c for c in cards if c.get("chapter") == chapter]
    if difficulty:
        cards = [c for c in cards if c.get("difficulty") == difficulty]
    return {"flashcards": cards, "total": len(cards)}


@router.get("/scenarios")
async def get_scenarios(category: Optional[str] = None, difficulty: Optional[str] = None):
    data = _load_json("scenarios.json")
    scenarios = data["scenarios"]
    if category:
        scenarios = [s for s in scenarios if s.get("category") == category]
    if difficulty:
        scenarios = [s for s in scenarios if s.get("difficulty") == difficulty]
    return {"scenarios": scenarios, "total": len(scenarios)}


@router.get("/decision-trees")
async def list_decision_trees():
    data = _load_json("decision_trees.json")
    trees = [{"id": t["id"], "title": t["title"], "description": t.get("description")} for t in data["decision_trees"]]
    return {"decision_trees": trees}


@router.get("/decision-tree/{tree_id}")
async def get_decision_tree(tree_id: str):
    data = _load_json("decision_trees.json")
    for tree in data["decision_trees"]:
        if tree["id"] == tree_id:
            return tree
    raise HTTPException(status_code=404, detail=f"Decision tree not found: {tree_id}")


@router.get("/quick-reference")
async def get_quick_reference():
    return _load_json("quick_reference.json")


@router.get("/taxonomy")
async def get_taxonomy():
    return _load_json("taxonomy.json")


@router.get("/learning-path/{path_id}")
async def get_learning_path(path_id: str):
    index = _load_json("index.json")
    for path in index["learning_paths"]:
        if path["id"] == path_id:
            chapters = []
            for ch_id in path["steps"]:
                try:
                    chapters.append(_load_chapter(ch_id))
                except HTTPException:
                    chapters.append({"id": ch_id, "title": ch_id, "error": "not found"})
            return {"path": path, "chapters": chapters}
    raise HTTPException(status_code=404, detail=f"Learning path not found: {path_id}")


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload GC TE Policy PDF and trigger ingestion."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    source_dir = KB_ROOT / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    dest = source_dir / "GC_TE_Policy_v202212.pdf"

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    try:
        import subprocess
        import sys
        script = KB_ROOT / "scripts" / "ingest_pdf.py"
        result = subprocess.run(
            [sys.executable, str(script), str(dest)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return {
                "status": "uploaded_but_ingest_failed",
                "filename": file.filename,
                "size_bytes": len(content),
                "error": result.stderr,
            }
        build_script = KB_ROOT / "scripts" / "build_study_materials.py"
        subprocess.run([sys.executable, str(build_script)], capture_output=True, timeout=60)
    except Exception as e:
        return {
            "status": "uploaded_but_ingest_failed",
            "filename": file.filename,
            "error": str(e),
        }

    return {
        "status": "success",
        "filename": file.filename,
        "size_bytes": len(content),
        "message": "PDF uploaded and knowledge base updated",
    }
