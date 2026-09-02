# Agentic Chat

A Claude-style chat application powered by OpenRouter. Chat with hundreds of models, create custom skills, and manage conversations.

## Features
- Chat with streaming responses and stop mid-stream
- Model picker: browse all OpenRouter models grouped by provider
- Skills: enable/disable built-in skills or create custom ones
- Conversations: sidebar with search, rename, delete, auto-title
- Attachments: upload images and text/code files
- Settings: API key management, default model, dark/light theme
- Export/Import: download conversations as JSON or Markdown

## Quick start
```bash
pip install httpx
export OPENROUTER_API_KEY=sk-or-...
cd _app && python server.py
```
Open http://localhost:8000

## Built with
- Python stdlib http.server + httpx (no frameworks)
- Vanilla JS frontend (no frameworks)
- OpenRouter API for model access