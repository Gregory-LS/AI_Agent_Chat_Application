import json

import pytest

from openrouter_metadata import extract_metadata


def sample_response():
    return {
        'id': 'gen-abc123',
        'model': 'openai/gpt-4o',
        'created': 1710000000,
        'object': 'chat.completion',
        'provider': 'OpenAI',
        'choices': [
            {
                'index': 0,
                'finish_reason': 'stop',
                'message': {
                    'role': 'assistant',
                    'content': 'Hello, world!',
                },
            }
        ],
        'usage': {
            'prompt_tokens': 12,
            'completion_tokens': 5,
            'total_tokens': 17,
            'cost': 0.0001,
        },
    }


def test_extract_metadata_from_dict():
    metadata = extract_metadata(sample_response())
    assert metadata['id'] == 'gen-abc123'
    assert metadata['model'] == 'openai/gpt-4o'
    assert metadata['provider'] == 'OpenAI'
    assert metadata['created'] == 1710000000
    assert metadata['usage']['total_tokens'] == 17
    assert metadata['choices'][0]['finish_reason'] == 'stop'
    assert metadata['choices'][0]['message']['role'] == 'assistant'
    assert 'content' not in metadata['choices'][0]['message']


def test_extract_metadata_from_json_string():
    response = json.dumps(sample_response())
    metadata = extract_metadata(response)
    assert metadata['id'] == 'gen-abc123'
    assert metadata['model'] == 'openai/gpt-4o'


def test_extract_metadata_from_bytes():
    response = json.dumps(sample_response()).encode('utf-8')
    metadata = extract_metadata(response)
    assert metadata['id'] == 'gen-abc123'


def test_streaming_chunk_content_is_excluded():
    chunk = {
        'id': 'gen-stream-1',
        'model': 'openai/gpt-4o',
        'choices': [
            {
                'index': 0,
                'finish_reason': None,
                'delta': {
                    'role': 'assistant',
                    'content': 'Hello',
                },
            }
        ],
    }
    metadata = extract_metadata(chunk)
    delta = metadata['choices'][0]['delta']
    assert delta['role'] == 'assistant'
    assert 'content' not in delta


def test_usage_keeps_unknown_fields():
    response = sample_response()
    response['usage']['custom_metric'] = 42
    metadata = extract_metadata(response)
    assert metadata['usage']['custom_metric'] == 42


def test_provider_extracted_from_usage():
    response = {
        'id': 'gen-provider',
        'model': 'some/model',
        'choices': [],
        'usage': {
            'prompt_tokens': 1,
            'completion_tokens': 1,
            'total_tokens': 2,
            'provider': 'OpenAI',
        },
    }
    metadata = extract_metadata(response)
    assert metadata['provider'] == 'OpenAI'
    assert metadata['usage']['provider'] == 'OpenAI'


def test_invalid_types_raise():
    with pytest.raises(TypeError):
        extract_metadata(['not', 'a', 'dict'])
    with pytest.raises(ValueError):
        extract_metadata('{invalid json}')
    with pytest.raises(ValueError):
        extract_metadata('[1,2,3]')
