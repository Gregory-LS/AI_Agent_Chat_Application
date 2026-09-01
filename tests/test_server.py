import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

import server


class FakeResponse:
    def __init__(self, status_code=200, lines=None, json_data=None):
        self.status_code = status_code
        self.lines = lines if lines is not None else []
        self.json_data = json_data
        self.closed = False

    def iter_lines(self, **kwargs):
        for line in self.lines:
            if isinstance(line, str):
                yield line.encode()
            else:
                yield line

    def json(self):
        if self.json_data is None:
            return {'error': {'message': 'upstream error'}}
        return self.json_data

    def close(self):
        self.closed = True


@pytest.fixture
 def client():
    app = server.create_app(
        openrouter_url='https://openrouter.test/v1/chat/completions',
        openrouter_api_key='test-key',
    )
    return app.test_client()


def test_proxies_and_streams_sse(client, monkeypatch):
    delta = json.dumps({'choices': [{'delta': {'content': 'Hello'}}]})
    lines = [
        'data: ' + delta,
        '',
        'data: [DONE]',
        '',
    ]
    captured = {}

    def fake_post(url, json=None, headers=None, stream=False, timeout=None):
        captured['url'] = url
        captured['json'] = json
        captured['headers'] = headers
        captured['stream'] = stream
        return FakeResponse(lines=lines)

    monkeypatch.setattr(server.requests, 'post', fake_post)

    response = client.post(
        '/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
        headers={'Authorization': 'Bearer client-test-key'},
    )

    assert response.status_code == 200
    assert response.mimetype == 'text/event-stream'

    body = response.get_data(as_text=True)
    assert 'data: ' in body
    assert 'Hello' in body
    assert 'data: [DONE]' in body
    assert captured['headers']['Authorization'] == 'Bearer client-test-key'
    assert captured['json']['stream'] is True
    assert captured['stream'] is True
    assert captured['url'].startswith('https://openrouter.test')


def test_missing_api_key_returns_401(client, monkeypatch):
    def fail_post(*args, **kwargs):
        raise AssertionError('requests.post should not be called')

    monkeypatch.setattr(server.requests, 'post', fail_post)
    client.application.config['OPENROUTER_API_KEY'] = ''

    response = client.post(
        '/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
    )

    assert response.status_code == 401
    assert 'API key' in response.get_json()['error']['message']


def test_invalid_json_returns_400(client, monkeypatch):
    def fail_post(*args, **kwargs):
        raise AssertionError('requests.post should not be called')

    monkeypatch.setattr(server.requests, 'post', fail_post)

    response = client.post(
        '/v1/chat/completions',
        data='{bad',
        content_type='application/json',
    )

    assert response.status_code == 400
    assert response.get_json()['error']['message'] == 'Invalid JSON body'


def test_forwards_upstream_error(client, monkeypatch):
    fake = FakeResponse(
        status_code=400,
        json_data={'error': {'message': 'Insufficient credits'}},
    )
    monkeypatch.setattr(server.requests, 'post', lambda *args, **kwargs: fake)

    response = client.post(
        '/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
        headers={'Authorization': 'Bearer key'},
    )

    assert response.status_code == 400
    assert response.get_json()['error']['message'] == 'Insufficient credits'


def test_upstream_connection_error_returns_502(client, monkeypatch):
    def raise_error(*args, **kwargs):
        raise server.requests.RequestException('network down')

    monkeypatch.setattr(server.requests, 'post', raise_error)

    response = client.post(
        '/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
        headers={'Authorization': 'Bearer key'},
    )

    assert response.status_code == 502
    assert 'network down' in response.get_json()['error']['message']


def test_stream_error_emits_sse_error_event(client, monkeypatch):
    class BrokenResponse(FakeResponse):
        def iter_lines(self, **kwargs):
            yield b'data: ok'
            raise IOError('pipe broken')

    monkeypatch.setattr(server.requests, 'post', lambda *args, **kwargs: BrokenResponse())

    response = client.post(
        '/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
        headers={'Authorization': 'Bearer key'},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'event: error' in body
    assert 'pipe broken' in body


def test_cors_preflight(client):
    response = client.options('/v1/chat/completions')
    assert response.status_code == 204
    assert response.headers['Access-Control-Allow-Origin'] == '*'


def test_api_alias_route(client, monkeypatch):
    fake = FakeResponse(lines=['data: [DONE]', ''])
    monkeypatch.setattr(server.requests, 'post', lambda *args, **kwargs: fake)

    response = client.post(
        '/api/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
        headers={'Authorization': 'Bearer key'},
    )

    assert response.status_code == 200
    assert 'data: [DONE]' in response.get_data(as_text=True)


def test_origin_forwarded_as_http_referer(client, monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, stream=False, timeout=None):
        captured['headers'] = headers
        return FakeResponse(lines=['data: [DONE]', ''])

    monkeypatch.setattr(server.requests, 'post', fake_post)

    response = client.post(
        '/v1/chat/completions',
        json={
            'model': 'openai/gpt-4o',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
        headers={'Authorization': 'Bearer key', 'Origin': 'https://app.example'},
    )

    assert response.status_code == 200
    assert captured['headers']['HTTP-Referer'] == 'https://app.example'


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}
