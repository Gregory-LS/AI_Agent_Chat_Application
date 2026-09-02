import json
import os
import uuid
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import httpx

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(exist_ok=True)
SKILLS_FILE = DATA_DIR / "skills.json"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(exist_ok=True)

if not SKILLS_FILE.exists():
    SKILLS_FILE.write_text("[]")
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text("{}")


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_api_key():
    config = load_config()
    return config.get("api_key") or os.environ.get("OPENROUTER_API_KEY", "")


class ChatHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/models":
            self.handle_models()
        elif path == "/api/balance":
            self.handle_balance()
        elif path == "/api/config":
            self.handle_get_config()
        elif path == "/api/conversations":
            self.handle_list_conversations()
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            conv_id = path.split("/")[3]
            fmt = params.get("format", ["json"])[0]
            self.handle_export_conversation(conv_id, fmt)
        elif path.startswith("/api/conversations/"):
            conv_id = path.split("/")[3]
            self.handle_get_conversation(conv_id)
        elif path == "/api/skills":
            self.handle_list_skills()
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_get_skill(skill_id)
        else:
            super().do_GET()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/config":
            self.handle_put_config()
        elif path.startswith("/api/conversations/"):
            conv_id = path.split("/")[3]
            self.handle_update_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_update_skill(skill_id)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/conversations":
            self.handle_create_conversation()
        elif path == "/api/conversations/import":
            self.handle_import_conversation()
        elif path == "/api/skills":
            self.handle_create_skill()
        elif path == "/api/attachments":
            self.handle_upload_attachment()
        elif path == "/api/chat":
            self.handle_chat()
        elif path == "/api/logout":
            self.handle_logout()
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/conversations/"):
            conv_id = path.split("/")[3]
            self.handle_delete_conversation(conv_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_delete_skill(skill_id)
        else:
            self.send_error(404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def handle_models(self):
        api_key = get_api_key()
        if not api_key:
            self.send_json({"error": "API key not configured"}, 401)
            return
        try:
            resp = httpx.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            self.send_json(resp.json())
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_balance(self):
        api_key = get_api_key()
        if not api_key:
            self.send_json({"error": "API key not configured"}, 401)
            return
        try:
            resp = httpx.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            self.send_json(resp.json())
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_get_config(self):
        config = load_config()
        # Never expose the full API key; mask it
        if "api_key" in config and config["api_key"]:
            config["api_key"] = config["api_key"][:8] + "..."
        self.send_json(config)

    def handle_put_config(self):
        body = self.read_body()
        config = load_config()
        if "api_key" in body:
            config["api_key"] = body["api_key"]
        if "default_model" in body:
            config["default_model"] = body["default_model"]
        if "theme" in body:
            config["theme"] = body["theme"]
        save_config(config)
        self.send_json({"status": "ok"})

    def handle_logout(self):
        config = load_config()
        config.pop("api_key", None)
        save_config(config)
        self.send_json({"status": "ok"})

    def handle_list_conversations(self):
        conversations = []
        for f in CONVERSATIONS_DIR.iterdir():
            if f.suffix == ".json":
                try:
                    data = json.loads(f.read_text())
                    conversations.append({"id": f.stem, **data})
                except:
                    pass
        self.send_json(conversations)

    def handle_create_conversation(self):
        body = self.read_body()
        conv_id = str(uuid.uuid4())
        conv = {
            "title": body.get("title", "New conversation"),
            "model": body.get("model", ""),
            "messages": [],
            "created_at": None,
            "updated_at": None,
        }
        (CONVERSATIONS_DIR / f"{conv_id}.json").write_text(json.dumps(conv, indent=2))
        self.send_json({"id": conv_id, **conv}, 201)

    def handle_get_conversation(self, conv_id):
        path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not path.exists():
            self.send_json({"error": "Not found"}, 404)
            return
        data = json.loads(path.read_text())
        self.send_json({"id": conv_id, **data})

    def handle_update_conversation(self, conv_id):
        path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not path.exists():
            self.send_json({"error": "Not found"}, 404)
            return
        body = self.read_body()
        existing = json.loads(path.read_text())
        existing.update(body)
        path.write_text(json.dumps(existing, indent=2))
        self.send_json({"id": conv_id, **existing})

    def handle_delete_conversation(self, conv_id):
        path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if path.exists():
            path.unlink()
        self.send_json({"status": "ok"})

    def handle_import_conversation(self):
        body = self.read_body()
        conv_id = str(uuid.uuid4())
        (CONVERSATIONS_DIR / f"{conv_id}.json").write_text(json.dumps(body, indent=2))
        self.send_json({"id": conv_id, **body}, 201)

    def handle_export_conversation(self, conv_id, fmt):
        path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not path.exists():
            self.send_json({"error": "Not found"}, 404)
            return
        data = json.loads(path.read_text())
        if fmt == "markdown":
            md = f"# {data.get('title', 'Conversation')}\n\n"
            for msg in data.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                md += f"**{role}:** {content}\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(md.encode())
        else:
            self.send_json({"id": conv_id, **data})

    def handle_list_skills(self):
        skills = json.loads(SKILLS_FILE.read_text())
        self.send_json(skills)

    def handle_get_skill(self, skill_id):
        skills = json.loads(SKILLS_FILE.read_text())
        for s in skills:
            if s["id"] == skill_id:
                self.send_json(s)
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_create_skill(self):
        body = self.read_body()
        skills = json.loads(SKILLS_FILE.read_text())
        skill = {
            "id": str(uuid.uuid4()),
            "name": body.get("name", ""),
            "prompt": body.get("prompt", ""),
            "enabled": body.get("enabled", True),
        }
        skills.append(skill)
        SKILLS_FILE.write_text(json.dumps(skills, indent=2))
        self.send_json(skill, 201)

    def handle_update_skill(self, skill_id):
        body = self.read_body()
        skills = json.loads(SKILLS_FILE.read_text())
        for i, s in enumerate(skills):
            if s["id"] == skill_id:
                skills[i].update(body)
                SKILLS_FILE.write_text(json.dumps(skills, indent=2))
                self.send_json(skills[i])
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_delete_skill(self, skill_id):
        skills = json.loads(SKILLS_FILE.read_text())
        skills = [s for s in skills if s["id"] != skill_id]
        SKILLS_FILE.write_text(json.dumps(skills, indent=2))
        self.send_json({"status": "ok"})

    def handle_upload_attachment(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        # Expect multipart; for simplicity, we save raw body as file
        att_id = str(uuid.uuid4())
        ext = ".bin"
        # Minimal attempt to detect extension from content-type
        content_type = self.headers.get("Content-Type", "")
        if "image/png" in content_type:
            ext = ".png"
        elif "image/jpeg" in content_type or "image/jpg" in content_type:
            ext = ".jpg"
        elif "image/gif" in content_type:
            ext = ".gif"
        elif "image/webp" in content_type:
            ext = ".webp"
        elif "text/plain" in content_type:
            ext = ".txt"
        elif "application/json" in content_type:
            ext = ".json"
        fname = f"{att_id}{ext}"
        (ATTACHMENTS_DIR / fname).write_bytes(body)
        self.send_json({"id": att_id, "filename": fname, "size": len(body)}, 201)

    def handle_chat(self):
        api_key = get_api_key()
        if not api_key:
            self.send_json({"error": "API key not configured"}, 401)
            return
        body = self.read_body()
        model = body.get("model", "openai/gpt-4o")
        messages = body.get("messages", [])
        # Append enabled skills as system messages
        skills = json.loads(SKILLS_FILE.read_text())
        for skill in skills:
            if skill.get("enabled", False):
                messages.insert(0, {"role": "system", "content": skill["prompt"]})
        # Handle attachments from messages (images)
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if part.get("type") == "image" and "file_id" in part:
                        # Load the image from disk and convert to base64 data URI
                        fname = part["file_id"]
                        fpath = ATTACHMENTS_DIR / fname
                        if fpath.exists():
                            import base64
                            data = fpath.read_bytes()
                            ext = fname.split(".")[-1] if "." in fname else "png"
                            mime = f"image/{ext}"
                            b64 = base64.b64encode(data).decode()
                            part["image_url"] = {"url": f"data:{mime};base64,{b64}"}
                            del part["file_id"]
        try:
            with httpx.Client(timeout=120) as client:
                with client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                    },
                ) as resp:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                self.wfile.write(b"event: done\ndata: {}\n\n")
                                self.wfile.flush()
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        event_data = json.dumps({"content": content})
                                        self.wfile.write(f"event: chunk\ndata: {event_data}\n\n".encode())
                                        self.wfile.flush()
                                # Check for usage
                                usage = chunk.get("usage")
                                if usage:
                                    self.wfile.write(f"event: usage\ndata: {json.dumps(usage)}\n\n".encode())
                                    self.wfile.flush()
                            except:
                                pass
        except Exception as e:
            self.send_json({"error": str(e)}, 500)


def run():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer((host, port), ChatHandler)
    print(f"Server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
