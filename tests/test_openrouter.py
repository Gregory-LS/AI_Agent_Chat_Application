import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import ChatHandler


class TestOpenRouterAPI(unittest.TestCase):
    def setUp(self):
        self.handler = ChatHandler.__new__(ChatHandler)
        self.handler.headers = {}
        self.handler.rfile = MagicMock()
        self.handler.wfile = MagicMock()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def test_get_api_key_from_env(self):
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'sk-or-test'}):
            key = self.handler._get_api_key()
            self.assertEqual(key, 'sk-or-test')

    def test_get_api_key_from_config(self):
        import tempfile
        import os
        from pathlib import Path
        from server import CONFIG_FILE
        
        # Temporarily change CONFIG_FILE
        original = CONFIG_FILE
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({'api_key': 'sk-or-config'}, f)
                temp_path = f.name
            
            # Monkey-patch CONFIG_FILE
            import server
            server.CONFIG_FILE = Path(temp_path)
            
            with patch.dict('os.environ', {}, clear=True):
                key = self.handler._get_api_key()
                self.assertEqual(key, 'sk-or-config')
            
            os.unlink(temp_path)
        finally:
            server.CONFIG_FILE = original


if __name__ == '__main__':
    unittest.main()
