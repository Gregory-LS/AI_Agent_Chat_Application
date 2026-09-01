import pytest
import json
import os
from conversation_sidebar import Conversation, ConversationSidebar

PERSISTENCE_FILE = "test_conversations.json"

@pytest.fixture
def sidebar():
    # Ensure clean state
    if os.path.exists(PERSISTENCE_FILE):
        os.remove(PERSISTENCE_FILE)
    sb = ConversationSidebar(persistence_file=PERSISTENCE_FILE)
    yield sb
    # Cleanup
    if os.path.exists(PERSISTENCE_FILE):
        os.remove(PERSISTENCE_FILE)

class TestConversation:
    def test_to_dict_from_dict(self):
        conv = Conversation("1", "Test", [{"role": "user", "content": "hello"}])
        data = conv.to_dict()
        restored = Conversation.from_dict(data)
        assert restored.conversation_id == "1"
        assert restored.title == "Test"
        assert restored.messages == [{"role": "user", "content": "hello"}]

    def test_default_messages(self):
        conv = Conversation("2", "Empty")
        assert conv.messages == []

class TestConversationSidebar:
    def test_initial_state(self, sidebar):
        assert sidebar.conversations == []
        assert sidebar.active_conversation_id is None

    def test_add_conversation(self, sidebar):
        conv = Conversation("1", "Chat 1")
        sidebar.add_conversation(conv)
        assert len(sidebar.conversations) == 1
        assert sidebar.conversations[0].title == "Chat 1"

    def test_add_conversation_persists(self, sidebar):
        conv = Conversation("1", "Chat 1")
        sidebar.add_conversation(conv)
        # Create new sidebar instance to load from file
        sidebar2 = ConversationSidebar(persistence_file=PERSISTENCE_FILE)
        assert len(sidebar2.conversations) == 1
        assert sidebar2.conversations[0].title == "Chat 1"

    def test_remove_conversation(self, sidebar):
        conv = Conversation("1", "Chat 1")
        sidebar.add_conversation(conv)
        assert sidebar.remove_conversation("1") == True
        assert len(sidebar.conversations) == 0

    def test_remove_nonexistent(self, sidebar):
        assert sidebar.remove_conversation("nonexistent") == False

    def test_select_conversation(self, sidebar):
        conv = Conversation("1", "Chat 1")
        sidebar.add_conversation(conv)
        assert sidebar.select_conversation("1") == True
        assert sidebar.active_conversation_id == "1"

    def test_select_nonexistent(self, sidebar):
        assert sidebar.select_conversation("nonexistent") == False
        assert sidebar.active_conversation_id is None

    def test_get_active_conversation(self, sidebar):
        conv = Conversation("1", "Chat 1", [{"role": "user", "content": "hi"}])
        sidebar.add_conversation(conv)
        sidebar.select_conversation("1")
        active = sidebar.get_active_conversation()
        assert active is not None
        assert active.conversation_id == "1"
        assert active.messages == [{"role": "user", "content": "hi"}]

    def test_get_active_conversation_none(self, sidebar):
        assert sidebar.get_active_conversation() is None

    def test_list_titles(self, sidebar):
        sidebar.add_conversation(Conversation("1", "First"))
        sidebar.add_conversation(Conversation("2", "Second"))
        assert sidebar.list_titles() == ["First", "Second"]

    def test_persistence_preserves_active(self, sidebar):
        conv = Conversation("1", "Chat 1")
        sidebar.add_conversation(conv)
        sidebar.select_conversation("1")
        sidebar2 = ConversationSidebar(persistence_file=PERSISTENCE_FILE)
        assert sidebar2.active_conversation_id == "1"
        assert sidebar2.get_active_conversation().title == "Chat 1"

    def test_corrupted_file(self, sidebar):
        # Write invalid JSON
        with open(PERSISTENCE_FILE, "w") as f:
            f.write("invalid json")
        sb = ConversationSidebar(persistence_file=PERSISTENCE_FILE)
        assert sb.conversations == []
        assert sb.active_conversation_id is None

    def test_remove_active_conversation(self, sidebar):
        conv = Conversation("1", "Chat 1")
        sidebar.add_conversation(conv)
        sidebar.select_conversation("1")
        sidebar.remove_conversation("1")
        assert sidebar.active_conversation_id is None
        assert sidebar.get_active_conversation() is None
