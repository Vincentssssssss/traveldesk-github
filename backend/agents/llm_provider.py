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


def extract_text_content(value) -> str:
    """
    Normalize LLM outputs into plain text.

    Azure OpenAI Responses may return `AIMessage.content` as a list of
    typed content blocks (dict/object), while other providers commonly
    return a plain string. This function supports both formats.
    """
    if value is None:
        return ""

    # Accept full message object as input.
    if hasattr(value, "content"):
        value = value.content

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            text = extract_text_content(item)
            if text:
                parts.append(text)
        return "".join(parts).strip()

    if isinstance(value, dict):
        # Common Responses API block: {"type":"output_text","text":"..."}
        text = value.get("text")
        if isinstance(text, str):
            return text
        if isinstance(text, list):
            return extract_text_content(text)

        # Fallbacks for other block shapes
        for key in ("content", "output_text", "value"):
            nested = value.get(key)
            if nested is not None:
                return extract_text_content(nested)
        return ""

    # Object-like content items from SDKs.
    for attr in ("text", "content", "output_text", "value"):
        if hasattr(value, attr):
            return extract_text_content(getattr(value, attr))

    return str(value)


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
