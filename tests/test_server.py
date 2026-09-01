import os
import json
import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport
from server import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture(autouse=True)
def set_env():
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    yield
    if "OPENROUTER_API_KEY" in os.environ:
        del os.environ["OPENROUTER_API_KEY"]


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_chat_completions_no_api_key():
    # Temporarily remove API key
    if "OPENROUTER_API_KEY" in os.environ:
        del os.environ["OPENROUTER_API_KEY"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/chat/completions",
            json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
        )
    assert response.status_code == 500
    assert "API key not configured" in response.json()["detail"]


@pytest.mark.asyncio
@patch("server.httpx.AsyncClient.stream")
async def test_chat_completions_success(mock_stream, client):
    # Mock the streaming response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = AsyncMock(return_value=[
        "data: {"choices":[{"delta":{"content":"Hello"}}]}",
        "data: {"choices":[{"delta":{"content":" world"}}]}",
        "data: [DONE]",
    ])
    mock_stream.return_value.__aenter__.return_value = mock_response

    response = await client.post(
        "/chat/completions",
        json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    # Read stream
    lines = response.text.strip().split("\n")
    assert len(lines) == 3
    assert lines[0] == "data: {"choices":[{"delta":{"content":"Hello"}}]}"
    assert lines[1] == "data: {"choices":[{"delta":{"content":" world"}}]}"
    assert lines[2] == "data: [DONE]"


@pytest.mark.asyncio
@patch("server.httpx.AsyncClient.stream")
async def test_chat_completions_api_error(mock_stream, client):
    # Mock an API error response
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.aread = AsyncMock(return_value=b"Unauthorized")
    mock_stream.return_value.__aenter__.return_value = mock_response

    response = await client.post(
        "/chat/completions",
        json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200  # We still return 200 with error in stream
    assert "data: {"error":"Unauthorized"}" in response.text
    assert "data: [DONE]" in response.text


@pytest.mark.asyncio
@patch("server.httpx.AsyncClient.stream")
async def test_chat_completions_extra_fields(mock_stream, client):
    # Test that extra fields are passed through
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = AsyncMock(return_value=[
        "data: {"choices":[{"delta":{"content":"ok"}}]}",
        "data: [DONE]",
    ])
    mock_stream.return_value.__aenter__.return_value = mock_response

    response = await client.post(
        "/chat/completions",
        json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 0.7,
            "max_tokens": 100,
        },
    )
    assert response.status_code == 200
    # Verify that the request sent to OpenRouter included extra fields
    call_args = mock_stream.call_args
    sent_json = call_args[1]["json"]
    assert sent_json["temperature"] == 0.7
    assert sent_json["max_tokens"] == 100
    assert sent_json["stream"] == True  # Overridden to True
