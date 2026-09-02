import http.server
import json
import os
import urllib.parse
from pathlib import Path

import httpx

DATA_DIR = Path("data")
CONFIG_FILE = DATA_DIR / "config.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
SKILLS_FILE = DATA_DIR / "skills.json"
ATTACHMENTS_DIR = DATA_DIR / "attachments"

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)
if not SKILLS_FILE.exists():
    SKILLS_FILE.write_text("[]")
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(json.dumps({"api_key": "", "default_model": ""}))

STATIC_DIR = Path("static")

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_api_key():
    return os.environ.get("OPENROUTER_API_KEY") or load_config().get("api_key", "")

class APIHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode() if length > 0 else "{}"

    def _parse_path(self):
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, dict(urllib.parse.parse_qsl(parsed.query))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path, params = self._parse_path()
        if path == "/api/models":
            self._handle_models()
        elif path == "/api/balance":
            self._handle_balance()
        elif path == "/api/config":
            self._send_json(load_config())
        elif path == "/api/conversations":
            self._list_conversations()
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            self._export_conversation(path)
        elif path.startswith("/api/conversations/"):
            self._get_conversation(path)
        elif path == "/api/skills":
            self._list_skills()
        elif path.startswith("/api/skills/"):
            self._get_skill(path)
        else:
            self._serve_static(path)

    def do_POST(self):
        path, params = self._parse_path()
        if path == "/api/config":
            self._update_config()
        elif path == "/api/conversations":
            self._create_conversation()
        elif path == "/api/conversations/import":
            self._import_conversation()
        elif path == "/api/skills":
            self._create_skill()
        elif path == "/api/attachments":
            self._upload_attachment()
        elif path == "/api/chat":
            self._handle_chat()
        elif path == "/api/logout":
            self._handle_logout()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        path, params = self._parse_path()
        if path == "/api/config":
            self._update_config()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_PATCH(self):
        path, params = self._parse_path()
        if path.startswith("/api/conversations/"):
            self._update_conversation(path)
        elif path.startswith("/api/skills/"):
            self._update_skill(path)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        path, params = self._parse_path()
        if path.startswith("/api/conversations/"):
            self._delete_conversation(path)
        elif path.startswith("/api/skills/"):
            self._delete_skill(path)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _serve_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"
        file_path = STATIC_DIR / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            self.send_response(200)
            ext = file_path.suffix
            content_type = {
                ".html": "text/html",
                ".css": "text/css",
                ".js": "application/javascript",
                ".json": "application/json",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
            }.get(ext, "application/octet-stream")
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_models(self):
        api_key = get_api_key()
        if not api_key:
            self._send_json({"error": "API key not configured"}, 401)
            return
        try:
            import openrouter
            models = openrouter.list_models(api_key)
            self._send_json(models)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_balance(self):
        api_key = get_api_key()
        if not api_key:
            self._send_json({"error": "API key not configured"}, 401)
            return
        try:
            import openrouter
            balance = openrouter.check_balance(api_key)
            self._send_json(balance)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_chat(self):
        api_key = get_api_key()
        if not api_key:
            self._send_json({"error": "API key not configured"}, 401)
            return
        body = json.loads(self._read_body())
        model = body.get("model", "")
        messages = body.get("messages", [])
        stream = body.get("stream", True)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            import openrouter
            for event in openrouter.stream_chat(api_key, model, messages):
                data = json.dumps(event)
                self.wfile.write(f"data: {data}\n\n".encode())
                self.wfile.flush()
        except Exception as e:
            error_data = json.dumps({"type": "error", "error": str(e)})
            self.wfile.write(f"data: {error_data}\n\n".encode())
            self.wfile.flush()

    def _update_config(self):
        body = json.loads(self._read_body())
        config = load_config()
        config.update(body)
        save_config(config)
        self._send_json(config)

    def _list_conversations(self):
        conversations = []
        for file in sorted(CONVERSATIONS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                conv = json.loads(file.read_text())
                conversations.append(conv)
            except json.JSONDecodeError:
                continue
        self._send_json(conversations)

    def _create_conversation(self):
        body = json.loads(self._read_body())
        conv_id = body.get("id", str(len(list(CONVERSATIONS_DIR.glob("*.json"))) + 1))
        conv = {
            "id": conv_id,
            "title": body.get("title", "New conversation"),
            "messages": body.get("messages", []),
            "model": body.get("model", ""),
            "created_at": body.get("created_at", ""),
            "updated_at": body.get("updated_at", ""),
        }
        (CONVERSATIONS_DIR / f"{conv_id}.json").write_text(json.dumps(conv, indent=2))
        self._send_json(conv, 201)

    def _get_conversation(self, path):
        conv_id = path.split("/")[3]
        conv_file = CONVERSATIONS_DIR / f"{conv_id}.json"
        if conv_file.exists():
            self._send_json(json.loads(conv_file.read_text()))
        else:
            self._send_json({"error": "Not found"}, 404)

    def _update_conversation(self, path):
        conv_id = path.split("/")[3]
        conv_file = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not conv_file.exists():
            self._send_json({"error": "Not found"}, 404)
            return
        conv = json.loads(conv_file.read_text())
        body = json.loads(self._read_body())
        conv.update(body)
        conv_file.write_text(json.dumps(conv, indent=2))
        self._send_json(conv)

    def _delete_conversation(self, path):
        conv_id = path.split("/")[3]
        conv_file = CONVERSATIONS_DIR / f"{conv_id}.json"
        if conv_file.exists():
            conv_file.unlink()
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def _export_conversation(self, path):
        # path is like /api/conversations/<id>/export?format=json|markdown
        parts = path.split("/")
        conv_id = parts[3]
        _, params = self._parse_path()
        fmt = params.get("format", "json")
        conv_file = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not conv_file.exists():
            self._send_json({"error": "Not found"}, 404)
            return
        conv = json.loads(conv_file.read_text())
        if fmt == "markdown":
            md = f"# {conv.get('title', 'Conversation')}\n\n"
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                md += f"**{role.capitalize()}:** {content}\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Content-Disposition", f"attachment; filename=\"{conv_id}.md\"")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(md.encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", f"attachment; filename=\"{conv_id}.json\"")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(conv, indent=2).encode())

    def _import_conversation(self):
        body = json.loads(self._read_body())
        conv_id = body.get("id", str(len(list(CONVERSATIONS_DIR.glob("*.json"))) + 1))
        conv = {
            "id": conv_id,
            "title": body.get("title", "Imported conversation"),
            "messages": body.get("messages", []),
            "model": body.get("model", ""),
            "created_at": body.get("created_at", ""),
            "updated_at": body.get("updated_at", ""),
        }
        (CONVERSATIONS_DIR / f"{conv_id}.json").write_text(json.dumps(conv, indent=2))
        self._send_json(conv, 201)

    def _list_skills(self):
        if SKILLS_FILE.exists():
            self._send_json(json.loads(SKILLS_FILE.read_text()))
        else:
            self._send_json([])

    def _create_skill(self):
        body = json.loads(self._read_body())
        skills = json.loads(SKILLS_FILE.read_text()) if SKILLS_FILE.exists() else []
        skill_id = body.get("id", str(len(skills) + 1))
        skill = {
            "id": skill_id,
            "name": body.get("name", "New skill"),
            "prompt": body.get("prompt", ""),
            "enabled": body.get("enabled", False),
        }
        skills.append(skill)
        SKILLS_FILE.write_text(json.dumps(skills, indent=2))
        self._send_json(skill, 201)

    def _get_skill(self, path):
        skill_id = path.split("/")[3]
        skills = json.loads(SKILLS_FILE.read_text()) if SKILLS_FILE.exists() else []
        for skill in skills:
            if skill["id"] == skill_id:
                self._send_json(skill)
                return
        self._send_json({"error": "Not found"}, 404)

    def _update_skill(self, path):
        skill_id = path.split("/")[3]
        skills = json.loads(SKILLS_FILE.read_text()) if SKILLS_FILE.exists() else []
        body = json.loads(self._read_body())
        for skill in skills:
            if skill["id"] == skill_id:
                skill.update(body)
                SKILLS_FILE.write_text(json.dumps(skills, indent=2))
                self._send_json(skill)
                return
        self._send_json({"error": "Not found"}, 404)

    def _delete_skill(self, path):
        skill_id = path.split("/")[3]
        skills = json.loads(SKILLS_FILE.read_text()) if SKILLS_FILE.exists() else []
        new_skills = [s for s in skills if s["id"] != skill_id]
        if len(new_skills) == len(skills):
            self._send_json({"error": "Not found"}, 404)
            return
        SKILLS_FILE.write_text(json.dumps(new_skills, indent=2))
        self._send_json({"status": "ok"})

    def _upload_attachment(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        # Expect multipart form data with file field
        import cgi
        import io
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" in content_type:
            fs = cgi.FieldStorage(
                fp=io.BytesIO(body),
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST"},
            )
            file_item = fs["file"]
            if file_item and file_item.filename:
                filename = file_item.filename
                file_data = file_item.file.read()
                file_path = ATTACHMENTS_DIR / filename
                with open(file_path, "wb") as f:
                    f.write(file_data)
                self._send_json({"filename": filename, "path": str(file_path)})
                return
        self._send_json({"error": "No file uploaded"}, 400)

    def _handle_logout(self):
        """Clear the stored API key from config."""
        config = load_config()
        config["api_key"] = ""
        save_config(config)
        self._send_json({"status": "ok", "message": "Logged out successfully"})

    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == "__main__":
    server = http.server.HTTPServer((HOST, PORT), APIHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    server.serve_forever()
