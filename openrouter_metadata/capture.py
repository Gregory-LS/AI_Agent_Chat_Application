'''Extract message metadata from OpenRouter API responses.'''

from __future__ import annotations

import json
from typing import Any, Dict, Union

_CONTENT_KEYS = frozenset({'content', 'reasoning_content', 'reasoning'})

_USAGE_FIELDS = (
    'prompt_tokens',
    'completion_tokens',
    'total_tokens',
    'reasoning_tokens',
    'cost',
    'latency',
)

_USAGE_NESTED_FIELDS = ('prompt_tokens_details', 'completion_tokens_details')


def _decode_response(response: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    '''Decode an OpenRouter response payload into a dictionary.'''
    if isinstance(response, bytes):
        try:
            response = response.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('response bytes must be UTF-8 encoded JSON') from exc

    if isinstance(response, str):
        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError('response must be a JSON string') from exc
        if not isinstance(data, dict):
            raise ValueError('response JSON must be an object')
        return data

    if isinstance(response, dict):
        return response

    raise TypeError('response must be a dict, JSON string, or bytes')


def _extract_message(message: Any) -> Any:
    '''Strip message content fields while preserving other message metadata.'''
    if not isinstance(message, dict):
        return message
    return {key: value for key, value in message.items() if key not in _CONTENT_KEYS}


def _extract_choice(choice: Any) -> Any:
    '''Extract metadata from a single choice object.'''
    if not isinstance(choice, dict):
        return choice
    extracted: Dict[str, Any] = {}
    for key, value in choice.items():
        if key == 'message':
            extracted['message'] = _extract_message(value)
        elif key == 'delta':
            extracted['delta'] = _extract_message(value)
        else:
            extracted[key] = value
    return extracted


def _extract_usage(usage: Any) -> Dict[str, Any]:
    '''Normalize OpenRouter usage information.'''
    if usage is None:
        return {}
    if not isinstance(usage, dict):
        return {'raw': usage}
    extracted: Dict[str, Any] = {}
    for field in _USAGE_FIELDS:
        if field in usage:
            extracted[field] = usage[field]
    for field in _USAGE_NESTED_FIELDS:
        if field in usage:
            extracted[field] = usage[field]
    for key, value in usage.items():
        if key not in extracted:
            extracted[key] = value
    return extracted


def extract_metadata(response: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    '''Extract metadata from an OpenRouter response.

    Args:
        response: A dict, JSON string, or UTF-8 bytes representing an OpenRouter response.

    Returns:
        A dictionary containing response metadata without message content.
    '''
    data = _decode_response(response)
    metadata: Dict[str, Any] = {}
    for key, value in data.items():
        if key == 'choices':
            if isinstance(value, list):
                metadata['choices'] = [_extract_choice(item) for item in value]
            else:
                metadata['choices'] = value
        elif key == 'usage':
            metadata['usage'] = _extract_usage(value)
        else:
            metadata[key] = value

    provider = data.get('provider')
    if provider is None and isinstance(data.get('usage'), dict):
        provider = data['usage'].get('provider')
    if provider is not None:
        metadata['provider'] = provider

    return metadata
