# OpenRouter SSE Proxy

A small Flask server that proxies `/v1/chat/completions` requests to OpenRouter and streams the results back as Server-Sent Events (SSE).

## Requirements

- Python 3.9+
- An [OpenRouter API key](https://openrouter.ai/keys)

## Setup

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=your_key_here
python server.py
```

The server listens on port `8000` by default. Use `PORT` to change it.

## Endpoints

- `POST /v1/chat/completions` - proxy to OpenRouter and stream SSE
- `POST /api/v1/chat/completions` - alias for the same proxy
- `GET /health` - health check

## Authentication

Pass an `Authorization: Bearer <key>` header, or set the `OPENROUTER_API_KEY` environment variable. The header takes precedence.

## Example

```bash
curl -N http://localhost:8000/v1/chat/completions \
  -H 'Authorization: Bearer $OPENROUTER_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"model": "openai/gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

The response is an SSE stream. The proxy forces `stream: true` upstream.

## Environment variables

- `OPENROUTER_API_KEY` - required unless a Bearer token is sent with the request
- `OPENROUTER_URL` - optional upstream URL override
- `OPENROUTER_APP_TITLE` - optional app title sent to OpenRouter as `X-Title`
- `PORT` - HTTP port to bind (default `8000`)

## Tests

```bash
pytest
```

CORS is enabled for browser-based clients.
