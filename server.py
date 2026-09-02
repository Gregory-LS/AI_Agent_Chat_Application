import os
import json
import hashlib
import hmac
import time
import uuid
import shutil
import mimetypes
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import httpx

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
DATA_DIR = Path('data')
CONFIG_FILE = DATA_DIR / 'config.json'
CONVERSATIONS_DIR = DATA_DIR / 'conversations'
SKILLS_FILE = DATA_DIR / 'skills.json'
ATTACHMENTS_DIR = DATA_DIR / 'attachments'
USERS_FILE = DATA_DIR / 'users.json'
JWT_SECRET = os.getenv('JWT_SECRET', 'change-this-secret-in-production')

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)

# Load or create users file
if not USERS_FILE.exists():
    USERS_FILE.write_text('{}')


def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return salt, hashed


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    _, computed = hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)


def create_jwt(user_id: str) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {'user_id': user_id, 'iat': int(time.time()), 'exp': int(time.time()) + 86400}
    header_b64 = urllib.parse.quote(json.dumps(header, separators=(',', ':')).encode('utf-8'), safe='').rstrip('=')
    payload_b64 = urllib.parse.quote(json.dumps(payload, separators=(',', ':')).encode('utf-8'), safe='').rstrip('=')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), f'{header_b64}.{payload_b64}'.encode('utf-8'), hashlib.sha256).hexdigest()
    return f'{header_b64}.{payload_b64}.{signature}'


def verify_jwt(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), f'{header_b64}.{payload_b64}'.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return None
        payload = json.loads(urllib.parse.unquote(payload_b64))
        if payload['exp'] < time.time():
            return None
        return payload
    except Exception:
        return None


def get_user_from_cookie(handler) -> str:
    cookie = handler.headers.get('Cookie', '')
    for part in cookie.split(';'):
        part = part.strip()
        if part.startswith('session='):
            token = part[8:]
            payload = verify_jwt(token)
            if payload:
                return payload['user_id']
    return None


class ChatHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='static', **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/models':
            self._handle_models()
        elif path == '/api/balance':
            self._handle_balance()
        elif path == '/api/config':
            self._handle_get_config()
        elif path == '/api/conversations':
            self._handle_list_conversations()
        elif path.startswith('/api/conversations/') and '/export' in path:
            conv_id = path.split('/')[3]
            self._handle_export_conversation(conv_id, query.get('format', ['json'])[0])
        elif path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            if self.path.endswith('/export'):
                self._handle_export_conversation(conv_id, query.get('format', ['json'])[0])
            else:
                self._handle_get_conversation(conv_id)
        elif path == '/api/skills':
            self._handle_list_skills()
        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            self._handle_get_skill(skill_id)
        elif path == '/api/auth/me':
            self._handle_auth_me()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/chat':
            self._handle_chat()
        elif path == '/api/conversations':
            self._handle_create_conversation()
        elif path == '/api/conversations/import':
            self._handle_import_conversation()
        elif path == '/api/skills':
            self._handle_create_skill()
        elif path == '/api/attachments':
            self._handle_upload_attachment()
        elif path == '/api/auth/register':
            self._handle_register()
        elif path == '/api/auth/login':
            self._handle_login()
        elif path == '/api/auth/logout':
            self._handle_logout()
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/config':
            self._handle_update_config()
        else:
            self.send_error(404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            self._handle_update_conversation(conv_id)
        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            self._handle_update_skill(skill_id)
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            self._handle_delete_conversation(conv_id)
        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            self._handle_delete_skill(skill_id)
        else:
            self.send_error(404)

    def _require_auth(self) -> str:
        user_id = get_user_from_cookie(self)
        if not user_id:
            self.send_json({'error': 'Authentication required'}, 401)
            return None
        return user_id

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return b''
        return self.rfile.read(length)

    def _handle_models(self):
        try:
            api_key = self._get_api_key()
            if not api_key:
                self.send_json({'error': 'API key not configured'}, 400)
                return
            client = httpx.Client(timeout=30)
            resp = client.get(
                'https://openrouter.ai/api/v1/models',
                headers={'Authorization': f'Bearer {api_key}'}
            )
            if resp.status_code == 200:
                models = resp.json()
                self.send_json(models)
            else:
                self.send_json({'error': 'Failed to fetch models'}, resp.status_code)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_balance(self):
        try:
            api_key = self._get_api_key()
            if not api_key:
                self.send_json({'error': 'API key not configured'}, 400)
                return
            client = httpx.Client(timeout=30)
            resp = client.get(
                'https://openrouter.ai/api/v1/auth/key',
                headers={'Authorization': f'Bearer {api_key}'}
            )
            if resp.status_code == 200:
                data = resp.json()
                credits = data.get('credits', 0)
                usage = data.get('usage', None)
                self.send_json({'credits': credits, 'usage': usage, 'total': credits})
            else:
                self.send_json({'error': 'Failed to fetch balance'}, resp.status_code)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _get_api_key(self):
        # Check environment variable first, then config file
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            return api_key
        if CONFIG_FILE.exists():
            try:
                config = json.loads(CONFIG_FILE.read_text())
                return config.get('api_key', '')
            except:
                pass
        return ''

    def _handle_get_config(self):
        config = {}
        if CONFIG_FILE.exists():
            try:
                config = json.loads(CONFIG_FILE.read_text())
            except:
                pass
        self.send_json(config)

    def _handle_update_config(self):
        body = self.read_body()
        try:
            new_config = json.loads(body)
            # Merge with existing config
            existing = {}
            if CONFIG_FILE.exists():
                try:
                    existing = json.loads(CONFIG_FILE.read_text())
                except:
                    pass
            existing.update(new_config)
            CONFIG_FILE.write_text(json.dumps(existing, indent=2))
            self.send_json({'status': 'ok'})
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_list_conversations(self):
        user_id = get_user_from_cookie(self)
        conversations = []
        if CONVERSATIONS_DIR.exists():
            for f in CONVERSATIONS_DIR.iterdir():
                if f.suffix == '.json':
                    try:
                        conv = json.loads(f.read_text())
                        # Filter by user if authenticated
                        if user_id and conv.get('user_id') and conv['user_id'] != user_id:
                            continue
                        conversations.append(conv)
                    except:
                        pass
        self.send_json(conversations)

    def _handle_create_conversation(self):
        user_id = get_user_from_cookie(self)
        body = self.read_body()
        try:
            data = json.loads(body)
            conv_id = str(uuid.uuid4())
            conv = {
                'id': conv_id,
                'title': data.get('title', 'New conversation'),
                'messages': [],
                'created_at': time.time(),
                'updated_at': time.time(),
                'model': data.get('model', 'openai/gpt-4o-mini'),
                'user_id': user_id  # Associate with user if logged in
            }
            conv_file = CONVERSATIONS_DIR / f'{conv_id}.json'
            conv_file.write_text(json.dumps(conv, indent=2))
            self.send_json(conv, 201)
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_get_conversation(self, conv_id):
        conv_file = CONVERSATIONS_DIR / f'{conv_id}.json'
        if not conv_file.exists():
            self.send_json({'error': 'Conversation not found'}, 404)
            return
        try:
            conv = json.loads(conv_file.read_text())
            self.send_json(conv)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_update_conversation(self, conv_id):
        body = self.read_body()
        conv_file = CONVERSATIONS_DIR / f'{conv_id}.json'
        if not conv_file.exists():
            self.send_json({'error': 'Conversation not found'}, 404)
            return
        try:
            existing = json.loads(conv_file.read_text())
            updates = json.loads(body)
            existing.update(updates)
            existing['updated_at'] = time.time()
            conv_file.write_text(json.dumps(existing, indent=2))
            self.send_json(existing)
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_delete_conversation(self, conv_id):
        conv_file = CONVERSATIONS_DIR / f'{conv_id}.json'
        if conv_file.exists():
            conv_file.unlink()
            self.send_json({'status': 'deleted'})
        else:
            self.send_json({'error': 'Conversation not found'}, 404)

    def _handle_export_conversation(self, conv_id, fmt):
        conv_file = CONVERSATIONS_DIR / f'{conv_id}.json'
        if not conv_file.exists():
            self.send_json({'error': 'Conversation not found'}, 404)
            return
        try:
            conv = json.loads(conv_file.read_text())
            if fmt == 'markdown':
                lines = [f'# {conv["title"]}\n']
                for msg in conv.get('messages', []):
                    role = msg.get('role', 'unknown').capitalize()
                    content = msg.get('content', '')
                    lines.append(f'**{role}:** {content}\n')
                markdown = '\n'.join(lines)
                self.send_response(200)
                self.send_header('Content-Type', 'text/markdown')
                self.send_header('Content-Disposition', f'attachment; filename="{conv_id}.md"')
                self.end_headers()
                self.wfile.write(markdown.encode('utf-8'))
            else:
                self.send_json(conv)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_import_conversation(self):
        body = self.read_body()
        try:
            data = json.loads(body)
            conv_id = data.get('id', str(uuid.uuid4()))
            conv = {
                'id': conv_id,
                'title': data.get('title', 'Imported conversation'),
                'messages': data.get('messages', []),
                'created_at': data.get('created_at', time.time()),
                'updated_at': time.time(),
                'model': data.get('model', 'openai/gpt-4o-mini')
            }
            conv_file = CONVERSATIONS_DIR / f'{conv_id}.json'
            conv_file.write_text(json.dumps(conv, indent=2))
            self.send_json(conv, 201)
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_list_skills(self):
        skills = []
        if SKILLS_FILE.exists():
            try:
                skills = json.loads(SKILLS_FILE.read_text())
            except:
                pass
        self.send_json(skills)

    def _handle_create_skill(self):
        body = self.read_body()
        try:
            data = json.loads(body)
            skill_id = str(uuid.uuid4())
            skill = {
                'id': skill_id,
                'name': data.get('name', 'New skill'),
                'prompt': data.get('prompt', ''),
                'enabled': data.get('enabled', True),
                'created_at': time.time()
            }
            existing = []
            if SKILLS_FILE.exists():
                try:
                    existing = json.loads(SKILLS_FILE.read_text())
                except:
                    pass
            existing.append(skill)
            SKILLS_FILE.write_text(json.dumps(existing, indent=2))
            self.send_json(skill, 201)
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_get_skill(self, skill_id):
        if not SKILLS_FILE.exists():
            self.send_json({'error': 'Skill not found'}, 404)
            return
        try:
            skills = json.loads(SKILLS_FILE.read_text())
            for skill in skills:
                if skill['id'] == skill_id:
                    self.send_json(skill)
                    return
            self.send_json({'error': 'Skill not found'}, 404)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_update_skill(self, skill_id):
        body = self.read_body()
        if not SKILLS_FILE.exists():
            self.send_json({'error': 'Skill not found'}, 404)
            return
        try:
            skills = json.loads(SKILLS_FILE.read_text())
            updates = json.loads(body)
            for i, skill in enumerate(skills):
                if skill['id'] == skill_id:
                    skills[i].update(updates)
                    SKILLS_FILE.write_text(json.dumps(skills, indent=2))
                    self.send_json(skills[i])
                    return
            self.send_json({'error': 'Skill not found'}, 404)
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_delete_skill(self, skill_id):
        if not SKILLS_FILE.exists():
            self.send_json({'error': 'Skill not found'}, 404)
            return
        try:
            skills = json.loads(SKILLS_FILE.read_text())
            new_skills = [s for s in skills if s['id'] != skill_id]
            if len(new_skills) == len(skills):
                self.send_json({'error': 'Skill not found'}, 404)
                return
            SKILLS_FILE.write_text(json.dumps(new_skills, indent=2))
            self.send_json({'status': 'deleted'})
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_upload_attachment(self):
        content_type = self.headers.get('Content-Type', '')
        body = self.read_body()
        try:
            import cgi
            form_data = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
            )
            file_item = form_data['file']
            if file_item.filename:
                ext = Path(file_item.filename).suffix or '.bin'
                attachment_id = str(uuid.uuid4()) + ext
                file_path = ATTACHMENTS_DIR / attachment_id
                with open(file_path, 'wb') as f:
                    f.write(file_item.file.read())
                self.send_json({
                    'id': attachment_id,
                    'filename': file_item.filename,
                    'url': f'/api/attachments/{attachment_id}'
                }, 201)
            else:
                self.send_json({'error': 'No file provided'}, 400)
        except Exception as e:
            self.send_json({'error': str(e)}, 400)

    def _handle_chat(self):
        body = self.read_body()
        try:
            data = json.loads(body)
            messages = data.get('messages', [])
            model = data.get('model', 'openai/gpt-4o-mini')
            stream = data.get('stream', True)
            api_key = self._get_api_key()
            if not api_key:
                self.send_json({'error': 'API key not configured'}, 400)
                return

            client = httpx.Client(timeout=120)
            payload = {
                'model': model,
                'messages': messages,
                'stream': stream
            }
            resp = client.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'http://localhost:8000',
                    'X-Title': 'Agentic Chat'
                },
                json=payload
            )
            if stream:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                for chunk in resp.iter_lines():
                    if chunk:
                        self.wfile.write(f'data: {chunk}\n\n'.encode('utf-8'))
                        self.wfile.flush()
                self.wfile.write(b'data: [DONE]\n\n')
                self.wfile.flush()
            else:
                data = resp.json()
                self.send_json(data)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_register(self):
        body = self.read_body()
        try:
            data = json.loads(body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            if not username or not password:
                self.send_json({'error': 'Username and password are required'}, 400)
                return
            if len(password) < 6:
                self.send_json({'error': 'Password must be at least 6 characters'}, 400)
                return
            users = json.loads(USERS_FILE.read_text())
            if username in users:
                self.send_json({'error': 'Username already exists'}, 409)
                return
            salt, hashed = hash_password(password)
            users[username] = {'salt': salt, 'hash': hashed}
            USERS_FILE.write_text(json.dumps(users, indent=2))
            # Create JWT and set cookie
            token = create_jwt(username)
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'session={token}; HttpOnly; Path=/; Max-Age=86400; SameSite=Lax')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'user': username}).encode('utf-8'))
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_login(self):
        body = self.read_body()
        try:
            data = json.loads(body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            if not username or not password:
                self.send_json({'error': 'Username and password are required'}, 400)
                return
            users = json.loads(USERS_FILE.read_text())
            if username not in users:
                self.send_json({'error': 'Invalid credentials'}, 401)
                return
            user_data = users[username]
            if not verify_password(password, user_data['salt'], user_data['hash']):
                self.send_json({'error': 'Invalid credentials'}, 401)
                return
            token = create_jwt(username)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'session={token}; HttpOnly; Path=/; Max-Age=86400; SameSite=Lax')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'user': username}).encode('utf-8'))
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def _handle_logout(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Set-Cookie', 'session=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))

    def _handle_auth_me(self):
        user_id = get_user_from_cookie(self)
        if user_id:
            self.send_json({'user': user_id})
        else:
            self.send_json({'user': None})

    def log_message(self, format, *args):
        # Suppress default logging for cleaner output
        pass


def run_server():
    server = HTTPServer((HOST, PORT), ChatHandler)
    print(f'Server running on http://{HOST}:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()


if __name__ == '__main__':
    run_server()
