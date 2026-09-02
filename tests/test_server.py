import json
import os
import sys
import tempfile
import unittest
from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Add parent directory to path to import server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import server


class TestLogoutEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a temporary directory for data
        cls.temp_dir = tempfile.TemporaryDirectory()
        server.DATA_DIR = cls.temp_dir.name
        server.CONFIG_FILE = os.path.join(cls.temp_dir.name, "config.json")
        server.CONVERSATIONS_DIR = os.path.join(cls.temp_dir.name, "conversations")
        server.SKILLS_FILE = os.path.join(cls.temp_dir.name, "skills.json")
        server.ATTACHMENTS_DIR = os.path.join(cls.temp_dir.name, "attachments")
        os.makedirs(server.CONVERSATIONS_DIR, exist_ok=True)
        os.makedirs(server.ATTACHMENTS_DIR, exist_ok=True)

        # Start server on a random port
        cls.server = HTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.temp_dir.cleanup()

    def setUp(self):
        # Ensure config exists with a key
        server.save_config({"api_key": "test-key-123", "default_model": "gpt-4"})

    def test_logout_clears_api_key(self):
        # Verify key is set
        config = server.load_config()
        self.assertEqual(config["api_key"], "test-key-123")

        # Send POST to /api/logout
        req = Request(
            f"http://127.0.0.1:{self.port}/api/logout",
            method="POST",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        resp = urlopen(req)
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read())
        self.assertEqual(data["status"], "ok")

        # Verify key is cleared
        config = server.load_config()
        self.assertEqual(config["api_key"], "")

    def test_logout_preserves_other_config(self):
        # Ensure default_model is not affected
        server.save_config({"api_key": "test-key", "default_model": "claude-3"})
        req = Request(
            f"http://127.0.0.1:{self.port}/api/logout",
            method="POST",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        urlopen(req)
        config = server.load_config()
        self.assertEqual(config["default_model"], "claude-3")
        self.assertEqual(config["api_key"], "")

    def test_logout_when_no_key(self):
        # Start with empty key
        server.save_config({"api_key": "", "default_model": ""})
        req = Request(
            f"http://127.0.0.1:{self.port}/api/logout",
            method="POST",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        resp = urlopen(req)
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read())
        self.assertEqual(data["status"], "ok")
        config = server.load_config()
        self.assertEqual(config["api_key"], "")


if __name__ == "__main__":
    unittest.main()
