import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import server module
import server

class TestAuth(unittest.TestCase):
    def setUp(self):
        # Use temporary directory for data
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch('server.DATA_DIR', self.temp_dir)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        
        # Reset sessions
        server.sessions.clear()
        
        # Create a test user
        self.test_username = 'testuser'
        self.test_password = 'testpass123'
        server.save_users({self.test_username: server.hash_password(self.test_password)})

    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_hash_password_and_verify(self):
        password = 'mypassword'
        hashed = server.hash_password(password)
        self.assertTrue(server.verify_password(password, hashed))
        self.assertFalse(server.verify_password('wrongpassword', hashed))

    def test_register_new_user(self):
        users = server.load_users()
        self.assertNotIn('newuser', users)
        
        # Simulate registration
        username = 'newuser'
        password = 'newpass123'
        users[username] = server.hash_password(password)
        server.save_users(users)
        
        loaded = server.load_users()
        self.assertIn(username, loaded)
        self.assertTrue(server.verify_password(password, loaded[username]))

    def test_register_duplicate_user(self):
        users = server.load_users()
        self.assertIn(self.test_username, users)
        
        # Attempt duplicate registration should keep original password
        users[self.test_username] = server.hash_password('newpassword')
        server.save_users(users)
        
        loaded = server.load_users()
        self.assertTrue(server.verify_password('newpassword', loaded[self.test_username]))

    def test_login_valid_credentials(self):
        users = server.load_users()
        stored = users.get(self.test_username)
        self.assertIsNotNone(stored)
        self.assertTrue(server.verify_password(self.test_password, stored))

    def test_login_invalid_credentials(self):
        users = server.load_users()
        stored = users.get(self.test_username)
        self.assertFalse(server.verify_password('wrongpass', stored))

    def test_session_create_and_get(self):
        session_id = server.create_session(self.test_username)
        username = server.get_session_user(session_id)
        self.assertEqual(username, self.test_username)
        
        # Invalid session
        self.assertIsNone(server.get_session_user('invalid-session'))

    def test_session_expiry(self):
        session_id = server.create_session(self.test_username)
        # Manually expire session
        with server.session_lock:
            server.sessions[session_id]['expires'] = 0
        username = server.get_session_user(session_id)
        self.assertIsNone(username)

    def test_delete_session(self):
        session_id = server.create_session(self.test_username)
        server.delete_session(session_id)
        self.assertIsNone(server.get_session_user(session_id))

if __name__ == '__main__':
    unittest.main()
