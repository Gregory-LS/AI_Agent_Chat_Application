#!/usr/bin/env python3
"""Unit tests for server.py"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    load_config,
    save_config,
    get_api_key,
    make_openrouter_headers,
    CONFIG_FILE,
    DATA_DIR,
    CONVERSATIONS_DIR,
    SKILLS_FILE,
    ATTACHMENTS_DIR,
)


class TestHelpers(unittest.TestCase):
    """Test helper functions."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_data_dir = DATA_DIR
        # Point to temp dir
        import server
        server.DATA_DIR = Path(self.temp_dir.name)
        server.CONFIG_FILE = server.DATA_DIR / "config.json"
        server.CONVERSATIONS_DIR = server.DATA_DIR / "conversations"
        server.SKILLS_FILE = server.DATA_DIR / "skills.json"
        server.ATTACHMENTS_DIR = server.DATA_DIR / "attachments"
        server.DATA_DIR.mkdir(exist_ok=True)
        server.CONVERSATIONS_DIR.mkdir(exist_ok=True)
        server.ATTACHMENTS_DIR.mkdir(exist_ok=True)
        if not server.SKILLS_FILE.exists():
            server.SKILLS_FILE.write_text("[]", encoding="utf-8")
        if not server.CONFIG_FILE.exists():
            server.CONFIG_FILE.write_text(json.dumps({"api_key": "", "default_model": ""}), encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()
        import server
        server.DATA_DIR = self.original_data_dir
        server.CONFIG_FILE = self.original_data_dir / "config.json"
        server.CONVERSATIONS_DIR = self.original_data_dir / "conversations"
        server.SKILLS_FILE = self.original_data_dir / "skills.json"
        server.ATTACHMENTS_DIR = self.original_data_dir / "attachments"

    def test_load_config_default(self):
        config = load_config()
        self.assertEqual(config, {"api_key": "", "default_model": ""})

    def test_save_and_load_config(self):
        new_config = {"api_key": "test-key", "default_model": "gpt-4"}
        save_config(new_config)
        loaded = load_config()
        self.assertEqual(loaded["api_key"], "test-key")
        self.assertEqual(loaded["default_model"], "gpt-4")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"})
    def test_get_api_key_from_env(self):
        key = get_api_key()
        self.assertEqual(key, "env-key")

    def test_get_api_key_from_config(self):
        save_config({"api_key": "config-key", "default_model": ""})
        key = get_api_key()
        self.assertEqual(key, "config-key")

    def test_get_api_key_empty(self):
        save_config({"api_key": "", "default_model": ""})
        key = get_api_key()
        self.assertEqual(key, "")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": ""})
    def test_make_openrouter_headers_no_key(self):
        headers = make_openrouter_headers()
        self.assertIsNone(headers)

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    def test_make_openrouter_headers_with_key(self):
        headers = make_openrouter_headers()
        self.assertIsNotNone(headers)
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
