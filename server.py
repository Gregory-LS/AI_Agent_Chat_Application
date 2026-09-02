import http.server
import json
import os
import urllib.parse

import openrouter

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))

class ChatHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/models':
            self.handle_get_models()
        elif path == '/api/balance':
            self.handle_get_balance()
        elif path == '/api/config':
            self.handle_get_config()
        elif path.startswith('/api/conversations/'):
            # extract conversation id and possible subpath
            parts = path.split('/')
            if len(parts) == 4 and parts[3]:
                conv_id = parts[3]
                self.handle_get_conversation(conv_id)
            elif len(parts) == 5 and parts[3] and parts[4] == 'export':
                conv_id = parts[3]
                qs = urllib.parse.parse_qs(parsed.query)
                fmt = qs.get('format', ['json'])[0]
                self.handle_export_conversation(conv_id, fmt)
            else:
                self.send_error(404)
        elif path == '/api/conversations':
            self.handle_list_conversations()
        elif path == '/api/skills':
            self.handle_list_skills()
        elif path.startswith('/static/'):
            self.serve_static()
        elif path == '/' or path == '/index.html':
            self.serve_static_file('static/index.html', 'text/html')
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/chat':
            self.handle_chat()
        elif path == '/api/conversations':
            self.handle_create_conversation()
        elif path == '/api/conversations/import':
            self.handle_import_conversation()
        elif path == '/api/skills':
            self.handle_create_skill()
        elif path == '/api/attachments':
            self.handle_upload_attachment()
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/config':
            self.handle_update_config()
        else:
            self.send_error(404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/conversations/'):
            parts = path.split('/')
            if len(parts) == 4 and parts[3]:
                conv_id = parts[3]
                self.handle_update_conversation(conv_id)
            else:
                self.send_error(404)
        elif path.startswith('/api/skills/'):
            parts = path.split('/')
            if len(parts) == 4 and parts[3]:
                skill_id = parts[3]
                self.handle_update_skill(skill_id)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/conversations/'):
            parts = path.split('/')
            if len(parts) == 4 and parts[3]:
                conv_id = parts[3]
                self.handle_delete_conversation(conv_id)
            else:
                self.send_error(404)
        elif path.startswith('/api/skills/'):
            parts = path.split('/')
            if len(parts) == 4 and parts[3]:
                skill_id = parts[3]
                self.handle_delete_skill(skill_id)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length > 0:
            return json.loads(self.rfile.read(length))
        return {}

    def handle_get_models(self):
        try:
            models = openrouter.fetch_models()
            self._send_json({'models': models})
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def handle_get_balance(self):
        try:
            balance = openrouter.fetch_balance()
            self._send_json(balance)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def handle_get_config(self):
        config = openrouter.load_config()
        self._send_json(config)

    def handle_update_config(self):
        body = self._read_body()
        openrouter.save_config(body)
        self._send_json({'status': 'ok'})

    def handle_list_conversations(self):
        convs = openrouter.list_conversations()
        self._send_json({'conversations': convs})

    def handle_create_conversation(self):
        body = self._read_body()
        conv = openrouter.create_conversation(body.get('model', ''), body.get('title', ''))
        self._send_json(conv, 201)

    def handle_get_conversation(self, conv_id):
        conv = openrouter.get_conversation(conv_id)
        if conv:
            self._send_json(conv)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def handle_update_conversation(self, conv_id):
        body = self._read_body()
        conv = openrouter.update_conversation(conv_id, body)
        if conv:
            self._send_json(conv)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def handle_delete_conversation(self, conv_id):
        success = openrouter.delete_conversation(conv_id)
        if success:
            self._send_json({'status': 'deleted'})
        else:
            self._send_json({'error': 'Not found'}, 404)

    def handle_import_conversation(self):
        body = self._read_body()
        conv = openrouter.import_conversation(body)
        self._send_json(conv, 201)

    def handle_export_conversation(self, conv_id, fmt):
        data = openrouter.export_conversation(conv_id, fmt)
        if data:
            if fmt == 'markdown':
                self.send_response(200)
                self.send_header('Content-Type', 'text/markdown')
                self.end_headers()
                self.wfile.write(data.encode())
            else:
                self._send_json(data)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def handle_list_skills(self):
        skills = openrouter.list_skills()
        self._send_json({'skills': skills})

    def handle_create_skill(self):
        body = self._read_body()
        skill = openrouter.create_skill(body)
        self._send_json(skill, 201)

    def handle_update_skill(self, skill_id):
        body = self._read_body()
        skill = openrouter.update_skill(skill_id, body)
        if skill:
            self._send_json(skill)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def handle_delete_skill(self, skill_id):
        success = openrouter.delete_skill(skill_id)
        if success:
            self._send_json({'status': 'deleted'})
        else:
            self._send_json({'error': 'Not found'}, 404)

    def handle_chat(self):
        body = self._read_body()
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        try:
            for event in openrouter.stream_chat(body):
                self.wfile.write(f'data: {json.dumps(event)}\n\n'.encode())
                self.wfile.flush()
        except Exception as e:
            error_event = {'type': 'error', 'error': str(e)}
            self.wfile.write(f'data: {json.dumps(error_event)}\n\n'.encode())
            self.wfile.flush()

    def handle_upload_attachment(self):
        # parse multipart form data
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self._send_json({'error': 'Expected multipart/form-data'}, 400)
            return
        boundary = content_type.split('boundary=')[1].strip()
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        # simple multipart parser
        parts = body.split(b'--' + boundary.encode())
        for part in parts:
            if b'Content-Disposition' in part and b'filename="' in part:
                # extract filename
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue
                headers_part = part[:header_end].decode(errors='replace')
                file_data = part[header_end+4:]
                # remove trailing \r\n--
                if file_data.endswith(b'\r\n'):
                    file_data = file_data[:-2]
                # extract filename
                import re
                match = re.search(r'filename="([^"]+)"', headers_part)
                if match:
                    filename = match.group(1)
                    result = openrouter.save_attachment(filename, file_data)
                    self._send_json(result, 201)
                    return
        self._send_json({'error': 'No file found'}, 400)

    def serve_static(self):
        path = self.path.lstrip('/')
        if not path:
            path = 'static/index.html'
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            mime_map = {
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
            }
            mime = mime_map.get(ext, 'application/octet-stream')
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.end_headers()
            with open(path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

    def serve_static_file(self, path, mime):
        if os.path.isfile(path):
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.end_headers()
            with open(path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

    def send_error(self, code, message=None):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_msg = message or http.server.BaseHTTPRequestHandler.responses.get(code, ('Unknown', 'Unknown'))[1]
        self.wfile.write(json.dumps({'error': error_msg}).encode())

def run():
    server = http.server.HTTPServer((HOST, PORT), ChatHandler)
    print(f'Server running on http://{HOST}:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()

if __name__ == '__main__':
    run()
