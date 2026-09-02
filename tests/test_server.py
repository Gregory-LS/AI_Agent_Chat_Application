import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


class TestServerHelpers(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for data
        self.temp_dir = tempfile.mkdtemp()
        self.orig_data_dir = server.DATA_DIR
        server.DATA_DIR = Path(self.temp_dir)
        server.CONFIG_FILE = server.DATA_DIR / "config.json"
        server.CONVERSATIONS_DIR = server.DATA_DIR / "conversations"
        server.SKILLS_FILE = server.DATA_DIR / "skills.json"
        server.ATTACHMENTS_DIR = server.DATA_DIR / "attachments"
        # Reinitialize directories
        for d in [server.DATA_DIR, server.CONVERSATIONS_DIR, server.ATTACHMENTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        if not server.CONFIG_FILE.exists():
            with open(server.CONFIG_FILE, "w") as f:
                json.dump(server.DEFAULT_CONFIG, f, indent=2)
        if not server.SKILLS_FILE.exists():
            with open(server.SKILLS_FILE, "w") as f:
                json.dump([], f, indent=2)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
        server.DATA_DIR = self.orig_data_dir

    def test_generate_id(self):
        id1 = server.generate_id()
        id2 = server.generate_id()
        self.assertNotEqual(id1, id2)
        self.assertIsInstance(id1, str)

    def test_load_save_json(self):
        path = server.DATA_DIR / "test.json"
        data = {"key": "value"}
        server.save_json(path, data)
        loaded = server.load_json(path)
        self.assertEqual(loaded, data)

    def test_get_config_default(self):
        cfg = server.get_config()
        self.assertIn("api_key", cfg)
        self.assertEqual(cfg["theme"], "dark")

    def test_save_config(self):
        cfg = {"api_key": "test-key", "default_model": "test-model", "theme": "light"}
        server.save_config(cfg)
        loaded = server.get_config()
        self.assertEqual(loaded["api_key"], "test-key")

    def test_get_api_key_from_config(self):
        server.save_config({"api_key": "cfg-key", "default_model": "", "theme": "dark"})
        key = server.get_api_key()
        self.assertEqual(key, "cfg-key")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"})
    def test_get_api_key_from_env(self):
        server.save_config({"api_key": "", "default_model": "", "theme": "dark"})
        key = server.get_api_key()
        self.assertEqual(key, "env-key")

    def test_skills_crud(self):
        # Initially empty
        self.assertEqual(server.get_skills(), [])
        # Add skill
        skills = [{"id": "1", "name": "Skill1", "prompt": "Prompt1", "enabled": True}]
        server.save_skills(skills)
        self.assertEqual(server.get_skills(), skills)

    def test_conversation_crud(self):
        id_ = "test-id"
        conv = {"id": id_, "title": "Test", "messages": [], "created_at": 0, "updated_at": 0}
        server.save_conversation(id_, conv)
        loaded = server.get_conversation(id_)
        self.assertEqual(loaded, conv)
        # Update
        conv["title"] = "Updated"
        server.save_conversation(id_, conv)
        loaded = server.get_conversation(id_)
        self.assertEqual(loaded["title"], "Updated")
        # Delete
        server.delete_conversation(id_)
        self.assertIsNone(server.get_conversation(id_))

    def test_list_conversations(self):
        conv1 = {"id": "1", "title": "A", "messages": [], "created_at": 1, "updated_at": 1}
        conv2 = {"id": "2", "title": "B", "messages": [], "created_at": 2, "updated_at": 2}
        server.save_conversation("1", conv1)
        server.save_conversation("2", conv2)
        convs = server.list_conversations()
        # Should be sorted by updated_at descending
        self.assertEqual(len(convs), 2)
        self.assertEqual(convs[0]["id"], "2")
        self.assertEqual(convs[1]["id"], "1")


class TestChatHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_data_dir = server.DATA_DIR
        server.DATA_DIR = Path(self.temp_dir)
        server.CONFIG_FILE = server.DATA_DIR / "config.json"
        server.CONVERSATIONS_DIR = server.DATA_DIR / "conversations"
        server.SKILLS_FILE = server.DATA_DIR / "skills.json"
        server.ATTACHMENTS_DIR = server.DATA_DIR / "attachments"
        for d in [server.DATA_DIR, server.CONVERSATIONS_DIR, server.ATTACHMENTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        if not server.CONFIG_FILE.exists():
            with open(server.CONFIG_FILE, "w") as f:
                json.dump(server.DEFAULT_CONFIG, f, indent=2)
        if not server.SKILLS_FILE.exists():
            with open(server.SKILLS_FILE, "w") as f:
                json.dump([], f, indent=2)

        # Build a mock request handler
        self.handler = server.ChatHandler
        self.handler.wfile = MagicMock()
        self.handler.wfile.write = MagicMock()
        self.handler.wfile.flush = MagicMock()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()
        self.handler.headers = {}
        self.handler.rfile = MagicMock()
        self.handler.path = "/"
        self.handler.command = "GET"
        self.handler.client_address = ("127.0.0.1", 12345)
        self.handler.server = MagicMock()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
        server.DATA_DIR = self.orig_data_dir

    def test_send_json(self):
        self.handler.send_json({"status": "ok"})
        self.handler.send_response.assert_called_with(200)
        self.handler.send_header.assert_any_call("Content-Type", "application/json")
        self.handler.wfile.write.assert_called_once()

    def test_send_json_error(self):
        self.handler.send_json({"error": "bad"}, 400)
        self.handler.send_response.assert_called_with(400)

    def test_serve_static_not_found(self):
        self.handler.path = "/nonexistent.html"
        self.handler.serve_static()
        self.handler.send_error.assert_called_with(404, "Not Found")

    def test_handle_get_config(self):
        self.handler.handle_get_config()
        self.handler.send_json.assert_called_once()
        args, _ = self.handler.send_json.call_args
        self.assertIn("api_key", args[0])

    def test_handle_update_config(self):
        self.handler.rfile.read = MagicMock(return_value=json.dumps({"theme": "light"}).encode())
        self.handler.headers["Content-Length"] = len(json.dumps({"theme": "light"}))
        self.handler.handle_update_config()
        self.handler.send_json.assert_called_once()
        args, _ = self.handler.send_json.call_args
        self.assertEqual(args[0]["theme"], "light")

    def test_handle_list_conversations(self):
        self.handler.handle_list_conversations()
        self.handler.send_json.assert_called_once_with([])

    def test_handle_create_conversation(self):
        self.handler.rfile.read = MagicMock(return_value=json.dumps({"title": "New"}).encode())
        self.handler.headers["Content-Length"] = len(json.dumps({"title": "New"}))
        self.handler.handle_create_conversation()
        self.handler.send_json.assert_called_once()
        args, kwargs = self.handler.send_json.call_args
        self.assertEqual(args[1], 201)
        self.assertEqual(args[0]["title"], "New")
        self.assertIn("id", args[0])

    def test_handle_get_conversation_not_found(self):
        self.handler.handle_get_conversation("nonexistent")
        self.handler.send_json.assert_called_with({"error": "Not found"}, 404)

    def test_handle_get_conversation_found(self):
        id_ = "test-id"
        conv = {"id": id_, "title": "Test", "messages": [], "created_at": 0, "updated_at": 0}
        server.save_conversation(id_, conv)
        self.handler.handle_get_conversation(id_)
        self.handler.send_json.assert_called_with(conv)

    def test_handle_delete_conversation(self):
        id_ = "test-id"
        conv = {"id": id_, "title": "Test", "messages": [], "created_at": 0, "updated_at": 0}
        server.save_conversation(id_, conv)
        self.handler.handle_delete_conversation(id_)
        self.handler.send_json.assert_called_with({"status": "deleted"})
        self.assertIsNone(server.get_conversation(id_))

    def test_handle_import_conversation(self):
        data = {"title": "Imported", "messages": [{"role": "user", "content": "hi"}]}
        self.handler.rfile.read = MagicMock(return_value=json.dumps(data).encode())
        self.handler.headers["Content-Length"] = len(json.dumps(data))
        self.handler.handle_import_conversation()
        self.handler.send_json.assert_called_once()
        args, kwargs = self.handler.send_json.call_args
        self.assertEqual(args[1], 201)
        self.assertIn("id", args[0])

    def test_handle_export_conversation_json(self):
        id_ = "test-id"
        conv = {"id": id_, "title": "Test", "messages": [], "created_at": 0, "updated_at": 0}
        server.save_conversation(id_, conv)
        self.handler.handle_export_conversation(id_, "json")
        self.handler.send_json.assert_called_with(conv)

    def test_handle_export_conversation_markdown(self):
        id_ = "test-id"
        conv = {"id": id_, "title": "Test", "messages": [{"role": "user", "content": "Hello"}]}
        server.save_conversation(id_, conv)
        self.handler.handle_export_conversation(id_, "markdown")
        # Should call send_response and write
        self.handler.send_response.assert_called_with(200)
        self.handler.send_header.assert_any_call("Content-Type", "text/markdown")
        self.handler.wfile.write.assert_called_once()

    def test_handle_list_skills(self):
        self.handler.handle_list_skills()
        self.handler.send_json.assert_called_with([])

    def test_handle_create_skill(self):
        data = {"name": "My Skill", "prompt": "Be helpful"}
        self.handler.rfile.read = MagicMock(return_value=json.dumps(data).encode())
        self.handler.headers["Content-Length"] = len(json.dumps(data))
        self.handler.handle_create_skill()
        self.handler.send_json.assert_called_once()
        args, kwargs = self.handler.send_json.call_args
        self.assertEqual(args[1], 201)
        self.assertEqual(args[0]["name"], "My Skill")

    def test_handle_update_skill(self):
        # First create a skill
        skill = {"id": "s1", "name": "Old", "prompt": "", "enabled": True}
        server.save_skills([skill])
        # Update
        update = {"name": "New Name"}
        self.handler.rfile.read = MagicMock(return_value=json.dumps(update).encode())
        self.handler.headers["Content-Length"] = len(json.dumps(update))
        self.handler.handle_update_skill("s1")
        self.handler.send_json.assert_called_once()
        args, _ = self.handler.send_json.call_args
        self.assertEqual(args[0]["name"], "New Name")

    def test_handle_delete_skill(self):
        skill = {"id": "s1", "name": "Skill", "prompt": "", "enabled": True}
        server.save_skills([skill])
        self.handler.handle_delete_skill("s1")
        self.handler.send_json.assert_called_with({"status": "deleted"})
        self.assertEqual(server.get_skills(), [])

    def test_handle_get_skill(self):
        skill = {"id": "s1", "name": "Skill", "prompt": "", "enabled": True}
        server.save_skills([skill])
        self.handler.handle_get_skill("s1")
        self.handler.send_json.assert_called_with(skill)

    def test_handle_get_skill_not_found(self):
        self.handler.handle_get_skill("nonexistent")
        self.handler.send_json.assert_called_with({"error": "Not found"}, 404)

    def test_handle_chat_missing_params(self):
        self.handler.rfile.read = MagicMock(return_value=json.dumps({}).encode())
        self.handler.headers["Content-Length"] = len(json.dumps({}))
        self.handler.handle_chat()
        self.handler.send_json.assert_called_with({"error": "Missing model or messages"}, 400)

    def test_handle_chat_no_api_key(self):
        server.save_config({"api_key": "", "default_model": "", "theme": "dark"})
        data = {"model": "test", "messages": [{"role": "user", "content": "hi"}]}
        self.handler.rfile.read = MagicMock(return_value=json.dumps(data).encode())
        self.handler.headers["Content-Length"] = len(json.dumps(data))
        self.handler.handle_chat()
        self.handler.send_json.assert_called_with({"error": "API key not configured"}, 401)

    @patch("server.httpx.Client")
    def test_handle_chat_stream(self, mock_client):
        server.save_config({"api_key": "test-key", "default_model": "", "theme": "dark"})
        data = {"model": "test-model", "messages": [{"role": "user", "content": "hi"}]}
        self.handler.rfile.read = MagicMock(return_value=json.dumps(data).encode())
        self.handler.headers["Content-Length"] = len(json.dumps(data))

        # Mock the streaming response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}",
            "data: [DONE]",
        ]
        mock_client_instance = MagicMock()
        mock_client_instance.stream.return_value.__enter__.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        self.handler.handle_chat()
        # Should have sent SSE events
        self.handler.wfile.write.assert_called()
        calls = self.handler.wfile.write.call_args_list
        # At least chunk and done events
        self.assertTrue(any(b"event: chunk" in c[0][0] for c in calls))
        self.assertTrue(any(b"event: done" in c[0][0] for c in calls))


if __name__ == "__main__":
    unittest.main()
