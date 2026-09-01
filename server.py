import os
import json
import logging
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenRouter Proxy with SSE")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable not set")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="openai/gpt-4o-mini", description="Model to use")
    messages: list[dict] = Field(..., description="List of messages")
    stream: bool = Field(default=True, description="Whether to stream the response")
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


async def stream_openrouter(request_body: dict) -> AsyncGenerator[str, None]:
    """
    Stream response from OpenRouter and yield SSE-formatted strings.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=request_body,
        ) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                logger.error(f"OpenRouter error {response.status_code}: {error_body}")
                yield f"data: {json.dumps({'error': {'message': error_body.decode(), 'code': response.status_code}})}\n\n"
                yield "data: [DONE]\n\n"
                return

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line + "\n\n"
                elif line.strip():
                    # Some streaming endpoints send extra lines; forward as-is
                    yield f"data: {line}\n\n"

            # Ensure stream termination
            yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Proxy endpoint that forwards to OpenRouter and streams response via SSE.
    """
    request_body = request.model_dump(exclude_none=True)
    # Force streaming via SSE
    request_body["stream"] = True

    return StreamingResponse(
        stream_openrouter(request_body),
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
