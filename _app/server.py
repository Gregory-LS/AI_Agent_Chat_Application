import json
import os
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# In-memory store for conversations (simulated database)
conversations = {}

class ChatHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/conversations':
            # Return all conversations, optionally filtered by archived status
            query = parse_qs(parsed.query)
            archived = query.get('archived', [None])[0]
            if archived is not None:
                archived = archived.lower() == 'true'
                result = [c for c in conversations.values() if c.get('archived') == archived]
            else:
                result = list(conversations.values())
            self._send_json(200, result)
        elif path.startswith('/api/conversations/'):
            # Get single conversation
            conv_id = path.split('/')[-1]
            conv = conversations.get(conv_id)
            if conv:
                self._send_json(200, conv)
            else:
                self._send_json(404, {'error': 'Conversation not found'})
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/conversations':
            # Create new conversation
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            data = json.loads(body) if body else {}
            conv_id = str(uuid.uuid4())
            conversations[conv_id] = {
                'id': conv_id,
                'title': data.get('title', 'New Conversation'),
                'messages': [],
                'archived': False,
                'created_at': '2025-01-01T00:00:00Z'
            }
            self._send_json(201, conversations[conv_id])
        elif path.startswith('/api/conversations/') and path.endswith('/archive'):
            conv_id = path.split('/')[-2]
            conv = conversations.get(conv_id)
            if not conv:
                self._send_json(404, {'error': 'Conversation not found'})
                return
            conv['archived'] = True
            self._send_json(200, conv)
        elif path.startswith('/api/conversations/') and path.endswith('/unarchive'):
            conv_id = path.split('/')[-2]
            conv = conversations.get(conv_id)
            if not conv:
                self._send_json(404, {'error': 'Conversation not found'})
                return
            conv['archived'] = False
            self._send_json(200, conv)
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_PUT(self):
        # For future use (e.g., rename)
        self._send_json(405, {'error': 'Method not allowed'})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith('/api/conversations/'):
            conv_id = path.split('/')[-1]
            if conv_id in conversations:
                del conversations[conv_id]
                self._send_json(200, {'status': 'deleted'})
            else:
                self._send_json(404, {'error': 'Conversation not found'})
        else:
            self._send_json(404, {'error': 'Not found'})

def run_server(host='0.0.0.0', port=8000):
    server = HTTPServer((host, port), ChatHandler)
    print(f'Server running on http://{host}:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    run_server()
