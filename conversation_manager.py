import json
import os
from typing import List, Dict, Any

class ConversationManager:
    """Manages conversation history with persistence to a JSON file."""

    def __init__(self, storage_path: str = "conversations.json"):
        self.storage_path = storage_path
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        """Load conversations from the storage file if it exists."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                self.conversations = json.load(f)

    def _save(self) -> None:
        """Save conversations to the storage file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.conversations, f, indent=2)

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation. Creates conversation if not exists."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append({"role": role, "content": content})
        self._save()

    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a given conversation ID."""
        return self.conversations.get(conversation_id, [])

    def list_conversations(self) -> List[str]:
        """Return a list of all conversation IDs."""
        return list(self.conversations.keys())

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID. Returns True if deleted, False if not found."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self._save()
            return True
        return False
