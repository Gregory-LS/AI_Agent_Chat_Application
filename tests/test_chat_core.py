import pytest
from datetime import datetime, timedelta
from chat_core import Message, ChatHistory, ChatService


class TestMessage:
    def test_create_message(self):
        msg = Message("user", "Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.id is not None
        assert msg.timestamp is not None

    def test_message_to_dict(self):
        msg = Message("assistant", "Hi there")
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert d["content"] == "Hi there"
        assert "id" in d
        assert "timestamp" in d


class TestChatHistory:
    def test_add_message(self):
        history = ChatHistory()
        msg = history.add_message("user", "Hello")
        assert len(history.messages) == 1
        assert msg.role == "user"

    def test_add_empty_role_raises_error(self):
        history = ChatHistory()
        with pytest.raises(ValueError, match="Role must not be empty"):
            history.add_message("", "Hello")

    def test_add_empty_content_raises_error(self):
        history = ChatHistory()
        with pytest.raises(ValueError, match="Content must not be empty"):
            history.add_message("user", "")

    def test_get_messages(self):
        history = ChatHistory()
        history.add_message("user", "First")
        history.add_message("user", "Second")
        msgs = history.get_messages()
        assert len(msgs) == 2

    def test_get_messages_since_filter(self):
        history = ChatHistory()
        msg1 = history.add_message("user", "First")
        # simulate a timestamp a bit later
        later = datetime.utcnow() + timedelta(seconds=1)
        msg2 = history.add_message("user", "Second")
        # since after msg1 timestamp, only msg2 should be returned
        filtered = history.get_messages(since=later)
        assert len(filtered) == 1

    def test_clear(self):
        history = ChatHistory()
        history.add_message("user", "Hello")
        history.clear()
        assert len(history.messages) == 0

    def test_last_message(self):
        history = ChatHistory()
        assert history.last_message() is None
        history.add_message("user", "Hello")
        history.add_message("assistant", "Hi")
        last = history.last_message()
        assert last.role == "assistant"
        assert last.content == "Hi"


class TestChatService:
    def test_send_message(self):
        service = ChatService()
        msg = service.send_message("Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        # A bot response should also be added
        assert len(service.history.messages) == 2
        assert service.history.messages[1].role == "assistant"
        assert service.history.messages[1].content == "Echo: Hello"

    def test_send_empty_message_raises_error(self):
        service = ChatService()
        with pytest.raises(ValueError, match="Message content cannot be empty"):
            service.send_message("")

    def test_get_conversation_history(self):
        service = ChatService()
        service.send_message("Hello")
        history = service.get_conversation_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_reset_conversation(self):
        service = ChatService()
        service.send_message("Hello")
        service.reset_conversation()
        assert len(service.history.messages) == 0
        assert service.get_conversation_history() == []
