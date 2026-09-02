import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Patch data directory before importing server
TEST_DIR = Path(tempfile.mkdtemp())
os.environ['OPENROUTER_API_KEY'] = 'test-key'

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# We'll test the server logic indirectly via unit tests on the handler methods
from server import ChatHandler, load_config, save_config, load_conversations, save_conversation, get_conversation, delete_conversation, DATA_DIR, CONFIG_FILE, CONVERSATIONS_DIR

class TestServerFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override data dir to temp
        global DATA_DIR, CONFIG_FILE, CONVERSATIONS_DIR
        # We'll just test the functions with the actual data dir but we can mock
        pass

    def setUp(self):
        # Ensure clean state
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        CONFIG_FILE.write_text(json.dumps({"api_key": "", "default_model": ""}))
        for f in CONVERSATIONS_DIR.glob("*.json"):
            f.unlink()

    def test_load_config_default(self):
        config = load_config()
        self.assertEqual(config["api_key"], "")
        self.assertEqual(config["default_model"], "")

    def test_save_and_load_config(self):
        save_config({"api_key": "sk-test", "default_model": "gpt-4"})
        config = load_config()
        self.assertEqual(config["api_key"], "sk-test")
        self.assertEqual(config["default_model"], "gpt-4")

    def test_save_and_get_conversation(self):
        conv_id = "test-123"
        data = {"title": "Test", "messages": []}
        save_conversation(conv_id, data)
        conv = get_conversation(conv_id)
        self.assertIsNotNone(conv)
        self.assertEqual(conv["title"], "Test")

    def test_delete_conversation(self):
        conv_id = "test-456"
        save_conversation(conv_id, {"title": "Delete me"})
        delete_conversation(conv_id)
        self.assertIsNone(get_conversation(conv_id))

    def test_load_conversations_empty(self):
        convs = load_conversations()
        self.assertEqual(convs, [])

    def test_load_conversations_multiple(self):
        save_conversation("a", {"title": "A", "updated_at": "2023-01-01"})
        save_conversation("b", {"title": "B", "updated_at": "2023-01-02"})
        convs = load_conversations()
        self.assertEqual(len(convs), 2)
        # Should be sorted by updated_at descending
        self.assertEqual(convs[0]["title"], "B")

class TestBalanceEndpoint(unittest.TestCase):
    def setUp(self):
        # Create a mock handler
        self.handler = ChatHandler.__new__(ChatHandler)
        self.handler.path = "/api/balance"
        self.handler.headers = {}
        self.handler.rfile = MagicMock()
        self.handler.wfile = MagicMock()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    @patch('server.openrouter.get_balance')
    def test_balance_success(self, mock_get_balance):
        mock_get_balance.return_value = {"credits": 100.0, "usage": 50.0, "total": 150.0}
        # Ensure API key is set
        with patch('server.get_api_key', return_value='test-key'):
            self.handler.do_GET()
            self.handler.send_json.assert_called_once_with({"credits": 100.0, "usage": 50.0, "total": 150.0})

    @patch('server.get_api_key', return_value='')
    def test_balance_no_api_key(self, mock_get_key):
        self.handler.do_GET()
        self.handler.send_error_json.assert_called_once_with("API key not configured", 401)

    @patch('server.openrouter.get_balance', side_effect=Exception("API error"))
    @patch('server.get_api_key', return_value='test-key')
    def test_balance_api_error(self, mock_get_key, mock_get_balance):
        self.handler.do_GET()
        self.handler.send_error_json.assert_called_once_with("API error", 502)

if __name__ == '__main__':
    unittest.main()
