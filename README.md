# Chat Core Module

A simple in-memory chat system.

## Features

- Send messages with username and content.
- Retrieve messages with optional pagination (limit and offset).
- Clear all messages.
- Message count property.

## Usage

```python
from chat.core import Chat

chat = Chat()
chat.send_message("Alice", "Hello!")
chat.send_message("Bob", "Hi there!")

# Get all messages
messages = chat.get_messages()
print(messages)

# Get last two messages
recent = chat.get_messages(limit=2, offset=0)

# Clear chat
chat.clear()
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Requirements

- Python 3.8+
- No external dependencies.
