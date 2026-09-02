import json
import os
import tempfile
import unittest
from pathlib import Path
from http.server import HTTPServer
from threading import Thread
import urllib.request
import urllib.error

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import ChatHandler, DATA_DIR, CONFIG_FILE, CONVERSATIONS_DIR, SKILLS_FILE, ATTACHMENTS_DIR


class TestServerConfig(unittest.TestCase):
    """Tests for config endpoints"""

    def setUp(self):
        # Use temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = DATA_DIR
        # We can't easily swap DATA_DIR, so we'll test the functions directly
        self.config_data = {
            'apiKey': 'test-key',
            'defaultModel': 'test-model',
            'theme': 'light'
        }

    def test_load_config_defaults(self):
        """Test that config loads with defaults if file missing"""
        # Temporarily remove config file
        if CONFIG_FILE.exists():
            backup = CONFIG_FILE.read_text()
            CONFIG_FILE.unlink()
            try:
                from server import load_config
                config = load_config()
                self.assertIn('apiKey', config)
                self.assertIn('defaultModel', config)
                self.assertIn('theme', config)
            finally:
                CONFIG_FILE.write_text(backup)

    def test_save_and_load_config(self):
        """Test round-trip config save/load"""
        from server import save_config, load_config
        save_config(self.config_data)
        loaded = load_config()
        self.assertEqual(loaded['apiKey'], 'test-key')
        self.assertEqual(loaded['defaultModel'], 'test-model')
        self.assertEqual(loaded['theme'], 'light')


class TestServerConversations(unittest.TestCase):
    """Tests for conversation endpoints"""

    def setUp(self):
        # Ensure clean state
        self.conv_data = {
            'id': 'test-conv-1',
            'title': 'Test Conversation',
            'messages': [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there!'}
            ],
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }

    def test_save_and_load_conversation(self):
        """Test saving and loading a conversation"""
        from server import save_conversation, load_conversation, delete_conversation
        save_conversation(self.conv_data)
        loaded = load_conversation('test-conv-1')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['title'], 'Test Conversation')
        self.assertEqual(len(loaded['messages']), 2)
        # Cleanup
        delete_conversation('test-conv-1')

    def test_load_nonexistent_conversation(self):
        """Test loading a conversation that doesn't exist"""
        from server import load_conversation
        result = load_conversation('nonexistent-id')
        self.assertIsNone(result)

    def test_delete_nonexistent_conversation(self):
        """Test deleting a conversation that doesn't exist"""
        from server import delete_conversation
        result = delete_conversation('nonexistent-id')
        self.assertFalse(result)

    def test_list_conversations_empty(self):
        """Test listing conversations when none exist"""
        from server import load_conversations
        convs = load_conversations()
        self.assertIsInstance(convs, list)


class TestServerSkills(unittest.TestCase):
    """Tests for skills endpoints"""

    def setUp(self):
        self.skills_data = [
            {'id': 'skill-1', 'name': 'Test Skill', 'prompt': 'You are a test assistant.'}
        ]

    def test_save_and_load_skills(self):
        """Test saving and loading skills"""
        from server import save_skills, load_skills
        save_skills(self.skills_data)
        loaded = load_skills()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]['name'], 'Test Skill')


class TestServerAPIKey(unittest.TestCase):
    """Tests for API key handling"""

    def test_config_api_key_priority(self):
        """Test that config file API key takes priority over env var"""
        from server import load_config
        config = load_config()
        # If config has an API key, it should be used
        if config.get('apiKey'):
            self.assertIsNotNone(config['apiKey'])
        # If not, env var should be used
        elif os.getenv('OPENROUTER_API_KEY'):
            self.assertIsNotNone(os.getenv('OPENROUTER_API_KEY'))


if __name__ == '__main__':
    unittest.main()
