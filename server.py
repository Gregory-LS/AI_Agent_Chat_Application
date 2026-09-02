import http.server
import json
import os
import re
import shutil
import time
import urllib.parse
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("data")
CONFIG_FILE = DATA_DIR / "config.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
SKILLS_FILE = DATA_DIR / "skills.json"
ATTACHMENTS_DIR = DATA_DIR / "attachments"

DEFAULT_CONFIG = {
    "api_key": "",
    "default_model": "openai/gpt-4o",
    "theme": "dark",
}

for d in [DATA_DIR, CONVERSATIONS_DIR, ATTACHMENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

if not CONFIG_FILE.exists():
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)

if not SKILLS_FILE.exists():
    with open(SKILLS_FILE, "w") as f:
        json.dump([], f, indent=2)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_config():
    return load_json(CONFIG_FILE)

def save_config(cfg):
    save_json(CONFIG_FILE, cfg)

def get_skills():
    return load_json(SKILLS_FILE)

def save_skills(skills):
    save_json(SKILLS_FILE, skills)

def get_conversation(id_):
    path = CONVERSATIONS_DIR / f"{id_}.json"
    if not path.exists():
        return None
    return load_json(path)

def save_conversation(id_, data):
    path = CONVERSATIONS_DIR / f"{id_}.json"
    save_json(path, data)

def delete_conversation(id_):
    path = CONVERSATIONS_DIR / f"{id_}.json"
    if path.exists():
        path.unlink()

def list_conversations():
    convs = []
    for f in CONVERSATIONS_DIR.iterdir():
        if f.suffix == ".json":
            data = load_json(f)
            convs.append(data)
    convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return convs

def generate_id():
    return f"{int(time.time() * 1000):x}-{os.urandom(4).hex()}"

def get_api_key():
    cfg = get_config()
    key = cfg.get("api_key", "")
    if not key:
        key = os.environ.get("OPENROUTER_API_KEY", "")
    return key

# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class ChatHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/models":
            self.handle_get_models()
        elif path == "/api/balance":
            self.handle_get_balance()
        elif path == "/api/config":
            self.handle_get_config()
        elif path == "/api/conversations":
            self.handle_list_conversations()
        elif re.match(r"^/api/conversations/([^/]+)$", path):
            match = re.match(r"^/api/conversations/([^/]+)$", path)
            self.handle_get_conversation(match.group(1))
        elif re.match(r"^/api/conversations/([^/]+)/export$", path):
            match = re.match(r"^/api/conversations/([^/]+)/export$", path)
            fmt = params.get("format", ["json"])[0]
            self.handle_export_conversation(match.group(1), fmt)
        elif path == "/api/skills":
            self.handle_list_skills()
        elif re.match(r"^/api/skills/([^/]+)$", path):
            match = re.match(r"^/api/skills/([^/]+)$", path)
            self.handle_get_skill(match.group(1))
        else:
            self.serve_static()

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
            self.send_error(404, "Not Found")

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self.handle_update_config()
        elif re.match(r"^/api/conversations/([^/]+)$", path):
            match = re.match(r"^/api/conversations/([^/]+)$", path)
            self.handle_update_conversation(match.group(1))
        elif re.match(r"^/api/skills/([^/]+)$", path):
            match = re.match(r"^/api/skills/([^/]+)$", path)
            self.handle_update_skill(match.group(1))
        else:
            self.send_error(404, "Not Found")

    def do_PATCH(self):
        # Reuse PUT logic
        self.do_PUT()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if re.match(r"^/api/conversations/([^/]+)$", path):
            match = re.match(r"^/api/conversations/([^/]+)$", path)
            self.handle_delete_conversation(match.group(1))
        elif re.match(r"^/api/skills/([^/]+)$", path):
            match = re.match(r"^/api/skills/([^/]+)$", path)
            self.handle_delete_skill(match.group(1))
        else:
            self.send_error(404, "Not Found")

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def serve_static(self):
        path = self.path.lstrip("/")
        if not path:
            path = "static/index.html"
        elif not path.startswith("static/"):
            path = "static/" + path
        full_path = Path(path)
        if not full_path.exists() or not full_path.is_file():
            self.send_error(404, "Not Found")
            return
        content = full_path.read_bytes()
        if path.endswith(".html"):
            ctype = "text/html"
        elif path.endswith(".css"):
            ctype = "text/css"
        elif path.endswith(".js"):
            ctype = "application/javascript"
        else:
            ctype = "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def get_httpx_client(self):
        api_key = get_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return httpx.Client(headers=headers, timeout=30.0)

    # -----------------------------------------------------------------------
    # API handlers
    # -----------------------------------------------------------------------

    def handle_get_models(self):
        try:
            with self.get_httpx_client() as client:
                resp = client.get("https://openrouter.ai/api/v1/models")
                resp.raise_for_status()
                data = resp.json()
            self.send_json(data)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_get_balance(self):
        try:
            with self.get_httpx_client() as client:
                resp = client.get("https://openrouter.ai/api/v1/auth/key")
                resp.raise_for_status()
                data = resp.json()
            self.send_json(data)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_get_config(self):
        cfg = get_config()
        self.send_json(cfg)

    def handle_update_config(self):
        try:
            cfg = self.read_body()
            current = get_config()
            current.update(cfg)
            save_config(current)
            self.send_json(current)
        except Exception as e:
            self.send_json({"error": str(e)}, 400)

    def handle_list_conversations(self):
        convs = list_conversations()
        self.send_json(convs)

    def handle_create_conversation(self):
        try:
            data = self.read_body()
            id_ = generate_id()
            now = time.time()
            conv = {
                "id": id_,
                "title": data.get("title", "New conversation"),
                "model": data.get("model", ""),
                "messages": [],
                "created_at": now,
                "updated_at": now,
            }
            save_conversation(id_, conv)
            self.send_json(conv, 201)
        except Exception as e:
            self.send_json({"error": str(e)}, 400)

    def handle_get_conversation(self, id_):
        conv = get_conversation(id_)
        if conv is None:
            self.send_json({"error": "Not found"}, 404)
            return
        self.send_json(conv)

    def handle_update_conversation(self, id_):
        conv = get_conversation(id_)
        if conv is None:
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            updates = self.read_body()
            conv.update(updates)
            conv["updated_at"] = time.time()
            save_conversation(id_, conv)
            self.send_json(conv)
        except Exception as e:
            self.send_json({"error": str(e)}, 400)

    def handle_delete_conversation(self, id_):
        conv = get_conversation(id_)
        if conv is None:
            self.send_json({"error": "Not found"}, 404)
            return
        delete_conversation(id_)
        self.send_json({"status": "deleted"})

    def handle_import_conversation(self):
        try:
            data = self.read_body()
            id_ = data.get("id", generate_id())
            now = time.time()
            if "created_at" not in data:
                data["created_at"] = now
            data["updated_at"] = now
            data["id"] = id_
            save_conversation(id_, data)
            self.send_json(data, 201)
        except Exception as e:
            self.send_json({"error": str(e)}, 400)

    def handle_export_conversation(self, id_, fmt):
        conv = get_conversation(id_)
        if conv is None:
            self.send_json({"error": "Not found"}, 404)
            return
        if fmt == "markdown":
            md = self._conv_to_markdown(conv)
            body = md.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Content-Disposition", f'attachment; filename="{id_}.md"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_json(conv)

    def _conv_to_markdown(self, conv):
        lines = [f"# {conv.get('title', 'Conversation')}", ""]
        for msg in conv.get("messages", []):
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            lines.append(f"## {role}")
            lines.append("")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)

    def handle_list_skills(self):
        skills = get_skills()
        self.send_json(skills)

    def handle_get_skill(self, id_):
        skills = get_skills()
        for s in skills:
            if s.get("id") == id_:
                self.send_json(s)
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_create_skill(self):
        try:
            data = self.read_body()
            id_ = generate_id()
            skill = {
                "id": id_,
                "name": data.get("name", "Untitled skill"),
                "prompt": data.get("prompt", ""),
                "enabled": data.get("enabled", True),
            }
            skills = get_skills()
            skills.append(skill)
            save_skills(skills)
            self.send_json(skill, 201)
        except Exception as e:
            self.send_json({"error": str(e)}, 400)

    def handle_update_skill(self, id_):
        skills = get_skills()
        for s in skills:
            if s.get("id") == id_:
                try:
                    updates = self.read_body()
                    s.update(updates)
                    save_skills(skills)
                    self.send_json(s)
                except Exception as e:
                    self.send_json({"error": str(e)}, 400)
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_delete_skill(self, id_):
        skills = get_skills()
        for i, s in enumerate(skills):
            if s.get("id") == id_:
                skills.pop(i)
                save_skills(skills)
                self.send_json({"status": "deleted"})
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_upload_attachment(self):
        # Expect multipart/form-data with file field "file"
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_json({"error": "Expected multipart/form-data"}, 400)
            return
        boundary = content_type.split("boundary=")[1].strip()
        body = self.rfile.read(int(self.headers["Content-Length"]))
        # Simple multipart parser (no external deps)
        parts = body.split(f"--{boundary}".encode())
        file_data = None
        filename = None
        for part in parts:
            if b"Content-Disposition" not in part:
                continue
            header_end = part.find(b"\r\n\r\n")
            if header_end == -1:
                continue
            headers_raw = part[:header_end].decode("utf-8", errors="ignore")
            content = part[header_end + 4:]
            # Remove trailing \r\n
            if content.endswith(b"\r\n"):
                content = content[:-2]
            # Find filename
            m = re.search(r'filename="([^"]+)"', headers_raw)
            if m:
                filename = m.group(1)
                file_data = content
                break
        if file_data is None:
            self.send_json({"error": "No file uploaded"}, 400)
            return
        # Save to attachments dir
        id_ = generate_id()
        ext = Path(filename).suffix if filename else ".bin"
        save_path = ATTACHMENTS_DIR / f"{id_}{ext}"
        with open(save_path, "wb") as f:
            f.write(file_data)
        self.send_json({"id": id_, "filename": filename, "path": str(save_path)}, 201)

    def handle_chat(self):
        """Streaming chat via SSE."""
        try:
            body = self.read_body()
        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        model = body.get("model", "")
        messages = body.get("messages", [])
        stream = body.get("stream", True)
        conversation_id = body.get("conversation_id")

        if not model or not messages:
            self.send_json({"error": "Missing model or messages"}, 400)
            return

        api_key = get_api_key()
        if not api_key:
            self.send_json({"error": "API key not configured"}, 401)
            return

        # Prepare payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        # Add any extra params from request
        for key in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
            if key in body:
                payload[key] = body[key]

        # Send SSE response
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            with httpx.Client(headers={"Authorization": f"Bearer {api_key}"}, timeout=60.0) as client:
                with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions", json=payload) as resp:
                    if resp.status_code != 200:
                        error_body = resp.read().decode("utf-8", errors="ignore")
                        self._send_sse("error", {"status": resp.status_code, "body": error_body})
                        return
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                self._send_sse("done", {})
                                break
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                for choice in choices:
                                    delta = choice.get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        self._send_sse("chunk", {"content": content})
                                    if choice.get("finish_reason"):
                                        # Also send usage if present
                                        usage = data.get("usage")
                                        if usage:
                                            self._send_sse("usage", usage)
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            self._send_sse("error", {"message": str(e)})

        # Update conversation if id provided
        if conversation_id:
            conv = get_conversation(conversation_id)
            if conv:
                # Append user message and assistant response
                # (we don't have the full response here, so we just update timestamp)
                conv["updated_at"] = time.time()
                save_conversation(conversation_id, conv)

    def _send_sse(self, event_type, data):
        try:
            msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
        except BrokenPipeError:
            pass

    # -----------------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------------

    def log_message(self, format, *args):
        pass  # Suppress default logging


def run(host="0.0.0.0", port=8000):
    server = http.server.HTTPServer((host, port), ChatHandler)
    print(f"Server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    run(host, port)
