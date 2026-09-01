import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    resp = client.get('/')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['message'] == 'Hello, World!'


def test_data_success(client):
    resp = client.post('/data', json={'name': 'Alice'})
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['greeting'] == 'Hello, Alice!'


def test_data_missing_json(client):
    resp = client.post('/data', data='not json', content_type='application/json')
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert 'error' in data


def test_data_missing_name(client):
    resp = client.post('/data', json={'other': 'value'})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert 'Missing' in data['error']


def test_data_invalid_name(client):
    resp = client.post('/data', json={'name': ''})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert 'non-empty' in data['error']


def test_extras_all(client):
    resp = client.get('/extras')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'random_string' in data
    assert 'random_int' in data
    assert 'random_float' in data


def test_extras_string_only(client):
    resp = client.get('/extras?type=random_string')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'random_string' in data
    assert 'random_int' not in data
    assert 'random_float' not in data


def test_extras_invalid_type(client):
    resp = client.get('/extras?type=invalid')
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert 'Invalid type parameter' in data['error']


def test_not_found(client):
    resp = client.get('/nonexistent')
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert 'error' in data


def test_method_not_allowed(client):
    resp = client.put('/data')
    assert resp.status_code == 405
    data = json.loads(resp.data)
    assert 'error' in data


def test_data_internal_error(client, monkeypatch):
    monkeypatch.setattr('app.request.get_json', side_effect=Exception('test error'))
    resp = client.post('/data', json={'name': 'test'})
    assert resp.status_code == 500
    data = json.loads(resp.data)
    assert 'error' in data


def test_extras_internal_error(client, monkeypatch):
    monkeypatch.setattr('app.random.randint', side_effect=Exception('test error'))
    resp = client.get('/extras?type=random_int')
    assert resp.status_code == 500
    data = json.loads(resp.data)
    assert 'error' in data
