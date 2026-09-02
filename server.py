import http.server
import json
import os
import uuid
import hashlib
import hmac
import time
import threading
from urllib.parse import urlparse, parse_qs
from http import HTTPStatus

# Attempt to import werkzeug for password hashing; fallback to plaintext if not available
try:
    from werkzeug.security import generate_password_hash, check_password_hash
    HAVE_WERKZEUG = True
except ImportError:
    HAVE_WERKZEUG = False
    import hashlib
    def generate_password_hash(password):
        salt = uuid.uuid4().hex
        return f'{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}'
    def check_password_hash(pwhash, password):
        try:
            salt, hsh = pwhash.split('$', 1)
            return hsh == hashlib.sha256((salt + password).encode()).hexdigest()
        except:
            return False

# Session management
SESSIONS_FILE = 'data/sessions.json'
USERS_FILE = 'data/users.json'
SESSION_DURATION = 86400 * 7  # 7 days

_data_lock = threading.Lock()

class AuthSystem:
    def __init__(self):
        self._ensure_data_dir()
        self._load_sessions()
        self._load_users()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_sessions(self):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                self.sessions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.sessions = {}

    def _save_sessions(self):
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(self.sessions, f)

    def _load_users(self):
        try:
            with open(USERS_FILE, 'r') as f:
                self.users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.users = {}

    def _save_users(self):
        with open(USERS_FILE, 'w') as f:
            json.dump(self.users, f)

    def register(self, username, password):
        if not username or not password:
            return None, 'Username and password required'
        if len(password) < 6:
            return None, 'Password must be at least 6 characters'
        with _data_lock:
            self._load_users()
            if username in self.users:
                return None, 'Username already exists'
            self.users[username] = {
                'password_hash': generate_password_hash(password),
                'created_at': time.time()
            }
            self._save_users()
        return {'username': username}, None

    def login(self, username, password):
        with _data_lock:
            self._load_users()
            user = self.users.get(username)
            if not user or not check_password_hash(user['password_hash'], password):
                return None, 'Invalid username or password'
            token = uuid.uuid4().hex
            self.sessions[token] = {
                'username': username,
                'created_at': time.time(),
                'expires_at': time.time() + SESSION_DURATION
            }
            self._save_sessions()
        return {'token': token, 'username': username}, None

    def validate_session(self, token):
        with _data_lock:
            self._load_sessions()
            session = self.sessions.get(token)
            if not session:
                return None
            if time.time() > session['expires_at']:
                del self.sessions[token]
                self._save_sessions()
                return None
            return session['username']

    def logout(self, token):
        with _data_lock:
            self._load_sessions()
            if token in self.sessions:
                del self.sessions[token]
                self._save_sessions()
                return True
        return False

    def cleanup_expired(self):
        with _data_lock:
            self._load_sessions()
            now = time.time()
            expired = [t for t, s in self.sessions.items() if now > s['expires_at']]
            for t in expired:
                del self.sessions[t]
            if expired:
                self._save_sessions()

# Initialize auth system
auth = AuthSystem()

# Protected API paths (require authentication)
PROTECTED_PATHS = [
    '/api/chat',
    '/api/config',
    '/api/conversations',
    '/api/skills',
    '/api/attachments',
    '/api/balance',
    '/api/models'
]

def get_token_from_headers(headers):
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None

def require_auth(handler_func):
    def wrapper(self, *args, **kwargs):
        token = get_token_from_headers(self.headers)
        username = auth.validate_session(token) if token else None
        if not username:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Authentication required'}).encode())
            return
        kwargs['username'] = username
        return handler_func(self, *args, **kwargs)
    return wrapper

class AuthHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b'{}'
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == '/api/auth/register':
            result, error = auth.register(data.get('username'), data.get('password'))
            if error:
                self._send_json({'error': error}, 400)
            else:
                self._send_json(result, 201)
        elif path == '/api/auth/login':
            result, error = auth.login(data.get('username'), data.get('password'))
            if error:
                self._send_json({'error': error}, 401)
            else:
                self._send_json(result)
        elif path == '/api/auth/logout':
            token = get_token_from_headers(self.headers)
            if token:
                auth.logout(token)
            self._send_json({'message': 'Logged out'})
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/auth/check':
            token = get_token_from_headers(self.headers)
            username = auth.validate_session(token) if token else None
            if username:
                self._send_json({'authenticated': True, 'username': username})
            else:
                self._send_json({'authenticated': False})
        else:
            self._send_json({'error': 'Not found'}, 404)

# Note: This is a simplified server for the auth system.
# The full server.py would also include the original chat, config, conversations, skills, attachments, and static file serving.
# For the full implementation, see the repository's server.py which extends this with the original functionality.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server = http.server.HTTPServer(('', port), AuthHandler)
    print(f'Server running on port {port}')
    server.serve_forever()