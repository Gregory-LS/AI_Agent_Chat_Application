#!/usr/bin/env python3
"""
Agentic Chat — Python backend
Uses stdlib http.server + httpx for OpenRouter API.
"""

import os
import json
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
DATA_DIR = Path('data')
CONFIG_FILE = DATA_DIR / 'config.json'
CONVERSATIONS_DIR = DATA_DIR / 'conversations'
SKILLS_FILE = DATA_DIR / 'skills.json'
ATTACHMENTS_DIR = DATA_DIR / 'attachments'

OPENROUTER_API_BASE = 'https://openrouter.ai/api/v1'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)
if not SKILLS_FILE.exists():
    SKILLS_FILE.write_text('[]')
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(json.dumps({
        'apiKey': os.getenv('OPENROUTER_API_KEY', ''),
        'defaultModel': '',
        'theme': 'light'
    }))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config():
    return json.loads(CONFIG_FILE.read_text())

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, indent=2))

def load_conversations():
    convs = []
    for f in CONVERSATIONS_DIR.iterdir():
        if f.suffix == '.json':
            convs.append(json.loads(f.read_text()))
    # Sort by updated_at descending
    convs.sort(key=lambda c: c.get('updated_at', ''), reverse=True)
    return convs

def load_conversation(conv_id):
    path = CONVERSATIONS_DIR / f'{conv_id}.json'
    if path.exists():
        return json.loads(path.read_text())
    return None

def save_conversation(data):
    conv_id = data.get('id')
    if not conv_id:
        import uuid
        conv_id = str(uuid.uuid4())
        data['id'] = conv_id
    path = CONVERSATIONS_DIR / f'{conv_id}.json'
    path.write_text(json.dumps(data, indent=2))
    return data

def delete_conversation(conv_id):
    path = CONVERSATIONS_DIR / f'{conv_id}.json'
    if path.exists():
        path.unlink()
        return True
    return False

def load_skills():
    return json.loads(SKILLS_FILE.read_text())

def save_skills(skills):
    SKILLS_FILE.write_text(json.dumps(skills, indent=2))

# ---------------------------------------------------------------------------
# Request Handler
# ---------------------------------------------------------------------------

class ChatHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status, message):
        self._send_json({'error': message}, status)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            return self.rfile.read(length)
        return b''

    def _parse_path(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        query = urllib.parse.parse_qs(parsed.query)
        return path, query

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        path, query = self._parse_path()

        if path == '/api/config':
            self._send_json(load_config())

        elif path == '/api/models':
            config = load_config()
            api_key = config.get('apiKey') or os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                self._send_error(401, 'API key not configured')
                return
            try:
                resp = httpx.get(
                    f'{OPENROUTER_API_BASE}/models',
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                self._send_json(data.get('data', []))
            except Exception as e:
                self._send_error(502, f'Failed to fetch models: {e}')

        elif path == '/api/balance':
            config = load_config()
            api_key = config.get('apiKey') or os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                self._send_error(401, 'API key not configured')
                return
            try:
                resp = httpx.get(
                    f'{OPENROUTER_API_BASE}/auth/key',
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                self._send_json({
                    'credits': data.get('credits', 0),
                    'usage': data.get('usage', 0),
                    'total': data.get('total', 0)
                })
            except Exception as e:
                self._send_error(502, f'Failed to fetch balance: {e}')

        elif path == '/api/conversations':
            self._send_json(load_conversations())

        elif path.startswith('/api/conversations/') and path.endswith('/export'):
            # Extract conversation ID
            parts = path.split('/')
            if len(parts) >= 4:
                conv_id = parts[3]
                fmt = query.get('format', ['json'])[0]
                conv = load_conversation(conv_id)
                if not conv:
                    self._send_error(404, 'Conversation not found')
                    return
                if fmt == 'markdown':
                    md = f"# {conv.get('title', 'Conversation')}\n\n"
                    for msg in conv.get('messages', []):
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        md += f"**{role.capitalize()}:** {content}\n\n"
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/markdown')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(md.encode())
                else:
                    self._send_json(conv)
            else:
                self._send_error(400, 'Invalid path')

        elif path.startswith('/api/conversations/'):
            parts = path.split('/')
            if len(parts) >= 4:
                conv_id = parts[3]
                conv = load_conversation(conv_id)
                if conv:
                    self._send_json(conv)
                else:
                    self._send_error(404, 'Conversation not found')
            else:
                self._send_error(400, 'Invalid path')

        elif path == '/api/skills':
            self._send_json(load_skills())

        elif path.startswith('/api/skills/'):
            parts = path.split('/')
            if len(parts) >= 4:
                skill_id = parts[3]
                skills = load_skills()
                skill = next((s for s in skills if s.get('id') == skill_id), None)
                if skill:
                    self._send_json(skill)
                else:
                    self._send_error(404, 'Skill not found')
            else:
                self._send_error(400, 'Invalid path')

        else:
            # Serve static files
            self._serve_static()

    def do_PUT(self):
        path, _ = self._parse_path()
        body = self._read_body()

        if path == '/api/config':
            try:
                data = json.loads(body)
                save_config(data)
                self._send_json(data)
            except json.JSONDecodeError:
                self._send_error(400, 'Invalid JSON')

        elif path.startswith('/api/conversations/'):
            parts = path.split('/')
            if len(parts) >= 4:
                conv_id = parts[3]
                try:
                    data = json.loads(body)
                    data['id'] = conv_id
                    save_conversation(data)
                    self._send_json(data)
                except json.JSONDecodeError:
                    self._send_error(400, 'Invalid JSON')
            else:
                self._send_error(400, 'Invalid path')

        elif path.startswith('/api/skills/'):
            parts = path.split('/')
            if len(parts) >= 4:
                skill_id = parts[3]
                try:
                    data = json.loads(body)
                    data['id'] = skill_id
                    skills = load_skills()
                    idx = next((i for i, s in enumerate(skills) if s.get('id') == skill_id), None)
                    if idx is not None:
                        skills[idx] = data
                    else:
                        skills.append(data)
                    save_skills(skills)
                    self._send_json(data)
                except json.JSONDecodeError:
                    self._send_error(400, 'Invalid JSON')
            else:
                self._send_error(400, 'Invalid path')

        else:
            self._send_error(404, 'Not found')

    def do_POST(self):
        path, _ = self._parse_path()
        body = self._read_body()

        if path == '/api/conversations':
            try:
                data = json.loads(body) if body else {}
                import uuid
                data['id'] = str(uuid.uuid4())
                data['created_at'] = data.get('created_at', '')
                data['updated_at'] = data.get('updated_at', '')
                data['messages'] = data.get('messages', [])
                save_conversation(data)
                self._send_json(data, 201)
            except json.JSONDecodeError:
                self._send_error(400, 'Invalid JSON')

        elif path == '/api/conversations/import':
            try:
                data = json.loads(body)
                if 'id' not in data:
                    import uuid
                    data['id'] = str(uuid.uuid4())
                save_conversation(data)
                self._send_json(data, 201)
            except json.JSONDecodeError:
                self._send_error(400, 'Invalid JSON')

        elif path == '/api/skills':
            try:
                data = json.loads(body) if body else {}
                import uuid
                data['id'] = str(uuid.uuid4())
                skills = load_skills()
                skills.append(data)
                save_skills(skills)
                self._send_json(data, 201)
            except json.JSONDecodeError:
                self._send_error(400, 'Invalid JSON')

        elif path == '/api/attachments':
            # Handle file upload
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in content_type:
                # Simple file save
                import uuid
                filename = f'{uuid.uuid4()}'
                filepath = ATTACHMENTS_DIR / filename
                filepath.write_bytes(body)
                self._send_json({'id': filename, 'url': f'/data/attachments/{filename}'}, 201)
            else:
                self._send_error(400, 'Expected multipart/form-data')

        elif path == '/api/chat':
            # Proxy chat to OpenRouter with streaming
            config = load_config()
            api_key = config.get('apiKey') or os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                self._send_error(401, 'API key not configured')
                return
            try:
                data = json.loads(body)
                model = data.get('model', config.get('defaultModel', 'openai/gpt-4o'))
                messages = data.get('messages', [])
                stream = data.get('stream', True)

                # Send SSE response
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                with httpx.Client(timeout=120) as client:
                    with client.stream(
                        'POST',
                        f'{OPENROUTER_API_BASE}/chat/completions',
                        headers={
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json',
                            'HTTP-Referer': 'http://localhost:8000',
                            'X-Title': 'Agentic Chat'
                        },
                        json={
                            'model': model,
                            'messages': messages,
                            'stream': stream
                        }
                    ) as resp:
                        if resp.status_code != 200:
                            error_body = resp.read().decode()
                            self.wfile.write(f'event: error\ndata: {json.dumps({"error": error_body})}\n\n'.encode())
                            return

                        for chunk in resp.iter_lines():
                            if chunk:
                                if chunk.startswith('data: '):
                                    chunk_data = chunk[6:]
                                    if chunk_data.strip() == '[DONE]':
                                        self.wfile.write('event: done\ndata: {}\n\n'.encode())
                                    else:
                                        try:
                                            parsed = json.loads(chunk_data)
                                            delta = parsed.get('choices', [{}])[0].get('delta', {})
                                            content = delta.get('content', '')
                                            if content:
                                                self.wfile.write(f'event: chunk\ndata: {json.dumps({"content": content})}\n\n'.encode())
                                        except json.JSONDecodeError:
                                            pass
                        self.wfile.write('event: done\ndata: {}\n\n'.encode())
            except json.JSONDecodeError:
                self._send_error(400, 'Invalid JSON')
            except Exception as e:
                self._send_error(502, f'Chat error: {e}')

        else:
            self._send_error(404, 'Not found')

    def do_PATCH(self):
        path, _ = self._parse_path()
        body = self._read_body()

        if path.startswith('/api/conversations/'):
            parts = path.split('/')
            if len(parts) >= 4:
                conv_id = parts[3]
                try:
                    updates = json.loads(body)
                    conv = load_conversation(conv_id)
                    if not conv:
                        self._send_error(404, 'Conversation not found')
                        return
                    conv.update(updates)
                    save_conversation(conv)
                    self._send_json(conv)
                except json.JSONDecodeError:
                    self._send_error(400, 'Invalid JSON')
            else:
                self._send_error(400, 'Invalid path')

        elif path.startswith('/api/skills/'):
            parts = path.split('/')
            if len(parts) >= 4:
                skill_id = parts[3]
                try:
                    updates = json.loads(body)
                    skills = load_skills()
                    idx = next((i for i, s in enumerate(skills) if s.get('id') == skill_id), None)
                    if idx is not None:
                        skills[idx].update(updates)
                        save_skills(skills)
                        self._send_json(skills[idx])
                    else:
                        self._send_error(404, 'Skill not found')
                except json.JSONDecodeError:
                    self._send_error(400, 'Invalid JSON')
            else:
                self._send_error(400, 'Invalid path')

        else:
            self._send_error(404, 'Not found')

    def do_DELETE(self):
        path, _ = self._parse_path()

        if path.startswith('/api/conversations/'):
            parts = path.split('/')
            if len(parts) >= 4:
                conv_id = parts[3]
                if delete_conversation(conv_id):
                    self._send_json({'status': 'deleted'})
                else:
                    self._send_error(404, 'Conversation not found')
            else:
                self._send_error(400, 'Invalid path')

        elif path.startswith('/api/skills/'):
            parts = path.split('/')
            if len(parts) >= 4:
                skill_id = parts[3]
                skills = load_skills()
                new_skills = [s for s in skills if s.get('id') != skill_id]
                if len(new_skills) < len(skills):
                    save_skills(new_skills)
                    self._send_json({'status': 'deleted'})
                else:
                    self._send_error(404, 'Skill not found')
            else:
                self._send_error(400, 'Invalid path')

        else:
            self._send_error(404, 'Not found')

    def _serve_static(self):
        path = self.path
        if path == '/' or path == '':
            path = '/static/index.html'
        elif path.startswith('/static/'):
            pass
        else:
            path = '/static' + path

        # Remove leading slash
        file_path = path.lstrip('/')
        full_path = Path(file_path)

        if full_path.exists() and full_path.is_file():
            content_type, _ = mimetypes.guess_type(str(full_path))
            if content_type is None:
                content_type = 'application/octet-stream'
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(full_path.read_bytes())
        else:
            self._send_error(404, 'File not found')

    def log_message(self, format, *args):
        # Suppress default logging
        pass

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    server = HTTPServer((HOST, PORT), ChatHandler)
    print(f'Server running on http://{HOST}:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()

if __name__ == '__main__':
    main()
