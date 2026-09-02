import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    load_users,
    save_users,
    hash_password,
    verify_password,
    create_jwt,
    verify_jwt,
    USERS_FILE,
    SECRET_KEY
)


class TestAuthFunctions(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.original_users_file = USERS_FILE
        # We'll patch the global in tests that need it

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_hash_and_verify_password(self):
        password = 'test_password_123'
        hashed = hash_password(password)
        self.assertIn(':', hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password('wrong_password', hashed))

    def test_verify_password_invalid_format(self):
        self.assertFalse(verify_password('test', 'invalid_format'))
        self.assertFalse(verify_password('test', ''))

    def test_create_and_verify_jwt(self):
        user_id = 'test-user-id'
        token = create_jwt(user_id)
        self.assertIsNotNone(token)
        self.assertEqual(verify_jwt(token), user_id)

    def test_verify_jwt_invalid_token(self):
        self.assertIsNone(verify_jwt('invalid.token.here'))
        self.assertIsNone(verify_jwt(''))
        self.assertIsNone(verify_jwt('a.b.c'))

    def test_verify_jwt_expired_token(self):
        import time
        import base64
        import json
        import hmac
        import hashlib
        # Create an expired token manually
        header = base64.urlsafe_b64encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()).rstrip(b'=').decode()
        payload = base64.urlsafe_b64encode(json.dumps({'sub': 'user', 'exp': int(time.time()) - 3600}).encode()).rstrip(b'=').decode()
        signature = hmac.new(SECRET_KEY.encode(), f'{header}.{payload}'.encode(), hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        token = f'{header}.{payload}.{sig_b64}'
        self.assertIsNone(verify_jwt(token))

    @patch('server.USERS_FILE', new_callable=lambda: os.path.join(tempfile.gettempdir(), 'test_users.json'))
    def test_load_users_empty_file(self, mock_file):
        # Ensure file exists with empty dict
        with open(mock_file, 'w') as f:
            json.dump({}, f)
        users = load_users()
        self.assertEqual(users, {})

    @patch('server.USERS_FILE', new_callable=lambda: os.path.join(tempfile.gettempdir(), 'test_users.json'))
    def test_save_and_load_users(self, mock_file):
        users = {'testuser': {'id': '123', 'password_hash': 'hash'}}
        save_users(users)
        loaded = load_users()
        self.assertEqual(loaded, users)


if __name__ == '__main__':
    unittest.main()
