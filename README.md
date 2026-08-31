# Conversation Import Endpoint

This project provides a minimal Flask application with a JSON endpoint to import conversations.

## Endpoint

### POST /api/conversations/import

Accepts a JSON body with the following structure:

```json
{
  "id": "optional-id",
  "title": "Meeting notes",
  "participants": ["alice", "bob"],
  "messages": [
    {"role": "user", "content": "Hello", "timestamp": "2024-01-01T12:00:00Z"},
    {"role": "assistant", "content": "Hi", "timestamp": "2024-01-01T12:00:01Z"}
  ],
  "metadata": {}
}
```

Required fields:
- `title`: string
- `messages`: non-empty array of objects with `role` and `content`

Optional fields:
- `id`: unique conversation ID (auto-generated if omitted)
- `participants`: array of strings
- `metadata`: arbitrary JSON object
- each message may include `timestamp` or other fields

On success: HTTP 201 with `{"status": "imported", "id": "...", "message_count": N}`.
On validation failure: HTTP 422 with details.
On malformed JSON: HTTP 400.

## Running

```
pip install -r requirements.txt
python app.py
```

Note: This is a standalone example. In a larger codebase, integrate the endpoint into the existing application and replace the in-memory `CONVERSATIONS` dict with the project's persistence layer.
