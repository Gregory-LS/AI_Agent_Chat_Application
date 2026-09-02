import json
import os
import sys
import http.server
import urllib.parse
import mimetypes
import io

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Default config
default_config = {
    'theme': 'light',
    'defaultModel': '',
    'apiKey': ''
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return dict(default_config)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/config':
            self.send_json(load_config())
        elif path.startswith('/static/') or path == '/' or path == '':
            self.serve_static(path)
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/config':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                new_config = json.loads(body)
                # Merge with existing config
                current = load_config()
                current.update(new_config)
                save_config(current)
                self.send_json(current)
            except json.JSONDecodeError:
                self.send_error(400, 'Invalid JSON')
        else:
            self.send_error(404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def serve_static(self, path):
        if path == '/' or path == '':
            path = '/static/index.html'
        elif not path.startswith('/static/'):
            path = '/static/' + path
        # Map to filesystem
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path.lstrip('/'))
        if not os.path.exists(file_path):
            self.send_error(404)
            return
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        with open(file_path, 'rb') as f:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(f.read())

def run(host='0.0.0.0', port=8000):
    server = http.server.HTTPServer((host, port), Handler)
    print(f'Server running on http://{host}:{port}')
    server.serve_forever()

if __name__ == '__main__':
    run()
