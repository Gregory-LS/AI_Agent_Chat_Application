import json
import os
import uuid
import shutil
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import io

import httpx

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_ATTACHMENT_TYPES = {
    'image/png': 'image',
    'image/jpeg': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'text/plain': 'text',
    'text/csv': 'text',
    'text/html': 'text',
    'application/json': 'text',
    'application/javascript': 'text',
    'text/javascript': 'text',
    'application/xml': 'text',
    'text/xml': 'text',
    'text/markdown': 'text',
    'text/x-python': 'text',
    'text/x-java': 'text',
    'text/x-c': 'text',
    'text/x-c++': 'text',
    'text/x-ruby': 'text',
    'text/x-php': 'text',
    'text/x-go': 'text',
    'text/x-rust': 'text',
    'text/x-typescript': 'text',
    'text/x-sh': 'text',
    'text/x-yaml': 'text',
    'text/x-toml': 'text',
    'application/pdf': 'text',
}


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_skills():
    if os.path.exists(SKILLS_FILE):
        with open(SKILLS_FILE, "r") as f:
            return json.load(f)
    return []


def save_skills(skills):
    with open(SKILLS_FILE, "w") as f:
        json.dump(skills, f, indent=2)


def get_conversation_path(conversation_id):
    return os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")


def load_conversation(conversation_id):
    path = get_conversation_path(conversation_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def save_conversation(conversation):
    path = get_conversation_path(conversation["id"])
    with open(path, "w") as f:
        json.dump(conversation, f, indent=2)


def list_conversations():
    if not os.path.exists(CONVERSATIONS_DIR):
        return []
    conversations = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(CONVERSATIONS_DIR, filename), "r") as f:
                conversations.append(json.load(f))
    conversations.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return conversations


def get_openrouter_api_key(config):
    api_key = config.get("api_key") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OpenRouter API key not configured")
    return api_key


class ChatHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the chat application."""

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

        if path == "/" or path == "/index.html":
            self.serve_static("static/index.html", "text/html")
        elif path == "/styles.css":
            self.serve_static("static/styles.css", "text/css")
        elif path == "/app.js":
            self.serve_static("static/app.js", "application/javascript")
        elif path == "/api/models":
            self.handle_get_models()
        elif path == "/api/balance":
            self.handle_get_balance()
        elif path == "/api/config":
            self.handle_get_config()
        elif path == "/api/conversations":
            self.handle_list_conversations()
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            parts = path.split("/")
            conversation_id = parts[3]
            export_format = query.get("format", ["json"])[0]
            self.handle_export_conversation(conversation_id, export_format)
        elif path.startswith("/api/conversations/"):
            conversation_id = path.split("/")[3]
            self.handle_get_conversation(conversation_id)
        elif path == "/api/skills":
            self.handle_list_skills()
        elif path.startswith("/api/attachments/") and path.endswith("/download"):
            attachment_id = path.split("/")[3]
            self.handle_download_attachment(attachment_id)
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self.handle_update_config()
        elif path == "/api/conversations":
            self.handle_create_conversation()
        elif path == "/api/conversations/import":
            self.handle_import_conversation()
        elif path == "/api/skills":
            self.handle_create_skill()
        elif path == "/api/chat":
            self.handle_chat()
        elif path == "/api/attachments":
            self.handle_upload_attachment()
        else:
            self.send_error(404, "Not found")

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self.handle_update_config()
        elif path.startswith("/api/conversations/"):
            conversation_id = path.split("/")[3]
            self.handle_update_conversation(conversation_id)
        else:
            self.send_error(404, "Not found")

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/conversations/"):
            conversation_id = path.split("/")[3]
            self.handle_update_conversation(conversation_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_update_skill(skill_id)
        else:
            self.send_error(404, "Not found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/conversations/"):
            conversation_id = path.split("/")[3]
            self.handle_delete_conversation(conversation_id)
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/")[3]
            self.handle_delete_skill(skill_id)
        else:
            self.send_error(404, "Not found")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error(self, status, message):
        self.send_json({"error": message}, status)

    def serve_static(self, filepath, content_type):
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            return self.rfile.read(content_length)
        return b""

    def read_json_body(self):
        body = self.read_body()
        if body:
            return json.loads(body)
        return {}

    def handle_get_models(self):
        try:
            config = load_config()
            api_key = get_openrouter_api_key(config)
            headers = {"Authorization": f"Bearer {api_key}"}
            with httpx.Client() as client:
                resp = client.get("https://openrouter.ai/api/v1/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    self.send_json(data.get("data", data))
                else:
                    self.send_error(resp.status_code, "Failed to fetch models")
        except ValueError as e:
            self.send_error(401, str(e))
        except Exception as e:
            self.send_error(500, str(e))

    def handle_get_balance(self):
        try:
            config = load_config()
            api_key = get_openrouter_api_key(config)
            headers = {"Authorization": f"Bearer {api_key}"}
            with httpx.Client() as client:
                resp = client.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    self.send_json(data)
                else:
                    self.send_error(resp.status_code, "Failed to fetch balance")
        except ValueError as e:
            self.send_error(401, str(e))
        except Exception as e:
            self.send_error(500, str(e))

    def handle_get_config(self):
        config = load_config()
        # Don't expose the full API key in the response
        safe_config = {}
        for key, value in config.items():
            if key == "api_key" and value:
                safe_config[key] = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            else:
                safe_config[key] = value
        self.send_json(safe_config)

    def handle_update_config(self):
        try:
            data = self.read_json_body()
            config = load_config()
            config.update(data)
            save_config(config)
            self.send_json({"status": "ok"})
        except Exception as e:
            self.send_error(400, str(e))

    def handle_list_conversations(self):
        conversations = list_conversations()
        self.send_json(conversations)

    def handle_create_conversation(self):
        try:
            data = self.read_json_body()
            conversation = {
                "id": str(uuid.uuid4()),
                "title": data.get("title", "New conversation"),
                "model": data.get("model", "openai/gpt-4o"),
                "messages": [],
                "created_at": None,
                "updated_at": None
            }
            save_conversation(conversation)
            self.send_json(conversation, 201)
        except Exception as e:
            self.send_error(400, str(e))

    def handle_get_conversation(self, conversation_id):
        conversation = load_conversation(conversation_id)
        if conversation:
            self.send_json(conversation)
        else:
            self.send_error(404, "Conversation not found")

    def handle_update_conversation(self, conversation_id):
        try:
            conversation = load_conversation(conversation_id)
            if not conversation:
                self.send_error(404, "Conversation not found")
                return
            data = self.read_json_body()
            conversation.update(data)
            save_conversation(conversation)
            self.send_json(conversation)
        except Exception as e:
            self.send_error(400, str(e))

    def handle_delete_conversation(self, conversation_id):
        path = get_conversation_path(conversation_id)
        if os.path.exists(path):
            os.remove(path)
            self.send_json({"status": "deleted"})
        else:
            self.send_error(404, "Conversation not found")

    def handle_import_conversation(self):
        try:
            data = self.read_json_body()
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            save_conversation(data)
            self.send_json(data, 201)
        except Exception as e:
            self.send_error(400, str(e))

    def handle_export_conversation(self, conversation_id, export_format):
        conversation = load_conversation(conversation_id)
        if not conversation:
            self.send_error(404, "Conversation not found")
            return
        if export_format == "markdown":
            md = f"# {conversation.get('title', 'Conversation')}\n\n"
            for msg in conversation.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                md += f"**{role.capitalize()}:** {content}\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Disposition", f'attachment; filename="{conversation_id}.md"')
            self.end_headers()
            self.wfile.write(md.encode())
        else:
            self.send_json(conversation)

    def handle_list_skills(self):
        skills = load_skills()
        self.send_json(skills)

    def handle_create_skill(self):
        try:
            data = self.read_json_body()
            skill = {
                "id": str(uuid.uuid4()),
                "name": data.get("name", "New skill"),
                "prompt": data.get("prompt", ""),
                "enabled": data.get("enabled", True)
            }
            skills = load_skills()
            skills.append(skill)
            save_skills(skills)
            self.send_json(skill, 201)
        except Exception as e:
            self.send_error(400, str(e))

    def handle_update_skill(self, skill_id):
        try:
            data = self.read_json_body()
            skills = load_skills()
            for skill in skills:
                if skill["id"] == skill_id:
                    skill.update(data)
                    save_skills(skills)
                    self.send_json(skill)
                    return
            self.send_error(404, "Skill not found")
        except Exception as e:
            self.send_error(400, str(e))

    def handle_delete_skill(self, skill_id):
        skills = load_skills()
        for i, skill in enumerate(skills):
            if skill["id"] == skill_id:
                skills.pop(i)
                save_skills(skills)
                self.send_json({"status": "deleted"})
                return
        self.send_error(404, "Skill not found")

    def handle_upload_attachment(self):
        """Handle file upload for attachments.

        Accepts multipart/form-data with a 'file' field.
        Validates file type against ALLOWED_ATTACHMENT_TYPES.
        Saves file to data/attachments/ with a unique ID.
        Returns attachment metadata.

        Returns:
            JSON with id, filename, type (image/text), url, size.
        """
        try:
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self.send_error(400, "Expected multipart/form-data")
                return

            # Parse the multipart form data
            form_data = cgi.FieldStorage(
                fp=io.BytesIO(self.read_body()),
                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
                headers={"content-type": content_type},
            )

            if "file" not in form_data:
                self.send_error(400, "No file provided")
                return

            file_item = form_data["file"]
            if not file_item.filename:
                self.send_error(400, "No file selected")
                return

            # Read file data
            file_data = file_item.file.read()
            file_size = len(file_data)

            if file_size == 0:
                self.send_error(400, "File is empty")
                return

            if file_size > MAX_ATTACHMENT_SIZE:
                self.send_error(413, f"File too large. Maximum size is {MAX_ATTACHMENT_SIZE // (1024*1024)} MB")
                return

            # Determine MIME type
            mime_type = file_item.type or mimetypes.guess_type(file_item.filename)[0] or "application/octet-stream"

            # Check if file type is allowed
            if mime_type not in ALLOWED_ATTACHMENT_TYPES:
                self.send_error(400, f"File type '{mime_type}' is not allowed. Allowed types: images (png, jpeg, gif, webp), text/code files")
                return

            attachment_type = ALLOWED_ATTACHMENT_TYPES[mime_type]

            # Generate unique ID and save file
            attachment_id = str(uuid.uuid4())
            _, ext = os.path.splitext(file_item.filename)
            saved_filename = f"{attachment_id}{ext}"
            saved_path = os.path.join(ATTACHMENTS_DIR, saved_filename)

            with open(saved_path, "wb") as f:
                f.write(file_data)

            # Build response
            attachment = {
                "id": attachment_id,
                "filename": file_item.filename,
                "type": attachment_type,
                "mime_type": mime_type,
                "size": file_size,
                "url": f"/api/attachments/{attachment_id}/download",
            }

            self.send_json(attachment, 201)

        except Exception as e:
            self.send_error(500, f"Failed to upload attachment: {str(e)}")

    def handle_download_attachment(self, attachment_id):
        """Serve an attachment file for download."""
        try:
            # Find the file in the attachments directory
            for filename in os.listdir(ATTACHMENTS_DIR):
                if filename.startswith(attachment_id):
                    filepath = os.path.join(ATTACHMENTS_DIR, filename)
                    if os.path.isfile(filepath):
                        mime_type, _ = mimetypes.guess_type(filename)
                        if mime_type is None:
                            mime_type = "application/octet-stream"
                        with open(filepath, "rb") as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", mime_type)
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                        self.end_headers()
                        self.wfile.write(content)
                        return
            self.send_error(404, "Attachment not found")
        except Exception as e:
            self.send_error(500, str(e))

    def handle_chat(self):
        try:
            data = self.read_json_body()
            messages = data.get("messages", [])
            model = data.get("model", "openai/gpt-4o")
            config = load_config()
            api_key = get_openrouter_api_key(config)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
            }

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with httpx.Client() as client:
                with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions",
                                   headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_data = resp.json() if resp.headers.get("content-type") == "application/json" else {"error": "Unknown error"}
                        self.wfile.write(f"data: {json.dumps({'type': 'error', 'error': error_data.get('error', {}).get('message', 'Request failed')})}\n\n".encode())
                        return

                    for line in resp.iter_lines():
                        if line:
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    self.wfile.write(f"data: {json.dumps({'type': 'done'})}\n\n".encode())
                                    self.wfile.flush()
                                else:
                                    try:
                                        json_data = json.loads(data_str)
                                        choices = json_data.get("choices", [])
                                        if choices:
                                            delta = choices[0].get("delta", {})
                                            content = delta.get("content", "")
                                            if content:
                                                self.wfile.write(f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n".encode())
                                                self.wfile.flush()
                                    except json.JSONDecodeError:
                                        pass

        except ValueError as e:
            self.send_error(401, str(e))
        except Exception as e:
            self.send_error(500, str(e))


def run_server():
    ensure_dirs()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer((host, port), ChatHandler)
    print(f"Server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server shutting down...")
        server.server_close()


if __name__ == "__main__":
    run_server()
