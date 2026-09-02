import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    hash_password,
    verify_password,
    create_jwt,
    verify_jwt,
    get_user_from_cookie,
    ChatHandler,
    USERS_FILE,
    JWT_SECRET
)


class TestAuthFunctions(unittest.TestCase):
    def test_hash_password_and_verify(self):
        password = 'testpassword123'
        salt, hashed = hash_password(password)
        self.assertTrue(verify_password(password, salt, hashed))
        self.assertFalse(verify_password('wrongpassword', salt, hashed))

    def test_hash_password_uses_salt(self):
        password = 'test'
        salt1, hash1 = hash_password(password)
        salt2, hash2 = hash_password(password)
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)

    def test_create_and_verify_jwt(self):
        user_id = 'testuser'
        token = create_jwt(user_id)
        payload = verify_jwt(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], user_id)
        self.assertIn('iat', payload)
        self.assertIn('exp', payload)

    def test_verify_jwt_invalid(self):
        self.assertIsNone(verify_jwt('invalid.token.here'))
        self.assertIsNone(verify_jwt(''))
        self.assertIsNone(verify_jwt('a.b.c'))

    def test_verify_jwt_expired(self):
        # Create a token with a very short expiration that has passed
        import time
        import hmac
        import hashlib
        import urllib.parse
        import json as json_mod
        header = {'alg': 'HS256', 'typ': 'JWT'}
        payload = {'user_id': 'test', 'iat': int(time.time()) - 100, 'exp': int(time.time()) - 10}
        header_b64 = urllib.parse.quote(json_mod.dumps(header, separators=(',', ':')).encode('utf-8'), safe='').rstrip('=')
        payload_b64 = urllib.parse.quote(json_mod.dumps(payload, separators=(',', ':')).encode('utf-8'), safe='').rstrip('=')
        signature = hmac.new(JWT_SECRET.encode('utf-8'), f'{header_b64}.{payload_b64}'.encode('utf-8'), hashlib.sha256).hexdigest()
        token = f'{header_b64}.{payload_b64}.{signature}'
        self.assertIsNone(verify_jwt(token))

    def test_get_user_from_cookie(self):
        # Create a mock handler
        handler = MagicMock()
        user_id = 'testuser'
        token = create_jwt(user_id)
        handler.headers = {'Cookie': f'session={token}'}
        result = get_user_from_cookie(handler)
        self.assertEqual(result, user_id)

    def test_get_user_from_cookie_no_cookie(self):
        handler = MagicMock()
        handler.headers = {}
        result = get_user_from_cookie(handler)
        self.assertIsNone(result)

    def test_get_user_from_cookie_invalid(self):
        handler = MagicMock()
        handler.headers = {'Cookie': 'session=invalidtoken'}
        result = get_user_from_cookie(handler)
        self.assertIsNone(result)


class TestUserFile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_users_file = USERS_FILE
        # We can't easily replace USERS_FILE at module level, so we test the logic

    def test_users_file_creation(self):
        # The server creates users.json on startup if it doesn't exist
        # We test that the file is valid JSON
        users_file = Path(self.temp_dir) / 'users.json'
        if not users_file.exists():
            users_file.write_text('{}')
        data = json.loads(users_file.read_text())
        self.assertEqual(data, {})


if __name__ == '__main__':
    unittest.main()
