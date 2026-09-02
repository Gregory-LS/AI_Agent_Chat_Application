import os
import json
import hashlib
import secrets
import threading
import uuid
import mimetypes
import shutil
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import httpx

# --- Configuration ---
DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# --- User management ---
users_lock = threading.Lock()
sessions = {}  # token -> username

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    with users_lock:
        users = load_users()
        if username in users:
            return False, "Username already exists"
        users[username] = {"password": hash_password(password)}
        save_users(users)
        return True, "User created"

def authenticate(username, password):
    with users_lock:
        users = load_users()
        user = users.get(username)
        if user and user["password"] == hash_password(password):
            token = secrets.token_hex(32)
            sessions[token] = username
            return True, token
        return False, None

def validate_session(token):
    return sessions.get(token)

def logout(token):
    if token in sessions:
        del sessions[token]

# --- Config management ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"api_key": OPENROUTER_API_KEY, "default_model": "openai/gpt-4o"}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# --- Skills management ---
def load_skills():
    if not os.path.exists(SKILLS_FILE):
        return []
    with open(SKILLS_FILE, "r") as f:
        return json.load(f)

def save_skills(skills):
    with open(SKILLS_FILE, "w") as f:
        json.dump(skills, f, indent=2)

# --- Conversation management ---
def list_conversations():
    convs = []
    for fname in os.listdir(CONVERSATIONS_DIR):
        if fname.endswith(".json"):
            conv_id = fname[:-5]
            with open(os.path.join(CONVERSATIONS_DIR, fname), "r") as f:
                data = json.load(f)
            convs.append({"id": conv_id, "title": data.get("title", "New conversation"), "updated_at": data.get("updated_at", "")})
    convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return convs

def get_conversation(conv_id):
    path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def save_conversation(conv_id, data):
    path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def delete_conversation(conv_id):
    path = os.path.join(CONVERSATIONS_DIR, f"{conv_id}.json")
    if os.path.exists(path):
        os.remove(path)

# --- OpenRouter client ---
openrouter_client = None
def get_openrouter_client():
    global openrouter_client
    if openrouter_client is None:
        openrouter_client = OpenRouterClient()
    return openrouter_client

