import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openrouter import (
    list_models,
    check_balance,
    stream_chat,
    _get_headers,
    OPENROUTER_BASE_URL,
)


class TestGetHeaders:
    def test_basic_headers(self):
        headers = _get_headers("test-key")
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers

    def test_headers_with_env(self):
        with patch.dict(os.environ, {"APP_URL": "https://example.com", "APP_NAME": "Test App"}):
            headers = _get_headers("test-key")
            assert headers["HTTP-Referer"] == "https://example.com"
            assert headers["X-Title"] == "Test App"


class TestListModels:
    def test_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4", "name": "GPT-4"},
                {"id": "anthropic/claude-3", "name": "Claude 3"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.return_value = mock_response

            models = list_models("test-key")
            assert len(models) == 2
            assert models[0]["id"] == "openai/gpt-4"
            assert models[1]["id"] == "anthropic/claude-3"

    def test_empty_response(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.return_value = mock_response

            models = list_models("test-key")
            assert models == []

    def test_http_error(self):
        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
            )

            with pytest.raises(httpx.HTTPStatusError):
                list_models("test-key")


class TestCheckBalance:
    def test_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "key": "sk-or-...",
            "credits": 100.50,
            "usage": 50.25,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.return_value = mock_response

            balance = check_balance("test-key")
            assert balance["credits"] == 100.50
            assert balance["usage"] == 50.25


class TestStreamChat:
    def test_stream_chunks(self):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            'data: {"choices": [{"delta": {"content": "Hello"}, "finish_reason": null}]}',
            'data: {"choices": [{"delta": {"content": " world"}, "finish_reason": null}]}',
            'data: {"choices": [{"delta": {"content": ""}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}',
            "data: [DONE]",
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.stream.return_value.__enter__.return_value = mock_response

            results = list(stream_chat("test-key", [{"role": "user", "content": "Hi"}]))
            assert len(results) == 4
            assert results[0] == {"type": "chunk", "content": "Hello"}
            assert results[1] == {"type": "chunk", "content": " world"}
            assert results[2] == {"type": "usage", "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            assert results[3] == {"type": "done"}

    def test_stream_error(self):
        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.stream.side_effect = httpx.RequestError("Connection failed")

            results = list(stream_chat("test-key", [{"role": "user", "content": "Hi"}]))
            assert len(results) == 1
            assert results[0]["type"] == "error"
            assert "Connection failed" in results[0]["error"]

    def test_stream_http_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "402 Payment Required", request=MagicMock(), response=MagicMock(status_code=402, text="Insufficient credits")
        )

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.stream.return_value.__enter__.return_value = mock_response

            results = list(stream_chat("test-key", [{"role": "user", "content": "Hi"}]))
            assert len(results) == 1
            assert results[0]["type"] == "error"
            assert "402" in results[0]["error"]

    def test_stream_empty_lines(self):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = ["", "   ", "data: [DONE]"]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.stream.return_value.__enter__.return_value = mock_response

            results = list(stream_chat("test-key", [{"role": "user", "content": "Hi"}]))
            assert len(results) == 1
            assert results[0] == {"type": "done"}

    def test_stream_custom_model(self):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = ["data: [DONE]"]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.stream.return_value.__enter__.return_value = mock_response

            results = list(stream_chat("test-key", [{"role": "user", "content": "Hi"}], model="anthropic/claude-3-opus"))
            # Verify the model was passed in the request
            call_kwargs = mock_client_instance.stream.call_args[1]
            assert call_kwargs["json"]["model"] == "anthropic/claude-3-opus"
            assert len(results) == 1
