from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, NotFound

DATA_DIR = Path(os.environ.get('SKILLS_DATA_DIR', 'data'))
DEFAULT_DATA_FILE = DATA_DIR / 'skills.json'


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_skills(data_file: Path) -> List[Dict[str, Any]]:
    if not data_file.exists():
        return []
    try:
        with data_file.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _save_skills(skills: List[Dict[str, Any]], data_file: Path) -> None:
    data_file.parent.mkdir(parents=True, exist_ok=True)
    with data_file.open('w', encoding='utf-8') as handle:
        json.dump(skills, handle, indent=2, ensure_ascii=False)


def _find_skill_index(skills: List[Dict[str, Any]], skill_id: str) -> Optional[int]:
    for index, skill in enumerate(skills):
        if skill.get('id') == skill_id:
            return index
    return None


def _find_skill(skills: List[Dict[str, Any]], skill_id: str) -> Optional[Dict[str, Any]]:
    index = _find_skill_index(skills, skill_id)
    if index is None:
        return None
    return skills[index]


def validate_skill_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise BadRequest('A JSON object is required.')
    if 'name' not in payload:
        raise BadRequest('Skill name is required.')
    name = str(payload.get('name', '')).strip()
    if not name:
        raise BadRequest('Skill name cannot be empty.')
    if len(name) > 100:
        raise BadRequest('Skill name must be 100 characters or fewer.')
    category = str(payload.get('category', 'General')).strip() or 'General'
    if len(category) > 50:
        raise BadRequest('Category must be 50 characters or fewer.')
    proficiency = payload.get('proficiency', 1)
    try:
        proficiency = int(proficiency)
    except (TypeError, ValueError):
        raise BadRequest('Proficiency must be an integer.')
    if proficiency < 1 or proficiency > 5:
        raise BadRequest('Proficiency must be between 1 and 5.')
    description = str(payload.get('description', '')).strip()
    if len(description) > 500:
        raise BadRequest('Description must be 500 characters or fewer.')
    return {
        'name': name,
        'category': category,
        'proficiency': proficiency,
        'description': description,
    }


def create_app(data_file: Optional[Path] = None) -> Flask:
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['DATA_FILE'] = Path(data_file) if data_file else DEFAULT_DATA_FILE

    @app.get('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.get('/api/skills')
    def list_skills():
        skills = _load_skills(app.config['DATA_FILE'])
        return jsonify({'skills': skills})

    @app.post('/api/skills')
    def create_skill():
        skills = _load_skills(app.config['DATA_FILE'])
        payload = validate_skill_payload(request.get_json(silent=True))
        now = _utcnow()
        skill = {
            'id': str(uuid.uuid4()),
            **payload,
            'created_at': now,
            'updated_at': now,
        }
        skills.append(skill)
        _save_skills(skills, app.config['DATA_FILE'])
        return jsonify(skill), 201

    @app.get('/api/skills/<skill_id>')
    def get_skill(skill_id: str):
        skills = _load_skills(app.config['DATA_FILE'])
        skill = _find_skill(skills, skill_id)
        if skill is None:
            raise NotFound('Skill not found.')
        return jsonify(skill)

    @app.put('/api/skills/<skill_id>')
    def update_skill(skill_id: str):
        skills = _load_skills(app.config['DATA_FILE'])
        index = _find_skill_index(skills, skill_id)
        if index is None:
            raise NotFound('Skill not found.')
        payload = validate_skill_payload(request.get_json(silent=True))
        skill = {**skills[index], **payload, 'updated_at': _utcnow()}
        skills[index] = skill
        _save_skills(skills, app.config['DATA_FILE'])
        return jsonify(skill)

    @app.delete('/api/skills/<skill_id>')
    def delete_skill(skill_id: str):
        skills = _load_skills(app.config['DATA_FILE'])
        index = _find_skill_index(skills, skill_id)
        if index is None:
            raise NotFound('Skill not found.')
        del skills[index]
        _save_skills(skills, app.config['DATA_FILE'])
        return jsonify({'deleted': True, 'id': skill_id})

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest):
        return jsonify({'error': error.description}), 400

    @app.errorhandler(NotFound)
    def handle_not_found(error: NotFound):
        return jsonify({'error': error.description}), 404

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
