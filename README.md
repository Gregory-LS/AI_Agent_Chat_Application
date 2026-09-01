# OpenRouter Proxy with SSE Streaming

This project provides a lightweight FastAPI server that acts as a proxy to the [OpenRouter API](https://openrouter.ai/). It accepts OpenAI-compatible chat completion requests and streams the responses back using Server-Sent Events (SSE).

## Features

- Proxy all chat completion requests to OpenRouter.
- Stream responses in real-time via SSE.
- Supports all OpenRouter models.
- Error forwarding: OpenRouter errors are sent as SSE events.
- Health check endpoint.

## Requirements

- Python 3.10+
- An OpenRouter API key

## Setup

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
4. Run the server:
   ```bash
   uvicorn server:app --reload
   ```
   The server will start at `http://localhost:8000`.

## API Endpoints

### `POST /v1/chat/completions`

Accepts a JSON body identical to the [OpenAI Chat Completion API](https://platform.openai.com/docs/api-reference/chat/create). The `stream` parameter is forced to `true`; all responses are SSE streams.

**Example request:**
```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [{"role": "user", "content": "Hello!"}],
  "max_tokens": 512
}
```

**Example response (SSE):**
```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"openai/gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}]}

data: [DONE]
```

### `GET /health`

Returns `{"status": "ok"}` if the server is running.

## Testing

Run tests with:
```bash
pytest tests/
```

## Configuration

All configuration is via environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key |

## License

MIT
