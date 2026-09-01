import pytest

from openrouter_metadata import MetadataStore, store_response


def sample_response():
    return {
        'id': 'gen-abc123',
        'model': 'openai/gpt-4o',
        'created': 1710000000,
        'provider': 'OpenAI',
        'choices': [
            {
                'index': 0,
                'finish_reason': 'stop',
                'message': {
                    'role': 'assistant',
                    'content': 'secret text',
                },
            }
        ],
        'usage': {
            'prompt_tokens': 12,
            'completion_tokens': 5,
            'total_tokens': 17,
        },
    }


def test_insert_metadata():
    store = MetadataStore()
    try:
        record_id = store.insert_metadata(
            {
                'id': 'gen-1',
                'model': 'openai/gpt-4o',
                'created': 123,
                'usage': {'total_tokens': 10},
            }
        )
        assert record_id > 0
        records = store.list_records()
        assert len(records) == 1
        assert records[0]['response_id'] == 'gen-1'
        assert records[0]['model'] == 'openai/gpt-4o'
        assert records[0]['created'] == 123
        assert records[0]['total_tokens'] == 10
        assert records[0]['metadata']['usage']['total_tokens'] == 10
        assert records[0]['captured_at'] != ''
    finally:
        store.close()


def test_store_response_method():
    with MetadataStore() as store:
        record_id = store.store_response(sample_response())
        assert record_id > 0
        assert store.count() == 1
        records = store.list_records(limit=1)
        assert records[0]['metadata']['model'] == 'openai/gpt-4o'
        assert records[0]['metadata']['choices'][0]['message']['role'] == 'assistant'
        assert 'content' not in records[0]['metadata']['choices'][0]['message']


def test_store_response_function(tmp_path):
    db_path = tmp_path / 'metadata.db'
    record_id = store_response(sample_response(), db_path=db_path)
    assert record_id > 0
    with MetadataStore(db_path) as store:
        assert store.count() == 1


def test_store_multiple_and_limit():
    with MetadataStore() as store:
        store.insert_metadata({'id': 'a', 'model': 'm'})
        store.insert_metadata({'id': 'b', 'model': 'm'})
        assert store.count() == 2
        assert len(store.list_records(limit=1)) == 1
        assert len(store.list_records(limit=0)) == 0


def test_negative_limit_raises():
    with MetadataStore() as store:
        with pytest.raises(ValueError):
            store.list_records(limit=-1)
