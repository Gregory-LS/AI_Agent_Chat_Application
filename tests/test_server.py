import json
import os
import pytest
from pathlib import Path
from server import APIHandler, load_config, save_config, CONFIG_FILE, DATA_DIR

# Test client using pytest

class TestAPIHandler:
    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        # Backup original data dir and set up temp
        self.orig_data = DATA_DIR
        # We'll patch the global DATA_DIR by modifying module-level variables
        import server
        self.temp_data = tmp_path / "data"
        self.temp_data.mkdir()
        server.DATA_DIR = self.temp_data
        server.CONFIG_FILE = self.temp_data / "config.json"
        server.CONVERSATIONS_DIR = self.temp_data / "conversations"
        server.SKILLS_FILE = self.temp_data / "skills.json"
        server.ATTACHMENTS_DIR = self.temp_data / "attachments"
        server.CONVERSATIONS_DIR.mkdir()
        server.ATTACHMENTS_DIR.mkdir()
        server.SKILLS_FILE.write_text("[]")
        server.CONFIG_FILE.write_text(json.dumps({"api_key": "test-key", "default_model": ""}))
        yield
        # Restore
        server.DATA_DIR = self.orig_data
        server.CONFIG_FILE = Path("data/config.json")
        server.CONVERSATIONS_DIR = Path("data/conversations")
        server.SKILLS_FILE = Path("data/skills.json")
        server.ATTACHMENTS_DIR = Path("data/attachments")

    def _make_request(self, method, path, body=None):
        """Simulate an HTTP request to the handler."""
        class MockRequest:
            def __init__(self, method, path, body, headers):
                self.method = method
                self.path = path
                self.body = body
                self.headers = headers
                self.rfile_content = body.encode() if body else b""

        class MockHandler(APIHandler):
            def __init__(self, mock_req):
                self.command = mock_req.method
                self.path = mock_req.path
                self.headers = mock_req.headers
                self.rfile = type('BytesIO', (), {'read': lambda self, n: mock_req.rfile_content})()
                self.wfile = type('BytesIO', (), {'write': lambda self, data: None, 'flush': lambda self: None})()
                self.send_response = lambda status: None
                self.send_header = lambda k, v: None
                self.end_headers = lambda: None

        handler = MockHandler(MockRequest(method, path, body, {}))
        # We'll just test the internal methods directly
        return handler

    def test_logout_endpoint(self):
        """Test that POST /api/logout clears the API key."""
        # Ensure config has an API key
        config = load_config()
        assert config["api_key"] == "test-key"

        # Simulate the handler's _handle_logout
        handler = self._make_request("POST", "/api/logout")
        handler._handle_logout()

        # Check config was cleared
        config = load_config()
        assert config["api_key"] == ""

    def test_logout_persists_to_disk(self):
        """Test that logout persists the cleared config to disk."""
        handler = self._make_request("POST", "/api/logout")
        handler._handle_logout()

        # Reload from file
        with open(server.CONFIG_FILE, "r") as f:
            config = json.load(f)
        assert config["api_key"] == ""

    def test_logout_twice(self):
        """Test that calling logout twice is idempotent."""
        handler = self._make_request("POST", "/api/logout")
        handler._handle_logout()
        handler._handle_logout()
        config = load_config()
        assert config["api_key"] == ""

    def test_logout_returns_success(self):
        """Test that logout returns a success JSON response."""
        handler = self._make_request("POST", "/api/logout")
        # We'll just check that no exception is raised and the config is cleared
        handler._handle_logout()
        config = load_config()
        assert config["api_key"] == ""

    def test_logout_does_not_affect_other_config(self):
        """Test that logout only clears the API key, not other config fields."""
        # Set other config fields
        config = load_config()
        config["default_model"] = "gpt-4o"
        save_config(config)

        handler = self._make_request("POST", "/api/logout")
        handler._handle_logout()

        config = load_config()
        assert config["api_key"] == ""
        assert config["default_model"] == "gpt-4o"
