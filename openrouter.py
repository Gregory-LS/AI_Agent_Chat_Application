import json
import os
from typing import Any, Dict, Generator, List, Optional, Tuple

import httpx


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _get_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("APP_URL", "http://localhost:8000"),
        "X-Title": os.environ.get("APP_NAME", "Agentic Chat"),
    }


def list_models(api_key: str) -> List[Dict[str, Any]]:
    """Fetch available models from OpenRouter."""
    with httpx.Client() as client:
        resp = client.get(
            f"{OPENROUTER_BASE_URL}/models",
            headers=_get_headers(api_key),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])


def check_balance(api_key: str) -> Dict[str, Any]:
    """Check API key balance and usage."""
    with httpx.Client() as client:
        resp = client.get(
            f"{OPENROUTER_BASE_URL}/auth/key",
            headers=_get_headers(api_key),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def stream_chat(
    api_key: str,
    messages: List[Dict[str, str]],
    model: str = "openai/gpt-4o-mini",
    **kwargs: Any,
) -> Generator[Dict[str, Any], None, None]:
    """Stream a chat completion from OpenRouter via SSE.

    Yields dicts with keys:
      - type: "chunk" | "done" | "error" | "usage"
      - content: str (for chunks)
      - usage: dict (for usage event)
      - error: str (for error event)
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        **kwargs,
    }

    with httpx.Client() as client:
        try:
            with client.stream(
                "POST",
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=_get_headers(api_key),
                json=payload,
                timeout=120,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: ")):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            yield {"type": "done"}
                            return
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choices = data.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield {"type": "chunk", "content": content}

                        finish_reason = choices[0].get("finish_reason")
                        if finish_reason == "stop":
                            usage = data.get("usage")
                            if usage:
                                yield {"type": "usage", "usage": usage}
                            yield {"type": "done"}
                            return

                        # Handle streaming usage if present in some models
                        usage = data.get("usage")
                        if usage:
                            yield {"type": "usage", "usage": usage}

        except httpx.HTTPStatusError as e:
            yield {"type": "error", "error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            yield {"type": "error", "error": f"Request failed: {str(e)}"}
        except Exception as e:
            yield {"type": "error", "error": f"Unexpected error: {str(e)}"}
