#!/usr/bin/env python3
"""TaskBuddy server.

A tiny HTTP server that serves a polished front-end and a simulated JSON API.
Uses only the Python standard library, so no dependencies need to be installed.
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


def _is_relative_to(path: Path, directory: Path) -> bool:
    """Return True if *path* is inside *directory* (works on older Python)."""
    try:
        common = os.path.commonpath([str(path.resolve()), str(directory.resolve())])
    except ValueError:
        return False
    return common == str(directory.resolve())


class AppHandler(BaseHTTPRequestHandler):
    """HTTP request handler for TaskBuddy."""

    def do_GET(self) -> None:  # noqa: N802 - name is part of BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/data":
            self._handle_api(parsed)
        elif path == "/":
            self._serve_file(ROOT / "index.html")
        elif path.startswith("/static/"):
            relative = path[len("/static/"):]
            requested = (ROOT / "static" / relative).resolve()
            static_root = (ROOT / "static").resolve()
            if not _is_relative_to(requested, static_root):
                self.send_error(403, "Forbidden")
            else:
                self._serve_file(requested)
        else:
            self.send_error(404, "Not Found")

    def _serve_file(self, file_path: Path) -> None:
        """Serve a static file if it exists."""
        if not file_path.is_file():
            self.send_error(404, "Not Found")
            return

        ext = file_path.suffix
        content_type = MIME_TYPES.get(ext, "application/octet-stream")
        body = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _handle_api(self, parsed) -> None:
        """Handle the /api/data endpoint."""
        params = parse_qs(parsed.query)

        if params.get("fail", ["0"])[0] == "1":
            self.send_error(500, "Simulated server error")
            return

        try:
            delay = min(max(float(params.get("delay", ["0.6"])[0]), 0.0), 3.0)
        except ValueError:
            delay = 0.6

        time.sleep(delay)

        payload = {
            "message": "Data loaded successfully",
            "items": [
                {"id": 1, "title": "Design the UI"},
                {"id": 2, "title": "Implement loading state"},
                {"id": 3, "title": "Add error toast"},
                {"id": 4, "title": "Audit accessibility"},
            ],
        }
        body = json.dumps(payload).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        """Suppress request logging so tests remain quiet."""
        pass


def create_server(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    """Create a TaskBuddy HTTP server."""
    return ThreadingHTTPServer((host, port), AppHandler)


def main() -> None:
    """Run the TaskBuddy server on localhost."""
    port = int(os.environ.get("PORT", "8000"))
    server = create_server(host="127.0.0.1", port=port)
    url = f"http://127.0.0.1:{port}"
    print(f"TaskBuddy is running at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down TaskBuddy.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
