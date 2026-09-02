import json
import os
import uuid
import hashlib
import hmac
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import httpx

DATA_DIR = 'data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')
ATTACHMENTS_DIR = os.path.join(DATA_DIR, 'attachments')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Simple in-memory session store
sessions = {}
session_lock = threading.Lock()

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return salt + '$' + pwd_hash

def verify_password(password, stored):
    salt, pwd_hash = stored.split('$', 1)
    return hash_password(password, salt) == stored

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_session_user(session_id):
    with session_lock:
        session = sessions.get(session_id)
        if session and session['expires'] > time.time():
            return session['username']
        return None

def create_session(username):
    session_id = str(uuid.uuid4())
    with session_lock:
        sessions[session_id] = {'username': username, 'expires': time.time() + 86400}
    return session_id

def delete_session(session_id):
    with session_lock:
        sessions.pop(session_id, None)

class ChatHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def _get_cookie(self):
        cookie = self.headers.get('Cookie', '')
        for part in cookie.split(';'):
            part = part.strip()
            if part.startswith('session='):
                return part[8:]
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Cookie')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/auth/register':
            self._handle_register()
        elif parsed.path == '/api/auth/login':
            self._handle_login()
        elif parsed.path == '/api/auth/logout':
            self._handle_logout()
        elif parsed.path == '/api/auth/me':
            self._handle_me()
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/auth/me':
            self._handle_me()
        else:
            self._send_json({'error': 'Not found'}, 404)

    def _handle_register(self):
        body = self._read_body()
        username = body.get('username', '').strip()
        password = body.get('password', '')
        if not username or not password:
            self._send_json({'error': 'Username and password required'}, 400)
            return
        if len(username) < 3 or len(password) < 6:
            self._send_json({'error': 'Username min 3 chars, password min 6 chars'}, 400)
            return
        users = load_users()
        if username in users:
            self._send_json({'error': 'Username already exists'}, 409)
            return
        users[username] = hash_password(password)
        save_users(users)
        session_id = create_session(username)
        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Set-Cookie', f'session={session_id}; HttpOnly; Path=/; Max-Age=86400')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(json.dumps({'username': username}).encode())

    def _handle_login(self):
        body = self._read_body()
        username = body.get('username', '').strip()
        password = body.get('password', '')
        users = load_users()
        stored = users.get(username)
        if not stored or not verify_password(password, stored):
            self._send_json({'error': 'Invalid credentials'}, 401)
            return
        session_id = create_session(username)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Set-Cookie', f'session={session_id}; HttpOnly; Path=/; Max-Age=86400')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(json.dumps({'username': username}).encode())

    def _handle_logout(self):
        session_id = self._get_cookie()
        if session_id:
            delete_session(session_id)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Set-Cookie', 'session=; HttpOnly; Path=/; Max-Age=0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True}).encode())

    def _handle_me(self):
        session_id = self._get_cookie()
        username = get_session_user(session_id)
        if username:
            self._send_json({'username': username})
        else:
            self._send_json({'username': None}, 401)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    server = HTTPServer((host, port), ChatHandler)
    print(f'Server running on http://{host}:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
