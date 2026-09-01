import datetime
from typing import List, Dict, Optional

class ChatMessage:
    """Represents a single chat message."""
    def __init__(self, role: str, content: str, timestamp: Optional[datetime.datetime] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

class ChatManager:
    """Manages chat conversations, storing messages and providing context."""
    def __init__(self, max_history: int = 100):
        self.messages: List[ChatMessage] = []
        self.max_history = max_history

    def send_message(self, role: str, content: str) -> ChatMessage:
        """Add a new message to the chat history.

        Args:
            role: The role of the sender (e.g., 'user', 'assistant').
            content: The text content of the message.

        Returns:
            The created ChatMessage instance.

        Raises:
            ValueError: If role or content is empty.
        """
        if not role or not role.strip():
            raise ValueError("Role must be a non-empty string.")
        if not content or not content.strip():
            raise ValueError("Content must be a non-empty string.")
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        # Enforce max history by removing oldest messages if necessary
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        return message

    def get_history(self) -> List[Dict]:
        """Retrieve the entire chat history as a list of dictionaries.

        Returns:
            A list of message dictionaries with keys 'role', 'content', and 'timestamp'.
        """
        return [msg.to_dict() for msg in self.messages]

    def get_context(self, limit: Optional[int] = None) -> List[Dict]:
        """Retrieve the most recent messages for context.

        Args:
            limit: Maximum number of recent messages to return. If None, returns all.

        Returns:
            A list of message dictionaries.
        """
        if limit is None:
            return self.get_history()
        return [msg.to_dict() for msg in self.messages[-limit:]]

    def clear_history(self) -> None:
        """Clear all messages from the chat history."""
        self.messages.clear()
