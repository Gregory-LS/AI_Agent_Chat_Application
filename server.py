'''OpenRouter proxy with SSE streaming.'''
from __future__ import annotations

import json
import os
from typing import Iterator, Optional

import requests
from flask import Flask, Response, jsonify, request, stream_with_context

DEFAULT_OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'


def create_app(
    openrouter_url: Optional[str] = None,
    openrouter_api_key: Optional[str] = None,
) -> Flask:
    '''Create and configure the Flask application.'''
    app = Flask(__name__)
    app.config['OPENROUTER_URL'] = openrouter_url or os.getenv(
        'OPENROUTER_URL', DEFAULT_OPENROUTER_URL
    )
    app.config['OPENROUTER_API_KEY'] = openrouter_api_key or os.getenv(
        'OPENROUTER_API_KEY', ''
    )

    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

    def _get_api_key() -> str:
        auth = request.headers.get('Authorization', '')
        if auth.lower().startswith('bearer '):
            key = auth[7:].strip()
            if key:
                return key
        return app.config.get('OPENROUTER_API_KEY', '')

    def _error_response(message: str, status_code: int) -> tuple:
        return (
            jsonify(
                {
                    'error': {
                        'message': message,
                        'type': 'proxy_error',
                        'code': status_code,
                    }
                }
            ),
            status_code,
        )

    @app.get('/health')
    def health() -> Response:
        return jsonify({'status': 'ok'})

    @app.route('/v1/chat/completions', methods=['POST', 'OPTIONS'])
    @app.route('/api/v1/chat/completions', methods=['POST', 'OPTIONS'])
    def chat_completions():
        if request.method == 'OPTIONS':
            return Response(status=204)

        if not request.is_json:
            return _error_response('Request body must be JSON', 400)

        try:
            payload = request.get_json()
        except Exception:
            return _error_response('Invalid JSON body', 400)

        if not isinstance(payload, dict):
            return _error_response('JSON body must be an object', 400)

        if 'messages' not in payload or not isinstance(payload['messages'], list):
            return _error_response('Missing or invalid messages field', 400)

        api_key = _get_api_key()
        if not api_key:
            return _error_response(
                'Missing OpenRouter API key. Set OPENROUTER_API_KEY or send an Authorization header.',
                401,
            )

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        if origin:
            headers['HTTP-Referer'] = origin
        elif referer:
            headers['HTTP-Referer'] = referer

        app_title = os.getenv('OPENROUTER_APP_TITLE')
        if app_title:
            headers['X-Title'] = app_title

        forwarded_payload = dict(payload)
        forwarded_payload['stream'] = True

        try:
            upstream = requests.post(
                app.config['OPENROUTER_URL'],
                json=forwarded_payload,
                headers=headers,
                stream=True,
                timeout=(10, 300),
            )
        except requests.RequestException as exc:
            return _error_response(f'Upstream request failed: {exc}', 502)

        if upstream.status_code != 200:
            upstream_payload = None
            try:
                upstream_payload = upstream.json()
            except Exception:
                pass
            upstream.close()
            if isinstance(upstream_payload, dict):
                return jsonify(upstream_payload), upstream.status_code
            return _error_response(
                f'OpenRouter returned HTTP {upstream.status_code}',
                upstream.status_code,
            )

        def generate() -> Iterator[str]:
            try:
                for raw_line in upstream.iter_lines():
                    if not raw_line:
                        yield '\n'
                        continue
                    if isinstance(raw_line, bytes):
                        raw_line = raw_line.decode('utf-8', errors='replace')
                    yield f'{raw_line}\n'
            except Exception as exc:
                error_payload = json.dumps({'error': {'message': str(exc)}})
                yield 'event: error\ndata: ' + error_payload + '\n\n'
            finally:
                upstream.close()

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
            },
        )


app = create_app()


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8000'))
    app.run(host='0.0.0.0', port=port, threaded=True)
