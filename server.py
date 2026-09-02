import http.server
import json
import os
import uuid
import shutil
import urllib.parse
from pathlib import Path

import openrouter

DATA_DIR = Path("data")
CONFIG_FILE = DATA_DIR / "config.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
SKILLS_FILE = DATA_DIR / "skills.json"
ATTACHMENTS_DIR = DATA_DIR / "attachments"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)
if not SKILLS_FILE.exists():
    SKILLS_FILE.write_text("[]")
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(json.dumps({"api_key": "", "default_model": ""}))

def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())

def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_api_key() -> str:
    config = load_config()
    return config.get("api_key") or os.getenv("OPENROUTER_API_KEY", "")

def load_conversations() -> list:
    conversations = []
    for f in CONVERSATIONS_DIR.glob("*.json"):
        conv = json.loads(f.read_text())
        conv["id"] = f.stem
        conversations.append(conv)
    conversations.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return conversations

def save_conversation(conv_id: str, data: dict):
    filepath = CONVERSATIONS_DIR / f"{conv_id}.json"
    filepath.write_text(json.dumps(data, indent=2))

def get_conversation(conv_id: str) -> dict:
    filepath = CONVERSATIONS_DIR / f"{conv_id}.json"
    if filepath.exists():
        return json.loads(filepath.read_text())
    return None

def delete_conversation(conv_id: str):
    filepath = CONVERSATIONS_DIR / f"{conv_id}.json"
    if filepath.exists():
        filepath.unlink()

def load_skills() -> list:
    return json.loads(SKILLS_FILE.read_text())

def save_skills(skills: list):
    SKILLS_FILE.write_text(json.dumps(skills, indent=2))

class ChatHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/models":
            api_key = get_api_key()
            if not api_key:
                self.send_error_json("API key not configured", 401)
                return
            try:
                models = openrouter.get_models(api_key)
                self.send_json(models)
            except Exception as e:
                self.send_error_json(str(e), 502)

        elif path == "/api/balance":
            api_key = get_api_key()
            if not api_key:
                self.send_error_json("API key not configured", 401)
                return
            try:
                balance = openrouter.get_balance(api_key)
                self.send_json(balance)
            except Exception as e:
                self.send_error_json(str(e), 502)

        elif path == "/api/config":
            self.send_json(load_config())

        elif path == "/api/conversations":
            self.send_json(load_conversations())

        elif path.startswith("/api/conversations/"):
            parts = path.split("/")
            if len(parts) == 4 and parts[3] == "import":
                self.send_error_json("Use POST to import", 405)
                return
            conv_id = parts[3]
            if len(parts) == 5 and parts[4] == "export":
                fmt = query.get("format", ["json"])[0]
                conv = get_conversation(conv_id)
                if not conv:
                    self.send_error_json("Conversation not found", 404)
                    return
                if fmt == "markdown":
                    self.send_response(200)
                    self.send_cors_headers()
                    self.send_header("Content-Type", "text/markdown")
                    self.send_header("Content-Disposition", f'attachment; filename="{conv_id}.md"')
                    self.end_headers()
                    lines = [f"# {conv.get('title', 'Conversation')}\n"]
                    for msg in conv.get("messages", []):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        lines.append(f"**{role}**: {content}\n")
                    self.wfile.write("\n".join(lines).encode())
                else:
                    self.send_json(conv)
                return
            conv = get_conversation(conv_id)
            if conv:
                self.send_json(conv)
            else:
                self.send_error_json("Conversation not found", 404)

        elif path == "/api/skills":
            self.send_json(load_skills())

        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            skills = load_skills()
            skill = next((s for s in skills if s.get("id") == skill_id), None)
            if skill:
                self.send_json(skill)
            else:
                self.send_error_json("Skill not found", 404)

        elif path.startswith("/static/") or path == "/" or path == "":
            if path == "/" or path == "":
                path = "/static/index.html"
            filepath = Path(".") / path.lstrip("/")
            if filepath.exists() and filepath.is_file():
                content_type = {
                    ".html": "text/html",
                    ".css": "text/css",
                    ".js": "application/javascript",
                    ".json": "application/json",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".svg": "image/svg+xml",
                }.get(filepath.suffix, "application/octet-stream")
                self.send_response(200)
                self.send_cors_headers()
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(filepath.read_bytes())
            else:
                self.send_error_json("File not found", 404)
        else:
            self.send_error_json("Not found", 404)

    def do_PUT(self):
        if self.path == "/api/config":
            config = self.read_body()
            save_config(config)
            self.send_json(config)
        else:
            self.send_error_json("Not found", 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/conversations":
            data = self.read_body()
            conv_id = str(uuid.uuid4())
            conversation = {
                "id": conv_id,
                "title": data.get("title", "New conversation"),
                "messages": data.get("messages", []),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "model": data.get("model", "")
            }
            save_conversation(conv_id, conversation)
            self.send_json(conversation, 201)

        elif path == "/api/conversations/import":
            data = self.read_body()
            conv_id = str(uuid.uuid4())
            conversation = {
                "id": conv_id,
                "title": data.get("title", "Imported conversation"),
                "messages": data.get("messages", []),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "model": data.get("model", "")
            }
            save_conversation(conv_id, conversation)
            self.send_json(conversation, 201)

        elif path == "/api/skills":
            data = self.read_body()
            skills = load_skills()
            skill = {
                "id": str(uuid.uuid4()),
                "name": data.get("name", ""),
                "prompt": data.get("prompt", ""),
                "enabled": data.get("enabled", True)
            }
            skills.append(skill)
            save_skills(skills)
            self.send_json(skill, 201)

        elif path == "/api/attachments":
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                # Handle file upload
                import cgi
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={"REQUEST_METHOD": "POST"}
                )
                file_item = form["file"]
                if file_item.filename:
                    filename = file_item.filename
                    file_data = file_item.file.read()
                    att_id = str(uuid.uuid4())
                    ext = Path(filename).suffix
                    att_path = ATTACHMENTS_DIR / f"{att_id}{ext}"
                    att_path.write_bytes(file_data)
                    self.send_json({
                        "id": att_id,
                        "filename": filename,
                        "path": str(att_path),
                        "size": len(file_data)
                    }, 201)
                else:
                    self.send_error_json("No file provided")
            else:
                self.send_error_json("Unsupported content type")

        elif path == "/api/chat":
            data = self.read_body()
            api_key = get_api_key()
            if not api_key:
                self.send_error_json("API key not configured", 401)
                return
            model = data.get("model", "")
            messages = data.get("messages", [])
            if not model or not messages:
                self.send_error_json("Missing model or messages")
                return
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                for chunk in openrouter.chat(api_key, model, messages):
                    self.wfile.write(f"data: {chunk}\n\n".encode())
                    self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception as e:
                self.wfile.write(f"data: {{\"error\": \"{str(e)}\"}}\n\n".encode())
                self.wfile.flush()
        else:
            self.send_error_json("Not found", 404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        parts = path.split("/")

        if len(parts) == 4 and parts[1] == "api" and parts[2] == "conversations":
            conv_id = parts[3]
            conv = get_conversation(conv_id)
            if not conv:
                self.send_error_json("Conversation not found", 404)
                return
            data = self.read_body()
            conv.update(data)
            save_conversation(conv_id, conv)
            self.send_json(conv)

        elif len(parts) == 4 and parts[1] == "api" and parts[2] == "skills":
            skill_id = parts[3]
            skills = load_skills()
            skill = next((s for s in skills if s.get("id") == skill_id), None)
            if not skill:
                self.send_error_json("Skill not found", 404)
                return
            data = self.read_body()
            skill.update(data)
            save_skills(skills)
            self.send_json(skill)
        else:
            self.send_error_json("Not found", 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        parts = path.split("/")

        if len(parts) == 4 and parts[1] == "api" and parts[2] == "conversations":
            conv_id = parts[3]
            delete_conversation(conv_id)
            self.send_json({"status": "deleted"})

        elif len(parts) == 4 and parts[1] == "api" and parts[2] == "skills":
            skill_id = parts[3]
            skills = load_skills()
            skills = [s for s in skills if s.get("id") != skill_id]
            save_skills(skills)
            self.send_json({"status": "deleted"})
        else:
            self.send_error_json("Not found", 404)

    def log_message(self, format, *args):
        # Suppress default logging to stderr
        pass

if __name__ == "__main__":
    server = http.server.HTTPServer((HOST, PORT), ChatHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    server.serve_forever()
