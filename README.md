# OpenRouter Proxy with SSE Streaming

A lightweight FastAPI server that proxies chat completion requests to [OpenRouter](https://openrouter.ai/) and streams responses back as Server-Sent Events (SSE).

## Features

- **SSE Streaming**: Real-time streaming of token responses from OpenRouter.
- **CORS Enabled**: Allows cross-origin requests from any origin (for development).
- **Health Check**: Simple `/health` endpoint.
- **Environment Configuration**: API key and base URL configurable via environment variables.

## Prerequisites

- Python 3.10+
- An OpenRouter API key ([get one here](https://openrouter.ai/keys))

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <project-directory>
   ```

2. Install dependencies:
   ```bash
   pip install fastapi uvicorn httpx sse-starlette pydantic
   ```

3. Set environment variables:
   ```bash
   export OPENROUTER_API_KEY="your-api-key"
   export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"  # optional, default shown
   ```

## Running the Server

Start the server with:

```bash
python server.py
```

Or using uvicorn directly:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`.

## API Endpoints

### GET /health

Returns `{"status": "healthy"}`.

### POST /chat/completions

Proxies the request to OpenRouter's `/chat/completions` endpoint and streams the response as SSE.

**Request body** (JSON):

| Field      | Type   | Required | Description                                      |
|------------|--------|----------|--------------------------------------------------|
| `model`    | string | Yes      | Model identifier (e.g., `openai/gpt-4`)          |
| `messages` | array  | Yes      | Array of message objects (role, content)         |
| `stream`   | bool   | No       | Always set to `true` by the proxy (ignored)      |

Additional fields (e.g., `temperature`, `max_tokens`) are passed through to OpenRouter.

**Example using curl:**

```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Example using JavaScript (browser):**

```javascript
const eventSource = new EventSource('/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'openai/gpt-4',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});
eventSource.onmessage = (event) => {
  if (event.data === '[DONE]') {
    eventSource.close();
  } else {
    console.log(JSON.parse(event.data));
  }
};
```

## Running Tests

Install test dependencies:

```bash
pip install pytest pytest-asyncio httpx
```

Run tests:

```bash
pytest tests/
```

## Environment Variables

| Variable             | Default                              | Description                     |
|----------------------|--------------------------------------|---------------------------------|
| `OPENROUTER_API_KEY` | (empty)                              | Your OpenRouter API key         |
| `OPENROUTER_BASE_URL`| `https://openrouter.ai/api/v1`       | Base URL for OpenRouter API     |

## License

MIT
