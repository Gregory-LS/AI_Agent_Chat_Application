# Conversation Manager

Standalone UI for searching, archiving/unarchiving, exporting, and importing conversations.

Open `/static/conversations.html` in the browser.

## Features
- Search conversations by title or message content.
- Filter by active/archived status.
- Archive/unarchive single or multiple conversations.
- Export one, selected, or all conversations as JSON.
- Import conversations from a JSON file with a `{ "conversations": [...] }` structure.

## API
The UI expects the following endpoints:
- `GET /api/conversations`
- `GET /api/conversations/{id}`
- `POST /api/conversations`
- `PATCH /api/conversations/{id}` with `{ "archived": boolean }`
- `DELETE /api/conversations/{id}`
