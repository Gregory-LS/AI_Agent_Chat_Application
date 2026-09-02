import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    ChatHandler,
    ensure_dirs,
    load_config,
    save_config,
    load_skills,
    save_skills,
    load_conversation,
    save_conversation,
    list_conversations,
    get_conversation_path,
    ATTACHMENTS_DIR,
    ALLOWED_ATTACHMENT_TYPES,
    MAX_ATTACHMENT_SIZE,
)


class TestAttachmentHandler(unittest.TestCase):
    """Tests for attachment handling in server.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = self.temp_dir
        # Patch the DATA_DIR in server module
        import server
        server.DATA_DIR = self.temp_dir
        server.CONFIG_FILE = os.path.join(self.temp_dir, "config.json")
        server.CONVERSATIONS_DIR = os.path.join(self.temp_dir, "conversations")
        server.SKILLS_FILE = os.path.join(self.temp_dir, "skills.json")
        server.ATTACHMENTS_DIR = os.path.join(self.temp_dir, "attachments")
        ensure_dirs()

        self.handler = ChatHandler
        self.handler.ATTACHMENTS_DIR = server.ATTACHMENTS_DIR

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
        if self.original_data_dir:
            os.environ["DATA_DIR"] = self.original_data_dir
        else:
            del os.environ["DATA_DIR"]

    def _make_request(self, body, content_type="multipart/form-data; boundary=----TestBoundary"):
        """Helper to create a mock request."""
        handler = self.handler.__new__(self.handler)
        handler.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
        handler.rfile = BytesIO(body)
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.send_error = MagicMock()
        handler.send_json = MagicMock()
        handler.path = "/api/attachments"
        handler.command = "POST"
        return handler

    def _create_multipart_body(self, field_name, filename, content, content_type="text/plain"):
        """Create a multipart form-data body."""
        boundary = "----TestBoundary"
        body = []
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode())
        body.append(f"Content-Type: {content_type}".encode())
        body.append(b"")
        body.append(content if isinstance(content, bytes) else content.encode())
        body.append(f"--{boundary}--".encode())
        return b"\r\n".join(body), boundary

    def test_upload_text_file(self):
        """Test uploading a text file."""
        body, boundary = self._create_multipart_body("file", "test.txt", "Hello, world!", "text/plain")
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_json.assert_called_once()
        args, _ = handler.send_json.call_args
        attachment = args[0]
        self.assertEqual(attachment["filename"], "test.txt")
        self.assertEqual(attachment["type"], "text")
        self.assertEqual(attachment["mime_type"], "text/plain")
        self.assertEqual(attachment["size"], 13)
        self.assertIn("id", attachment)
        self.assertIn("url", attachment)
        self.assertTrue(attachment["url"].endswith("/download"))

    def test_upload_image_file(self):
        """Test uploading an image file."""
        body, boundary = self._create_multipart_body("file", "photo.png", b"fake_png_data", "image/png")
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_json.assert_called_once()
        args, _ = handler.send_json.call_args
        attachment = args[0]
        self.assertEqual(attachment["filename"], "photo.png")
        self.assertEqual(attachment["type"], "image")
        self.assertEqual(attachment["mime_type"], "image/png")

    def test_upload_invalid_file_type(self):
        """Test uploading a file with disallowed MIME type."""
        body, boundary = self._create_multipart_body("file", "script.exe", b"fake_exe", "application/x-msdownload")
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_error.assert_called_once_with(400, "File type 'application/x-msdownload' is not allowed. Allowed types: images (png, jpeg, gif, webp), text/code files")

    def test_upload_no_file_field(self):
        """Test uploading without a file field."""
        boundary = "----TestBoundary"
        body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"other\"\r\n\r\nvalue\r\n--{boundary}--\r\n".encode()
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_error.assert_called_once_with(400, "No file provided")

    def test_upload_empty_file(self):
        """Test uploading an empty file."""
        body, boundary = self._create_multipart_body("file", "empty.txt", "", "text/plain")
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_error.assert_called_once_with(400, "File is empty")

    def test_upload_file_too_large(self):
        """Test uploading a file exceeding size limit."""
        large_content = "x" * (MAX_ATTACHMENT_SIZE + 1)
        body, boundary = self._create_multipart_body("file", "large.txt", large_content, "text/plain")
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_error.assert_called_once_with(413, f"File too large. Maximum size is {MAX_ATTACHMENT_SIZE // (1024*1024)} MB")

    def test_upload_not_multipart(self):
        """Test uploading with wrong content type."""
        handler = self._make_request(b"{}", "application/json")
        handler.handle_upload_attachment()
        handler.send_error.assert_called_once_with(400, "Expected multipart/form-data")

    def test_download_attachment(self):
        """Test downloading an attachment."""
        # First upload a file
        body, boundary = self._create_multipart_body("file", "test.txt", "Hello, world!", "text/plain")
        content_type = f"multipart/form-data; boundary={boundary}"
        handler = self._make_request(body, content_type)
        handler.handle_upload_attachment()
        handler.send_json.assert_called_once()
        args, _ = handler.send_json.call_args
        attachment = args[0]
        attachment_id = attachment["id"]

        # Now download it
        handler2 = self.handler.__new__(self.handler)
        handler2.headers = {}
        handler2.rfile = BytesIO(b"")
        handler2.wfile = BytesIO()
        handler2.send_response = MagicMock()
        handler2.send_header = MagicMock()
        handler2.end_headers = MagicMock()
        handler2.send_error = MagicMock()
        handler2.send_json = MagicMock()
        handler2.path = f"/api/attachments/{attachment_id}/download"
        handler2.command = "GET"
        handler2.handle_download_attachment(attachment_id)
        handler2.send_response.assert_called_once_with(200)

    def test_download_attachment_not_found(self):
        """Test downloading a non-existent attachment."""
        handler = self.handler.__new__(self.handler)
        handler.headers = {}
        handler.rfile = BytesIO(b"")
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.send_error = MagicMock()
        handler.send_json = MagicMock()
        handler.path = "/api/attachments/nonexistent/download"
        handler.command = "GET"
        handler.handle_download_attachment("nonexistent")
        handler.send_error.assert_called_once_with(404, "Attachment not found")


class TestGeneralServerFunctions(unittest.TestCase):
    """Tests for general server functions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        import server
        server.DATA_DIR = self.temp_dir
        server.CONFIG_FILE = os.path.join(self.temp_dir, "config.json")
        server.CONVERSATIONS_DIR = os.path.join(self.temp_dir, "conversations")
        server.SKILLS_FILE = os.path.join(self.temp_dir, "skills.json")
        server.ATTACHMENTS_DIR = os.path.join(self.temp_dir, "attachments")
        ensure_dirs()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_ensure_dirs_creates_directories(self):
        import server
        server.DATA_DIR = self.temp_dir + "_new"
        server.CONVERSATIONS_DIR = os.path.join(self.temp_dir + "_new", "conversations")
        server.ATTACHMENTS_DIR = os.path.join(self.temp_dir + "_new", "attachments")
        ensure_dirs()
        self.assertTrue(os.path.exists(self.temp_dir + "_new"))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir + "_new", "conversations")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir + "_new", "attachments")))
        os.rmdir(os.path.join(self.temp_dir + "_new", "attachments"))
        os.rmdir(os.path.join(self.temp_dir + "_new", "conversations"))
        os.rmdir(self.temp_dir + "_new")

    def test_config_save_and_load(self):
        config = {"api_key": "test-key", "theme": "dark"}
        save_config(config)
        loaded = load_config()
        self.assertEqual(loaded["api_key"], "test-key")
        self.assertEqual(loaded["theme"], "dark")

    def test_config_load_default(self):
        loaded = load_config()
        self.assertEqual(loaded, {})

    def test_skills_save_and_load(self):
        skills = [{"id": "1", "name": "Test", "prompt": "You are a test assistant.", "enabled": True}]
        save_skills(skills)
        loaded = load_skills()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["name"], "Test")

    def test_conversation_save_and_load(self):
        conv = {"id": "test-id", "title": "Test", "messages": [], "model": "openai/gpt-4o"}
        save_conversation(conv)
        loaded = load_conversation("test-id")
        self.assertEqual(loaded["title"], "Test")
        self.assertEqual(loaded["model"], "openai/gpt-4o")

    def test_conversation_load_not_found(self):
        loaded = load_conversation("nonexistent")
        self.assertIsNone(loaded)

    def test_list_conversations_empty(self):
        convs = list_conversations()
        self.assertEqual(convs, [])

    def test_list_conversations(self):
        conv1 = {"id": "1", "title": "A", "updated_at": "2024-01-01"}
        conv2 = {"id": "2", "title": "B", "updated_at": "2024-01-02"}
        save_conversation(conv1)
        save_conversation(conv2)
        convs = list_conversations()
        self.assertEqual(len(convs), 2)
        self.assertEqual(convs[0]["id"], "2")  # Most recent first
        self.assertEqual(convs[1]["id"], "1")


if __name__ == "__main__":
    unittest.main()
