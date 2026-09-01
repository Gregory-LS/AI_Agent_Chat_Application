from pathlib import Path

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    data_file = tmp_path / 'skills.json'
    application = create_app(data_file)
    application.config.update(TESTING=True)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def _skill_payload(**overrides):
    payload = {
        'name': 'Python',
        'category': 'Backend',
        'proficiency': 4,
        'description': 'Core language for backend development.',
    }
    payload.update(overrides)
    return payload


def test_list_skills_empty(client):
    response = client.get('/api/skills')
    assert response.status_code == 200
    assert response.get_json() == {'skills': []}


def test_create_and_get_skill(client):
    response = client.post('/api/skills', json=_skill_payload())
    assert response.status_code == 201
    skill = response.get_json()
    assert skill['name'] == 'Python'
    assert skill['category'] == 'Backend'
    assert skill['proficiency'] == 4
    assert 'id' in skill
    assert 'created_at' in skill
    assert 'updated_at' in skill

    get_response = client.get('/api/skills/' + skill['id'])
    assert get_response.status_code == 200
    assert get_response.get_json()['id'] == skill['id']


def test_update_skill(client):
    created = client.post('/api/skills', json=_skill_payload()).get_json()
    skill_id = created['id']
    response = client.put(
        '/api/skills/' + skill_id,
        json={
            'name': 'Advanced Python',
            'category': 'Backend',
            'proficiency': 5,
            'description': 'Expert level Python development.',
        },
    )
    assert response.status_code == 200
    updated = response.get_json()
    assert updated['name'] == 'Advanced Python'
    assert updated['proficiency'] == 5
    assert updated['id'] == created['id']
    assert updated['created_at'] == created['created_at']
    assert updated['updated_at'] >= created['updated_at']


def test_delete_skill(client):
    created = client.post('/api/skills', json=_skill_payload()).get_json()
    skill_id = created['id']
    response = client.delete('/api/skills/' + skill_id)
    assert response.status_code == 200
    assert response.get_json()['deleted'] is True
    assert client.get('/api/skills').get_json() == {'skills': []}


def test_validation_errors(client):
    assert client.post('/api/skills', json={}).status_code == 400
    assert client.post('/api/skills', json={'name': '   '}).status_code == 400
    assert client.post('/api/skills', json={'name': 'X', 'proficiency': 9}).status_code == 400
    assert client.post('/api/skills', json={'name': 'X', 'proficiency': 'abc'}).status_code == 400
    assert client.post('/api/skills', json={'name': 'X', 'proficiency': 0}).status_code == 400
    assert client.post('/api/skills', json={'name': 'x' * 101}).status_code == 400


def test_not_found(client):
    assert client.get('/api/skills/missing').status_code == 404
    assert client.put('/api/skills/missing', json=_skill_payload()).status_code == 404
    assert client.delete('/api/skills/missing').status_code == 404


def test_persistence(tmp_path):
    data_file = tmp_path / 'skills.json'
    app = create_app(data_file)
    app.config.update(TESTING=True)
    client = app.test_client()
    client.post('/api/skills', json=_skill_payload())

    second_app = create_app(data_file)
    second_app.config.update(TESTING=True)
    second_client = second_app.test_client()
    response = second_client.get('/api/skills')
    assert response.status_code == 200
    assert len(response.get_json()['skills']) == 1


def test_index_served(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Skills Drawer' in response.data
