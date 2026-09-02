import json
import os
import sys
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import httpx

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"api_key": "", "default_model": ""}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key():
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key
    config = load_config()
    return config.get("api_key", "")


def load_conversations():
    conversations = []
    if os.path.isdir(CONVERSATIONS_DIR):
        for fname in os.listdir(CONVERSATIONS_DIR):
            if fname.endswith(".json"):
                with open(os.path.join(CONVERSATIONS_DIR, fname), "r") as f:
                    conversations.append(json.load(f))
    return conversations


def save_conversation(conv):
    with open(os.path.join(CONVERSATIONS_DIR, f"{conv['id']}.json"), "w") as f:
        json.dump(conv, f, indent=2)


def load_skills():
    if os.path.exists(SKILLS_FILE):
        with open(SKILLS_FILE, "r") as f:
            return json.load(f)
    return []


def save_skills(skills):
    with open(SKILLS_FILE, "w") as f:
        json.dump(skills, f, indent=2)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return self.rfile.read(length).decode()
        return ""

    def _parse_path(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def _handle_cors(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._handle_cors()

    def do_GET(self):
        path, query = self._parse_path()
        if path == "/api/models":
            self._handle_get_models()
        elif path == "/api/balance":
            self._handle_get_balance()
        elif path == "/api/config":
            self._send_json(load_config())
        elif path == "/api/conversations":
            self._send_json(load_conversations())
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            self._handle_export_conversation(path, query)
        elif path.startswith("/api/conversations/"):
            conv_id = path.split("/")[-1]
            self._handle_get_conversation(conv_id)
        elif path == "/api/skills":
            self._send_json(load_skills())
        else:
            self._serve_static()

    def do_POST(self):
        path, query = self._parse_path()
        if path == "/api/logout":
            self._handle_logout()
        elif path == "/api/config":
            self._handle_put_config()
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
            self._send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        path, query = self._parse_path()
        if path == "/api/config":
            self._handle_put_config()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_PATCH(self):
        path, query = self._parse_path()
        if path.startswith("/api/conversations/"):
            conv_id = path.split("/")[-1]
            self._handle_patch_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[-1]
            self._handle_patch_skill(skill_id)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        path, query = self._parse_path()
        if path.startswith("/api/conversations/"):
            conv_id = path.split("/")[-1]
            self._handle_delete_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[-1]
            self._handle_delete_skill(skill_id)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_logout(self):
        config = load_config()
        config["api_key"] = ""
        save_config(config)
        self._send_json({"status": "ok"})

    def _handle_get_models(self):
        api_key = get_api_key()
        if not api_key:
            self._send_json({"error": "API key not set"}, 401)
            return
        try:
            resp = httpx.get(
                f"{OPENROUTER_BASE}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            if resp.status_code == 200:
                self._send_json(resp.json())
            else:
                self._send_json({"error": "Failed to fetch models"}, resp.status_code)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_get_balance(self):
        api_key = get_api_key()
        if not api_key:
            self._send_json({"error": "API key not set"}, 401)
            return
        try:
            resp = httpx.get(
                f"{OPENROUTER_BASE}/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self._send_json({"data": data.get("data", {})})
            else:
                self._send_json({"error": "Failed to fetch balance"}, resp.status_code)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_put_config(self):
        try:
            body = json.loads(self._read_body())
            current = load_config()
            current.update(body)
            save_config(current)
            self._send_json(current)
        except Exception as e:
            self._send_json({"error": str(e)}, 400)

    def _handle_create_conversation(self):
        try:
            body = json.loads(self._read_body())
            conv = {
                "id": str(uuid.uuid4()),
                "title": body.get("title", "New conversation"),
                "messages": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            save_conversation(conv)
            self._send_json(conv, 201)
        except Exception as e:
            self._send_json({"error": str(e)}, 400)

    def _handle_get_conversation(self, conv_id):
        path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self._send_json(json.load(f))
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_patch_conversation(self, conv_id):
        path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
        if not os.path.exists(path):
            self._send_json({"error": "Not found"}, 404)
            return
        try:
            body = json.loads(self._read_body())
            with open(path, "r") as f:
                conv = json.load(f)
            conv.update(body)
            conv["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_conversation(conv)
            self._send_json(conv)
        except Exception as e:
            self._send_json({"error": str(e)}, 400)

    def _handle_delete_conversation(self, conv_id):
        path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
        if os.path.exists(path):
            os.remove(path)
            self._send_json({"status": "deleted"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_export_conversation(self, path, query):
        parts = path.split("/")
        conv_id = parts[-2] if len(parts) >= 4 else None
        if not conv_id:
            self._send_json({"error": "Bad request"}, 400)
            return
        conv_path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
        if not os.path.exists(conv_path):
            self._send_json({"error": "Not found"}, 404)
            return
        with open(conv_path, "r") as f:
            conv = json.load(f)
        fmt = query.get("format", ["json"])[0]
        if fmt == "markdown":
            lines = [f"# {conv['title']}\n"]
            for msg in conv.get("messages", []):
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                lines.append(f"**{role}:** {content}\n")
            text = "\n".join(lines)
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(text.encode())
        else:
            self._send_json(conv)

    def _handle_import_conversation(self):
        try:
            body = json.loads(self._read_body())
            conv = body
            if "id" not in conv:
                conv["id"] = str(uuid.uuid4())
            conv["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_conversation(conv)
            self._send_json(conv, 201)
        except Exception as e:
            self._send_json({"error": str(e)}, 400)

    def _handle_create_skill(self):
        try:
            body = json.loads(self._read_body())
            skills = load_skills()
            skill = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", "New skill"),
                "prompt": body.get("prompt", ""),
                "enabled": body.get("enabled", True),
            }
            skills.append(skill)
            save_skills(skills)
            self._send_json(skill, 201)
        except Exception as e:
            self._send_json({"error": str(e)}, 400)

    def _handle_patch_skill(self, skill_id):
        skills = load_skills()
        for skill in skills:
            if skill["id"] == skill_id:
                try:
                    body = json.loads(self._read_body())
                    skill.update(body)
                    save_skills(skills)
                    self._send_json(skill)
                    return
                except Exception as e:
                    self._send_json({"error": str(e)}, 400)
                    return
        self._send_json({"error": "Not found"}, 404)

    def _handle_delete_skill(self, skill_id):
        skills = load_skills()
        for i, skill in enumerate(skills):
            if skill["id"] == skill_id:
                del skills[i]
                save_skills(skills)
                self._send_json({"status": "deleted"})
                return
        self._send_json({"error": "Not found"}, 404)

    def _handle_upload_attachment(self):
        # Simplified: expects multipart form with file
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json({"error": "Expected multipart/form-data"}, 400)
            return
        boundary = content_type.split("boundary=")[-1].strip()
        body = self.rfile.read(int(self.headers["Content-Length"]))
        # Very basic multipart parsing (for demo)
        try:
            # Find filename and content
            parts = body.split(b"\r\n")
            filename = None
            file_content = b""
            in_content = False
            for part in parts:
                if part.startswith(b"Content-Disposition"):
                    if b'filename="' in part:
                        start = part.find(b'filename="') + 10
                        end = part.find(b'"', start)
                        filename = part[start:end].decode()
                elif part == b"":
                    in_content = True
                    continue
                if in_content and part != b"--" + boundary.encode() and part != b"--" + boundary.encode() + b"--":
                    file_content += part + b"\r\n"
            if not filename:
                self._send_json({"error": "No file uploaded"}, 400)
                return
            file_id = str(uuid.uuid4())
            ext = os.path.splitext(filename)[1] or ".bin"
            dest = os.path.join(ATTACHMENTS_DIR, f"{file_id}{ext}")
            with open(dest, "wb") as f:
                f.write(file_content.rstrip(b"\r\n"))
            self._send_json({"id": file_id, "filename": filename, "path": dest}, 201)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_chat(self):
        api_key = get_api_key()
        if not api_key:
            self._send_json({"error": "API key not set"}, 401)
            return
        try:
            body = json.loads(self._read_body())
            model = body.get("model", "openai/gpt-4o")
            messages = body.get("messages", [])
            stream = body.get("stream", True)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
            }
            # Add skills if any
            skills = load_skills()
            enabled_skills = [s for s in skills if s.get("enabled", False)]
            if enabled_skills:
                system_prompts = [s["prompt"] for s in enabled_skills if s.get("prompt")]
                if system_prompts:
                    # Prepend system messages
                    payload["messages"] = [
                        {"role": "system", "content": "\n\n".join(system_prompts)}
                    ] + messages

            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with httpx.stream(
                    "POST",
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120,
                ) as resp:
                    for chunk in resp.iter_bytes():
                        self.wfile.write(chunk)
                        self.wfile.flush()
            else:
                resp = httpx.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                self._send_json(resp.json(), resp.status_code)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _serve_static(self):
        path = self.path.lstrip("/")
        if not path:
            path = "index.html"
        # Map / to static/index.html
        if path == "static/":
            path = "static/index.html"
        # Ensure we only serve from static/
        if not path.startswith("static/"):
            path = "static/" + path
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            ext = os.path.splitext(full_path)[1]
            content_type = {
                ".html": "text/html",
                ".css": "text/css",
                ".js": "application/javascript",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
            }.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        # Suppress default logging
        pass


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Server running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.shutdown()
