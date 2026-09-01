import os
import json
import pytest
from unittest.mock import patch, AsyncMock

from httpx import AsyncClient
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)

# Mock environment variable
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    # Reload module to pick up env var
    import importlib
    import server
    importlib.reload(server)
    yield


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    import importlib
    import server
    importlib.reload(server)
    test_client = TestClient(server.app)
    response = test_client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert response.status_code == 500
    assert "OPENROUTER_API_KEY not set" in response.text


def test_invalid_json():
    response = client.post("/v1/chat/completions", data="not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert "Invalid JSON" in response.text


def test_missing_messages():
    response = client.post("/v1/chat/completions", json={"model": "gpt-3.5-turbo"})
    assert response.status_code == 400
    assert "Missing or invalid 'messages'" in response.text


@pytest.mark.asyncio
async def test_streaming_success():
    """Test that the streaming endpoint returns SSE events."""
    from server import stream_from_openrouter

    # Mock httpx async client to return fake chunks
    async def mock_aiter_bytes():
        yield b'{"choices":[{"delta":{"content":"Hello"}}]}'
        yield b'{"choices":[{"delta":{"content":" world"}}]}'

    class MockResponse:
        status_code = 200
        async def aiter_bytes(self):
            return mock_aiter_bytes()
        async def aread(self):
            return b""

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.stream.return_value.__aenter__.return_value = MockResponse()

    with patch("server.httpx.AsyncClient", return_value=mock_client):
        chunks = []
        async for chunk in stream_from_openrouter({"messages": [{"role": "user", "content": "hi"}]}):
            chunks.append(chunk)

    # Expect two data events + [DONE]
    assert len(chunks) == 3
    assert chunks[0].startswith(b"data: ")
    assert chunks[1].startswith(b"data: ")
    assert chunks[2] == b"data: [DONE]\n\n"


def test_streaming_endpoint_integration():
    """Integration test using TestClient (mock the actual external call)."""
    # We'll patch the stream_from_openrouter to return a known sequence
    from server import stream_from_openrouter
    async def fake_stream(payload):
        yield b"data: {\"choices\":[{\"delta\":{\"content\":\"test\"}}]}\n\n"
        yield b"data: [DONE]\n\n"

    with patch("server.stream_from_openrouter", side_effect=fake_stream):
        response = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "hi"}]}
        )
        assert response.status_code == 200
        assert response.text.startswith("data: ")
        assert "[DONE]" in response.text
