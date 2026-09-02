import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import HTTPServer
from server import ChatHandler, ATTACHMENTS_DIR, ALLOWED_MIME_TYPES, MAX_ATTACHMENT_SIZE


class TestAttachmentHandling(unittest.TestCase):
    """Tests for attachment upload endpoint."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.attachments_dir = os.path.join(self.temp_dir, 'attachments')
        os.makedirs(self.attachments_dir, exist_ok=True)

        # Patch ATTACHMENTS_DIR
        self.patcher = patch('server.ATTACHMENTS_DIR', self.attachments_dir)
        self.patcher.start()

        # Create a mock request handler
        self.handler = ChatHandler.__new__(ChatHandler)
        self.handler.path = '/api/attachments'
        self.handler.headers = {}
        self.handler.rfile = BytesIO()
        self.handler.wfile = BytesIO()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def tearDown(self):
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def _build_multipart_body(self, file_data, filename, field_name='file', content_type='text/plain'):
        """Build a multipart/form-data body."""
        boundary = '----TestBoundary12345'
        body = b''
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
        body += f'Content-Type: {content_type}\r\n'.encode()
        body += b'\r\n'
        body += file_data
        body += b'\r\n'
        body += f'--{boundary}--\r\n'.encode()
        return body, boundary

    def test_upload_success(self):
        """Test successful file upload."""
        file_data = b'Hello, world!'
        body, boundary = self._build_multipart_body(file_data, 'test.txt', content_type='text/plain')
        self.handler.headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        self.handler.rfile = BytesIO(body)

        # Mock _send_json to capture output
        self.handler._send_json = MagicMock()

        self.handler.do_POST()

        # Check that _send_json was called with success
        args, kwargs = self.handler._send_json.call_args
        response_data = args[0]
        status = args[1] if len(args) > 1 else kwargs.get('status', 200)

        self.assertEqual(status, 201)
        self.assertIn('filename', response_data)
        self.assertEqual(response_data['original_name'], 'test.txt')
        self.assertEqual(response_data['mime_type'], 'text/plain')
        self.assertEqual(response_data['size'], 13)

        # Verify file was saved
        saved_path = os.path.join(self.attachments_dir, response_data['filename'])
        self.assertTrue(os.path.exists(saved_path))
        with open(saved_path, 'rb') as f:
            self.assertEqual(f.read(), file_data)

    def test_upload_no_file(self):
        """Test upload with no file part."""
        boundary = '----TestBoundary12345'
        body = f'--{boundary}--\r\n'.encode()
        self.handler.headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        self.handler.rfile = BytesIO(body)

        self.handler._send_json = MagicMock()

        self.handler.do_POST()

        args, kwargs = self.handler._send_json.call_args
        response_data = args[0]
        status = args[1] if len(args) > 1 else kwargs.get('status', 200)

        self.assertEqual(status, 400)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'No file found in upload')

    def test_upload_invalid_mime_type(self):
        """Test upload with unsupported MIME type."""
        file_data = b'some binary'
        body, boundary = self._build_multipart_body(file_data, 'test.exe', content_type='application/x-msdownload')
        self.handler.headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        self.handler.rfile = BytesIO(body)

        self.handler._send_json = MagicMock()

        self.handler.do_POST()

        args, kwargs = self.handler._send_json.call_args
        response_data = args[0]
        status = args[1] if len(args) > 1 else kwargs.get('status', 200)

        self.assertEqual(status, 415)
        self.assertIn('error', response_data)
        self.assertIn('Unsupported file type', response_data['error'])

    def test_upload_oversized(self):
        """Test upload with file exceeding size limit."""
        file_data = b'x' * (MAX_ATTACHMENT_SIZE + 1)
        body, boundary = self._build_multipart_body(file_data, 'large.txt', content_type='text/plain')
        self.handler.headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        self.handler.rfile = BytesIO(body)

        self.handler._send_json = MagicMock()

        self.handler.do_POST()

        args, kwargs = self.handler._send_json.call_args
        response_data = args[0]
        status = args[1] if len(args) > 1 else kwargs.get('status', 200)

        self.assertEqual(status, 413)
        self.assertIn('error', response_data)
        self.assertIn('File too large', response_data['error'])

    def test_upload_server_error(self):
        """Test upload when file cannot be saved."""
        file_data = b'test data'
        body, boundary = self._build_multipart_body(file_data, 'test.txt', content_type='text/plain')
        self.handler.headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        self.handler.rfile = BytesIO(body)

        self.handler._send_json = MagicMock()

        # Make ATTACHMENTS_DIR point to a non-writable location
        with patch('server.ATTACHMENTS_DIR', '/nonexistent/path'):
            self.handler.do_POST()

            args, kwargs = self.handler._send_json.call_args
            response_data = args[0]
            status = args[1] if len(args) > 1 else kwargs.get('status', 200)

            self.assertEqual(status, 500)
            self.assertIn('error', response_data)
            self.assertIn('Failed to save file', response_data['error'])


if __name__ == '__main__':
    unittest.main()