import http.server
import json
import os
import cgi
import uuid
import shutil
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import httpx

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
if not os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"api_key": "", "default_model": "", "theme": "light"}, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def load_skills():
    with open(SKILLS_FILE, "r") as f:
        return json.load(f)

def save_skills(skills):
    with open(SKILLS_FILE, "w") as f:
        json.dump(skills, f, indent=2)

def get_conversation_path(conv_id):
    return os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")

def load_conversation(conv_id):
    path = get_conversation_path(conv_id)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def save_conversation(conv_id, data):
    with open(get_conversation_path(conv_id), "w") as f:
        json.dump(data, f, indent=2)

def list_conversations():
    convs = []
    for fname in sorted(os.listdir(CONVERSATIONS_DIR), reverse=True):
        if fname.endswith(".json"):
            conv_id = fname[:-5]
            conv = load_conversation(conv_id)
            if conv:
                convs.append(conv)
    return convs

def get_api_key():
    config = load_config()
    return config.get("api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")

class ChatHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/models":
            self.handle_get_models()
        elif path == "/api/balance":
            self.handle_get_balance()
        elif path == "/api/config":
            self.handle_get_config()
        elif path == "/api/conversations":
            self.handle_list_conversations()
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            conv_id = path.split("/")[3]
            fmt = query.get("format", ["json"])[0]
            self.handle_export_conversation(conv_id, fmt)
        elif path.startswith("/api/conversations/"):
            conv_id = path.split("/")[3]
            self.handle_get_conversation(conv_id)
        elif path == "/api/skills":
            self.handle_list_skills()
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_get_skill(skill_id)
        elif path == "/" or path == "/index.html":
            self.serve_static("static/index.html", "text/html")
        elif path == "/styles.css":
            self.serve_static("static/styles.css", "text/css")
        elif path == "/app.js":
            self.serve_static("static/app.js", "application/javascript")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if path == "/api/config":
            self.handle_update_config(body)
        elif path == "/api/conversations":
            self.handle_create_conversation(body)
        elif path == "/api/conversations/import":
            self.handle_import_conversation(body)
        elif path == "/api/skills":
            self.handle_create_skill(body)
        elif path == "/api/attachments":
            self.handle_upload_attachment(body)
        elif path == "/api/chat":
            self.handle_chat(body)
        elif path == "/api/logout":
            self.handle_logout()
        else:
            self.send_error(404, "Not found")

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if path == "/api/config":
            self.handle_update_config(body)
        else:
            self.send_error(404, "Not found")

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if path.startswith("/api/conversations/"):
            conv_id = path.split("/")[3]
            self.handle_update_conversation(conv_id, body)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_update_skill(skill_id, body)
        else:
            self.send_error(404, "Not found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/conversations/"):
            conv_id = path.split("/")[3]
            self.handle_delete_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_delete_skill(skill_id)
        else:
            self.send_error(404, "Not found")

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def serve_static(self, filepath, mime_type):
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def handle_get_models(self):
        api_key = get_api_key()
        if not api_key:
            self.send_json_response({"error": "API key not configured"}, 401)
            return
        try:
            import openrouter
            models = openrouter.list_models(api_key)
            self.send_json_response(models)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)

    def handle_get_balance(self):
        api_key = get_api_key()
        if not api_key:
            self.send_json_response({"error": "API key not configured"}, 401)
            return
        try:
            import openrouter
            balance = openrouter.get_balance(api_key)
            self.send_json_response(balance)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)

    def handle_get_config(self):
        config = load_config()
        # Sanitize: do not expose full API key
        safe = config.copy()
        if safe.get("api_key"):
            safe["api_key"] = safe["api_key"][:8] + "..."
        self.send_json_response(safe)

    def handle_update_config(self, body):
        try:
            updates = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        config = load_config()
        config.update(updates)
        save_config(config)
        safe = config.copy()
        if safe.get("api_key"):
            safe["api_key"] = safe["api_key"][:8] + "..."
        self.send_json_response(safe)

    def handle_list_conversations(self):
        convs = list_conversations()
        self.send_json_response(convs)

    def handle_create_conversation(self, body):
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        conv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        conv = {
            "id": conv_id,
            "title": data.get("title", "New conversation"),
            "model": data.get("model", ""),
            "messages": [],
            "created_at": now,
            "updated_at": now
        }
        save_conversation(conv_id, conv)
        self.send_json_response(conv, 201)

    def handle_get_conversation(self, conv_id):
        conv = load_conversation(conv_id)
        if conv is None:
            self.send_json_response({"error": "Conversation not found"}, 404)
            return
        self.send_json_response(conv)

    def handle_update_conversation(self, conv_id, body):
        conv = load_conversation(conv_id)
        if conv is None:
            self.send_json_response({"error": "Conversation not found"}, 404)
            return
        try:
            updates = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        conv.update(updates)
        conv["updated_at"] = datetime.utcnow().isoformat() + "Z"
        save_conversation(conv_id, conv)
        self.send_json_response(conv)

    def handle_delete_conversation(self, conv_id):
        path = get_conversation_path(conv_id)
        if not os.path.exists(path):
            self.send_json_response({"error": "Conversation not found"}, 404)
            return
        os.remove(path)
        self.send_json_response({"status": "deleted"})

    def handle_import_conversation(self, body):
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        conv_id = data.get("id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat() + "Z"
        conv = {
            "id": conv_id,
            "title": data.get("title", "Imported conversation"),
            "model": data.get("model", ""),
            "messages": data.get("messages", []),
            "created_at": data.get("created_at", now),
            "updated_at": now
        }
        save_conversation(conv_id, conv)
        self.send_json_response(conv, 201)

    def handle_export_conversation(self, conv_id, fmt):
        conv = load_conversation(conv_id)
        if conv is None:
            self.send_json_response({"error": "Conversation not found"}, 404)
            return
        if fmt == "markdown":
            md = f"# {conv['title']}\n\n"
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                md += f"**{role.capitalize()}:** {content}\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Content-Disposition", f'attachment; filename="{conv_id}.md"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(md.encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", f'attachment; filename="{conv_id}.json"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(conv, indent=2).encode())

    def handle_list_skills(self):
        skills = load_skills()
        self.send_json_response(skills)

    def handle_get_skill(self, skill_id):
        skills = load_skills()
        for skill in skills:
            if skill.get("id") == skill_id:
                self.send_json_response(skill)
                return
        self.send_json_response({"error": "Skill not found"}, 404)

    def handle_create_skill(self, body):
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        skills = load_skills()
        skill_id = str(uuid.uuid4())
        skill = {
            "id": skill_id,
            "name": data.get("name", "New skill"),
            "prompt": data.get("prompt", ""),
            "enabled": data.get("enabled", True)
        }
        skills.append(skill)
        save_skills(skills)
        self.send_json_response(skill, 201)

    def handle_update_skill(self, skill_id, body):
        try:
            updates = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        skills = load_skills()
        for skill in skills:
            if skill.get("id") == skill_id:
                skill.update(updates)
                save_skills(skills)
                self.send_json_response(skill)
                return
        self.send_json_response({"error": "Skill not found"}, 404)

    def handle_delete_skill(self, skill_id):
        skills = load_skills()
        for i, skill in enumerate(skills):
            if skill.get("id") == skill_id:
                skills.pop(i)
                save_skills(skills)
                self.send_json_response({"status": "deleted"})
                return
        self.send_json_response({"error": "Skill not found"}, 404)

    def handle_upload_attachment(self, body):
        # Simple upload: expects JSON with "filename" and "content" (base64 or text)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        filename = data.get("filename", "upload.bin")
        content = data.get("content", "")
        import base64
        try:
            decoded = base64.b64decode(content)
        except Exception:
            decoded = content.encode()
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1]
        dest = os.path.join(ATTACHMENTS_DIR, f"{file_id}{ext}")
        with open(dest, "wb") as f:
            f.write(decoded)
        self.send_json_response({"id": file_id, "filename": filename, "path": dest}, 201)

    def handle_chat(self, body):
        api_key = get_api_key()
        if not api_key:
            self.send_json_response({"error": "API key not configured"}, 401)
            return
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return

        import openrouter
        model = data.get("model", "")
        messages = data.get("messages", [])
        skills = data.get("skills", [])

        # Prepend skill prompts as system messages
        for skill in skills:
            if skill.get("enabled", True) and skill.get("prompt"):
                messages.insert(0, {"role": "system", "content": skill["prompt"]})

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            for event in openrouter.stream_chat(api_key, model, messages):
                line = f"data: {json.dumps(event)}\n\n"
                self.wfile.write(line.encode())
                self.wfile.flush()
        except Exception as e:
            error_event = {"type": "error", "error": str(e)}
            self.wfile.write(f"data: {json.dumps(error_event)}\n\n".encode())
            self.wfile.flush()

    def handle_logout(self):
        """Clear the stored API key and return success."""
        config = load_config()
        config["api_key"] = ""
        save_config(config)
        self.send_json_response({"status": "logged_out", "message": "API key cleared. You are logged out."})

def run():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    server = http.server.HTTPServer((host, port), ChatHandler)
    print(f"Server running on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
