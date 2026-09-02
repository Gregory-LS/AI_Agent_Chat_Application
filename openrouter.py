import httpx

BASE_URL = "https://openrouter.ai/api/v1"

def get_models(api_key: str) -> list:
    """Fetch available models from OpenRouter."""
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/models", headers=headers)
        resp.raise_for_status()
        return resp.json().get("data", [])

def get_balance(api_key: str) -> dict:
    """Fetch account balance from OpenRouter."""
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/auth/key", headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "credits": data.get("credits", 0),
            "usage": data.get("usage", 0),
            "total": data.get("total_credits", 0)
        }

def chat(api_key: str, model: str, messages: list, **kwargs):
    """Stream a chat completion from OpenRouter."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        **kwargs
    }
    with httpx.Client() as client:
        with client.stream("POST", f"{BASE_URL}/chat/completions", json=payload, headers=headers) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]
