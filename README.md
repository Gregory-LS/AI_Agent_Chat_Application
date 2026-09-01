# OpenRouter Proxy with SSE Streaming

A FastAPI server that proxies requests to [OpenRouter](https://openrouter.ai/) and streams responses via Server-Sent Events (SSE).

## Features

- OpenAI-compatible endpoint (`/v1/chat/completions`)
- True SSE streaming using `text/event-stream`
- Secure API key handling via environment variable
- Error handling and validation
- Health check endpoint

## Requirements

- Python 3.9+
- `fastapi`, `uvicorn`, `httpx`

Install dependencies:

```bash
pip install fastapi uvicorn httpx
```

## Configuration

Set the `OPENROUTER_API_KEY` environment variable with your OpenRouter API key:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

## Usage

Start the server:

```bash
uvicorn server:app --reload --port 8000
```

### Endpoints

#### `POST /v1/chat/completions`

Accepts a JSON payload compatible with the OpenAI Chat Completions API. The `stream` parameter is automatically set to `true`.

**Example request:**

```json
{
  "model": "openai/gpt-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

**Response:** Server-Sent Events stream with `data:` lines.

#### `GET /health`

Returns `{"status": "ok"}` if the server is running.

## Testing

Run tests with `pytest`:

```bash
pytest tests/
```

## Project Structure

```
.
├── server.py          # FastAPI application
├── tests/
│   └── test_server.py # Unit tests
└── README.md          # This file
```
