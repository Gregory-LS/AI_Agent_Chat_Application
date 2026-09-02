import json
import os
import tempfile
import unittest
from unittest.mock import patch

from server import (
    load_conversation,
    save_conversation,
    delete_conversation,
    list_conversations,
    CONVERSATIONS_DIR
)


class TestConversationPersistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch("server.CONVERSATIONS_DIR", self.temp_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_save_and_load_conversation(self):
        conv = {
            "id": "test123",
            "title": "Test",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "model": "gpt-3.5-turbo",
            "system_prompt": ""
        }
        save_conversation(conv)
        loaded = load_conversation("test123")
        self.assertEqual(loaded, conv)

    def test_load_nonexistent_conversation(self):
        loaded = load_conversation("nonexistent")
        self.assertIsNone(loaded)

    def test_delete_conversation(self):
        conv = {
            "id": "todelete",
            "title": "Delete me",
            "messages": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "model": "",
            "system_prompt": ""
        }
        save_conversation(conv)
        self.assertTrue(delete_conversation("todelete"))
        self.assertIsNone(load_conversation("todelete"))

    def test_delete_nonexistent_conversation(self):
        self.assertFalse(delete_conversation("nonexistent"))

    def test_list_conversations(self):
        conv1 = {
            "id": "first",
            "title": "First",
            "messages": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
            "model": "",
            "system_prompt": ""
        }
        conv2 = {
            "id": "second",
            "title": "Second",
            "messages": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-03T00:00:00",
            "model": "",
            "system_prompt": ""
        }
        save_conversation(conv1)
        save_conversation(conv2)
        convs = list_conversations()
        self.assertEqual(len(convs), 2)
        self.assertEqual(convs[0]["id"], "second")  # Most recent first
        self.assertEqual(convs[1]["id"], "first")

    def test_list_conversations_empty(self):
        convs = list_conversations()
        self.assertEqual(convs, [])


if __name__ == "__main__":
    unittest.main()
