import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import server module
import server

class TestUserAuth(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for data
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = server.DATA_DIR
        server.DATA_DIR = self.temp_dir
        server.USERS_FILE = os.path.join(self.temp_dir, "users.json")
        server.CONFIG_FILE = os.path.join(self.temp_dir, "config.json")
        server.CONVERSATIONS_DIR = os.path.join(self.temp_dir, "conversations")
        server.SKILLS_FILE = os.path.join(self.temp_dir, "skills.json")
        server.ATTACHMENTS_DIR = os.path.join(self.temp_dir, "attachments")
        os.makedirs(server.CONVERSATIONS_DIR, exist_ok=True)
        os.makedirs(server.ATTACHMENTS_DIR, exist_ok=True)
        # Clear sessions
        server.sessions.clear()
    
    def tearDown(self):
        server.DATA_DIR = self.original_data_dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_user(self):
        success, msg = server.create_user("testuser", "password123")
        self.assertTrue(success)
        self.assertEqual(msg, "User created")
        # Verify user was saved
        users = server.load_users()
        self.assertIn("testuser", users)
        self.assertNotEqual(users["testuser"]["password"], "password123")  # Hashed
    
    def test_create_duplicate_user(self):
        server.create_user("testuser", "password123")
        success, msg = server.create_user("testuser", "otherpass")
        self.assertFalse(success)
        self.assertEqual(msg, "Username already exists")
    
    def test_authenticate_success(self):
        server.create_user("testuser", "password123")
        success, token = server.authenticate("testuser", "password123")
        self.assertTrue(success)
        self.assertIsNotNone(token)
        # Token should be in sessions
        self.assertIn(token, server.sessions)
        self.assertEqual(server.sessions[token], "testuser")
    
    def test_authenticate_wrong_password(self):
        server.create_user("testuser", "password123")
        success, token = server.authenticate("testuser", "wrongpass")
        self.assertFalse(success)
        self.assertIsNone(token)
    
    def test_authenticate_nonexistent_user(self):
        success, token = server.authenticate("nouser", "password123")
        self.assertFalse(success)
        self.assertIsNone(token)
    
    def test_validate_session(self):
        server.create_user("testuser", "password123")
        _, token = server.authenticate("testuser", "password123")
        username = server.validate_session(token)
        self.assertEqual(username, "testuser")
    
    def test_validate_invalid_session(self):
        username = server.validate_session("invalidtoken")
        self.assertIsNone(username)
    
    def test_logout(self):
        server.create_user("testuser", "password123")
        _, token = server.authenticate("testuser", "password123")
        server.logout(token)
        self.assertNotIn(token, server.sessions)
        username = server.validate_session(token)
        self.assertIsNone(username)

class TestServerEndpoints(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = server.DATA_DIR
        server.DATA_DIR = self.temp_dir
        server.USERS_FILE = os.path.join(self.temp_dir, "users.json")
        server.CONFIG_FILE = os.path.join(self.temp_dir, "config.json")
        server.CONVERSATIONS_DIR = os.path.join(self.temp_dir, "conversations")
        server.SKILLS_FILE = os.path.join(self.temp_dir, "skills.json")
        server.ATTACHMENTS_DIR = os.path.join(self.temp_dir, "attachments")
        os.makedirs(server.CONVERSATIONS_DIR, exist_ok=True)
        os.makedirs(server.ATTACHMENTS_DIR, exist_ok=True)
        server.sessions.clear()
        # Create a test user and get token
        server.create_user("testuser", "password123")
        _, self.token = server.authenticate("testuser", "password123")
    
    def tearDown(self):
        server.DATA_DIR = self.original_data_dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_auth_check_authenticated(self):
        # Simulate request handling
        from http.server import HTTPServer
        # We'll test the functions directly
        result = server.validate_session(self.token)
        self.assertEqual(result, "testuser")
    
    def test_auth_check_unauthenticated(self):
        result = server.validate_session("invalid")
        self.assertIsNone(result)
    
    def test_protected_endpoint_without_token(self):
        # Test that _require_auth returns None without token
        # We can't easily instantiate the handler, but we can test the logic
        self.assertIsNone(server.validate_session(None))

if __name__ == "__main__":
    unittest.main()