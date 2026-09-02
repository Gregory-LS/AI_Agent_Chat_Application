#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from http.server import HTTPServer
from io import BytesIO
from unittest.mock import patch

# Add parent directory to path to import server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from _app.server import RequestHandler, load_conversations, save_conversations

class TestArchiveEndpoint(unittest.TestCase):
    def setUp(self):
        # Create a temporary conversations file
        self.temp_dir = tempfile.mkdtemp()
        self.conversations_file = os.path.join(self.temp_dir, 'conversations.json')
        self.patcher = patch('_app.server.CONVERSATIONS_FILE', self.conversations_file)
        self.patcher.start()
        # Seed with test data
        self.test_conversations = {
            'conv-1': {'id': 'conv-1', 'title': 'Test', 'archived': False},
            'conv-2': {'id': 'conv-2', 'title': 'Archived', 'archived': True}
        }
        save_conversations(self.test_conversations)

    def tearDown(self):
        self.patcher.stop()
        # Clean up temp files
        if os.path.exists(self.conversations_file):
            os.remove(self.conversations_file)
        os.rmdir(self.temp_dir)

    def _make_request(self, method, path, body=None):
        # Simulate a request using the handler's do_POST
        handler = RequestHandler(None, ('127.0.0.1', 0), None)
        handler.path = path
        handler.command = method
        handler.headers = {}
        if body:
            handler.rfile = BytesIO(body.encode())
        else:
            handler.rfile = BytesIO(b'')
        handler.send_response = self._mock_send_response
        handler.send_header = lambda k, v: None
        handler.end_headers = lambda: None
        self.response_data = None
        self.response_status = None
        def mock_write(data):
            self.response_data = json.loads(data.decode())
        handler.wfile.write = mock_write
        if method == 'POST':
            handler.do_POST()
        return handler

    def _mock_send_response(self, status):
        self.response_status = status

    def test_toggle_archive_non_archived(self):
        self._make_request('POST', '/api/conversations/conv-1/archive')
        self.assertEqual(self.response_status, 200)
        self.assertTrue(self.response_data['archived'])
        # Verify persistence
        convs = load_conversations()
        self.assertTrue(convs['conv-1']['archived'])

    def test_toggle_archive_archived(self):
        self._make_request('POST', '/api/conversations/conv-2/archive')
        self.assertEqual(self.response_status, 200)
        self.assertFalse(self.response_data['archived'])
        convs = load_conversations()
        self.assertFalse(convs['conv-2']['archived'])

    def test_invalid_conversation_id_format(self):
        self._make_request('POST', '/api/conversations/INVALID/archive')
        self.assertEqual(self.response_status, 400)
        self.assertIn('error', self.response_data)

    def test_nonexistent_conversation(self):
        self._make_request('POST', '/api/conversations/nonexistent/archive')
        self.assertEqual(self.response_status, 404)
        self.assertIn('error', self.response_data)

if __name__ == '__main__':
    unittest.main()
