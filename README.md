# Conversation Sidebar

Persistent conversation history management for multi-turn AI interactions.

## Usage

```python
from conversation_manager import ConversationManager

manager = ConversationManager("conversations.json")

manager.add_message("session-1", "user", "What is AI?")
manager.add_message("session-1", "assistant", "Artificial Intelligence...")

history = manager.get_conversation("session-1")
print(history)

# List all conversations
print(manager.list_conversations())

# Delete a conversation
manager.delete_conversation("session-1")
```

## API

### `add_message(conversation_id, role, content)`
Adds a message to a conversation. Creates a new conversation if the ID doesn't exist.

### `get_conversation(conversation_id)`
Returns a list of message dicts (`{"role": ..., "content": ...}`). Returns empty list if not found.

### `list_conversations()`
Returns a list of all conversation IDs.

### `delete_conversation(conversation_id)`
Deletes a conversation. Returns `True` if deleted, `False` if not found.

## Persistence

All conversations are stored in a JSON file specified at initialization (default: `conversations.json`).

## Testing

```bash
pytest tests/test_conversation_manager.py -v
```
