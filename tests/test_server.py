import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import ChatHandler, load_config, save_config, get_api_key

class TestServerConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch('server.DATA_DIR', self.temp_dir)
        self.patcher.start()
        self.config_file = os.path.join(self.temp_dir, 'config.json')
        # Ensure DATA_DIR subdirs exist
        os.makedirs(os.path.join(self.temp_dir, 'conversations'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'attachments'), exist_ok=True)

    def tearDown(self):
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_config_empty(self):
        config = load_config()
        self.assertEqual(config, {})

    def test_save_and_load_config(self):
        save_config({'api_key': 'test-key'})
        config = load_config()
        self.assertEqual(config.get('api_key'), 'test-key')

    def test_get_api_key_from_config(self):
        save_config({'api_key': 'config-key'})
        key = get_api_key()
        self.assertEqual(key, 'config-key')

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'env-key'}, clear=True)
    def test_get_api_key_from_env(self):
        # Remove config file so it falls back to env
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        key = get_api_key()
        self.assertEqual(key, 'env-key')

class TestChatHandlerModels(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch('server.DATA_DIR', self.temp_dir)
        self.patcher.start()
        os.makedirs(os.path.join(self.temp_dir, 'conversations'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'attachments'), exist_ok=True)
        # Create a mock request handler
        self.handler = ChatHandler.__new__(ChatHandler)
        self.handler.path = '/api/models'
        self.handler.headers = {}
        self.handler.rfile = MagicMock()
        self.handler.wfile = MagicMock()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def tearDown(self):
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('server.get_client')
    def test_handle_get_models_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_models.return_value = [
            {'id': 'model-1', 'name': 'Model 1', 'provider': 'Provider A', 'context_length': 8192, 'pricing': {'prompt': 0.01, 'completion': 0.02}}
        ]
        mock_get_client.return_value = mock_client
        self.handler.handle_get_models()
        self.handler.send_response.assert_called_with(200)
        # Check that json was written
        written = self.handler.wfile.write.call_args[0][0]
        data = json.loads(written)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], 'model-1')

    @patch('server.get_client')
    def test_handle_get_models_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_models.side_effect = Exception('API error')
        mock_get_client.return_value = mock_client
        self.handler.handle_get_models()
        self.handler.send_response.assert_called_with(500)
        written = self.handler.wfile.write.call_args[0][0]
        data = json.loads(written)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
