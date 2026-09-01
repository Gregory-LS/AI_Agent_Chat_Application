import json
import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from server import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_completions_streaming(client):
    """Test that streaming works and yields SSE events."""
    # We need to mock the OpenRouter API call
    async def mock_stream(*args, **kwargs):
        class MockResponse:
            status_code = 200
            async def aiter_lines(self):
                yield "data: {"choices":[{"delta":{"content":"Hello"}}]}"
                yield "data: [DONE]"
            async def aread(self):
                return b""
        return MockResponse()

    with patch("httpx.AsyncClient.stream", new=mock_stream):
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say hello"}],
            "stream": True,
        }
        async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(line)
            # Should have at least the data line and [DONE]
            assert len(lines) >= 2
            assert "data: {" in lines[0] or "data: [DONE]" in lines[0]


@pytest.mark.asyncio
async def test_chat_completions_error(client):
    """Test that API errors are forwarded as SSE error events."""
    async def mock_stream_error(*args, **kwargs):
        class MockResponse:
            status_code = 401
            async def aiter_lines(self):
                return iter([])
            async def aread(self):
                return b"{\"error\":{\"message\":\"Invalid API key\"}}"
        return MockResponse()

    with patch("httpx.AsyncClient.stream", new=mock_stream_error):
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "test"}],
        }
        async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
            assert response.status_code == 200  # We always return 200 for SSE
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(line)
            # Should contain error event
            error_event = [l for l in lines if "error" in l]
            assert len(error_event) > 0
            assert "Invalid API key" in error_event[0]


@pytest.mark.asyncio
async def test_invalid_payload(client):
    """Test that invalid request body returns 422."""
    response = await client.post("/v1/chat/completions", json={"model": "test"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_no_api_key():
    """Test that server raises error if API key missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            # Reload module to trigger env check
            import importlib
            import server
            importlib.reload(server)
