"""Claude-style chat + skills web app - OpenRouter backend.

Run:
    pip install httpx
    set OPENROUTER_API_KEY=sk-...
    python server.py
    open http://localhost:8000

Stdlib HTTP server + httpx. Windows-friendly, UTF-8 everywhere.
The OpenRouter API key stays server-side; the browser never sees it.
"""

from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import re
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
CONVERSATIONS = DATA / "conversations"
ATTACHMENTS = DATA / "attachments"
CONFIG_FILE = DATA / "config.json"
SKILLS_FILE = DATA / "skills.json"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_TEXT_BYTES = 500 * 1024
IMAGE_TYPES = {"png", "jpeg", "jpg", "webp", "gif"}
TEXT_TYPES = {"txt", "md", "py", "js", "ts", "html", "css", "json", "yml", "yaml", "toml", "sh", "sql",
              "c", "cpp", "h", "java", "go", "rs"}

TIMEOUT = httpx.Timeout(120.0, connect=30.0)

DATA.mkdir(parents=True, exist_ok=True)
CONVERSATIONS.mkdir(parents=True, exist_ok=True)
ATTACHMENTS.mkdir(parents=True, exist_ok=True)

DEFAULT_SKILLS = [
    {"id": "code-review", "name": "Code Review", "description": "Critique code for bugs, security, and style.",
     "prompt": "You are acting under the 'Code Review' skill. Review any provided code for correctness, security issues, edge cases, and readability. Be specific and suggest concrete fixes."},
    {"id": "unit-tests", "name": "Write Unit Tests", "description": "Generate thorough unit tests.",
     "prompt": "You are acting under the 'Write Unit Tests' skill. Produce complete, runnable unit tests covering happy paths, edge cases, and failures."},
    {"id": "refactor", "name": "Refactor", "description": "Improve structure without changing behavior.",
     "prompt": "You are acting under the 'Refactor' skill. Improve structure, naming, and cohesion while preserving behavior. Prefer small, explainable changes."},
    {"id": "eli5", "name": "Explain Like I'm 5", "description": "Explain complex topics simply.",
     "prompt": "You are acting under the 'Explain Like I'm 5' skill. Explain complex subjects with simple language, vivid analogies, and short sentences."},
    {"id": "regex-builder", "name": "Regex Builder", "description": "Build and explain regular expressions.",
     "prompt": "You are acting under the 'Regex Builder' skill. Provide a regex with a breakdown and test examples."},
    {"id": "sql-assistant", "name": "SQL Assistant", "description": "Write and review SQL queries.",
     "prompt": "You are acting under the 'SQL Assistant' skill. Write clear, efficient SQL and explain what each part does."},
    {"id": "summarize", "name": "Summarize This", "description": "Summarize long text into key points.",
     "prompt": "You are acting under the 'Summarize This' skill. Produce a concise summary of key points, decisions, and open questions."},
]
# --------------------------------------------------------------------------- helpers
def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _config() -> dict[str, Any]:
    cfg = _load_json(CONFIG_FILE, {})
    cfg.setdefault("api_key", os.getenv("OPENROUTER_API_KEY", ""))
    return cfg


def _save_config(cfg: dict[str, Any]) -> None:
    if cfg.get("api_key") == os.getenv("OPENROUTER_API_KEY", ""):
        cfg.pop("api_key", None)
    _save_json(CONFIG_FILE, cfg)


def _api_key() -> str:
    return _config().get("api_key") or os.getenv("OPENROUTER_API_KEY", "")


def _skills() -> list[dict[str, Any]]:
    data = _load_json(SKILLS_FILE, None)
    if data is None:
        _save_json(SKILLS_FILE, DEFAULT_SKILLS)
        return [dict(s) for s in DEFAULT_SKILLS]
    return data


def _save_skills(skills: list[dict[str, Any]]) -> None:
    _save_json(SKILLS_FILE, skills)


def _load_conversation(cid: str) -> dict[str, Any] | None:
    path = CONVERSATIONS / f"{cid}.json"
    if not path.exists() or not path.is_file():
        return None
    return _load_json(path, None)


def _save_conversation(convo: dict[str, Any]) -> None:
    _save_json(CONVERSATIONS / f"{convo['id']}.json", convo)


def _new_conversation() -> dict[str, Any]:
    now = int(time.time() * 1000)
    cid = f"{now:x}{os.urandom(3).hex()}"
    return {
        "id": cid, "title": "New chat", "created": now, "updated": now,
        "model": _config().get("default_model", ""), "system_prompt": "",
        "skills": [], "reasoning": False, "temperature": 0.7, "max_tokens": 4096,
        "messages": [], "archived": False,
    }


