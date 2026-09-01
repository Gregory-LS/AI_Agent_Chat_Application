import os
import json
import logging
from typing import AsyncGenerator, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)

app = FastAPI(title="OpenRouter Proxy", version="1.0.0")

# CORS configuration (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatCompletionRequest(BaseModel):
    """Request model matching OpenRouter's chat completion endpoint."""
    model: str = Field(..., description="Model identifier")
    messages: list[dict] = Field(..., description="List of message objects")
    stream: bool = Field(True, description="Whether to stream the response")
    # Additional optional fields can be added; we pass everything through
    class Config:
        extra = "allow"


async def stream_openrouter_response(
    request_data: dict, api_key: str, base_url: str
) -> AsyncGenerator[str, None]:
    """
    Stream response from OpenRouter API and yield SSE-formatted strings.

    Args:
        request_data: The request payload (dict).
        api_key: OpenRouter API key.
        base_url: Base URL for OpenRouter API.

    Yields:
        SSE event strings.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{base_url}/chat/completions",
            json=request_data,
            headers=headers,
        ) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                logger.error(
                    f"OpenRouter API error {response.status_code}: {error_body}"
                )
                yield f"data: {json.dumps({'error': error_body.decode()})}\n\n"
                yield "data: [DONE]\n\n"
                return

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line + "\n"
                elif line.strip() == "data: [DONE]":
                    yield "data: [DONE]\n\n"


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Proxy endpoint for OpenRouter chat completions with SSE streaming.

    Accepts a ChatCompletionRequest and streams the response from OpenRouter
    as Server-Sent Events. If the request has `stream: false`, it will still
    stream but will send the complete response in one event.
    """
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable.",
        )

    # Convert request to dict, include extra fields
    request_data = request.model_dump()

    # Ensure stream is True for SSE; we always stream from the proxy
    request_data["stream"] = True

    return EventSourceResponse(
        stream_openrouter_response(
            request_data=request_data,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
