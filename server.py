import http.server
import json
import os
import uuid
import hashlib
import hmac
import base64
import time
from urllib.parse import urlparse, parse_qs

import httpx


DATA_DIR = 'data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')
ATTACHMENTS_DIR = os.path.join(DATA_DIR, 'attachments')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

SECRET_KEY = os.environ.get('JWT_SECRET', 'change-me-in-production')

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Initialize users file if not exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)


def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt).decode('utf-8') + ':' + base64.b64encode(pwd_hash).decode('utf-8')


def verify_password(password, stored):
    try:
        salt_b64, hash_b64 = stored.split(':')
        salt = base64.b64decode(salt_b64)
        stored_hash = base64.b64decode(hash_b64)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(stored_hash, pwd_hash)
    except Exception:
        return False


def create_jwt(user_id):
    header = base64.urlsafe_b64encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()).rstrip(b'=').decode()
    payload = base64.urlsafe_b64encode(json.dumps({'sub': user_id, 'exp': int(time.time()) + 86400 * 7}).encode()).rstrip(b'=').decode()
    signature = hmac.new(SECRET_KEY.encode(), f'{header}.{payload}'.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    return f'{header}.{payload}.{sig_b64}'


def verify_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header, payload, sig_b64 = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), f'{header}.{payload}'.encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + '=' * (4 - len(sig_b64) % 4))
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload_data = json.loads(base64.urlsafe_b64decode(payload + '=' * (4 - len(payload) % 4)))
        if payload_data.get('exp', 0) < time.time():
            return None
        return payload_data.get('sub')
    except Exception:
        return None


class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Serve login page
        if path == '/login':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            login_html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Login - Agentic Chat</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f0f0; }
.login-container { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 300px; }
h1 { margin-top: 0; }
label { display: block; margin-bottom: 0.5rem; }
input { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
button { width: 100%; padding: 0.75rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #0056b3; }
.error { color: red; margin-bottom: 1rem; }
</style>
</head>
<body>
<div class="login-container">
<h1>Login</h1>
<div id="error" class="error" style="display:none;"></div>
<form id="loginForm">
<label for="username">Username</label>
<input type="text" id="username" name="username" required>
<label for="password">Password</label>
<input type="password" id="password" name="password" required>
<button type="submit">Login</button>
</form>
<p>Don't have an account? <a href="/register">Register</a></p>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error');
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        if (response.ok) {
            window.location.href = '/';
        } else {
            const data = await response.json();
            errorDiv.textContent = data.error || 'Login failed';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.textContent = 'Network error';
        errorDiv.style.display = 'block';
    }
});
</script>
</body>
</html>'''
            self.wfile.write(login_html.encode())
            return

        # Serve register page
        if path == '/register':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            register_html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Register - Agentic Chat</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f0f0; }
.register-container { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 300px; }
h1 { margin-top: 0; }
label { display: block; margin-bottom: 0.5rem; }
input { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
button { width: 100%; padding: 0.75rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #0056b3; }
.error { color: red; margin-bottom: 1rem; }
</style>
</head>
<body>
<div class="register-container">
<h1>Register</h1>
<div id="error" class="error" style="display:none;"></div>
<form id="registerForm">
<label for="username">Username</label>
<input type="text" id="username" name="username" required>
<label for="password">Password</label>
<input type="password" id="password" name="password" required>
<button type="submit">Register</button>
</form>
<p>Already have an account? <a href="/login">Login</a></p>
</div>
<script>
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error');
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        if (response.ok) {
            window.location.href = '/login';
        } else {
            const data = await response.json();
            errorDiv.textContent = data.error || 'Registration failed';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.textContent = 'Network error';
        errorDiv.style.display = 'block';
    }
});
</script>
</body>
</html>'''
            self.wfile.write(register_html.encode())
            return

        # Check authentication for other paths
        auth = self.authenticate()
        if not auth and path != '/api/login' and path != '/api/register' and not path.startswith('/static/'):
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return

        # Continue with existing handler logic
        # For simplicity, we delegate to the original handler for static files and API
        # This is a simplified version; in production you'd merge with existing server
        if path.startswith('/api/'):
            self.send_api_response(path)
        else:
            # Serve static files from 'static' directory
            if path == '/' or path == '':
                path = '/index.html'
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        data = json.loads(body) if body else {}

        if path == '/api/register':
            self.handle_register(data)
        elif path == '/api/login':
            self.handle_login(data)
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def handle_register(self, data):
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Username and password required'}).encode())
            return

        if len(password) < 6:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Password must be at least 6 characters'}).encode())
            return

        users = load_users()
        if username in users:
            self.send_response(409)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Username already exists'}).encode())
            return

        user_id = str(uuid.uuid4())
        users[username] = {
            'id': user_id,
            'password_hash': hash_password(password)
        }
        save_users(users)

        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'message': 'User created successfully'}).encode())

    def handle_login(self, data):
        username = data.get('username', '').strip()
        password = data.get('password', '')

        users = load_users()
        if username not in users:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid credentials'}).encode())
            return

        user = users[username]
        if not verify_password(password, user['password_hash']):
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid credentials'}).encode())
            return

        token = create_jwt(user['id'])
        self.send_response(200)
        self.send_header('Set-Cookie', f'auth_token={token}; HttpOnly; Path=/; Max-Age=604800; SameSite=Lax')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'message': 'Login successful'}).encode())

    def authenticate(self):
        cookie = self.headers.get('Cookie', '')
        for part in cookie.split(';'):
            part = part.strip()
            if part.startswith('auth_token='):
                token = part[11:]
                user_id = verify_jwt(token)
                return user_id
        return None

    def send_api_response(self, path):
        # Placeholder for API responses; in production, integrate with existing server
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'API not fully implemented in auth handler'}).encode())


def run(host='0.0.0.0', port=8000):
    server = http.server.HTTPServer((host, port), AuthHandler)
    print(f'Server running on http://{host}:{port}')
    server.serve_forever()


if __name__ == '__main__':
    run()
