import os
import json
import asyncio
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="OpenRouter Proxy SSE")

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

def error_response(message: str, status_code: int = 500):
    return {"error": {"message": message, "type": "server_error", "code": status_code}}

async def stream_from_openrouter(payload: dict) -> AsyncGenerator[bytes, None]:
    """
    Send request to OpenRouter and yield SSE-formatted chunks.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{OPENROUTER_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                error_data = await response.aread()
                yield f"data: {json.dumps(error_response(error_data.decode(), response.status_code))}\n\n".encode()
                return

            async for chunk in response.aiter_bytes():
                yield f"data: {chunk.decode()}\n\n".encode()

        yield "data: [DONE]\n\n".encode()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Proxy endpoint that forwards to OpenRouter and streams the response.
    Accepts OpenAI-compatible JSON payload.
    """
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Ensure streaming is enabled
    body["stream"] = True

    # Validate required fields
    if "messages" not in body or not isinstance(body["messages"], list):
        raise HTTPException(status_code=400, detail="Missing or invalid 'messages' field")

    return StreamingResponse(
        stream_from_openrouter(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
