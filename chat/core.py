import datetime
from typing import List, Optional, Dict, Any


class Chat:
    """Simple in-memory chat system."""

    def __init__(self) -> None:
        self._messages: List[Dict[str, Any]] = []

    def send_message(self, user: str, content: str) -> Dict[str, Any]:
        """
        Send a message from a user.

        Args:
            user: Username (must be non-empty string).
            content: Message content (must be non-empty string).

        Returns:
            The created message dict with keys: user, content, timestamp.

        Raises:
            ValueError: If user or content is empty or not a string.
        """
        if not isinstance(user, str) or not user.strip():
            raise ValueError("User must be a non-empty string")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content must be a non-empty string")

        message = {
            "user": user.strip(),
            "content": content.strip(),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        self._messages.append(message)
        return message

    def get_messages(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve messages with optional pagination.

        Args:
            limit: Maximum number of messages to return (None = all).
            offset: Number of messages to skip from the start (default 0).

        Returns:
            List of message dicts in chronological order.

        Raises:
            ValueError: If limit <= 0 or offset < 0.
        """
        if limit is not None and limit <= 0:
            raise ValueError("Limit must be positive or None")
        if offset < 0:
            raise ValueError("Offset must be non-negative")

        start = offset
        end = None if limit is None else offset + limit
        return self._messages[start:end]

    def clear(self) -> None:
        """Remove all messages from the chat."""
        self._messages.clear()

    @property
    def message_count(self) -> int:
        """Return the number of messages stored."""
        return len(self._messages)
