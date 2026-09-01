import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_conversations(client):
    """Test GET /api/conversations returns list of conversations."""
    response = client.get('/api/conversations')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'id' in data[0]
    assert 'title' in data[0]

def test_get_conversations_with_search(client):
    """Test search functionality."""
    response = client.get('/api/conversations?search=bug')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['title'] == 'Bug Triage'

def test_get_conversations_no_match(client):
    """Test search with no match returns empty list."""
    response = client.get('/api/conversations?search=zzz')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == []

def test_create_conversation(client):
    """Test POST /api/conversations creates a new conversation."""
    response = client.post('/api/conversations',
                           data=json.dumps({'title': 'Test Conversation'}),
                           content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['title'] == 'Test Conversation'
    assert 'id' in data

def test_create_conversation_missing_title(client):
    """Test POST with missing title returns 400."""
    response = client.post('/api/conversations',
                           data=json.dumps({}),
                           content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_create_conversation_empty_title(client):
    """Test POST with empty title returns 400."""
    response = client.post('/api/conversations',
                           data=json.dumps({'title': ''}),
                           content_type='application/json')
    assert response.status_code == 400

def test_index_page(client):
    """Test the main page returns HTML."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<div class="sidebar"' in response.data
