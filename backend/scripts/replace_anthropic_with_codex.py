#!/usr/bin/env python3
"""
Heuristic script to replace common Anthropic usage with call_codex usage.
- Backs up modified files to <file>.bak
- Replacements are conservative but require manual review.
"""
import os
import re
from pathlib import Path

ROOT = Path(".").resolve()
SEARCH_PATTERNS = ["anthropic", "Anthropic", "HUMAN_PROMPT", "AI_PROMPT"]

def file_needs_patch(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return any(p in text for p in SEARCH_PATTERNS)

def patch_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    orig = text

    # 1) Replace "from anthropic import ..." with local wrapper import
    text = re.sub(
        r"from\s+anthropic\s+import\s+[^\n]+",
        "from backend.ai.openai_codex_client import call_codex",
        text
    )
    # 2) Replace "import anthropic" with wrapper import
    text = re.sub(r"^\s*import\s+anthropic\s*$", "from backend.ai.openai_codex_client import call_codex", text, flags=re.MULTILINE)

    # 3) Remove or replace Anthropic client instantiation lines like: client = Anthropic(api_key=...)
    text = re.sub(r"^[ \t]*[A-Za-z0-9_]+\s*=\s*Anthropic\([^\)]*\)\s*$", "", text, flags=re.MULTILINE)

    # 4) Replace calls to client.completions.create(...) -> call_codex(...)
    text = re.sub(r"[A-Za-z0-9_]*\.completions\.create\s*\(", "call_codex(", text)

    # 5) Replace HUMAN_PROMPT + var + AI_PROMPT -> var (heuristic)
    text = re.sub(r"HUMAN_PROMPT\s*\+\s*([A-Za-z0-9_\"'\(\)\[\]\s\.]+?)\s*\+\s*AI_PROMPT", r"\1", text)

    # 6) If code expects resp['completion'] or resp['completion_text'], normalize by introducing resp_text variable.
    # Add a small post-processing: replace usages of resp['completion'] with resp_text
    text = re.sub(r"resp\[['\"]completion['\"]\]", "resp_text", text)
    text = re.sub(r"resp\[['\"]completion_text['\"]\]", "resp_text", text)

    # 7) If function called client.chat.completions.create or client.chat.completions, catch common variants
    text = re.sub(r"[A-Za-z0-9_]*\.chat\.completions\.create\s*\(", "call_codex(", text)
    text = re.sub(r"[A-Za-z0-9_]*\.completions\s*\(", "call_codex(", text)

    if text != orig:
        bak = path.with_suffix(path.suffix + ".bak")
        path.write_text(text, encoding="utf-8")
        bak.write_text(orig, encoding="utf-8")
        print(f"Patched {path} (backup: {bak})")
    else:
        print(f"No changes for {path}")

def main():
    py_files = list(ROOT.rglob("*.py"))
    skip_dirs = {"venv", ".venv", ".git", "build", "dist", "__pycache__"}
    for p in py_files:
        if any(part in skip_dirs for part in p.parts):
            continue
        try:
            if file_needs_patch(p):
                patch_file(p)
        except Exception as e:
            print(f"Error patching {p}: {e}")

if __name__ == "__main__":
    main()
