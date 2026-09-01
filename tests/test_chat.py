import pytest
from chat.core import Chat


class TestChat:
    def test_send_message_creates_message(self):
        chat = Chat()
        msg = chat.send_message("Alice", "Hello!")
        assert msg["user"] == "Alice"
        assert msg["content"] == "Hello!"
        assert "timestamp" in msg
        assert chat.message_count == 1

    def test_send_message_strips_whitespace(self):
        chat = Chat()
        msg = chat.send_message("  Bob  ", "  Hi  ")
        assert msg["user"] == "Bob"
        assert msg["content"] == "Hi"

    def test_send_message_empty_user_raises(self):
        chat = Chat()
        with pytest.raises(ValueError, match="User must be a non-empty string"):
            chat.send_message("", "Hello")

    def test_send_message_whitespace_user_raises(self):
        chat = Chat()
        with pytest.raises(ValueError):
            chat.send_message("   ", "Hello")

    def test_send_message_empty_content_raises(self):
        chat = Chat()
        with pytest.raises(ValueError, match="Content must be a non-empty string"):
            chat.send_message("Alice", "")

    def test_send_message_non_string_user_raises(self):
        chat = Chat()
        with pytest.raises(ValueError):
            chat.send_message(123, "Hello")

    def test_send_message_non_string_content_raises(self):
        chat = Chat()
        with pytest.raises(ValueError):
            chat.send_message("Alice", 456)

    def test_get_messages_empty(self):
        chat = Chat()
        assert chat.get_messages() == []

    def test_get_messages_all(self):
        chat = Chat()
        chat.send_message("A", "m1")
        chat.send_message("B", "m2")
        msgs = chat.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["content"] == "m1"
        assert msgs[1]["content"] == "m2"

    def test_get_messages_with_limit(self):
        chat = Chat()
        chat.send_message("A", "m1")
        chat.send_message("B", "m2")
        chat.send_message("C", "m3")
        msgs = chat.get_messages(limit=2)
        assert len(msgs) == 2
        assert msgs[0]["content"] == "m1"
        assert msgs[1]["content"] == "m2"

    def test_get_messages_with_offset(self):
        chat = Chat()
        chat.send_message("A", "m1")
        chat.send_message("B", "m2")
        chat.send_message("C", "m3")
        msgs = chat.get_messages(offset=1)
        assert len(msgs) == 2
        assert msgs[0]["content"] == "m2"
        assert msgs[1]["content"] == "m3"

    def test_get_messages_with_limit_and_offset(self):
        chat = Chat()
        for i in range(5):
            chat.send_message("U", f"msg{i}")
        msgs = chat.get_messages(limit=2, offset=2)
        assert len(msgs) == 2
        assert msgs[0]["content"] == "msg2"
        assert msgs[1]["content"] == "msg3"

    def test_get_messages_limit_zero_raises(self):
        chat = Chat()
        with pytest.raises(ValueError, match="Limit must be positive or None"):
            chat.get_messages(limit=0)

    def test_get_messages_limit_negative_raises(self):
        chat = Chat()
        with pytest.raises(ValueError):
            chat.get_messages(limit=-1)

    def test_get_messages_offset_negative_raises(self):
        chat = Chat()
        with pytest.raises(ValueError, match="Offset must be non-negative"):
            chat.get_messages(offset=-1)

    def test_clear_removes_all_messages(self):
        chat = Chat()
        chat.send_message("A", "m1")
        chat.send_message("B", "m2")
        chat.clear()
        assert chat.message_count == 0
        assert chat.get_messages() == []

    def test_message_count(self):
        chat = Chat()
        assert chat.message_count == 0
        chat.send_message("A", "m1")
        assert chat.message_count == 1
        chat.send_message("B", "m2")
        assert chat.message_count == 2
