import json
import os
import uuid
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

import httpx

from openrouter import OpenRouterClient

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))

DATA_DIR = 'data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')
ATTACHMENTS_DIR = os.path.join(DATA_DIR, 'attachments')

for d in [DATA_DIR, CONVERSATIONS_DIR, ATTACHMENTS_DIR]:
    os.makedirs(d, exist_ok=True)

if not os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, 'w') as f:
        json.dump([], f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_api_key():
    config = load_config()
    return config.get('api_key') or os.getenv('OPENROUTER_API_KEY', '')

def get_client():
    return OpenRouterClient(api_key=get_api_key())

def parse_path(path):
    parsed = urllib.parse.urlparse(path)
    parts = parsed.path.strip('/').split('/')
    return parts, parsed.query

class ChatHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parts, query = parse_path(self.path)
        if self.path == '/api/models':
            self.handle_get_models()
        elif self.path == '/api/balance':
            self.handle_get_balance()
        elif self.path == '/api/config':
            self.handle_get_config()
        elif self.path == '/api/conversations':
            self.handle_list_conversations()
        elif len(parts) == 3 and parts[0] == 'api' and parts[1] == 'conversations':
            conv_id = parts[2]
            if 'export' in self.path:
                self.handle_export_conversation(conv_id, query)
            else:
                self.handle_get_conversation(conv_id)
        elif self.path == '/api/skills':
            self.handle_list_skills()
        elif len(parts) == 3 and parts[0] == 'api' and parts[1] == 'skills':
            self.handle_get_skill(parts[2])
        else:
            self.serve_static()

    def do_POST(self):
        parts, query = parse_path(self.path)
        if self.path == '/api/chat':
            self.handle_chat()
        elif self.path == '/api/conversations':
            self.handle_create_conversation()
        elif self.path == '/api/conversations/import':
            self.handle_import_conversation()
        elif self.path == '/api/skills':
            self.handle_create_skill()
        elif self.path == '/api/attachments':
            self.handle_upload_attachment()
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path == '/api/config':
            self.handle_update_config()
        else:
            self.send_error(404)

    def do_PATCH(self):
        parts, query = parse_path(self.path)
        if len(parts) == 3 and parts[0] == 'api' and parts[1] == 'conversations':
            self.handle_update_conversation(parts[2])
        elif len(parts) == 3 and parts[0] == 'api' and parts[1] == 'skills':
            self.handle_update_skill(parts[2])
        else:
            self.send_error(404)

    def do_DELETE(self):
        parts, query = parse_path(self.path)
        if len(parts) == 3 and parts[0] == 'api' and parts[1] == 'conversations':
            self.handle_delete_conversation(parts[2])
        elif len(parts) == 3 and parts[0] == 'api' and parts[1] == 'skills':
            self.handle_delete_skill(parts[2])
        else:
            self.send_error(404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            return json.loads(self.rfile.read(content_length))
        return {}

    def handle_get_models(self):
        try:
            client = get_client()
            models = client.get_models()
            self.send_json(models)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def handle_get_balance(self):
        try:
            client = get_client()
            balance = client.get_balance()
            self.send_json(balance)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def handle_get_config(self):
        config = load_config()
        self.send_json(config)

    def handle_update_config(self):
        body = self.read_body()
        config = load_config()
        config.update(body)
        save_config(config)
        self.send_json(config)

    def handle_list_conversations(self):
        conversations = []
        if os.path.exists(CONVERSATIONS_DIR):
            for fname in os.listdir(CONVERSATIONS_DIR):
                if fname.endswith('.json'):
                    with open(os.path.join(CONVERSATIONS_DIR, fname)) as f:
                        conversations.append(json.load(f))
        conversations.sort(key=lambda c: c.get('updated_at', ''), reverse=True)
        self.send_json(conversations)

    def handle_create_conversation(self):
        body = self.read_body()
        conv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        conversation = {
            'id': conv_id,
            'title': body.get('title', 'New conversation'),
            'model': body.get('model', ''),
            'messages': [],
            'created_at': now,
            'updated_at': now
        }
        with open(os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json'), 'w') as f:
            json.dump(conversation, f)
        self.send_json(conversation, 201)

    def handle_get_conversation(self, conv_id):
        path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
        if not os.path.exists(path):
            self.send_json({'error': 'Conversation not found'}, 404)
            return
        with open(path) as f:
            self.send_json(json.load(f))

    def handle_update_conversation(self, conv_id):
        path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
        if not os.path.exists(path):
            self.send_json({'error': 'Conversation not found'}, 404)
            return
        body = self.read_body()
        with open(path) as f:
            conversation = json.load(f)
        conversation.update(body)
        conversation['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        with open(path, 'w') as f:
            json.dump(conversation, f)
        self.send_json(conversation)

    def handle_delete_conversation(self, conv_id):
        path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
        if os.path.exists(path):
            os.remove(path)
        self.send_json({'ok': True})

    def handle_export_conversation(self, conv_id, query):
        path = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
        if not os.path.exists(path):
            self.send_json({'error': 'Conversation not found'}, 404)
            return
        with open(path) as f:
            conversation = json.load(f)
        fmt = urllib.parse.parse_qs(query).get('format', ['json'])[0]
        if fmt == 'markdown':
            lines = [f'# {conversation.get("title", "Conversation")}\n']
            for msg in conversation.get('messages', []):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                lines.append(f'**{role}**: {content}\n')
            text = '\n'.join(lines)
            self.send_response(200)
            self.send_header('Content-Type', 'text/markdown')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(text.encode())
        else:
            self.send_json(conversation)

    def handle_import_conversation(self):
        body = self.read_body()
        conv_id = body.get('id', str(uuid.uuid4()))
        now = datetime.utcnow().isoformat() + 'Z'
        conversation = {
            'id': conv_id,
            'title': body.get('title', 'Imported conversation'),
            'model': body.get('model', ''),
            'messages': body.get('messages', []),
            'created_at': body.get('created_at', now),
            'updated_at': now
        }
        with open(os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json'), 'w') as f:
            json.dump(conversation, f)
        self.send_json(conversation, 201)

    def handle_list_skills(self):
        if os.path.exists(SKILLS_FILE):
            with open(SKILLS_FILE) as f:
                skills = json.load(f)
        else:
            skills = []
        self.send_json(skills)

    def handle_create_skill(self):
        body = self.read_body()
        skills = []
        if os.path.exists(SKILLS_FILE):
            with open(SKILLS_FILE) as f:
                skills = json.load(f)
        skill_id = str(uuid.uuid4())
        skill = {
            'id': skill_id,
            'name': body.get('name', 'New skill'),
            'prompt': body.get('prompt', ''),
            'enabled': body.get('enabled', True)
        }
        skills.append(skill)
        with open(SKILLS_FILE, 'w') as f:
            json.dump(skills, f)
        self.send_json(skill, 201)

    def handle_get_skill(self, skill_id):
        if os.path.exists(SKILLS_FILE):
            with open(SKILLS_FILE) as f:
                skills = json.load(f)
            for skill in skills:
                if skill['id'] == skill_id:
                    self.send_json(skill)
                    return
        self.send_json({'error': 'Skill not found'}, 404)

    def handle_update_skill(self, skill_id):
        body = self.read_body()
        if os.path.exists(SKILLS_FILE):
            with open(SKILLS_FILE) as f:
                skills = json.load(f)
            for skill in skills:
                if skill['id'] == skill_id:
                    skill.update(body)
                    with open(SKILLS_FILE, 'w') as f:
                        json.dump(skills, f)
                    self.send_json(skill)
                    return
        self.send_json({'error': 'Skill not found'}, 404)

    def handle_delete_skill(self, skill_id):
        if os.path.exists(SKILLS_FILE):
            with open(SKILLS_FILE) as f:
                skills = json.load(f)
            skills = [s for s in skills if s['id'] != skill_id]
            with open(SKILLS_FILE, 'w') as f:
                json.dump(skills, f)
        self.send_json({'ok': True})

    def handle_upload_attachment(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        multipart_data = urllib.parse.parse_qs(body.decode())
        # Simplified: assume file data in 'file' field
        file_data = multipart_data.get('file', [b''])[0]
        if isinstance(file_data, bytes):
            ext = '.bin'
            fname = f'{uuid.uuid4()}{ext}'
            path = os.path.join(ATTACHMENTS_DIR, fname)
            with open(path, 'wb') as f:
                f.write(file_data)
            self.send_json({'url': f'/data/attachments/{fname}', 'filename': fname})
        else:
            self.send_json({'error': 'No file provided'}, 400)

    def handle_chat(self):
        body = self.read_body()
        messages = body.get('messages', [])
        model = body.get('model', 'openai/gpt-4o')
        stream = body.get('stream', True)
        try:
            client = get_client()
            if stream:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                for event in client.chat_stream(messages=messages, model=model):
                    data = json.dumps(event)
                    self.wfile.write(f'data: {data}\n\n'.encode())
                    self.wfile.flush()
            else:
                response = client.chat(messages=messages, model=model)
                self.send_json(response)
        except Exception as e:
            if stream:
                self.wfile.write(f'data: {{"error": "{str(e)}"}}\n\n'.encode())
            else:
                self.send_json({'error': str(e)}, 500)

    def serve_static(self):
        path = self.path.lstrip('/')
        if not path or path == '/':
            path = 'static/index.html'
        elif path.startswith('data/'):
            pass  # serve from data dir
        else:
            path = f'static/{path}'
        if not os.path.exists(path):
            self.send_error(404)
            return
        ext = os.path.splitext(path)[1]
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.md': 'text/markdown',
        }
        ctype = content_types.get(ext, 'application/octet-stream')
        with open(path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass

def run():
    server = HTTPServer((HOST, PORT), ChatHandler)
    print(f'Server running on http://{HOST}:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    run()
