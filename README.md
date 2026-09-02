# Agentic Chat Application

## Overview
A simple chat application with a Python backend (using http.server) and static frontend.

## API Endpoints

### GET /api/conversations
Returns all conversations (JSON array).

### POST /api/conversations/{id}/archive
Toggles the `archived` status of a conversation. Returns the updated conversation object.
- `{id}` must be a valid UUID-style string.
- Returns 400 if ID format is invalid.
- Returns 404 if conversation does not exist.
- Returns 200 with the updated conversation on success.

## Running
```bash
cd _app
python server.py
```

## Testing
```bash
python -m pytest tests/
```
