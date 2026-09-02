# Agentic Chat

A Claude-style chat application powered by OpenRouter. Chat with hundreds of models, create custom skills, and manage conversations.

## Features

- **Chat** — stream responses, stop mid-stream, copy messages, message metadata
- **Model picker** — browse all OpenRouter models, grouped by provider, searchable, with context/pricing info
- **Balance check** — view your OpenRouter account balance (credits remaining) in the settings drawer
- **Skills** — enable/disable built-in skills or create your own custom system prompts
- **Conversations** — sidebar with search, rename, delete, auto-title from first message
- **Attachments** — upload images (sent to vision-capable models), text/code files (inlined as context)
- **Settings** — API key management, default model, dark/light theme
- **Export/Import** — download conversations as JSON or Markdown, restore from backup
- **Authentication** — user registration, login/logout, session-based auth (7-day expiry)

## Quick start

```bash
pip install httpx werkzeug
set OPENROUTER_API_KEY=sk-or-...
python server.py
```

Open http://localhost:8000 in your browser.

The `data/` directory (config, conversations, skills, attachments, sessions, users) is created automatically on first run.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Your OpenRouter API key (required) |
| `HOST` | `[IP_ADDRESS]` | Server bind address |
| `PORT` | `8000` | Server port |

The API key can also be set via the Settings UI (persisted to `data/config.json`).

## Authentication

The application includes a built-in authentication system:

- **Registration**: POST `/api/auth/register` with `{username, password}`
- **Login**: POST `/api/auth/login` returns a session token
- **Logout**: POST `/api/auth/logout` (requires Bearer token)
- **Session check**: GET `/api/auth/check` (returns authenticated status)

All protected API endpoints require a `Bearer` token in the `Authorization` header.
Sessions expire after 7 days of inactivity.

## File layout

```
├── openrouter.py           # OpenRouter API client (models, balance, chat)
├── server.py              # Python backend (stdlib + httpx)
├── static/
│   ├── index.html         # Single-page app markup
│   ├── styles.css         # Dark/light theme CSS
│   └── app.js             # Frontend JavaScript with state management and streaming fetch
├── data/
│   ├── config.json        # API key, default model
│   ├── conversations/     # Per-conversation JSON files
│   ├── skills.json        # Custom skills
│   ├── attachments/       # Uploaded images
│   ├── sessions.json      # Active sessions
│   └── users.json         # Registered users
├── tests/
│   ├── test_app.html      # Test runner for app.js
│   ├── test_app.js        # Unit tests for app.js state management and streaming
│   ├── test_openrouter.py # OpenRouter API unit tests
│   ├── test_styles.py
│   └── test_server.py     # Backend unit tests
└── README.md
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/auth/check` | Check authentication status |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get session token |
| POST | `/api/auth/logout` | Logout and invalidate session |
| GET | `/api/models` | List OpenRouter models (protected) |
| GET | `/api/balance` | Check API key balance (protected) |
| GET/PUT | `/api/config` | Read/write settings (protected) |
| GET/POST | `/api/conversations` | List/create conversations (protected) |
| GET/PATCH/DELETE | `/api/conversations/:id` | Get/update/delete conversation (protected) |
| POST | `/api/conversations/import` | Import a conversation backup (protected) |
| GET | `/api/conversations/:id/export?format=json|markdown` | Export (protected) |
| GET/POST | `/api/skills` | List/create skills (protected) |
| PATCH/DELETE | `/api/skills/:id` | Update/delete skill (protected) |
| POST | `/api/attachments` | Upload an attachment (protected) |
| POST | `/api/chat` | Stream a chat response (SSE) (protected) |

The `/api/chat` endpoint returns a Server-Sent Events (SSE) stream. Each event has type `chunk` (partial content), `done` (final), `error` (failure), or `usage` (token usage). The frontend `streamFetch` function in `app.js` processes these events, updating the UI incrementally as chunks arrive, and supports cancellation via an `AbortController`.

The `/api/balance` endpoint returns a JSON object with `credits`, `usage`, and `total` fields representing the OpenRouter account balance.

## Requirements

- Python 3.10+
- httpx (install via `pip install httpx`)
- werkzeug (install via `pip install werkzeug`)
- OpenRouter API key (get one at https://openrouter.ai/keys)

## Tests

Basic tests are located in `tests/`. Run them with:

```bash
python -m pytest tests/
```

(Requires `pytest` installed.)

For frontend tests, open `tests/test_app.html` in a browser or run with Node.js:

```bash
node tests/test_app.js
```

## Styling

The UI uses CSS custom properties for theming. Two themes are supported:
- **Light** (default) — white backgrounds, dark text, blue accent
- **Dark** — dark backgrounds, light text, light blue accent

Toggle theme via the settings drawer or `data-theme` attribute on `<html>`.