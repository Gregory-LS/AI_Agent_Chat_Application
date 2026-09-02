# Agentic Chat

A Claude-style chat application powered by OpenRouter. Chat with hundreds of models, create custom skills, and manage conversations.

## Features

- **Chat** — stream responses, stop mid-stream, copy messages, message metadata
- **Model picker** — browse all OpenRouter models, grouped by provider, searchable, with context/pricing info
- **Skills** — enable/disable built-in skills or create your own custom system prompts
- **Conversations** — sidebar with search, rename, delete, auto-title from first message
- **Attachments** — upload images (sent to vision-capable models), text/code files (inlined as context)
- **Settings** — API key management, default model, dark/light theme
- **Export/Import** — download conversations as JSON or Markdown, restore from backup

## Quick start

```bash
pip install httpx
set OPENROUTER_API_KEY=sk-or-...
python server.py
```

Open http://localhost:8000 in your browser.

The `data/` directory (config, conversations, skills, attachments) is created automatically on first run.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Your OpenRouter API key (required) |
| `HOST` | `[IP_ADDRESS]` | Server bind address |
| `PORT` | `8000` | Server port |

The API key can also be set via the Settings UI (persisted to `data/config.json`).

## File layout

```
├── server.py              # Python backend (stdlib + httpx)
├── static/
│   ├── index.html         # Single-page app markup
│   ├── styles.css         # Dark/light theme CSS
│   └── app.js             # Frontend JavaScript
├── data/
│   ├── config.json        # API key, default model
│   ├── conversations/     # Per-conversation JSON files
│   ├── skills.json        # Custom skills
│   └── attachments/       # Uploaded images
├── tests/
│   ├── test_app.html
│   ├── test_app.js
│   └── test_styles.py
└── README.md
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/models` | List OpenRouter models |
| GET | `/api/balance` | Check API key balance |
| GET/PUT | `/api/config` | Read/write settings |
| GET/POST | `/api/conversations` | List/create conversations |
| GET/PATCH/DELETE | `/api/conversations/:id` | Get/update/delete conversation |
| POST | `/api/conversations/import` | Import a conversation backup |
| GET | `/api/conversations/:id/export?format=json|markdown` | Export |
| GET/POST | `/api/skills` | List/create skills |
| PATCH/DELETE | `/api/skills/:id` | Update/delete skill |
| POST | `/api/attachments` | Upload an attachment |
| POST | `/api/chat` | Stream a chat response (SSE) — see below |

The `/api/chat` endpoint returns a Server-Sent Events (SSE) stream. Each event has type `chunk` (partial content), `done` (final), `error` (failure), or `usage` (token usage).

## Requirements

- Python 3.10+
- httpx (install via `pip install httpx`)
- OpenRouter API key (get one at https://openrouter.ai/keys)

## Tests

Basic tests are located in `tests/`. Run them with:

```bash
python -m pytest tests/
```

(Requires `pytest` installed.)
