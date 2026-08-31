"""
Module for capturing and storing metadata from OpenRouter API responses.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

# Default log file path (can be overridden via set_metadata_log_path)
_metadata_log_path: Path = Path("openrouter_metadata.jsonl")


def set_metadata_log_path(path: str | Path) -> None:
    """Set the path for the metadata log file."""
    global _metadata_log_path
    _metadata_log_path = Path(path)


def extract_metadata(response: httpx.Response) -> Dict[str, Any]:
    """
    Extract metadata from an OpenRouter API response.

    Parses standard OpenRouter response headers and optional body fields.

    Args:
        response: The httpx.Response object from an OpenRouter API call.

    Returns:
        Dict with keys: request_id, model, tokens_input, tokens_output, cost,
        finish_reason, query_duration_ms, timestamp.
    """
    headers = response.headers

    metadata: Dict[str, Any] = {
        "request_id": headers.get("x-request-id"),
        "model": headers.get("x-openai-model"),
        "tokens_input": _safe_int(headers.get("x-openai-tokens-input")),
        "tokens_output": _safe_int(headers.get("x-openai-tokens-output")),
        "cost": _safe_float(headers.get("x-openai-cost")),
        "finish_reason": None,
        "query_duration_ms": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Attempt to get finer details from the response body (if available)
    try:
        body = response.json()
        if isinstance(body, dict):
            usage = body.get("usage", {})
            if isinstance(usage, dict):
                metadata["tokens_input"] = usage.get("prompt_tokens", metadata["tokens_input"])
                metadata["tokens_output"] = usage.get("completion_tokens", metadata["tokens_output"])
            choices = body.get("choices", [])
            if choices:
                first = choices[0]
                if isinstance(first, dict):
                    metadata["finish_reason"] = first.get("finish_reason", metadata["finish_reason"])
        # Duration might be in headers as x-query-time-ms (non-standard but sometimes present)
        metadata["query_duration_ms"] = _safe_float(headers.get("x-query-time-ms"))
    except (json.JSONDecodeError, AttributeError):
        logger.debug("Response body is not valid JSON; skipping body extraction.")

    return metadata


def store_metadata(metadata: Dict[str, Any], log_path: str | Path | None = None) -> None:
    """
    Append metadata dict as a JSON line to the metadata log file.

    Args:
        metadata: Dict of metadata (as returned by extract_metadata).
        log_path: Optional override for the log file path.
    """
    path = Path(log_path) if log_path else _metadata_log_path
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata, default=str) + "\n")
        logger.debug(f"Metadata written to {path}")
    except OSError as e:
        logger.error(f"Failed to write metadata to {path}: {e}")


def _safe_int(value: Any) -> int | None:
    """Convert value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
n    except (ValueError, TypeError):
        logger.warning(f"Cannot convert {value!r} to int")
        return None

def _safe_float(value: Any) -> float | None:
    """Convert value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
n    except (ValueError, TypeError):
t        logger.warning(f"Cannot convert {value!r} to float")
        return None