class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self):
        self.api_key = None
    
    def update_api_key(self, api_key):
        self.api_key = api_key
    
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Agentic Chat"
        }
    
    async def list_models(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/models", headers=self._headers())
            resp.raise_for_status()
            return resp.json()
    
    async def get_balance(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/credits", headers=self._headers())
            resp.raise_for_status()
            return resp.json()
    
    async def chat_stream(self, model, messages, **kwargs):
        body = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.BASE_URL}/chat/completions", json=body, headers=self._headers()) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield line[6:]

# --- Request handler ---
class Handler(BaseHTTPRequestHandler):
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
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        return path, query
    
    def _get_session_token(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None
    
    def _require_auth(self):
        token = self._get_session_token()
        username = validate_session(token)
        if not username:
            self._send_error("Unauthorized", 401)
            return None
        return username
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    
    def do_GET(self):
        path, query = self._parse_path()
        
        # Auth endpoints
        if path == "/api/auth/check":
            token = self._get_session_token()
            username = validate_session(token)
            if username:
                self._send_json({"authenticated": True, "username": username})
            else:
                self._send_json({"authenticated": False}, 401)
            return
        
        # Protected endpoints
        if path.startswith("/api/"):
            username = self._require_auth()
            if not username:
                return
        
        if path == "/api/models":
            config = load_config()
            api_key = config.get("api_key", "")
            if not api_key:
                self._send_error("API key not configured", 400)
                return
            client = get_openrouter_client()
            client.update_api_key(api_key)
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                models = loop.run_until_complete(client.list_models())
                self._send_json(models)
            except Exception as e:
                self._send_error(str(e), 500)
            finally:
                loop.close()
        elif path == "/api/balance":
            config = load_config()
            api_key = config.get("api_key", "")
            if not api_key:
                self._send_error("API key not configured", 400)
                return
            client = get_openrouter_client()
            client.update_api_key(api_key)
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                balance = loop.run_until_complete(client.get_balance())
                self._send_json(balance)
            except Exception as e:
                self._send_error(str(e), 500)
            finally:
                loop.close()
        elif path == "/api/config":
            self._send_json(load_config())
        elif path == "/api/conversations":
            self._send_json(list_conversations())
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            conv_id = path.split("/")[3]
            conv = get_conversation(conv_id)
            if not conv:
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
        elif re.match(r"^/api/conversations/[a-f0-9-]+$", path):
            conv_id = path.split("/")[3]
            conv = get_conversation(conv_id)
            if not conv:
                self._send_error("Conversation not found", 404)
                return
            self._send_json(conv)
        elif path == "/api/skills":
            self._send_json(load_skills())
        elif re.match(r"^/api/skills/[a-f0-9-]+$", path):
            skill_id = path.split("/")[3]
            skills = load_skills()
            skill = next((s for s in skills if s["id"] == skill_id), None)
            if not skill:
                self._send_error("Skill not found", 404)
                return
            self._send_json(skill)
        elif path.startswith("/static/") or path == "/" or path == "":
            self._serve_static(path)
        else:
            self._send_error("Not found", 404)
    
    def do_POST(self):
        path, query = self._parse_path()
        
        # Auth endpoints
        if path == "/api/auth/register":
            body = json.loads(self._read_body())
            username = body.get("username", "").strip()
            password = body.get("password", "")
            if not username or not password:
                self._send_error("Username and password required")
                return
            success, msg = create_user(username, password)
            if success:
                self._send_json({"message": msg}, 201)
            else:
                self._send_error(msg, 409)
            return
        
        if path == "/api/auth/login":
            body = json.loads(self._read_body())
            username = body.get("username", "").strip()
            password = body.get("password", "")
            if not username or not password:
                self._send_error("Username and password required")
                return
            success, token = authenticate(username, password)
            if success:
                self._send_json({"token": token, "username": username})
            else:
                self._send_error("Invalid credentials", 401)
            return
        
        if path == "/api/auth/logout":
            token = self._get_session_token()
            logout(token)
            self._send_json({"message": "Logged out"})
            return
        
        # Protected endpoints
        username = self._require_auth()
        if not username:
            return
        
        if path == "/api/config":
            config = load_config()
            body = json.loads(self._read_body())
            config.update(body)
            save_config(config)
            self._send_json(config)
        elif path == "/api/conversations":
            body = json.loads(self._read_body())
            conv_id = str(uuid.uuid4())
            conv = {
                "id": conv_id,
                "title": body.get("title", "New conversation"),
                "messages": [],
                "created_at": body.get("created_at", ""),
                "updated_at": body.get("updated_at", ""),
                "model": body.get("model", "openai/gpt-4o")
            }
            save_conversation(conv_id, conv)
            self._send_json(conv, 201)
        elif path == "/api/conversations/import":
            body = json.loads(self._read_body())
            conv_id = body.get("id", str(uuid.uuid4()))
            save_conversation(conv_id, body)
            self._send_json(body, 201)
        elif path == "/api/skills":
            body = json.loads(self._read_body())
            skills = load_skills()
            skill = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", "Unnamed skill"),
                "prompt": body.get("prompt", ""),
                "enabled": body.get("enabled", True)
            }
            skills.append(skill)
            save_skills(skills)
            self._send_json(skill, 201)
        elif path == "/api/attachments":
            # Parse multipart form data
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self._send_error("Expected multipart/form-data")
                return
            boundary = content_type.split("boundary=")[1].strip()
            body = self._read_body()
            # Simple multipart parser
            parts = body.split(b"--" + boundary.encode())
            for part in parts:
                if b"Content-Disposition" not in part:
                    continue
                headers_part, _, data = part.partition(b"\r\n\r\n")
                data = data.rstrip(b"\r\n--")
                disposition = headers_part.decode()
                if 'name="file"' in disposition:
                    filename = ""
                    for line in disposition.split("\r\n"):
                        if "filename=" in line:
                            filename = line.split("filename=")[1].strip('"')
                    if not filename:
                        filename = "upload"
                    file_id = str(uuid.uuid4())
                    ext = os.path.splitext(filename)[1]
                    stored_name = f"{file_id}{ext}"
                    path = os.path.join(ATTACHMENTS_DIR, stored_name)
                    with open(path, "wb") as f:
                        f.write(data)
                    self._send_json({"id": file_id, "filename": filename, "stored_name": stored_name, "size": len(data)}, 201)
                    return
            self._send_error("No file found")
        elif path == "/api/chat":
            body = json.loads(self._read_body())
            model = body.get("model", "openai/gpt-4o")
            messages = body.get("messages", [])
            config = load_config()
            api_key = config.get("api_key", "")
            if not api_key:
                self._send_error("API key not configured", 400)
                return
            client = get_openrouter_client()
            client.update_api_key(api_key)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                async def stream():
                    async for data in client.chat_stream(model, messages):
                        self.wfile.write(f"data: {data}\n\n".encode())
                        self.wfile.flush()
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                loop.run_until_complete(stream())
            except Exception as e:
                self.wfile.write(f"data: {{\"error\": \"{str(e)}\"}}\n\n".encode())
                self.wfile.flush()
            finally:
                loop.close()
        else:
            self._send_error("Not found", 404)
    
    def do_PUT(self):
        path, query = self._parse_path()
        username = self._require_auth()
        if not username:
            return
        if path == "/api/config":
            config = load_config()
            body = json.loads(self._read_body())
            config.update(body)
            save_config(config)
            self._send_json(config)
        else:
            self._send_error("Not found", 404)
    
    def do_PATCH(self):
        path, query = self._parse_path()
        username = self._require_auth()
        if not username:
            return
        if re.match(r"^/api/conversations/[a-f0-9-]+$", path):
            conv_id = path.split("/")[3]
            conv = get_conversation(conv_id)
            if not conv:
                self._send_error("Conversation not found", 404)
                return
            body = json.loads(self._read_body())
            conv.update(body)
            save_conversation(conv_id, conv)
            self._send_json(conv)
        elif re.match(r"^/api/skills/[a-f0-9-]+$", path):
            skill_id = path.split("/")[3]
            skills = load_skills()
            skill = next((s for s in skills if s["id"] == skill_id), None)
            if not skill:
                self._send_error("Skill not found", 404)
                return
            body = json.loads(self._read_body())
            skill.update(body)
            save_skills(skills)
            self._send_json(skill)
        else:
            self._send_error("Not found", 404)
    
    def do_DELETE(self):
        path, query = self._parse_path()
        username = self._require_auth()
        if not username:
            return
        if re.match(r"^/api/conversations/[a-f0-9-]+$", path):
            conv_id = path.split("/")[3]
            delete_conversation(conv_id)
            self._send_json({"message": "Deleted"})
        elif re.match(r"^/api/skills/[a-f0-9-]+$", path):
            skill_id = path.split("/")[3]
            skills = load_skills()
            skills = [s for s in skills if s["id"] != skill_id]
            save_skills(skills)
            self._send_json({"message": "Deleted"})
        else:
            self._send_error("Not found", 404)
    
    def _serve_static(self, path):
        if path == "/" or path == "":
            path = "/static/index.html"
        file_path = path.lstrip("/")
        if not os.path.exists(file_path):
            self._send_error("Not found", 404)
            return
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"
        with open(file_path, "rb") as f:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(f.read())
    
    def _conv_to_markdown(self, conv):
        lines = [f"# {conv.get('title', 'Conversation')}\n"]
        for msg in conv.get("messages", []):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"**{role.capitalize()}:** {content}\n")
        return "\n".join(lines)
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

def run_server():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Server running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_server()