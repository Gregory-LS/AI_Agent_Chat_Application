import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# We'll test the handler methods directly by simulating requests
# Since server.py uses http.server, we test the logic by patching the handler

class TestServerLogout(unittest.TestCase):
    def setUp(self):
        # Create a temporary data directory
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch("server.DATA_DIR", self.test_dir)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(lambda: shutil.rmtree(self.test_dir, ignore_errors=True))

        # Re-import server with patched DATA_DIR
        import importlib
        import server
        importlib.reload(server)
        self.server = server

        # Create a minimal config
        config = {"api_key": "sk-or-test-key-12345678", "default_model": "gpt-4", "theme": "light"}
        with open(os.path.join(self.test_dir, "config.json"), "w") as f:
            json.dump(config, f)

        # Create a mock handler
        self.handler = server.ChatHandler
        self.mock_request = MagicMock()
        self.mock_request.makefile = MagicMock()
        self.mock_request.makefile.return_value = MagicMock()
        self.handler_instance = self.handler(self.mock_request, ("127.0.0.1", 12345), None)
        self.handler_instance.path = "/api/logout"
        self.handler_instance.headers = MagicMock()
        self.handler_instance.rfile = MagicMock()
        self.handler_instance.wfile = MagicMock()
        self.handler_instance.send_response = MagicMock()
        self.handler_instance.send_header = MagicMock()
        self.handler_instance.end_headers = MagicMock()

    def test_logout_clears_api_key(self):
        """Test that POST /api/logout clears the API key in config.json."""
        # Verify initial state
        config = self.server.load_config()
        self.assertEqual(config["api_key"], "sk-or-test-key-12345678")

        # Call logout
        self.handler_instance.handle_logout()

        # Verify config was updated
        config = self.server.load_config()
        self.assertEqual(config["api_key"], "")

        # Verify response
        self.handler_instance.send_response.assert_called_with(200)
        self.handler_instance.send_header.assert_called_with("Content-Type", "application/json")
        self.handler_instance.end_headers.assert_called_once()

        # Get the response body
        written = self.handler_instance.wfile.write.call_args[0][0]
        response = json.loads(written.decode())
        self.assertEqual(response["status"], "logged_out")
        self.assertIn("API key cleared", response["message"])

    def test_logout_with_no_api_key(self):
        """Test logout when no API key is set (should still succeed)."""
        # Set empty key
        config = self.server.load_config()
        config["api_key"] = ""
        self.server.save_config(config)

        # Call logout
        self.handler_instance.handle_logout()

        # Verify config is still empty
        config = self.server.load_config()
        self.assertEqual(config["api_key"], "")

        # Verify response
        written = self.handler_instance.wfile.write.call_args[0][0]
        response = json.loads(written.decode())
        self.assertEqual(response["status"], "logged_out")

    def test_logout_preserves_other_config(self):
        """Test that logout only clears API key, not other settings."""
        # Call logout
        self.handler_instance.handle_logout()

        # Verify other config fields are preserved
        config = self.server.load_config()
        self.assertEqual(config["default_model"], "gpt-4")
        self.assertEqual(config["theme"], "light")

if __name__ == "__main__":
    import shutil
    unittest.main()
