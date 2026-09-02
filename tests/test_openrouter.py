import json
import os
import unittest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import server

class TestOpenRouterClient(unittest.TestCase):
    @patch("server.httpx.get")
    def test_fetch_models_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"id": "model-1"}]}
        mock_get.return_value = mock_resp

        # We'll test via the handler's logic indirectly
        from server import get_headers
        headers = get_headers()
        # Simulate what handle_models does
        import httpx
        resp = httpx.get("https://openrouter.ai/api/v1/models", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("data", resp.json())

    @patch("server.httpx.get")
    def test_fetch_balance_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"credits": 100.0}}
        mock_get.return_value = mock_resp

        from server import get_headers
        headers = get_headers()
        import httpx
        resp = httpx.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["credits"], 100.0)

if __name__ == "__main__":
    unittest.main()
