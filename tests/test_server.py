import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# We'll test server logic by importing the module and testing functions directly
import server

class TestServerFunctions(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.orig_data_dir = server.DATA_DIR
        self.orig_config_file = server.CONFIG_FILE
        self.orig_conversations_dir = server.CONVERSATIONS_DIR
        self.orig_skills_file = server.SKILLS_FILE
        self.orig_attachments_dir = server.ATTACHMENTS_DIR
        server.DATA_DIR = self.tempdir
        server.CONFIG_FILE = os.path.join(self.tempdir, "config.json")
        server.CONVERSATIONS_DIR = os.path.join(self.tempdir, "conversations")
        server.SKILLS_FILE = os.path.join(self.tempdir, "skills.json")
        server.ATTACHMENTS_DIR = os.path.join(self.tempdir, "attachments")
        os.makedirs(server.CONVERSATIONS_DIR, exist_ok=True)
        os.makedirs(server.ATTACHMENTS_DIR, exist_ok=True)
        with open(server.SKILLS_FILE, "w") as f:
            json.dump([], f)
        with open(server.CONFIG_FILE, "w") as f:
            json.dump({"api_key": "", "default_model": ""}, f)

    def tearDown(self):
        server.DATA_DIR = self.orig_data_dir
        server.CONFIG_FILE = self.orig_config_file
        server.CONVERSATIONS_DIR = self.orig_conversations_dir
        server.SKILLS_FILE = self.orig_skills_file
        server.ATTACHMENTS_DIR = self.orig_attachments_dir
        import shutil
        shutil.rmtree(self.tempdir)

    def test_get_config_default(self):
        cfg = server.get_config()
        self.assertEqual(cfg["api_key"], "")
        self.assertEqual(cfg["default_model"], "")

    def test_save_and_get_config(self):
        server.save_config({"api_key": "test-key", "default_model": "model-x"})
        cfg = server.get_config()
        self.assertEqual(cfg["api_key"], "test-key")
        self.assertEqual(cfg["default_model"], "model-x")

    def test_skills_empty(self):
        skills = server.get_skills()
        self.assertEqual(skills, [])

    def test_save_and_get_skills(self):
        skills = [{"id": "1", "name": "test"}]
        server.save_skills(skills)
        self.assertEqual(server.get_skills(), skills)

    def test_conversation_crud(self):
        cid = "test-id"
        conv = {"id": cid, "title": "Test", "messages": []}
        server.save_conversation(cid, conv)
        loaded = server.get_conversation(cid)
        self.assertEqual(loaded["title"], "Test")
        self.assertTrue(server.delete_conversation(cid))
        self.assertIsNone(server.get_conversation(cid))
        self.assertFalse(server.delete_conversation("nonexistent"))

    def test_list_conversations(self):
        server.save_conversation("a", {"id": "a", "title": "A", "created": "now", "updated": "now"})
        server.save_conversation("b", {"id": "b", "title": "B", "created": "now", "updated": "now"})
        convs = server.get_conversations()
        self.assertEqual(len(convs), 2)

    def test_get_headers_no_key(self):
        with patch.dict(os.environ, {}, clear=True):
            headers = server.get_headers()
            self.assertEqual(headers["Authorization"], "Bearer ")

    def test_get_headers_env_key(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=True):
            headers = server.get_headers()
            self.assertEqual(headers["Authorization"], "Bearer env-key")

    def test_get_headers_config_key(self):
        server.save_config({"api_key": "cfg-key", "default_model": ""})
        headers = server.get_headers()
        self.assertEqual(headers["Authorization"], "Bearer cfg-key")

if __name__ == "__main__":
    unittest.main()
