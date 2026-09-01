# Chat Application

This is a simple chat application core that provides:
- **Message**: A data class representing a single message.
- **ChatHistory**: Manages conversation history (add, get, clear, last message).
- **ChatService**: High-level service to send messages and retrieve history.

## Usage

```python
from chat_core import ChatService

service = ChatService()
service.send_message("Hello, world!")
history = service.get_conversation_history()
print(history)
```

## Tests

Run tests with:
```bash
pytest tests/test_chat_core.py -v
```

## Files
- `chat_core.py` - Core implementation
- `tests/test_chat_core.py` - Unit tests
