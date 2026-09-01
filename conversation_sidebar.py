import json
import os
from typing import List, Optional

PERSISTENCE_FILE = "conversations.json"

class Conversation:
    def __init__(self, conversation_id: str, title: str, messages: List[dict] = None):
        self.conversation_id = conversation_id
        self.title = title
        self.messages = messages if messages is not None else []

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "messages": self.messages
        }

    @staticmethod
    def from_dict(data: dict) -> "Conversation":
        return Conversation(
            conversation_id=data["conversation_id"],
            title=data["title"],
            messages=data.get("messages", [])
        )

class ConversationSidebar:
    def __init__(self, persistence_file: str = PERSISTENCE_FILE):
        self.conversations: List[Conversation] = []
        self.active_conversation_id: Optional[str] = None
        self.persistence_file = persistence_file
        self._load()

    def add_conversation(self, conversation: Conversation) -> None:
        self.conversations.append(conversation)
        self._save()

    def remove_conversation(self, conversation_id: str) -> bool:
        for conv in self.conversations:
            if conv.conversation_id == conversation_id:
                self.conversations.remove(conv)
                if self.active_conversation_id == conversation_id:
                    self.active_conversation_id = None
                self._save()
                return True
        return False

    def select_conversation(self, conversation_id: str) -> bool:
        for conv in self.conversations:
            if conv.conversation_id == conversation_id:
                self.active_conversation_id = conversation_id
                self._save()
                return True
        return False

    def get_active_conversation(self) -> Optional[Conversation]:
        for conv in self.conversations:
            if conv.conversation_id == self.active_conversation_id:
                return conv
        return None

    def list_titles(self) -> List[str]:
        return [conv.title for conv in self.conversations]

    def _save(self) -> None:
        data = {
            "active_conversation_id": self.active_conversation_id,
            "conversations": [conv.to_dict() for conv in self.conversations]
        }
        with open(self.persistence_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        if not os.path.exists(self.persistence_file):
            return
        try:
            with open(self.persistence_file, "r") as f:
                data = json.load(f)
            self.active_conversation_id = data.get("active_conversation_id")
            self.conversations = [Conversation.from_dict(conv) for conv in data.get("conversations", [])]
        except (json.JSONDecodeError, KeyError):
            # If file is corrupted, start fresh
            self.conversations = []
            self.active_conversation_id = None
