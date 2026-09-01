# Conversation Sidebar with Persistence

This module provides a conversation sidebar that persists conversations to a local JSON file.

## Features

- Add, remove, and select conversations
- Persist conversations and active selection to disk
- Load conversations on startup
- Handle corrupted persistence file gracefully

## Usage

```python
from conversation_sidebar import Conversation, ConversationSidebar

sidebar = ConversationSidebar()
conv = Conversation("1", "My Chat")
sidebar.add_conversation(conv)
sidebar.select_conversation("1")
active = sidebar.get_active_conversation()
print(active.title)  # "My Chat"
```

## Tests

Run tests with pytest:

```bash
pytest tests/test_conversation_sidebar.py
```

## Files

- `conversation_sidebar.py` - Main module
- `tests/test_conversation_sidebar.py` - Unit tests
- `README.md` - This file
