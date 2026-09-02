import http.server
import json
import os
import urllib.parse
import uuid
from datetime import datetime, timezone

import httpx

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
DATA_DIR = "data"
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
SKILLS_PATH = os.path.join(DATA_DIR, "skills.json")
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")

os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def load_conversation(conv_id):
    path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def save_conversation(conv):
    path = os.path.join(CONVERSATIONS_DIR, f"{conv['id']}.json")
    with open(path, "w") as f:
        json.dump(conv, f, indent=2)


def delete_conversation(conv_id):
    path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def list_conversations():
    convs = []
    for fname in os.listdir(CONVERSATIONS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(CONVERSATIONS_DIR, fname), "r") as f:
                conv = json.load(f)
                convs.append(conv)
    convs.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return convs


def load_skills():
    if os.path.exists(SKILLS_PATH):
        with open(SKILLS_PATH, "r") as f:
            return json.load(f)
    return []


def save_skills(skills):
    with open(SKILLS_PATH, "w") as f:
        json.dump(skills, f, indent=2)


class ChatHandler(http.server.BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, message, status=400):
        self._send_json({"error": message}, status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return b""
        return self.rfile.read(length)

    def _parse_path(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)
        return path, query

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path, query = self._parse_path()

        if path == "/api/conversations":
            convs = list_conversations()
            self._send_json(convs)

        elif path.startswith("/api/conversations/"):
            parts = path.split("/")
            if len(parts) == 4 and parts[3]:
                conv_id = parts[3]
                conv = load_conversation(conv_id)
                if conv is None:
                    self._send_error("Conversation not found", 404)
                else:
                    self._send_json(conv)
            elif len(parts) == 5 and parts[3] and parts[4] == "export":
                conv_id = parts[3]
                conv = load_conversation(conv_id)
                if conv is None:
                    self._send_error("Conversation not found", 404)
                    return
                fmt = query.get("format", ["json"])[0]
                if fmt == "markdown":
                    md = self._conv_to_markdown(conv)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/markdown")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(md.encode())
                else:
                    self._send_json(conv)
            else:
                self._send_error("Not found", 404)

        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        path, query = self._parse_path()
        body = self._read_body()

        if path == "/api/conversations":
            data = json.loads(body) if body else {}
            conv_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            conv = {
                "id": conv_id,
                "title": data.get("title", "New conversation"),
                "messages": data.get("messages", []),
                "created_at": now,
                "updated_at": now,
                "model": data.get("model", ""),
                "system_prompt": data.get("system_prompt", "")
            }
            save_conversation(conv)
            self._send_json(conv, 201)

        elif path == "/api/conversations/import":
            data = json.loads(body) if body else {}
            if "id" not in data:
                self._send_error("Missing conversation id")
                return
            conv = data
            if "created_at" not in conv:
                conv["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in conv:
                conv["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_conversation(conv)
            self._send_json(conv, 201)

        else:
            self._send_error("Not found", 404)

    def do_PATCH(self):
        path, query = self._parse_path()
        body = self._read_body()

        if path.startswith("/api/conversations/"):
            parts = path.split("/")
            if len(parts) == 4 and parts[3]:
                conv_id = parts[3]
                conv = load_conversation(conv_id)
                if conv is None:
                    self._send_error("Conversation not found", 404)
                    return
                data = json.loads(body) if body else {}
                for key in ["title", "messages", "model", "system_prompt"]:
                    if key in data:
                        conv[key] = data[key]
                conv["updated_at"] = datetime.now(timezone.utc).isoformat()
                save_conversation(conv)
                self._send_json(conv)
            else:
                self._send_error("Not found", 404)
        else:
            self._send_error("Not found", 404)

    def do_DELETE(self):
        path, query = self._parse_path()

        if path.startswith("/api/conversations/"):
            parts = path.split("/")
            if len(parts) == 4 and parts[3]:
                conv_id = parts[3]
                if delete_conversation(conv_id):
                    self._send_json({"status": "deleted"})
                else:
                    self._send_error("Conversation not found", 404)
            else:
                self._send_error("Not found", 404)
        else:
            self._send_error("Not found", 404)

    def _conv_to_markdown(self, conv):
        lines = [f"# {conv.get('title', 'Conversation')}\n"]
        for msg in conv.get("messages", []):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"## {role.capitalize()}\n\n{content}\n")
        return "\n".join(lines)

    def log_message(self, format, *args):
        pass  # Suppress default logging


def run():
    server = http.server.HTTPServer((HOST, PORT), ChatHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
