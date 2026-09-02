import json
import os
import urllib.parse
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import httpx

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")  # nosec
PORT = int(os.getenv("PORT", "8000"))
DATA_DIR = Path("data")
CONFIG_FILE = DATA_DIR / "config.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
SKILLS_FILE = DATA_DIR / "skills.json"
ATTACHMENTS_DIR = DATA_DIR / "attachments"

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)

# Load config
config = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        config = json.load(f)

# Authentication
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD") or config.get("auth_password")
sessions = {}  # session_token -> bool

# OpenRouter API key
openrouter_api_key = os.getenv("OPENROUTER_API_KEY") or config.get("api_key")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def require_auth(handler):
    """Decorator to check authentication for API handlers."""
    if not AUTH_PASSWORD:
        return handler
    def wrapper(self, *args, **kwargs):
        cookies = self.headers.get("Cookie", "")
        token = None
        for cookie in cookies.split(";"):
            cookie = cookie.strip()
            if cookie.startswith("session="):
                token = cookie[len("session="):]
                break
        if not token or token not in sessions:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return
        return handler(self, *args, **kwargs)
    return wrapper


class ChatHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/models":
            self._handle_models()
        elif path == "/api/balance":
            self._handle_balance()
        elif path == "/api/config":
            self._handle_get_config()
        elif path == "/api/conversations":
            self._handle_list_conversations()
        elif path.startswith("/api/conversations/") and "/export" in path:
            self._handle_export_conversation(params)
        elif path.startswith("/api/conversations/"):
            conv_id = path.split("/api/conversations/")[1].split("/")[0]
            self._handle_get_conversation(conv_id)
        elif path == "/api/skills":
            self._handle_list_skills()
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/api/skills/")[1].split("/")[0]
            self._handle_get_skill(skill_id)
        elif path == "/login.html" or path == "/login":
            # Serve login page without auth
            self._serve_static("login.html")
        elif path == "/" or path == "/index.html":
            if AUTH_PASSWORD:
                self._serve_static("login.html")
            else:
                self._serve_static("index.html")
        else:
            # Try to serve static files
            self._serve_static(path.lstrip("/"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/login":
            self._handle_login()
        elif path == "/api/logout":
            self._handle_logout()
        elif path == "/api/config":
            self._handle_update_config()
        elif path == "/api/conversations":
            self._handle_create_conversation()
        elif path == "/api/conversations/import":
            self._handle_import_conversation()
        elif path == "/api/skills":
            self._handle_create_skill()
        elif path == "/api/attachments":
            self._handle_upload_attachment()
        elif path == "/api/chat":
            self._handle_chat()
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/config":
            self._handle_update_config()
        else:
            self.send_error(404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/conversations/"):
            conv_id = path.split("/api/conversations/")[1].split("/")[0]
            self._handle_update_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/api/skills/")[1].split("/")[0]
            self._handle_update_skill(skill_id)
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/conversations/"):
            conv_id = path.split("/api/conversations/")[1].split("/")[0]
            self._handle_delete_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/api/skills/")[1].split("/")[0]
            self._handle_delete_skill(skill_id)
        else:
            self.send_error(404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode() if length > 0 else "{}"

    def _serve_static(self, filename):
        if not filename:
            filename = "index.html"
        # Security: prevent directory traversal
        filename = Path(filename).name
        static_dir = Path("static")
        filepath = static_dir / filename
        if not filepath.exists():
            self.send_error(404)
            return
        self.send_response(200)
        if filename.endswith(".html"):
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif filename.endswith(".css"):
            self.send_header("Content-Type", "text/css")
        elif filename.endswith(".js"):
            self.send_header("Content-Type", "application/javascript")
        else:
            self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    # Authentication handlers
    def _handle_login(self):
        if not AUTH_PASSWORD:
            self._send_json({"error": "Authentication not configured"}, 403)
            return
        body = json.loads(self._read_body())
        password = body.get("password")
        if password == AUTH_PASSWORD:
            token = str(uuid.uuid4())
            sessions[token] = True
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", f"session={token}; Path=/; HttpOnly; SameSite=Lax")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())
        else:
            self._send_json({"error": "Invalid password"}, 401)

    def _handle_logout(self):
        if not AUTH_PASSWORD:
            self._send_json({"error": "Authentication not configured"}, 403)
            return
        cookies = self.headers.get("Cookie", "")
        token = None
        for cookie in cookies.split(";"):
            cookie = cookie.strip()
            if cookie.startswith("session="):
                token = cookie[len("session="):]
                break
        if token and token in sessions:
            del sessions[token]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", "session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode())

    # API handlers with auth check
    @require_auth
    def _handle_models(self):
        # ... existing implementation (unchanged, omitted for brevity)
        self._send_json({"models": []})

    @require_auth
    def _handle_balance(self):
        # ... existing implementation
        self._send_json({"credits": 0, "usage": 0, "total": 0})

    @require_auth
    def _handle_get_config(self):
        # ... existing
        self._send_json(config)

    @require_auth
    def _handle_update_config(self):
        # ... existing
        body = json.loads(self._read_body())
        config.update(body)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        self._send_json(config)

    @require_auth
    def _handle_list_conversations(self):
        # ... existing
        self._send_json([])

    @require_auth
    def _handle_get_conversation(self, conv_id):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_create_conversation(self):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_update_conversation(self, conv_id):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_delete_conversation(self, conv_id):
        # ... existing
        self._send_json({"success": True})

    @require_auth
    def _handle_export_conversation(self, params):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_import_conversation(self):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_list_skills(self):
        # ... existing
        self._send_json([])

    @require_auth
    def _handle_get_skill(self, skill_id):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_create_skill(self):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_update_skill(self, skill_id):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_delete_skill(self, skill_id):
        # ... existing
        self._send_json({"success": True})

    @require_auth
    def _handle_upload_attachment(self):
        # ... existing
        self._send_json({})

    @require_auth
    def _handle_chat(self):
        # ... existing streaming implementation
        self._send_json({})

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def run():
    server = HTTPServer((HOST, PORT), ChatHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    print(f"Auth enabled: {bool(AUTH_PASSWORD)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    run()
