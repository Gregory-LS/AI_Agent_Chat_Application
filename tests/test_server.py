import json
import pytest
from unittest.mock import patch, MagicMock

# We'll test the handler methods directly
from server import ChatHandler

class MockRequest:
    def __init__(self, path='/'):
        self.path = path
        self.headers = {}
        self.body = b''
        self.method = 'GET'

class MockResponse:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.body = b''

class MockHandler(ChatHandler):
    def __init__(self):
        self.path = '/'
        self.headers = {}
        self.rfile = MagicMock()
        self.wfile = MagicMock()
        self.send_response = MagicMock()
        self.send_header = MagicMock()
        self.end_headers = MagicMock()
        self.server = MagicMock()
        self.request = MagicMock()
        self.client_address = ('127.0.0.1', 12345)
        self.command = 'GET'
        self._send_json_called = False
        self._send_json_status = None
        self._send_json_data = None

    def _send_json(self, data, status=200):
        self._send_json_called = True
        self._send_json_status = status
        self._send_json_data = data

    def send_error(self, code, message=None):
        self._send_json({'error': message or 'Error'}, code)

def test_get_models_success():
    mock_models = [{'id': 'model1', 'name': 'Model 1'}]
    with patch('openrouter.fetch_models', return_value=mock_models):
        handler = MockHandler()
        handler.handle_get_models()
        assert handler._send_json_called
        assert handler._send_json_status == 200
        assert handler._send_json_data == {'models': mock_models}

def test_get_models_empty():
    with patch('openrouter.fetch_models', return_value=[]):
        handler = MockHandler()
        handler.handle_get_models()
        assert handler._send_json_status == 200
        assert handler._send_json_data == {'models': []}

def test_get_models_api_error():
    with patch('openrouter.fetch_models', side_effect=Exception('API error')):
        handler = MockHandler()
        handler.handle_get_models()
        assert handler._send_json_status == 500
        assert 'error' in handler._send_json_data

def test_get_models_server_error():
    with patch('openrouter.fetch_models', side_effect=RuntimeError('Server failure')):
        handler = MockHandler()
        handler.handle_get_models()
        assert handler._send_json_status == 500
        assert 'error' in handler._send_json_data

def test_do_get_models_routing():
    handler = MockHandler()
    handler.path = '/api/models'
    with patch.object(handler, 'handle_get_models') as mock_handle:
        handler.do_GET()
        mock_handle.assert_called_once()

def test_do_get_unknown_path():
    handler = MockHandler()
    handler.path = '/api/unknown'
    with patch.object(handler, 'send_error') as mock_error:
        handler.do_GET()
        mock_error.assert_called_once_with(404)
