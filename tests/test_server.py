import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import AuthSystem, auth, get_token_from_headers, require_auth

class TestAuthSystem(unittest.TestCase):
    def setUp(self):
        # Use temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_data_dir = 'data'
        # Patch data directory
        self.patcher = patch('server.SESSIONS_FILE', os.path.join(self.test_dir, 'sessions.json'))
        self.patcher_sessions = self.patcher.start()
        self.patcher2 = patch('server.USERS_FILE', os.path.join(self.test_dir, 'users.json'))
        self.patcher_users = self.patcher2.start()
        
        # Create auth system with test data
        self.auth = AuthSystem()
        # Clear any existing data
        self.auth.users = {}
        self.auth.sessions = {}
        self.auth._save_users()
        self.auth._save_sessions()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()
        # Clean up test files
        for f in ['sessions.json', 'users.json']:
            fpath = os.path.join(self.test_dir, f)
            if os.path.exists(fpath):
                os.remove(fpath)
        os.rmdir(self.test_dir)

    def test_register_success(self):
        result, error = self.auth.register('testuser', 'password123')
        self.assertIsNone(error)
        self.assertEqual(result, {'username': 'testuser'})
        
        # Verify user was saved
        self.auth._load_users()
        self.assertIn('testuser', self.auth.users)
        self.assertIn('password_hash', self.auth.users['testuser'])

    def test_register_duplicate(self):
        self.auth.register('testuser', 'password123')
        result, error = self.auth.register('testuser', 'otherpass')
        self.assertIsNone(result)
        self.assertEqual(error, 'Username already exists')

    def test_register_empty_username(self):
        result, error = self.auth.register('', 'password123')
        self.assertIsNone(result)
        self.assertEqual(error, 'Username and password required')

    def test_register_short_password(self):
        result, error = self.auth.register('testuser', '12345')
        self.assertIsNone(result)
        self.assertEqual(error, 'Password must be at least 6 characters')

    def test_login_success(self):
        self.auth.register('testuser', 'password123')
        result, error = self.auth.login('testuser', 'password123')
        self.assertIsNone(error)
        self.assertIn('token', result)
        self.assertEqual(result['username'], 'testuser')

    def test_login_wrong_password(self):
        self.auth.register('testuser', 'password123')
        result, error = self.auth.login('testuser', 'wrongpass')
        self.assertIsNone(result)
        self.assertEqual(error, 'Invalid username or password')

    def test_login_nonexistent_user(self):
        result, error = self.auth.login('nonexistent', 'password123')
        self.assertIsNone(result)
        self.assertEqual(error, 'Invalid username or password')

    def test_validate_session_valid(self):
        self.auth.register('testuser', 'password123')
        login_result, _ = self.auth.login('testuser', 'password123')
        token = login_result['token']
        
        username = self.auth.validate_session(token)
        self.assertEqual(username, 'testuser')

    def test_validate_session_invalid(self):
        username = self.auth.validate_session('invalidtoken')
        self.assertIsNone(username)

    def test_validate_session_expired(self):
        self.auth.register('testuser', 'password123')
        login_result, _ = self.auth.login('testuser', 'password123')
        token = login_result['token']
        
        # Manually expire the session
        self.auth.sessions[token]['expires_at'] = 0
        self.auth._save_sessions()
        
        username = self.auth.validate_session(token)
        self.assertIsNone(username)
        # Session should be removed
        self.assertNotIn(token, self.auth.sessions)

    def test_logout(self):
        self.auth.register('testuser', 'password123')
        login_result, _ = self.auth.login('testuser', 'password123')
        token = login_result['token']
        
        result = self.auth.logout(token)
        self.assertTrue(result)
        self.assertNotIn(token, self.auth.sessions)

    def test_logout_invalid_token(self):
        result = self.auth.logout('invalidtoken')
        self.assertFalse(result)

    def test_cleanup_expired(self):
        self.auth.register('testuser', 'password123')
        login_result, _ = self.auth.login('testuser', 'password123')
        token = login_result['token']
        
        # Add expired session
        self.auth.sessions['expiredtoken'] = {
            'username': 'testuser',
            'created_at': 0,
            'expires_at': 0
        }
        self.auth._save_sessions()
        
        self.auth.cleanup_expired()
        self.assertNotIn('expiredtoken', self.auth.sessions)
        # Valid session should remain
        self.assertIn(token, self.auth.sessions)

    def test_get_token_from_headers(self):
        headers = {'Authorization': 'Bearer sometoken123'}
        token = get_token_from_headers(headers)
        self.assertEqual(token, 'sometoken123')

    def test_get_token_from_headers_missing(self):
        headers = {}
        token = get_token_from_headers(headers)
        self.assertIsNone(token)

    def test_get_token_from_headers_wrong_format(self):
        headers = {'Authorization': 'Basic dXNlcjpwYXNz'}
        token = get_token_from_headers(headers)
        self.assertIsNone(token)


class TestAuthHandler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch('server.SESSIONS_FILE', os.path.join(self.test_dir, 'sessions.json'))
        self.patcher.start()
        self.patcher2 = patch('server.USERS_FILE', os.path.join(self.test_dir, 'users.json'))
        self.patcher2.start()
        
        # Reinitialize auth with test data
        import server
        server.auth = AuthSystem()
        server.auth.users = {}
        server.auth.sessions = {}
        server.auth._save_users()
        server.auth._save_sessions()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()
        for f in ['sessions.json', 'users.json']:
            fpath = os.path.join(self.test_dir, f)
            if os.path.exists(fpath):
                os.remove(fpath)
        os.rmdir(self.test_dir)

    def test_require_auth_decorator_valid(self):
        # Register and login
        server.auth.register('testuser', 'password123')
        login_result, _ = server.auth.login('testuser', 'password123')
        token = login_result['token']
        
        # Create mock handler
        mock_handler = MagicMock()
        mock_handler.headers = {'Authorization': f'Bearer {token}'}
        
        @require_auth
        def test_endpoint(self, username):
            return username
        
        result = test_endpoint(mock_handler)
        self.assertEqual(result, 'testuser')

    def test_require_auth_decorator_invalid(self):
        mock_handler = MagicMock()
        mock_handler.headers = {'Authorization': 'Bearer invalidtoken'}
        mock_handler.send_response = MagicMock()
        mock_handler.send_header = MagicMock()
        mock_handler.end_headers = MagicMock()
        mock_handler.wfile = MagicMock()
        
        @require_auth
        def test_endpoint(self, username):
            return username
        
        result = test_endpoint(mock_handler)
        self.assertIsNone(result)
        mock_handler.send_response.assert_called_with(401)

    def test_require_auth_decorator_no_token(self):
        mock_handler = MagicMock()
        mock_handler.headers = {}
        mock_handler.send_response = MagicMock()
        mock_handler.send_header = MagicMock()
        mock_handler.end_headers = MagicMock()
        mock_handler.wfile = MagicMock()
        
        @require_auth
        def test_endpoint(self, username):
            return username
        
        result = test_endpoint(mock_handler)
        self.assertIsNone(result)
        mock_handler.send_response.assert_called_with(401)


if __name__ == '__main__':
    unittest.main()