import os
import sys
import io
import json
import tempfile
import pytest
from app import app, db, Attachment

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    # Cleanup
    with app.app_context():
        db.drop_all()

def test_index_returns_form(client):
    """Test that main page loads and shows upload form."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Upload Attachment' in response.data

def test_upload_valid_file(client):
    """Test uploading a valid txt file."""
    data = {'file': (io.BytesIO(b'Hello, world!'), 'test.txt')}
    response = client.post('/upload', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'File uploaded successfully' in response.data

def test_upload_no_file(client):
    """Test upload with no file part."""
    response = client.post('/upload', data={}, follow_redirects=True)
    assert b'No file part' in response.data

def test_upload_empty_filename(client):
    """Test upload with empty filename."""
    data = {'file': (io.BytesIO(b'some content'), '')}
    response = client.post('/upload', data=data, follow_redirects=True)
    assert b'No selected file' in response.data

def test_upload_disallowed_type(client):
    """Test uploading a file with disallowed extension."""
    data = {'file': (io.BytesIO(b'<?php...'), 'shell.php')}
    response = client.post('/upload', data=data, follow_redirects=True)
    assert b'File type not allowed' in response.data

def test_list_attachments_json(client):
    """Test JSON endpoint returns empty list."""
    response = client.get('/attachments')
    assert response.status_code == 200
    assert response.json == []

def test_upload_and_list(client):
    """Test upload and then check JSON list contains the file."""
    data = {'file': (io.BytesIO(b'Attachment content'), 'notes.txt')}
    client.post('/upload', data=data, follow_redirects=True)
    response = client.get('/attachments')
    assert response.status_code == 200
    attachments = response.json
    assert len(attachments) == 1
    assert attachments[0]['original_filename'] == 'notes.txt'
    assert attachments[0]['file_size'] == len(b'Attachment content')

def test_file_size_limit(client):
    """Test that very large file is rejected (max 16MB)."""
    app.config['MAX_CONTENT_LENGTH'] = 10  # Set very low for test
    data = {'file': (io.BytesIO(b'A' * 100), 'large.txt')}
    response = client.post('/upload', data=data)
    # Werkzeug returns 413 for Request Entity Too Large
    assert response.status_code == 413