from __future__ import annotations

import os


def _read_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _normalize_base_url(url: str) -> str:
    """
    Accept either:
    - .../openai/v1
    - .../openai/v1/responses
    and normalize to the API root expected by ChatOpenAI.
    """
    normalized = url.rstrip("/")
    if normalized.endswith("/responses"):
        normalized = normalized[: -len("/responses")]
    return normalized


def is_demo_mode() -> bool:
    key = _read_env("OPENAI_API_KEY")
    return not key or key.startswith("your_") or key == "test-key"


def create_openai_chat(default_model: str, max_tokens: int):
    from langchain_openai import ChatOpenAI

    base_url = _normalize_base_url(_read_env("OPENAI_BASE_URL"))
    model = _read_env("OPENAI_MODEL", default_model) or default_model
    return ChatOpenAI(
        model=model,
        api_key=_read_env("OPENAI_API_KEY"),
        base_url=base_url or None,
        max_tokens=max_tokens,
        temperature=0,
    )
