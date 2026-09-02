#!/usr/bin/env python3
"""
Agentic Chat - Backend server

Serves static frontend and proxies OpenRouter API calls.
"""

import json
import os
import sys
import time
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

DATA_DIR = Path("data")
CONFIG_FILE = DATA_DIR / "config.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
SKILLS_FILE = DATA_DIR / "skills.json"
ATTACHMENTS_DIR = DATA_DIR / "attachments"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# ---------------------------------------------------------------------------
# Data directory setup
# ---------------------------------------------------------------------------

DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)
if not SKILLS_FILE.exists():
    SKILLS_FILE.write_text("[]", encoding="utf-8")
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(json.dumps({"api_key": "", "default_model": ""}), encoding="utf-8")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config():
    """Load config from data/config.json."""
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return {"api_key": "", "default_model": ""}


def save_config(config):
    """Save config to data/config.json."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_api_key():
    """Get API key from environment or config."""
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key
    config = load_config()
    return config.get("api_key", "")


def make_openrouter_headers():
    """Build headers for OpenRouter API requests."""
    api_key = get_api_key()
    if not api_key:
        return None
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": f"http://localhost:{PORT}/",  # Required by OpenRouter
        "X-Title": "Agentic Chat",
    }

# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class ChatHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with API routes."""

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/models":
            self.handle_get_models()
        elif path == "/api/balance":
            self.handle_get_balance()
        elif path == "/api/config":
            self.handle_get_config()
        elif path.startswith("/api/conversations"):
            self.handle_get_conversations(parsed)
        elif path.startswith("/api/skills"):
            self.handle_get_skills()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/chat":
            self.handle_post_chat()
        elif path == "/api/config":
            self.handle_put_config()
        elif path == "/api/conversations":
            self.handle_post_conversations()
        elif path == "/api/conversations/import":
            self.handle_post_conversations_import()
        elif path == "/api/skills":
            self.handle_post_skills()
        elif path == "/api/attachments":
            self.handle_post_attachments()
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/config":
            self.handle_put_config()
        else:
            self.send_error(404)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/conversations/"):
            self.handle_patch_conversations(parsed)
        elif path.startswith("/api/skills/"):
            self.handle_patch_skills(parsed)
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/conversations/"):
            self.handle_delete_conversations(parsed)
        elif path.startswith("/api/skills/"):
            self.handle_delete_skills(parsed)
        else:
            self.send_error(404)

    # -----------------------------------------------------------------------
    # API: /api/models
    # -----------------------------------------------------------------------

    def handle_get_models(self):
        headers = make_openrouter_headers()
        if not headers:
            self.send_json({"error": "API key not configured"}, 401)
            return
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{OPENROUTER_BASE}/models", headers=headers)
            self.send_json(resp.json(), resp.status_code)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # -----------------------------------------------------------------------
    # API: /api/balance
    # -----------------------------------------------------------------------

    def handle_get_balance(self):
        headers = make_openrouter_headers()
        if not headers:
            self.send_json({"error": "API key not configured"}, 401)
            return
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{OPENROUTER_BASE}/auth/key", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # OpenRouter returns credits, usage, total
                self.send_json(data, 200)
            else:
                self.send_json({"error": "Failed to fetch balance"}, resp.status_code)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # -----------------------------------------------------------------------
    # API: /api/chat (SSE streaming)
    # -----------------------------------------------------------------------

    def handle_post_chat(self):
        headers = make_openrouter_headers()
        if not headers:
            self.send_json({"error": "API key not configured"}, 401)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        # Ensure model is specified
        if "model" not in payload:
            self.send_json({"error": "Model is required"}, 400)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            with httpx.Client(timeout=120) as client:
                with client.stream("POST", f"{OPENROUTER_BASE}/chat/completions",
                                   json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        error_body = resp.read().decode("utf-8", errors="replace")
                        self.wfile.write(f"data: {json.dumps({'type': 'error', 'error': error_body})}\n\n".encode())
                        self.wfile.flush()
                        return

                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                self.wfile.write(f"data: {json.dumps({'type': 'done'})}\n\n".encode())
                                self.wfile.flush()
                                break
                            try:
                                data = json.loads(data_str)
                                # Extract content delta
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        self.wfile.write(f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n".encode())
                                        self.wfile.flush()
                                # Check for usage
                                if "usage" in data:
                                    self.wfile.write(f"data: {json.dumps({'type': 'usage', 'usage': data['usage']})}\n\n".encode())
                                    self.wfile.flush()
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            self.wfile.write(f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n".encode())
            self.wfile.flush()

    # -----------------------------------------------------------------------
    # API: /api/config
    # -----------------------------------------------------------------------

    def handle_get_config(self):
        config = load_config()
        self.send_json(config, 200)

    def handle_put_config(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            new_config = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        config = load_config()
        config.update(new_config)
        save_config(config)
        self.send_json(config, 200)

    # -----------------------------------------------------------------------
    # API: /api/conversations
    # -----------------------------------------------------------------------

    def handle_get_conversations(self, parsed):
        path = parsed.path
        if path == "/api/conversations":
            conversations = []
            for file in CONVERSATIONS_DIR.iterdir():
                if file.suffix == ".json":
                    try:
                        conv = json.loads(file.read_text(encoding="utf-8"))
                        conversations.append(conv)
                    except (json.JSONDecodeError, OSError):
                        pass
            self.send_json(conversations, 200)
        else:
            # /api/conversations/:id
            parts = path.split("/")
            if len(parts) == 4:
                conv_id = parts[3]
                conv_path = CONVERSATIONS_DIR / f"{conv_id}.json"
                if conv_path.exists():
                    try:
                        conv = json.loads(conv_path.read_text(encoding="utf-8"))
                        self.send_json(conv, 200)
                    except (json.JSONDecodeError, OSError):
                        self.send_json({"error": "Failed to read conversation"}, 500)
                else:
                    self.send_json({"error": "Not found"}, 404)
            else:
                self.send_json({"error": "Invalid path"}, 400)

    def handle_post_conversations(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        conv_id = str(uuid.uuid4())
        data["id"] = conv_id
        data["created_at"] = time.time()
        data["updated_at"] = time.time()
        conv_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        conv_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.send_json(data, 201)

    def handle_post_conversations_import(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        conv_id = data.get("id", str(uuid.uuid4()))
        data["id"] = conv_id
        data["updated_at"] = time.time()
        conv_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        conv_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.send_json(data, 201)

    def handle_patch_conversations(self, parsed):
        parts = parsed.path.split("/")
        if len(parts) != 4:
            self.send_json({"error": "Invalid path"}, 400)
            return
        conv_id = parts[3]
        conv_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not conv_path.exists():
            self.send_json({"error": "Not found"}, 404)
            return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            updates = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        try:
            conv = json.loads(conv_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.send_json({"error": "Failed to read conversation"}, 500)
            return
        conv.update(updates)
        conv["updated_at"] = time.time()
        conv_path.write_text(json.dumps(conv, indent=2), encoding="utf-8")
        self.send_json(conv, 200)

    def handle_delete_conversations(self, parsed):
        parts = parsed.path.split("/")
        if len(parts) != 4:
            self.send_json({"error": "Invalid path"}, 400)
            return
        conv_id = parts[3]
        conv_path = CONVERSATIONS_DIR / f"{conv_id}.json"
        if not conv_path.exists():
            self.send_json({"error": "Not found"}, 404)
            return
        conv_path.unlink()
        self.send_json({"status": "deleted"}, 200)

    # -----------------------------------------------------------------------
    # API: /api/skills
    # -----------------------------------------------------------------------

    def handle_get_skills(self):
        try:
            skills = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            skills = []
        self.send_json(skills, 200)

    def handle_post_skills(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            new_skill = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        new_skill["id"] = str(uuid.uuid4())
        try:
            skills = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            skills = []
        skills.append(new_skill)
        SKILLS_FILE.write_text(json.dumps(skills, indent=2), encoding="utf-8")
        self.send_json(new_skill, 201)

    def handle_patch_skills(self, parsed):
        parts = parsed.path.split("/")
        if len(parts) != 4:
            self.send_json({"error": "Invalid path"}, 400)
            return
        skill_id = parts[3]
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            updates = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        try:
            skills = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            skills = []
        for skill in skills:
            if skill.get("id") == skill_id:
                skill.update(updates)
                SKILLS_FILE.write_text(json.dumps(skills, indent=2), encoding="utf-8")
                self.send_json(skill, 200)
                return
        self.send_json({"error": "Not found"}, 404)

    def handle_delete_skills(self, parsed):
        parts = parsed.path.split("/")
        if len(parts) != 4:
            self.send_json({"error": "Invalid path"}, 400)
            return
        skill_id = parts[3]
        try:
            skills = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            skills = []
        new_skills = [s for s in skills if s.get("id") != skill_id]
        if len(new_skills) == len(skills):
            self.send_json({"error": "Not found"}, 404)
            return
        SKILLS_FILE.write_text(json.dumps(new_skills, indent=2), encoding="utf-8")
        self.send_json({"status": "deleted"}, 200)

    # -----------------------------------------------------------------------
    # API: /api/attachments
    # -----------------------------------------------------------------------

    def handle_post_attachments(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        # Expect multipart form data with file
        import cgi
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_json({"error": "Expected multipart/form-data"}, 400)
            return
        fs = cgi.FieldStorage(fp=body, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
        file_item = fs.getfirst("file")
        if not file_item:
            self.send_json({"error": "No file provided"}, 400)
            return
        filename = file_item.filename or "upload"
        data = file_item.file.read()
        attachment_id = str(uuid.uuid4())
        ext = Path(filename).suffix if filename else ".bin"
        attachment_path = ATTACHMENTS_DIR / f"{attachment_id}{ext}"
        attachment_path.write_bytes(data)
        self.send_json({"id": attachment_id, "filename": filename, "path": str(attachment_path)}, 201)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def send_json(self, data, status=200):
        """Send a JSON response."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    server = HTTPServer((HOST, PORT), ChatHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
