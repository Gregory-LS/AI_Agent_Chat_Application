#!/usr/bin/env python3
import json
import os
import re
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

CONVERSATIONS_FILE = os.path.join(os.path.dirname(__file__), 'conversations.json')

def load_conversations():
    if os.path.exists(CONVERSATIONS_FILE):
        with open(CONVERSATIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_conversations(conversations):
    with open(CONVERSATIONS_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _parse_path(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        return path, parse_qs(parsed.query)

    def do_GET(self):
        path, _ = self._parse_path()
        if path == '/api/conversations':
            conversations = load_conversations()
            # Return only non-archived by default? For simplicity return all
            self._send_json(list(conversations.values()))
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        path, _ = self._parse_path()
        if path.startswith('/api/conversations/') and path.endswith('/archive'):
            # Extract conversation ID
            match = re.match(r'/api/conversations/([a-f0-9\-]+)/archive', path)
            if not match:
                self._send_json({'error': 'Invalid conversation ID'}, 400)
                return
            conv_id = match.group(1)
            conversations = load_conversations()
            if conv_id not in conversations:
                self._send_json({'error': 'Conversation not found'}, 404)
                return
            # Toggle archived status
            conversations[conv_id]['archived'] = not conversations[conv_id].get('archived', False)
            save_conversations(conversations)
            self._send_json(conversations[conv_id])
        else:
            self._send_json({'error': 'Not found'}, 404)

    def log_message(self, format, *args):
        # Suppress default logging for cleaner test output
        pass

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
