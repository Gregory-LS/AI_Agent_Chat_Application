import uuid
from datetime import datetime
from typing import List, Optional


class Message:
    """Represents a single chat message."""
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.id = str(uuid.uuid4())
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()

    def __repr__(self):
        return f"<Message {self.role}: {self.content[:30]}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class ChatHistory:
    """Manages the list of messages in a chat session."""
    def __init__(self):
        self.messages: List[Message] = []

    def add_message(self, role: str, content: str) -> Message:
        """Add a message to the history."""
        if not role:
            raise ValueError("Role must not be empty")
        if not content:
            raise ValueError("Content must not be empty")
        message = Message(role, content)
        self.messages.append(message)
        return message

    def get_messages(self, since: Optional[datetime] = None) -> List[Message]:
        """Get messages, optionally filtered by timestamp."""
        if since is None:
            return self.messages[:]
        return [m for m in self.messages if m.timestamp >= since]

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def last_message(self) -> Optional[Message]:
        """Get the last message, or None if empty."""
        if not self.messages:
            return None
        return self.messages[-1]


class ChatService:
    """Core chat service that manages a conversation."""
    def __init__(self, history: Optional[ChatHistory] = None):
        self.history = history or ChatHistory()

    def send_message(self, content: str) -> Message:
        """Send a user message and get an automatic 'echo' response."""
        if not content:
            raise ValueError("Message content cannot be empty")
        user_msg = self.history.add_message("user", content)
        # For now, respond with a simple echo message
        response_content = f"Echo: {content}"
        bot_msg = self.history.add_message("assistant", response_content)
        return user_msg

    def get_conversation_history(self) -> List[dict]:
        """Return the conversation history as a list of dicts."""
        return [msg.to_dict() for msg in self.history.get_messages()]

    def reset_conversation(self) -> None:
        """Reset the conversation by clearing history."""
        self.history.clear()
