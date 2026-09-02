import json
import os
import tempfile
import unittest
from pathlib import Path
from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Ensure we use the test server module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import ChatHandler, DATA_DIR, CONFIG_FILE, CONVERSATIONS_DIR, SKILLS_FILE, ATTACHMENTS_DIR


class TestLogoutEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a temporary directory for data
        cls.temp_dir = tempfile.mkdtemp()
        cls.orig_data_dir = DATA_DIR
        # Monkey-patch paths
        import server
        server.DATA_DIR = Path(cls.temp_dir)
        server.CONFIG_FILE = server.DATA_DIR / "config.json"
        server.CONVERSATIONS_DIR = server.DATA_DIR / "conversations"
        server.SKILLS_FILE = server.DATA_DIR / "skills.json"
        server.ATTACHMENTS_DIR = server.DATA_DIR / "attachments"
        server.CONVERSATIONS_DIR.mkdir(exist_ok=True)
        server.ATTACHMENTS_DIR.mkdir(exist_ok=True)
        if not server.SKILLS_FILE.exists():
            server.SKILLS_FILE.write_text("[]")
        if not server.CONFIG_FILE.exists():
            server.CONFIG_FILE.write_text("{}")

        # Start a test server
        cls.server = HTTPServer(('localhost', 0), ChatHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        import server
        server.DATA_DIR = cls.orig_data_dir

    def setUp(self):
        # Ensure config exists with an API key
        server.save_config({"api_key": "sk-or-test-key-12345"})

    def test_logout_clears_api_key(self):
        # Verify key exists before
        config = server.load_config()
        self.assertIn("api_key", config)
        self.assertEqual(config["api_key"], "sk-or-test-key-12345")

        # Call logout
        req = Request(f"http://localhost:{self.port}/api/logout", method='POST')
        resp = urlopen(req)
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read().decode())
        self.assertEqual(data["status"], "ok")

        # Verify key is gone
        config = server.load_config()
        self.assertNotIn("api_key", config)

    def test_logout_with_no_key(self):
        # Remove key first
        server.save_config({})
        req = Request(f"http://localhost:{self.port}/api/logout", method='POST')
        resp = urlopen(req)
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read().decode())
        self.assertEqual(data["status"], "ok")

    def test_logout_requires_post(self):
        # GET should fail
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"http://localhost:{self.port}/api/logout")
        self.assertEqual(ctx.exception.code, 405)  # Method Not Allowed


if __name__ == '__main__':
    unittest.main()
