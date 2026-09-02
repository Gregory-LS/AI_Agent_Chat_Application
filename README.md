# Agentic Chat

A Claude-style chat application powered by OpenRouter. Chat with hundreds of models, create custom skills, and manage conversations.

## Features

- **Chat** — stream responses, stop mid-stream, copy messages, message metadata
- **Model picker** — browse all OpenRouter models, grouped by provider, searchable, with context/pricing info
- **Balance check** — view your OpenRouter account balance (credits remaining) in the settings drawer
- **Skills** — enable/disable built-in skills or create your own custom system prompts
- **Conversations** — sidebar with search, rename, delete, auto-title from first message
- **Attachments** — upload images (sent to vision-capable models), text/code files (inlined as context)
- **Settings** — API key management, default model, dark/light theme toggle
- **Export/Import** — download conversations as JSON or Markdown, restore from backup
- **Theme toggle** — switch between light and dark themes via the Settings drawer; preference is saved to localStorage
- **Keyboard shortcuts** — navigate and control the app without leaving the keyboard (see below)

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
│   └── attachments/       # Uploaded images
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
| GET | `/api/models` | List OpenRouter models |
| GET | `/api/balance` | Check API key balance (credits, usage, total) |
| GET/PUT | `/api/config` | Read/write settings |
| GET/POST | `/api/conversations` | List/create conversations |
| GET/PATCH/DELETE | `/api/conversations/:id` | Get/update/delete conversation |
| POST | `/api/conversations/import` | Import a conversation backup |
| GET | `/api/conversations/:id/export?format=json|markdown` | Export |
| GET/POST | `/api/skills` | List/create skills |
| PATCH/DELETE | `/api/skills/:id` | Update/delete skill |
| POST | `/api/attachments` | Upload an attachment |
| POST | `/api/chat` | Stream a chat response (SSE) — see below |

The `/api/chat` endpoint returns a Server-Sent Events (SSE) stream. Each event has type `chunk` (partial content), `done` (final), `error` (failure), or `usage` (token usage). The frontend `streamFetch` function in `app.js` processes these events, updating the UI incrementally as chunks arrive, and supports cancellation via an `AbortController`.

The `/api/balance` endpoint returns a JSON object with `credits`, `usage`, and `total` fields representing the OpenRouter account balance.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+O` | Focus the composer |
| `Ctrl+Shift+N` | New conversation |
| `Ctrl+Shift+,` | Open settings |
| `Ctrl+Shift+E` | Open skills |
| `Escape` | Close modals/drawers or stop generation |
| `Ctrl+Shift+Delete` | Clear all conversations |
| `Ctrl+Shift+ArrowUp` | Previous conversation |
| `Ctrl+Shift+ArrowDown` | Next conversation |
| `Ctrl+Shift+S` | Toggle theme |

Shortcuts do not fire when the user is typing in an input, textarea, or contenteditable element (except for `Ctrl+Shift+O` and `Escape`, which work globally).

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

For frontend tests, open `tests/test_app.html` in a browser or run with Node.js:

```bash
node tests/test_app.js
```

## Styling

The UI uses CSS custom properties for theming. Two themes are supported:
- **Light** (default) — white backgrounds, dark text, blue accent
- **Dark** — dark backgrounds, light text, light blue accent

Toggle theme via the settings drawer or `data-theme` attribute on `<html>`. The preference is saved in `localStorage` and persists across sessions.
