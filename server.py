import json
import os
import uuid
import urllib.parse
import html
import io
import base64
from http.server import HTTPServer, SimpleHTTPRequestHandler
from http import HTTPStatus

import httpx

from openrouter import OpenRouterClient

DATA_DIR = 'data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')
ATTACHMENTS_DIR = os.path.join(DATA_DIR, 'attachments')

# Ensure data directories exist
for d in [DATA_DIR, CONVERSATIONS_DIR, ATTACHMENTS_DIR]:
    os.makedirs(d, exist_ok=True)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({}, f)
if not os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, 'w') as f:
        json.dump([], f)

# Allowed MIME types for attachments
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/gif', 'image/webp',
    'text/plain', 'text/html', 'text/css', 'text/javascript',
    'application/json', 'application/xml', 'text/x-python',
    'text/markdown', 'text/csv'
}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB


class ChatHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the chat application."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.', **kwargs)

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data, status=200):
        """Send a JSON response."""
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        """Read and return the request body."""
        content_length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(content_length)

    def _parse_path(self):
        """Parse the URL path into components."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        query = urllib.parse.parse_qs(parsed.query)
        return path, query

    def _get_api_key(self):
        """Get API key from config or environment."""
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            api_key = config.get('api_key', api_key)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return api_key

    def _get_client(self):
        """Get an OpenRouter client instance."""
        api_key = self._get_api_key()
        return OpenRouterClient(api_key=api_key)

    def do_GET(self):
        """Handle GET requests."""
        path, query = self._parse_path()

        if path == '/api/models':
            self._handle_get_models()
        elif path == '/api/balance':
            self._handle_get_balance()
        elif path == '/api/config':
            self._handle_get_config()
        elif path == '/api/conversations':
            self._handle_list_conversations()
        elif path.startswith('/api/conversations/') and path.endswith('/export'):
            conv_id = path.split('/')[3]
            self._handle_export_conversation(conv_id, query)
        elif path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            if len(path.split('/')) == 4:
                self._handle_get_conversation(conv_id)
            else:
                self._send_json({'error': 'Not found'}, 404)
        elif path == '/api/skills':
            self._handle_list_skills()
        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            self._handle_get_skill(skill_id)
        elif path == '/api/config/theme':
            self._handle_get_theme()
        else:
            super().do_GET()

    def do_PUT(self):
        """Handle PUT requests."""
        path, _ = self._parse_path()

        if path == '/api/config':
            self._handle_update_config()
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        """Handle POST requests."""
        path, _ = self._parse_path()

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
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_PATCH(self):
        """Handle PATCH requests."""
        path, _ = self._parse_path()

        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            self._handle_update_conversation(conv_id)
        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            self._handle_update_skill(skill_id)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_DELETE(self):
        """Handle DELETE requests."""
        path, _ = self._parse_path()

        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[3]
            self._handle_delete_conversation(conv_id)
        elif path.startswith('/api/skills/'):
            skill_id = path.split('/')[3]
            self._handle_delete_skill(skill_id)
        else:
            self._send_json({'error': 'Not found'}, 404)

    # ---- Attachment handling ----

    def _handle_upload_attachment(self):
        """Handle file upload via multipart/form-data."""
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self._send_json({'error': 'Content-Type must be multipart/form-data'}, 400)
            return

        # Parse boundary
        try:
            boundary = content_type.split('boundary=')[1].strip()
        except IndexError:
            self._send_json({'error': 'Missing boundary in Content-Type'}, 400)
            return

        body = self._read_body()

        # Parse multipart data manually (stdlib only)
        try:
            file_data, filename, mime_type = self._parse_multipart(body, boundary)
        except ValueError as e:
            self._send_json({'error': str(e)}, 400)
            return

        # Validate file size
        if len(file_data) > MAX_ATTACHMENT_SIZE:
            self._send_json({'error': 'File too large (max 10 MB)'}, 413)
            return

        # Validate MIME type
        if mime_type not in ALLOWED_MIME_TYPES:
            self._send_json({'error': f'Unsupported file type: {mime_type}'}, 415)
            return

        # Save file with UUID to prevent overwrites
        ext = os.path.splitext(filename)[1] if '.' in filename else ''
        saved_name = f'{uuid.uuid4().hex}{ext}'
        file_path = os.path.join(ATTACHMENTS_DIR, saved_name)

        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        except IOError as e:
            self._send_json({'error': f'Failed to save file: {str(e)}'}, 500)
            return

        self._send_json({
            'filename': saved_name,
            'original_name': filename,
            'mime_type': mime_type,
            'size': len(file_data)
        }, 201)

    def _parse_multipart(self, body, boundary):
        """Parse multipart/form-data body. Returns (file_data, filename, mime_type)."""
        boundary_bytes = boundary.encode('utf-8')
        parts = body.split(b'--' + boundary_bytes)

        for part in parts:
            if part.strip() == b'' or part.strip() == b'--':
                continue

            # Split headers and body
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue

            headers_raw = part[:header_end].decode('utf-8', errors='replace')
            data = part[header_end + 4:]

            # Remove trailing \r\n-- if present
            if data.endswith(b'\r\n'):
                data = data[:-2]
            if data.endswith(b'--'):
                data = data[:-2]

            # Check if this part has a filename (file upload)
            if 'filename="' in headers_raw:
                # Extract filename
                start = headers_raw.index('filename="') + len('filename="')
                end = headers_raw.index('"', start)
                filename = headers_raw[start:end]

                # Extract Content-Type
                mime_type = 'application/octet-stream'
                if 'Content-Type:' in headers_raw:
                    ct_start = headers_raw.index('Content-Type:') + len('Content-Type: ')
                    ct_end = headers_raw.index('\r\n', ct_start)
                    mime_type = headers_raw[ct_start:ct_end].strip()

                return data, filename, mime_type

        raise ValueError('No file found in upload')

    # ---- Models ----

    def _handle_get_models(self):
        """Fetch and return the list of models from OpenRouter."""
        try:
            client = self._get_client()
            models = client.get_models()
            self._send_json(models)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_get_balance(self):
        """Fetch and return the account balance from OpenRouter."""
        try:
            client = self._get_client()
            balance = client.get_balance()
            self._send_json(balance)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    # ---- Config ----

    def _handle_get_config(self):
        """Return the current configuration."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            # Mask API key
            if 'api_key' in config and config['api_key']:
                config['api_key'] = config['api_key'][:8] + '...'
            self._send_json(config)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_update_config(self):
        """Update the configuration."""
        try:
            body = json.loads(self._read_body())
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            config.update(body)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            self._send_json({'status': 'ok'})
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    # ---- Conversations ----

    def _handle_list_conversations(self):
        """List all conversations."""
        try:
            conversations = []
            for fname in os.listdir(CONVERSATIONS_DIR):
                if fname.endswith('.json'):
                    with open(os.path.join(CONVERSATIONS_DIR, fname), 'r') as f:
                        conv = json.load(f)
                        conversations.append(conv)
            conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            self._send_json(conversations)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_create_conversation(self):
        """Create a new conversation."""
        try:
            body = json.loads(self._read_body())
            conv_id = str(uuid.uuid4())
            conversation = {
                'id': conv_id,
                'title': body.get('title', 'New conversation'),
                'model': body.get('model', ''),
                'messages': [],
                'created_at': None,
                'updated_at': None
            }
            with open(os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json'), 'w') as f:
                json.dump(conversation, f)
            self._send_json(conversation, 201)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_get_conversation(self, conv_id):
        """Get a single conversation."""
        try:
            filepath = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(filepath):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            with open(filepath, 'r') as f:
                conversation = json.load(f)
            self._send_json(conversation)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_update_conversation(self, conv_id):
        """Update a conversation."""
        try:
            filepath = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(filepath):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            body = json.loads(self._read_body())
            with open(filepath, 'r') as f:
                conversation = json.load(f)
            conversation.update(body)
            with open(filepath, 'w') as f:
                json.dump(conversation, f)
            self._send_json(conversation)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_delete_conversation(self, conv_id):
        """Delete a conversation."""
        try:
            filepath = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(filepath):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            os.remove(filepath)
            self._send_json({'status': 'ok'})
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_import_conversation(self):
        """Import a conversation from backup."""
        try:
            body = json.loads(self._read_body())
            conv_id = body.get('id', str(uuid.uuid4()))
            filepath = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            with open(filepath, 'w') as f:
                json.dump(body, f)
            self._send_json({'id': conv_id, 'status': 'imported'}, 201)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_export_conversation(self, conv_id, query):
        """Export a conversation as JSON or Markdown."""
        try:
            filepath = os.path.join(CONVERSATIONS_DIR, f'{conv_id}.json')
            if not os.path.exists(filepath):
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            with open(filepath, 'r') as f:
                conversation = json.load(f)

            fmt = query.get('format', ['json'])[0]
            if fmt == 'markdown':
                md = f"# {conversation.get('title', 'Conversation')}\n\n"
                for msg in conversation.get('messages', []):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    md += f"**{role}:** {content}\n\n"
                body = md.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/markdown; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="{conv_id}.md"')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                body = json.dumps(conversation, indent=2).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Disposition', f'attachment; filename="{conv_id}.json"')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    # ---- Skills ----

    def _handle_list_skills(self):
        """List all skills."""
        try:
            with open(SKILLS_FILE, 'r') as f:
                skills = json.load(f)
            self._send_json(skills)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_get_skill(self, skill_id):
        """Get a single skill."""
        try:
            with open(SKILLS_FILE, 'r') as f:
                skills = json.load(f)
            for skill in skills:
                if skill.get('id') == skill_id:
                    self._send_json(skill)
                    return
            self._send_json({'error': 'Skill not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_create_skill(self):
        """Create a new skill."""
        try:
            body = json.loads(self._read_body())
            skill_id = str(uuid.uuid4())
            skill = {
                'id': skill_id,
                'name': body.get('name', 'New skill'),
                'prompt': body.get('prompt', ''),
                'enabled': body.get('enabled', True)
            }
            with open(SKILLS_FILE, 'r') as f:
                skills = json.load(f)
            skills.append(skill)
            with open(SKILLS_FILE, 'w') as f:
                json.dump(skills, f)
            self._send_json(skill, 201)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_update_skill(self, skill_id):
        """Update a skill."""
        try:
            body = json.loads(self._read_body())
            with open(SKILLS_FILE, 'r') as f:
                skills = json.load(f)
            for i, skill in enumerate(skills):
                if skill.get('id') == skill_id:
                    skills[i].update(body)
                    with open(SKILLS_FILE, 'w') as f:
                        json.dump(skills, f)
                    self._send_json(skills[i])
                    return
            self._send_json({'error': 'Skill not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _handle_delete_skill(self, skill_id):
        """Delete a skill."""
        try:
            with open(SKILLS_FILE, 'r') as f:
                skills = json.load(f)
            for i, skill in enumerate(skills):
                if skill.get('id') == skill_id:
                    del skills[i]
                    with open(SKILLS_FILE, 'w') as f:
                        json.dump(skills, f)
                    self._send_json({'status': 'ok'})
                    return
            self._send_json({'error': 'Skill not found'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    # ---- Theme ----

    def _handle_get_theme(self):
        """Return the current theme setting."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            theme = config.get('theme', 'light')
            self._send_json({'theme': theme})
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    # ---- Chat ----

    def _handle_chat(self):
        """Handle streaming chat requests via SSE."""
        try:
            body = json.loads(self._read_body())
            messages = body.get('messages', [])
            model = body.get('model', '')
            api_key = self._get_api_key()

            if not api_key:
                self._send_json({'error': 'API key not configured'}, 400)
                return

            client = OpenRouterClient(api_key=api_key)

            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            for event in client.stream_chat(messages, model):
                event_type = event.get('type', '')
                data = json.dumps(event)
                self.wfile.write(f'data: {data}\n\n'.encode('utf-8'))
                self.wfile.flush()

                if event_type in ('done', 'error'):
                    break

        except Exception as e:
            self._send_json({'error': str(e)}, 500)


def run_server():
    """Start the HTTP server."""
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer((host, port), ChatHandler)
    print(f'Server running on http://{host}:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()


if __name__ == '__main__':
    run_server()