def _list_conversations() -> list[dict[str, Any]]:
    convos = []
    for p in CONVERSATIONS.glob("*.json"):
        data = _load_json(p, None)
        if isinstance(data, dict):
            convos.append(data)
    convos.sort(key=lambda c: c.get("updated", 0), reverse=True)
    return convos


def _safe_cid(cid: str) -> str | None:
    return cid if re.fullmatch(r"[0-9a-f]{12,16}", cid) else None
# --------------------------------------------------------------------------- OpenRouter helpers
def _attachment_blocks(attachments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for att in attachments or []:
        if str(att.get("type", "text")) == "image":
            data = str(att.get("data", ""))
            if data:
                blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{att.get('mime', 'image/png')};base64,{data}"},
                })
        else:
            text = str(att.get("content", ""))
            if text:
                blocks.append({"type": "text", "text": f"[Attachment: {att.get('label', att.get('name', 'file'))}]\n\n{text}"})
    return blocks


def _build_messages(convo: dict[str, Any], new_content: str, attachments_raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    skills = {s["id"]: s for s in _skills()}
    enabled = [skills[sid] for sid in convo.get("skills", []) if sid in skills]
    system_parts = ["You are a helpful, thoughtful assistant in a Claude-style chat app."]
    if convo.get("system_prompt", "").strip():
        system_parts.append(f"## User system prompt\n{convo.get('system_prompt', '').strip()}")
    if enabled:
        skills_text = "\n\n".join(f"### {s['name']}\n{s['prompt']}" for s in enabled)
        system_parts.append(f"## Active skills\n{skills_text}")

    messages: list[dict[str, Any]] = [{"role": "system", "content": "\n\n".join(system_parts)}]
    for msg in convo.get("messages", []):
        role = "assistant" if msg.get("role") == "assistant" else "user"
        content = str(msg.get("content", ""))
        if msg.get("attachments"):
            blocks = [{"type": "text", "text": content or "(attachments sent)"}]
            blocks.extend(_attachment_blocks(msg.get("attachments", [])))
            messages.append({"role": role, "content": blocks})
        else:
            messages.append({"role": role, "content": content})

    if attachments_raw:
        blocks = [{"type": "text", "text": new_content or ""}]
        blocks.extend(_attachment_blocks(attachments_raw))
        messages.append({"role": "user", "content": blocks})
    else:
        messages.append({"role": "user", "content": new_content})

    meta = {"system": "\n\n".join(system_parts), "skills": [s["name"] for s in enabled]}
    return messages, meta


def _approximate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
async def _stream_openrouter(messages: list[dict[str, Any]], api_key: str, *, model: str,
                             temperature: float, max_tokens: int, reasoning: bool,
                             send: Any = None) -> dict[str, Any]:
    """Stream OpenRouter chat; push token/reasoning/usage events via ``send`` queue. Returns meta."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if reasoning and not model.endswith(":thinking"):
        payload["reasoning"] = {"enabled": True}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/",  # OpenRouter wants a referer
        "X-Title": "Agentic Chat App",
    }

    reasoning_text: list[str] = []
    content_parts: list[str] = []
    usage: dict[str, Any] = {}
    start = time.time()

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", f"{OPENROUTER_BASE}/chat/completions",
                                 headers=headers, json=payload, timeout=TIMEOUT) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"OpenRouter {resp.status_code}: {body}")
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choice = (chunk.get("choices") or [{}])[0]
                delta = choice.get("delta") or {}
                finish = choice.get("finish_reason")
                if chunk.get("usage"):
                    usage = chunk["usage"]
                r = delta.get("reasoning") or delta.get("reasoning_content")
                c = delta.get("content")
                if r:
                    reasoning_text.append(str(r))
                    if send is not None:
                        await send.put({"type": "reasoning", "text": str(r)})
                if c:
                    content_parts.append(str(c))
                    if send is not None:
                        await send.put({"type": "token", "text": str(c)})
                if finish:
                    break

    if not content_parts and not reasoning_text:
        raise RuntimeError("Model returned no content.")

    meta = {
        "model": model,
        "prompt_tokens": usage.get("prompt_tokens") or _approximate_tokens(str(messages)),
        "completion_tokens": usage.get("completion_tokens") or _approximate_tokens("".join(content_parts)),
        "latency_ms": int((time.time() - start) * 1000),
    }
    if send is not None:
        await send.put({"type": "usage", "usage": meta})
    return meta
# --------------------------------------------------------------------------- HTTP handler
def _json_response(handler: BaseHTTPRequestHandler, status: int, data: Any) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _error(handler: BaseHTTPRequestHandler, status: int, msg: str) -> None:
    _json_response(handler, status, {"error": msg})


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        return None
    if length <= 0 or length > 2 * 1024 * 1024:
        return None
    try:
        data = json.loads(handler.rfile.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None
class ChatHandler(BaseHTTPRequestHandler):
    server_version = "AgenticChat/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[http] {self.address_string()} - {fmt % args}")

    # ------------------------------------------------------------------ GET
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._static_file("index.html")
        elif path.startswith("/static/"):
            self._static_file(path[len("/static/"):])
        elif path == "/api/models":
            asyncio.run(self._api_models())
        elif path == "/api/balance":
            asyncio.run(self._api_balance())
        elif path == "/api/config":
            _json_response(self, 200, _config())
        elif path == "/api/conversations":
            self._list_conversations_api()
        elif path.startswith("/api/conversations/"):
            self._get_conversation_api(path)
        elif path == "/api/skills":
            _json_response(self, 200, _skills())
        elif path.startswith("/api/attachments/"):
            self._serve_attachment(path.split("/")[-1])
        else:
            _error(self, 404, "Not found")

    def _static_file(self, rel: str) -> None:
        rel = rel.lstrip("/")
        if not rel:
            rel = "index.html"
        path = (STATIC / rel).resolve()
        if not str(path).startswith(str(STATIC.resolve())) or not path.is_file():
            _error(self, 404, "Not found")
            return
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix == ".js":
            ctype = "text/javascript"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _list_conversations_api(self) -> None:
        q = urllib.parse.parse_qs(urlparse(self.path).query).get("q", [""])[0].strip().lower()
        convos = _list_conversations()
        if q:
            convos = [c for c in convos if q in c.get("title", "").lower()
                      or any(q in str(m.get("content", "")).lower() for m in c.get("messages", []))]
        _json_response(self, 200, [{
            "id": c["id"], "title": c.get("title", "New chat"), "created": c.get("created"),
            "updated": c.get("updated"), "archived": c.get("archived", False),
            "message_count": len(c.get("messages", [])),
        } for c in convos])

    def _get_conversation_api(self, path: str) -> None:
        cid = path.split("/")[-1]
        if not _safe_cid(cid):
            _error(self, 400, "Bad conversation id")
            return
        convo = _load_conversation(cid)
        if convo is None:
            _error(self, 404, "Conversation not found")
            return
        _json_response(self, 200, convo)

    def _serve_attachment(self, att_id: str) -> None:
        if not re.fullmatch(r"[0-9a-f]{12,16}", att_id):
            _error(self, 400, "Bad attachment id")
            return
        path = (ATTACHMENTS / att_id).resolve()
        if not str(path).startswith(str(ATTACHMENTS.resolve())) or not path.is_file():
            _error(self, 404, "Attachment not found")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    async def _api_models(self) -> None:
        key = _api_key()
        if not key:
            _error(self, 401, "No OpenRouter API key configured.")
            return
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{OPENROUTER_BASE}/models")
                resp.raise_for_status()
                data = resp.json()
            _json_response(self, 200, data.get("data", []))
        except Exception as exc:  # noqa: BLE001
            _error(self, 502, f"Failed to fetch models: {exc}")

    async def _api_balance(self) -> None:
        key = _api_key()
        if not key:
            _error(self, 401, "No OpenRouter API key configured.")
            return
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{OPENROUTER_BASE}/auth/key",
                                        headers={"Authorization": f"Bearer {key}"})
                resp.raise_for_status()
                data = resp.json()
            _json_response(self, 200, data.get("data", {}))
        except Exception as exc:  # noqa: BLE001
            _error(self, 502, f"Failed to fetch balance: {exc}")
# ------------------------------------------------------------------ POST
    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/conversations":
            self._create_conversation()
        elif path == "/api/conversations/import":
            self._import_conversation()
        elif path.startswith("/api/conversations/") and path.endswith("/export"):
            self._export_conversation(path.split("/")[-2])
        elif path == "/api/skills":
            self._create_skill()
        elif path == "/api/attachments":
            self._upload_attachment()
        elif path == "/api/chat":
            self._chat_sse()
        else:
            _error(self, 404, "Not found")

    def _create_conversation(self) -> None:
        body = _read_json_body(self) or {}
        convo = _new_conversation()
        if body.get("model"):
            convo["model"] = str(body["model"])
        if body.get("title"):
            convo["title"] = str(body["title"])[:120]
        _save_conversation(convo)
        _json_response(self, 201, convo)

    def _import_conversation(self) -> None:
        body = _read_json_body(self)
        if not body or "title" not in body:
            _error(self, 400, "Invalid conversation export")
            return
        convo = _new_conversation()
        for k in ("title", "model", "system_prompt", "skills", "reasoning", "temperature", "max_tokens", "messages", "archived"):
            if k in body:
                convo[k] = body[k]
        _save_conversation(convo)
        _json_response(self, 201, convo)

    def _export_conversation(self, cid: str) -> None:
        if not _safe_cid(cid):
            _error(self, 400, "Bad conversation id")
            return
        convo = _load_conversation(cid)
        if convo is None:
            _error(self, 404, "Conversation not found")
            return
        fmt = urllib.parse.parse_qs(urlparse(self.path).query).get("format", ["json"])[0]
        if fmt == "markdown":
            parts = [f"# {convo.get('title', 'Chat')}", ""]
            for m in convo.get("messages", []):
                who = "**User**" if m.get("role") == "user" else "**Assistant**"
                parts.append(f"{who}: {m.get('content', '')}")
            out = "\n".join(parts).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{cid}.md"')
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
        else:
            _json_response(self, 200, convo)

    def _create_skill(self) -> None:
        body = _read_json_body(self)
        if not body or not str(body.get("name", "")).strip():
            _error(self, 400, "Skill needs a name")
            return
        skills = _skills()
        if any(str(s.get("name", "")).strip().lower() == str(body["name"]).strip().lower() for s in skills):
            _error(self, 409, "Skill with that name already exists")
            return
        skill = {
            "id": str(body.get("id") or f"skill-{time.time():.0f}"),
            "name": str(body["name"]).strip()[:80],
            "description": str(body.get("description", "")).strip()[:300],
            "prompt": str(body.get("prompt", "")).strip(),
        }
        skills.append(skill)
        _save_skills(skills)
        _json_response(self, 201, skill)

    def _upload_attachment(self) -> None:
        body = _read_json_body(self)
        if not body:
            _error(self, 400, "Invalid attachment payload")
            return
        name = str(body.get("name", "file"))
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        try:
            raw = base64.b64decode(str(body.get("data", "")), validate=True)
        except Exception:  # noqa: BLE001
            _error(self, 400, "Invalid base64 data")
            return
        if ext in IMAGE_TYPES:
            if len(raw) > MAX_IMAGE_BYTES:
                _error(self, 413, "Image too large (max 4 MB)")
                return
            att_id = f"{int(time.time() * 1000):x}{os.urandom(2).hex()}"
            (ATTACHMENTS / att_id).write_bytes(raw)
            _json_response(self, 201, {"id": att_id, "type": "image", "name": name,
                                       "mime": f"image/{ext}" if ext != "jpg" else "image/jpeg", "size": len(raw)})
        elif ext in TEXT_TYPES:
            if len(raw) > MAX_TEXT_BYTES:
                _error(self, 413, "Text file too large (max 500 KB)")
                return
            att_id = f"{int(time.time() * 1000):x}{os.urandom(2).hex()}"
            _json_response(self, 201, {"id": att_id, "type": "text", "name": name, "mime": "text/plain",
                                       "content": raw.decode("utf-8", errors="replace"), "label": name})
        else:
            _error(self, 415, "Unsupported file type")
# ------------------------------------------------------------------ chat (SSE)
    def _chat_sse(self) -> None:
        """POST /api/chat — stream the OpenRouter response as SSE events."""
        body = _read_json_body(self)
        if not body:
            _error(self, 400, "Invalid request body")
            return
        api_key = _api_key()
        if not api_key:
            _error(self, 401, "No OpenRouter API key configured.")
            return
        cid = str(body.get("conversation_id") or "")
        if not _safe_cid(cid):
            _error(self, 400, "conversation_id is required")
            return
        convo = _load_conversation(cid)
        if convo is None:
            _error(self, 404, "Conversation not found")
            return
        model = str(body.get("model") or convo.get("model") or "").strip()
        if not model:
            _error(self, 400, "No model selected")
            return
        message = str(body.get("message") or "")
        if not message.strip():
            _error(self, 400, "Message is empty")
            return
        attachments = body.get("attachments") or []
        temperature = float(body.get("temperature", convo.get("temperature", 0.7)))
        max_tokens = int(body.get("max_tokens", convo.get("max_tokens", 4096)))
        reasoning = bool(body.get("reasoning", convo.get("reasoning", False)))

        convo.setdefault("messages", []).append({
            "role": "user", "content": message, "attachments": attachments or [],
            "ts": int(time.time() * 1000),
        })
        if convo.get("title") in (None, "", "New chat"):
            title = message.strip()
            convo["title"] = (title[:50] + "…") if len(title) > 50 else title
        convo["updated"] = int(time.time() * 1000)
        _save_conversation(convo)

        messages, _meta = _build_messages(convo, message, attachments)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        import queue as _queue  # noqa: PLC0415

        q: _queue.Queue = _queue.Queue()

        def sse(data_obj: dict[str, Any]) -> None:
            self.wfile.write(f"data: {json.dumps(data_obj, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()

        def run_producer() -> None:
            try:
                asyncio.run(_stream_openrouter(
                    messages, api_key, model=model, temperature=temperature,
                    max_tokens=max_tokens, reasoning=reasoning, send=q,
                ))
            except Exception as exc:  # noqa: BLE001
                _put_quiet(q, {"type": "error", "message": str(exc)})
            _put_quiet(q, {"type": "__end__"})

        t = threading.Thread(target=run_producer, daemon=True)
        t.start()

        collected: list[str] = []
        had_error = False
        while True:
            item = q.get()
            if item.get("type") == "__end__":
                break
            if item.get("type") == "error":
                had_error = True
            elif item.get("type") == "token":
                collected.append(str(item.get("text", "")))
            try:
                sse(item)
            except Exception:  # noqa: BLE001  client disconnected
                return
        t.join(timeout=5)

        if not had_error and collected:
            final = _load_conversation(cid)
            if final is not None:
                final.setdefault("messages", []).append({
                    "role": "assistant", "content": "".join(collected),
                    "model": model, "ts": int(time.time() * 1000),
                })
                final["updated"] = int(time.time() * 1000)
                _save_conversation(final)
        try:
            sse({"type": "done", "error": had_error})
        except Exception:  # noqa: BLE001
            pass
# ------------------------------------------------------------------ PATCH / DELETE
    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/config":
            body = _read_json_body(self) or {}
            cfg = _config()
            if "api_key" in body:
                cfg["api_key"] = str(body["api_key"])
            if "default_model" in body:
                cfg["default_model"] = str(body["default_model"])
            _save_config(cfg)
            _json_response(self, 200, cfg)
        elif path == "/api/skills":
            body = _read_json_body(self) or {}
            skills = _skills()
            sid = str(body.get("id", ""))
            name = str(body.get("name", "")).strip().lower()
            live = [s for s in skills if str(s.get("id", "")) == sid
                    or str(s.get("name", "")).strip().lower() == name]
            if not live:
                _error(self, 404, "Skill not found")
                return
            for k in ("name", "description", "prompt"):
                if k in body:
                    live[0][k] = str(body[k])
            _save_skills(skills)
            _json_response(self, 200, live[0])
        elif path.startswith("/api/conversations/"):
            cid = path.split("/")[-1]
            if not _safe_cid(cid):
                _error(self, 400, "Bad conversation id")
                return
            convo = _load_conversation(cid)
            if convo is None:
                _error(self, 404, "Conversation not found")
                return
            body = _read_json_body(self) or {}
            if "title" in body and isinstance(body["title"], str):
                convo["title"] = body["title"][:120]
            for k in ("model", "system_prompt", "skills", "reasoning", "temperature", "max_tokens", "archived"):
                if k in body:
                    convo[k] = body[k]
            if "messages" in body and isinstance(body["messages"], list):
                convo["messages"] = body["messages"]
            convo["updated"] = int(time.time() * 1000)
            _save_conversation(convo)
            _json_response(self, 200, convo)
        else:
            _error(self, 404, "Not found")

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/conversations/"):
            cid = path.split("/")[-1]
            if not _safe_cid(cid):
                _error(self, 400, "Bad conversation id")
                return
            convo_path = CONVERSATIONS / f"{cid}.json"
            if not convo_path.exists():
                _error(self, 404, "Conversation not found")
                return
            convo_path.unlink()
            _json_response(self, 200, {"ok": True})
        elif path.startswith("/api/skills/"):
            sid = urllib.parse.unquote(path.split("/")[-1])
            skills = _skills()
            nxt = [s for s in skills if str(s.get("id", "")) != sid
                   and str(s.get("name", "")).strip().lower() != sid.lower()]
            if len(nxt) == len(skills):
                _error(self, 404, "Skill not found")
                return
            _save_skills(nxt)
            _json_response(self, 200, {"ok": True})
        else:
            _error(self, 404, "Not found")


# --------------------------------------------------------------------------- helpers
def _put_quiet(q: Any, item: dict[str, Any]) -> None:
    try:
        q.put(item)
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- main
def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print(f"Agentic Chat running at http://{HOST}:{PORT}")
    print(f"  data dir: {DATA}")
    print("  press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()