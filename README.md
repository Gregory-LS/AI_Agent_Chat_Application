# Chat Core System

A minimal chat core library providing message management and conversation history.

## Features

- Send messages with roles (user, assistant, etc.)
- Retrieve full or limited chat history
- Configurable maximum history size
- Clear conversation history

## Installation

Clone the repository and install dependencies (if any):

```bash
pip install -r requirements.txt  # if required
```

## Usage

```python
from chat_core import ChatManager

manager = ChatManager(max_history=100)

# Send messages
manager.send_message("user", "Hello!")
manager.send_message("assistant", "How can I help you?")

# Get full history
history = manager.get_history()
# [{'role': 'user', 'content': 'Hello!', 'timestamp': ...}, ...]

# Get recent context
context = manager.get_context(limit=5)

# Clear history
manager.clear_history()
```

## Running Tests

```bash
pytest tests/
```
