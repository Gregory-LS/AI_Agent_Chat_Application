import http.server
import json
import os
import uuid
import urllib.parse
import mimetypes
import threading
import io
import re
from http import HTTPStatus

import httpx

from openrouter import OpenRouterClient

HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 8000))
DATA_DIR = 'data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')
ATTACHMENTS_DIR = os.path.join(DATA_DIR, 'attachments')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'api_key': os.environ.get('OPENROUTER_API_KEY', ''), 'default_model': ''}, f)

if not os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, 'w') as f:
        json.dump([], f)


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_conversations():
    conversations = []
    for fname in os.listdir(CONVERSATIONS_DIR):
        if fname.endswith('.json'):
            with open(os.path.join(CONVERSATIONS_DIR, fname)) as f:
                conversations.append(json.load(f))
    return conversations


def save_conversation(conv):
    with open(os.path.join(CONVERSATIONS_DIR, conv['id'] + '.json'), 'w') as f:
        json.dump(conv, f, indent=2)


def load_skills():
    with open(SKILLS_FILE) as f:
        return json.load(f)


def save_skills(skills):
    with open(SKILLS_FILE, 'w') as f:
        json.dump(skills, f, indent=2)


class ChatHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress default logging

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length)

    def _parse_path(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        query = urllib.parse.parse_qs(parsed.query)
        return path, query

    def _get_client(self):
        config = load_config()
        api_key = config.get('api_key', '')
        return OpenRouterClient(api_key=api_key)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_GET(self):
        path, query = self._parse_path()

        if path == '/api/models':
            try:
                client = self._get_client()
                models = client.list_models()
                self._send_json(models)
            except Exception as e:
                self._send_json({'error': str(e)}, 500)

        elif path == '/api/balance':
            try:
                client = self._get_client()
                balance = client.check_balance()
                self._send_json(balance)
            except Exception as e:
                self._send_json({'error': str(e)}, 500)

        elif path == '/api/config':
            self._send_json(load_config())

        elif path == '/api/conversations':
            conversations = load_conversations()
            self._send_json(conversations)

        elif path.startswith('/api/conversations/') and path.endswith('/export'):
            conv_id = path.split('/')[3]
            fmt = query.get('format', ['json'])[0]
            conv_path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(conv_path):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            with open(conv_path) as f:
                conv = json.load(f)
            if fmt == 'markdown':
                md = self._conv_to_markdown(conv)
                body = md.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/markdown; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._send_json(conv)

        elif path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            conv_path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(conv_path):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            with open(conv_path) as f:
                conv = json.load(f)
            self._send_json(conv)

        elif path == '/api/skills':
            self._send_json(load_skills())

        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            skills = load_skills()
            skill = next((s for s in skills if s['id'] == skill_id), None)
            if not skill:
                self._send_json({'error': 'Skill not found'}, 404)
                return
            self._send_json(skill)

        else:
            self._serve_static()

    def _serve_static(self):
        path, _ = self._parse_path()
        if path == '' or path == '/':
            path = '/index.html'
        filepath = 'static' + path
        if not os.path.isfile(filepath):
            filepath = 'static/index.html'
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'
        try:
            with open(filepath, 'rb') as f:
                body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path, _ = self._parse_path()

        if path == '/api/logout':
            config = load_config()
            config['api_key'] = ''
            save_config(config)
            self._send_json({'status': 'ok'})

        elif path == '/api/config':
            try:
                body = json.loads(self._read_body())
                config = load_config()
                config.update(body)
                save_config(config)
                self._send_json(config)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        elif path == '/api/conversations/import':
            try:
                body = json.loads(self._read_body())
                conv = body
                if 'id' not in conv:
                    conv['id'] = str(uuid.uuid4())
                save_conversation(conv)
                self._send_json(conv, 201)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        elif path == '/api/conversations':
            try:
                body = json.loads(self._read_body())
                conv = {
                    'id': str(uuid.uuid4()),
                    'title': body.get('title', 'New conversation'),
                    'messages': body.get('messages', []),
                    'model': body.get('model', ''),
                    'created_at': __import__('datetime').datetime.now().isoformat(),
                    'updated_at': __import__('datetime').datetime.now().isoformat()
                }
                save_conversation(conv)
                self._send_json(conv, 201)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        elif path == '/api/skills':
            try:
                body = json.loads(self._read_body())
                skills = load_skills()
                skill = {
                    'id': str(uuid.uuid4()),
                    'name': body.get('name', 'New skill'),
                    'prompt': body.get('prompt', ''),
                    'builtin': body.get('builtin', False)
                }
                skills.append(skill)
                save_skills(skills)
                self._send_json(skill, 201)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        elif path == '/api/attachments':
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    import cgi
                    form = cgi.FieldStorage(
                        fp=io.BytesIO(self._read_body()),
                        headers=self.headers,
                        environ={'REQUEST_METHOD': 'POST'}
                    )
                    file_item = form['file']
                    if file_item.filename:
                        ext = os.path.splitext(file_item.filename)[1]
                        fname = str(uuid.uuid4()) + ext
                        fpath = os.path.join(ATTACHMENTS_DIR, fname)
                        with open(fpath, 'wb') as f:
                            f.write(file_item.file.read())
                        self._send_json({'filename': fname, 'original': file_item.filename}, 201)
                    else:
                        self._send_json({'error': 'No file provided'}, 400)
                else:
                    self._send_json({'error': 'Unsupported content type'}, 400)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        elif path == '/api/chat':
            try:
                body = json.loads(self._read_body())
                messages = body.get('messages', [])
                model = body.get('model', '')
                stream = body.get('stream', True)

                config = load_config()
                api_key = config.get('api_key', '')
                if not api_key:
                    self._send_json({'error': 'API key not configured. Set it in Settings.'}, 400)
                    return

                client = OpenRouterClient(api_key=api_key)

                # Check for enabled skills
                skills = load_skills()
                enabled_skills = [s for s in skills if s.get('enabled', False)]
                system_prompts = [s['prompt'] for s in enabled_skills if s.get('prompt')]

                if system_prompts:
                    system_content = '\n\n'.join(system_prompts)
                    messages.insert(0, {'role': 'system', 'content': system_content})

                if stream:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self._cors_headers()
                    self.end_headers()

                    for event in client.chat_stream(messages, model=model):
                        data = json.dumps(event)
                        line = f'data: {data}\n\n'
                        try:
                            self.wfile.write(line.encode('utf-8'))
                            self.wfile.flush()
                        except BrokenPipeError:
                            break
                else:
                    response = client.chat(messages, model=model)
                    self._send_json(response)

            except Exception as e:
                if stream:
                    line = f'data: {json.dumps({"type": "error", "content": str(e)})}\n\n'
                    try:
                        self.wfile.write(line.encode('utf-8'))
                        self.wfile.flush()
                    except BrokenPipeError:
                        pass
                else:
                    self._send_json({'error': str(e)}, 500)

        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        path, _ = self._parse_path()

        if path == '/api/config':
            try:
                body = json.loads(self._read_body())
                config = load_config()
                config.update(body)
                save_config(config)
                self._send_json(config)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PATCH(self):
        path, _ = self._parse_path()

        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            conv_path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(conv_path):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            try:
                body = json.loads(self._read_body())
                with open(conv_path) as f:
                    conv = json.load(f)
                conv.update(body)
                conv['updated_at'] = __import__('datetime').datetime.now().isoformat()
                save_conversation(conv)
                self._send_json(conv)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            skills = load_skills()
            skill = next((s for s in skills if s['id'] == skill_id), None)
            if not skill:
                self._send_json({'error': 'Skill not found'}, 404)
                return
            try:
                body = json.loads(self._read_body())
                skill.update(body)
                save_skills(skills)
                self._send_json(skill)
            except Exception as e:
                self._send_json({'error': str(e)}, 400)

        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        path, _ = self._parse_path()

        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            conv_path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(conv_path):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            os.remove(conv_path)
            self._send_json({'status': 'deleted'})

        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            skills = load_skills()
            skill = next((s for s in skills if s['id'] == skill_id), None)
            if not skill:
                self._send_json({'error': 'Skill not found'}, 404)
                return
            skills = [s for s in skills if s['id'] != skill_id]
            save_skills(skills)
            self._send_json({'status': 'deleted'})

        else:
            self.send_response(404)
            self.end_headers()

    def _conv_to_markdown(self, conv):
        md = f"# {conv.get('title', 'Conversation')}\n\n"
        for msg in conv.get('messages', []):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            md += f"**{role.capitalize()}:** {content}\n\n"
        return md


def run():
    server = http.server.HTTPServer((HOST, PORT), ChatHandler)
    print(f'Server running on http://{HOST}:{PORT}')
    server.serve_forever()


if __name__ == '__main__':
    run()
