# OpenRouter Metadata Capture

Utilities for extracting and storing metadata from OpenRouter API responses.

## Features

- Extract response metadata such as `id`, `model`, `created`, `provider`, and usage token counts.
- Accept a response dict, a JSON string, or UTF-8 bytes.
- Exclude message content from stored metadata to avoid persisting assistant/user text.
- Persist metadata records to SQLite for later analysis.

## Installation

The package has no third-party runtime dependencies. To run the test suite, install pytest and run it from the repository root:

```bash
pip install pytest
pytest
```

## Usage

```python
from openrouter_metadata import extract_metadata, MetadataStore

response = {
    'id': 'gen-abc',
    'model': 'openai/gpt-4o',
    'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30},
}

metadata = extract_metadata(response)

with MetadataStore('metadata.db') as store:
    store.store_response(response)
    records = store.list_records()
```

## Stored Schema

The SQLite table `openrouter_metadata` contains the following columns:

- `id`: auto-incrementing primary key
- `response_id`: the OpenRouter response `id` when present
- `model`: the model name
- `provider`: the upstream provider when present
- `created`: the response creation timestamp
- `total_tokens`: total token usage from `usage.total_tokens`
- `metadata_json`: the full extracted metadata as JSON (without message content)
- `captured_at`: UTC timestamp when the record was stored
