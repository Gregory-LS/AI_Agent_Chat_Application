import http.server
import json
import os
import urllib.parse
import uuid
import shutil
import io
import base64
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
        json.dump({"api_key": "", "default_model": ""}, f)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def get_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_skills():
    with open(SKILLS_FILE, "r") as f:
        return json.load(f)

def save_skills(skills):
    with open(SKILLS_FILE, "w") as f:
        json.dump(skills, f, indent=2)

def get_conversations():
    convs = []
    for fname in os.listdir(CONVERSATIONS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(CONVERSATIONS_DIR, fname), "r") as f:
                convs.append(json.load(f))
    return convs

def get_conversation(cid):
    path = os.path.join(CONVERSATIONS_DIR, f"{cid}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_conversation(cid, data):
    path = os.path.join(CONVERSATIONS_DIR, f"{cid}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def delete_conversation(cid):
    path = os.path.join(CONVERSATIONS_DIR, f"{cid}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def get_headers():
    cfg = get_config()
    api_key = cfg.get("api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

class ChatHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/models":
            self.handle_models()
        elif path == "/api/balance":
            self.handle_balance()
        elif path == "/api/config":
            self.handle_get_config()
        elif path == "/api/conversations":
            self.handle_list_conversations()
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            parts = path.split("/")
            cid = parts[3]
            fmt = query.get("format", ["json"])[0]
            self.handle_export_conversation(cid, fmt)
        elif path.startswith("/api/conversations/"):
            cid = path.split("/")[3]
            self.handle_get_conversation(cid)
        elif path == "/api/skills":
            self.handle_list_skills()
        elif path.startswith("/api/skills/"):
            sid = path.split("/")[3]
            self.handle_get_skill(sid)
        elif path.startswith("/static/") or path == "/":
            self.serve_static(path)
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self.handle_update_config()
        elif path == "/api/conversations":
            self.handle_create_conversation()
        elif path == "/api/conversations/import":
            self.handle_import_conversation()
        elif path == "/api/skills":
            self.handle_create_skill()
        elif path == "/api/attachments":
            self.handle_upload_attachment()
        elif path == "/api/chat":
            self.handle_chat()
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self.handle_update_config()
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/conversations/"):
            cid = path.split("/")[3]
            self.handle_update_conversation(cid)
        elif path.startswith("/api/skills/"):
            sid = path.split("/")[3]
            self.handle_update_skill(sid)
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/conversations/"):
            cid = path.split("/")[3]
            self.handle_delete_conversation(cid)
        elif path.startswith("/api/skills/"):
            sid = path.split("/")[3]
            self.handle_delete_skill(sid)
        else:
            self.send_json({"error": "Not found"}, 404)

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

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return json.loads(self.rfile.read(length))
        return {}

    # --- API handlers ---

    def handle_models(self):
        headers = get_headers()
        if not headers["Authorization"]:
            self.send_json({"error": "API key not configured"}, 400)
            return
        try:
            resp = httpx.get(f"{OPENROUTER_BASE}/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                self.send_json(resp.json())
            else:
                self.send_json({"error": "Failed to fetch models"}, resp.status_code)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_balance(self):
        headers = get_headers()
        if not headers["Authorization"]:
            self.send_json({"error": "API key not configured"}, 400)
            return
        try:
            resp = httpx.get(f"{OPENROUTER_BASE}/auth/key", headers=headers, timeout=10)
            if resp.status_code == 200:
                self.send_json(resp.json())
            else:
                self.send_json({"error": "Failed to fetch balance"}, resp.status_code)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_get_config(self):
        self.send_json(get_config())

    def handle_update_config(self):
        cfg = self.read_body()
        existing = get_config()
        existing.update(cfg)
        save_config(existing)
        self.send_json(existing)

    def handle_list_conversations(self):
        convs = get_conversations()
        # Return only metadata (not full messages) for listing
        meta = []
        for c in convs:
            meta.append({"id": c.get("id"), "title": c.get("title", ""), "created": c.get("created", ""), "updated": c.get("updated", "")})
        self.send_json(meta)

    def handle_create_conversation(self):
        data = self.read_body()
        cid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conv = {
            "id": cid,
            "title": data.get("title", "New conversation"),
            "created": now,
            "updated": now,
            "messages": [],
        }
        save_conversation(cid, conv)
        self.send_json(conv, 201)

    def handle_get_conversation(self, cid):
        conv = get_conversation(cid)
        if conv:
            self.send_json(conv)
        else:
            self.send_json({"error": "Not found"}, 404)

    def handle_update_conversation(self, cid):
        conv = get_conversation(cid)
        if not conv:
            self.send_json({"error": "Not found"}, 404)
            return
        data = self.read_body()
        conv.update(data)
        conv["updated"] = datetime.utcnow().isoformat()
        save_conversation(cid, conv)
        self.send_json(conv)

    def handle_delete_conversation(self, cid):
        if delete_conversation(cid):
            self.send_json({"status": "deleted"})
        else:
            self.send_json({"error": "Not found"}, 404)

    def handle_export_conversation(self, cid, fmt):
        conv = get_conversation(cid)
        if not conv:
            self.send_json({"error": "Not found"}, 404)
            return
        if fmt == "markdown":
            md = f"# {conv.get('title', 'Conversation')}\n\n"
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                md += f"**{role.capitalize()}:** {content}\n\n"
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Content-Disposition", f'attachment; filename="{cid}.md"')
            self.end_headers()
            self.wfile.write(md.encode())
        else:
            self.send_json(conv)

    def handle_import_conversation(self):
        data = self.read_body()
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        cid = data["id"]
        now = datetime.utcnow().isoformat()
        if "created" not in data:
            data["created"] = now
        data["updated"] = now
        save_conversation(cid, data)
        self.send_json(data, 201)

    def handle_list_skills(self):
        self.send_json(get_skills())

    def handle_get_skill(self, sid):
        skills = get_skills()
        for s in skills:
            if s.get("id") == sid:
                self.send_json(s)
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_create_skill(self):
        data = self.read_body()
        sid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        skill = {
            "id": sid,
            "name": data.get("name", "New skill"),
            "prompt": data.get("prompt", ""),
            "created": now,
            "updated": now,
        }
        skills = get_skills()
        skills.append(skill)
        save_skills(skills)
        self.send_json(skill, 201)

    def handle_update_skill(self, sid):
        skills = get_skills()
        for i, s in enumerate(skills):
            if s.get("id") == sid:
                data = self.read_body()
                s.update(data)
                s["updated"] = datetime.utcnow().isoformat()
                skills[i] = s
                save_skills(skills)
                self.send_json(s)
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_delete_skill(self, sid):
        skills = get_skills()
        for i, s in enumerate(skills):
            if s.get("id") == sid:
                del skills[i]
                save_skills(skills)
                self.send_json({"status": "deleted"})
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_upload_attachment(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self.send_json({"error": "No file provided"}, 400)
            return
        # Read raw multipart or binary; for simplicity, expect base64 JSON
        data = self.read_body()
        filename = data.get("filename", "attachment")
        content_b64 = data.get("content", "")
        if not content_b64:
            self.send_json({"error": "No content"}, 400)
            return
        try:
            content = base64.b64decode(content_b64)
        except:
            self.send_json({"error": "Invalid base64"}, 400)
            return
        ext = os.path.splitext(filename)[1] or ".bin"
        aid = str(uuid.uuid4()) + ext
        path = os.path.join(ATTACHMENTS_DIR, aid)
        with open(path, "wb") as f:
            f.write(content)
        self.send_json({"id": aid, "filename": filename, "path": path}, 201)

    def handle_chat(self):
        data = self.read_body()
        model = data.get("model", "")
        messages = data.get("messages", [])
        stream = data.get("stream", True)

        headers = get_headers()
        if not headers["Authorization"]:
            self.send_json({"error": "API key not configured"}, 400)
            return

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            with httpx.Client(timeout=30) as client:
                with client.stream("POST", f"{OPENROUTER_BASE}/chat/completions", json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        error_body = resp.read().decode()
                        self.wfile.write(f"event: error\ndata: {json.dumps({'error': error_body})}\n\n".encode())
                        self.wfile.flush()
                        return
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                self.wfile.write("event: done\ndata: {}\n\n".encode())
                                self.wfile.flush()
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        self.wfile.write(f"event: chunk\ndata: {json.dumps({'content': content})}\n\n".encode())
                                        self.wfile.flush()
                                if "usage" in chunk:
                                    self.wfile.write(f"event: usage\ndata: {json.dumps(chunk['usage'])}\n\n".encode())
                                    self.wfile.flush()
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            self.wfile.write(f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n".encode())
            self.wfile.flush()

    def serve_static(self, path):
        if path == "/":
            path = "/static/index.html"
        # Remove leading /static/
        file_path = path.lstrip("/")
        if file_path.startswith("static/"):
            file_path = file_path[7:]
        full_path = os.path.join("static", file_path)
        if not os.path.exists(full_path) or os.path.isdir(full_path):
            self.send_json({"error": "Not found"}, 404)
            return
        ext = os.path.splitext(full_path)[1]
        mime_map = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }
        mime = mime_map.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", mime)
        self.end_headers()
        with open(full_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    server = http.server.HTTPServer((host, port), ChatHandler)
    print(f"Server running on http://{host}:{port}")
    server.serve_forever()
