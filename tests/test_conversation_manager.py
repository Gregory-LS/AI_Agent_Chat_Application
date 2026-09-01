import pytest
import json
import tempfile
import os
from conversation_manager import ConversationManager

@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = f.name
        json.dump({}, f)
    yield path
    os.unlink(path)

@pytest.fixture
def manager(temp_storage):
    return ConversationManager(temp_storage)

def test_add_and_get_message(manager):
    manager.add_message("conv1", "user", "Hello")
    history = manager.get_conversation("conv1")
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"

def test_add_multiple_messages(manager):
    manager.add_message("conv1", "user", "Hi")
    manager.add_message("conv1", "assistant", "Hello!")
    history = manager.get_conversation("conv1")
    assert len(history) == 2

def test_get_nonexistent_conversation(manager):
    history = manager.get_conversation("nonexistent")
    assert history == []

def test_list_conversations(manager):
    manager.add_message("a", "user", "1")
    manager.add_message("b", "user", "2")
    conversations = manager.list_conversations()
    assert "a" in conversations
    assert "b" in conversations
    assert len(conversations) == 2

def test_delete_conversation(manager):
    manager.add_message("conv1", "user", "test")
    assert manager.delete_conversation("conv1") is True
    assert manager.get_conversation("conv1") == []
    assert "conv1" not in manager.list_conversations()

def test_delete_nonexistent(manager):
    assert manager.delete_conversation("ghost") is False

def test_persistence(temp_storage):
    mgr1 = ConversationManager(temp_storage)
    mgr1.add_message("persist", "user", "stored")
    del mgr1
    mgr2 = ConversationManager(temp_storage)
    history = mgr2.get_conversation("persist")
    assert len(history) == 1
    assert history[0]["content"] == "stored"

def test_auto_creates_conversation(manager):
    manager.add_message("new_conv", "system", "init")
    assert "new_conv" in manager.list_conversations()
