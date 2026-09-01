# Conversation Sidebar Feature

This module implements a reusable conversation sidebar for a chat application.

## Features
- List all conversations
- Search conversations by title or last message
- Create new conversations
- Click to select a conversation (dispatches custom event)
- Responsive design

## Tech Stack
- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript (vanilla)
- Testing: pytest

## Setup

1. Install dependencies:
   ```bash
   pip install flask flask-cors pytest
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open `http://localhost:5000` in your browser.

## API Endpoints

### GET /api/conversations
Returns list of conversations. Optional query parameter `search` filters by title or last message.

### POST /api/conversations
Creates a new conversation. Requires JSON body with `title` field.

## Running Tests

```bash
pytest tests/
```

## File Structure
- `app.py` - Flask application with API endpoints
- `static/sidebar.css` - Styles for the sidebar
- `static/sidebar.js` - Client-side logic
- `templates/sidebar.html` - HTML template for the sidebar
- `tests/test_sidebar.py` - Unit tests for the API
- `README.md` - This file
