import os
import requests
from typing import Optional, List

AZURE_OPENAI_ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT",
    "https://foundry0805.services.ai.azure.com/openai/v1/responses"
)
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
DEFAULT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "codex-deployment")

if not AZURE_OPENAI_KEY:
    raise RuntimeError("AZURE_OPENAI_KEY environment variable is not set")

_HEADERS = {
    "Content-Type": "application/json",
    "api-key": AZURE_OPENAI_KEY
}

def call_codex(prompt: str,
               deployment: Optional[str] = None,
               max_tokens: int = 300,
               temperature: float = 0.2,
               stop: Optional[List[str]] = None,
               top_p: Optional[float] = None,
               timeout: int = 60,
               **kwargs) -> str:
    """
    Sends a request to the Azure OpenAI Responses endpoint and returns best-effort text output.
    - prompt: the text prompt to send.
    - deployment: the deployment/model name on your Azure OpenAI resource (defaults to env).
    Returns: result text (str). Raises on HTTP error.
    """
    url = AZURE_OPENAI_ENDPOINT
    deployment = deployment or DEFAULT_DEPLOYMENT

    payload = {
        "model": deployment,
        "input": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    if stop:
        payload["stop"] = stop
    if top_p is not None:
        payload["top_p"] = top_p
    payload.update(kwargs)

    resp = requests.post(url, headers=_HEADERS, json=payload, timeout=timeout)
    resp.raise_for_status()
    j = resp.json()

    # Best-effort parsing for common response shapes
    if isinstance(j, dict):
        # Responses API style: "output": [ { "content": [...] }, ... ]
        if "output" in j and isinstance(j["output"], list):
            pieces = []
            for item in j["output"]:
                if isinstance(item, dict):
                    content = item.get("content")
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict):
                                pieces.append(c.get("text") or c.get("content") or c.get("value") or "")
                            else:
                                pieces.append(str(c))
                    else:
                        pieces.append(item.get("text") or "")
                else:
                    pieces.append(str(item))
            result = "".join(pieces).strip()
            if result:
                return result

        # completion-like: "choices"[0]["text"] or chat-style message
        if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
            first = j["choices"][0]
            if isinstance(first, dict):
                if "text" in first:
                    return first["text"]
                if "message" in first and isinstance(first["message"], dict):
                    # chat-style wrapper
                    msg = first["message"].get("content")
                    if isinstance(msg, str):
                        return msg
                    # if content is dict/list, try to join
                    if isinstance(msg, list):
                        return "".join([m.get("text","") if isinstance(m, dict) else str(m) for m in msg])

        # direct string fields
        for k in ("text", "response", "result"):
            if k in j and isinstance(j[k], str):
                return j[k]

    # fallback: return raw JSON string
    return str(j)
