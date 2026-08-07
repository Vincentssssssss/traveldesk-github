#!/usr/bin/env python3
"""
GC TE Policy PDF Ingestion Script

Extracts text from GC TE Policy PDF and structures it into the knowledge base.
Usage: python scripts/ingest_pdf.py [path_to_pdf]
"""

import json
import re
import sys
from pathlib import Path

KB_ROOT = Path(__file__).parent.parent
SOURCE_DIR = KB_ROOT / "source"
DATA_DIR = KB_ROOT / "data"
CHAPTERS_DIR = DATA_DIR / "chapters"


def extract_pdf_text(pdf_path: Path) -> list[dict]:
    """Extract text from PDF, returning list of {page, text}."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Installing PyMuPDF...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf", "-q"])
        import fitz

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append({"page": i + 1, "text": text.strip()})
    doc.close()
    return pages


def detect_sections(pages: list[dict]) -> list[dict]:
    """Detect section headings and split content into chapters."""
    full_text = "\n\n".join(p["text"] for p in pages)

    heading_patterns = [
        r"(?:^|\n)(\d+\.?\s+[A-Z][^\n]{5,80})\n",
        r"(?:^|\n)([A-Z][A-Z\s&]{5,60})\n",
        r"(?:^|\n)(第[一二三四五六七八九十\d]+[章节条][^\n]{3,60})\n",
    ]

    sections = []
    for pattern in heading_patterns:
        matches = list(re.finditer(pattern, full_text))
        if len(matches) >= 3:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                sections.append({
                    "title": match.group(1).strip(),
                    "content": full_text[start:end].strip(),
                })
            break

    if not sections:
        chunk_size = max(len(full_text) // 12, 500)
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i + chunk_size]
            sections.append({
                "title": f"Section {len(sections) + 1}",
                "content": chunk,
            })

    return sections


def update_chapters_from_pdf(sections: list[dict]) -> int:
    """Update existing chapter files with extracted PDF content where matched."""
    updated = 0
    existing = sorted(CHAPTERS_DIR.glob("ch*.json"))

    for i, section in enumerate(sections):
        if i >= len(existing):
            break
        chapter_path = existing[i]
        with open(chapter_path) as f:
            chapter = json.load(f)

        chapter["pdf_extract"] = {
            "title": section["title"],
            "raw_content": section["content"][:5000],
            "source": "pdf_ingestion",
        }
        chapter["keywords"] = list(set(
            chapter.get("keywords", []) +
            [w.lower() for w in re.findall(r'\b[A-Za-z]{4,}\b', section["content"][:2000])][:20]
        ))

        with open(chapter_path, "w", encoding="utf-8") as f:
            json.dump(chapter, f, ensure_ascii=False, indent=2)
        updated += 1

    return updated


def save_raw_extract(pages: list[dict], pdf_path: Path):
    """Save raw PDF extract for reference."""
    extract_path = DATA_DIR / "pdf_extract.json"
    extract = {
        "source_file": pdf_path.name,
        "total_pages": len(pages),
        "pages": pages,
    }
    with open(extract_path, "w", encoding="utf-8") as f:
        json.dump(extract, f, ensure_ascii=False, indent=2)
    print(f"  Raw extract saved: {extract_path}")


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE_DIR / "GC_TE_Policy_v202212.pdf"

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        print(f"Please place GC TE Policy PDF at: {SOURCE_DIR / 'GC_TE_Policy_v202212.pdf'}")
        sys.exit(1)

    print(f"Ingesting: {pdf_path}")
    pages = extract_pdf_text(pdf_path)
    print(f"  Extracted {len(pages)} pages")

    save_raw_extract(pages, pdf_path)

    sections = detect_sections(pages)
    print(f"  Detected {len(sections)} sections")

    updated = update_chapters_from_pdf(sections)
    print(f"  Updated {updated} chapter files")

    index_path = DATA_DIR / "index.json"
    with open(index_path) as f:
        index = json.load(f)
    index["meta"]["last_updated"] = __import__("datetime").date.today().isoformat()
    index["meta"]["pdf_ingested"] = True
    index["meta"]["pdf_pages"] = len(pages)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print("Ingestion complete. Run build_study_materials.py to refresh flashcards/scenarios.")


if __name__ == "__main__":
    main()
