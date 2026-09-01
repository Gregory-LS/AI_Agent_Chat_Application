import pytest
from chat_core import ChatManager, ChatMessage

class TestChatManager:
    def setup_method(self):
        self.manager = ChatManager(max_history=5)

    def test_send_message_creates_message(self):
        msg = self.manager.send_message("user", "Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_send_message_adds_to_history(self):
        self.manager.send_message("user", "Hi")
        history = self.manager.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hi"

    def test_get_history_with_multiple_messages(self):
        self.manager.send_message("user", "First")
        self.manager.send_message("assistant", "Second")
        history = self.manager.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_max_history_enforced(self):
        for i in range(10):
            self.manager.send_message("user", f"Message {i}")
        history = self.manager.get_history()
        assert len(history) == 5
        assert history[0]["content"] == "Message 5"
        assert history[-1]["content"] == "Message 9"

    def test_get_context_with_limit(self):
        for i in range(5):
            self.manager.send_message("user", str(i))
        context = self.manager.get_context(limit=3)
        assert len(context) == 3
        assert context[0]["content"] == "2"
        assert context[-1]["content"] == "4"

    def test_get_context_no_limit(self):
        self.manager.send_message("user", "A")
        self.manager.send_message("user", "B")
        context = self.manager.get_context()
        assert len(context) == 2

    def test_clear_history(self):
        self.manager.send_message("user", "Test")
        self.manager.clear_history()
        assert self.manager.get_history() == []

    def test_send_message_empty_role_raises(self):
        with pytest.raises(ValueError):
            self.manager.send_message("", "Hello")

    def test_send_message_empty_content_raises(self):
        with pytest.raises(ValueError):
            self.manager.send_message("user", "")

    def test_send_message_whitespace_role_raises(self):
        with pytest.raises(ValueError):
            self.manager.send_message("   ", "Hello")

    def test_send_message_whitespace_content_raises(self):
        with pytest.raises(ValueError):
            self.manager.send_message("user", "   ")

class TestChatMessage:
    def test_to_dict(self):
        import datetime
        ts = datetime.datetime(2023, 1, 1, 12, 0, 0)
        msg = ChatMessage("user", "Hello", timestamp=ts)
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"
        assert d["timestamp"] == "2023-01-01T12:00:00"

    def test_default_timestamp(self):
        msg = ChatMessage("user", "Hi")
        assert msg.timestamp is not None
