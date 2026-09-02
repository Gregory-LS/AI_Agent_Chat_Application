import json
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, '.')

import openrouter

class TestOpenRouterBalance(unittest.TestCase):
    @patch('openrouter.httpx.Client')
    def test_get_balance_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "credits": 123.456,
                "usage": 50.0,
                "total_credits": 173.456
            }
        }
        mock_client.get.return_value = mock_response

        result = openrouter.get_balance("test-api-key")
        self.assertEqual(result["credits"], 123.456)
        self.assertEqual(result["usage"], 50.0)
        self.assertEqual(result["total"], 173.456)

    @patch('openrouter.httpx.Client')
    def test_get_balance_http_error(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 401")
        mock_client.get.return_value = mock_response

        with self.assertRaises(Exception):
            openrouter.get_balance("bad-key")

    @patch('openrouter.httpx.Client')
    def test_get_balance_missing_data(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.get.return_value = mock_response

        result = openrouter.get_balance("test-api-key")
        self.assertEqual(result["credits"], 0)
        self.assertEqual(result["usage"], 0)
        self.assertEqual(result["total"], 0)

if __name__ == '__main__':
    unittest.main()
