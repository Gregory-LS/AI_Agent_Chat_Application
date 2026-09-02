import json
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import load_config, OPENROUTER_API_BASE


class TestOpenRouterConfig(unittest.TestCase):
    """Tests for OpenRouter configuration"""

    def test_api_base_url(self):
        """Test that the API base URL is correct"""
        self.assertEqual(OPENROUTER_API_BASE, 'https://openrouter.ai/api/v1')

    def test_config_has_api_key_field(self):
        """Test that config has apiKey field"""
        config = load_config()
        self.assertIn('apiKey', config)

    def test_config_has_default_model_field(self):
        """Test that config has defaultModel field"""
        config = load_config()
        self.assertIn('defaultModel', config)

    def test_config_has_theme_field(self):
        """Test that config has theme field"""
        config = load_config()
        self.assertIn('theme', config)


if __name__ == '__main__':
    unittest.main()
