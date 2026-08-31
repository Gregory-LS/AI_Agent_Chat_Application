from flask import Blueprint, request, jsonify
from app import db
from models import Conversation, Message
from services.conversation_service import auto_title, search_conversations, export_conversation, import_conversation

conversations_bp = Blueprint('conversations', __name__)

# Helper to get user_id from header (simplified auth)
def get_user_id():
    return request.headers.get('X-User-Id', type=int)

@conversations_bp.route('', methods=['POST'])
def create_conversation():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400
    data = request.get_json() or {}
    title = data.get('title', '')
    conversation = Conversation(user_id=user_id, title=title)
    db.session.add(conversation)
    db.session.flush()  # to get id
    # Auto-title if no title provided
    if not title:
        messages_data = data.get('messages', [])
        if messages_data:
            for msg_data in messages_data:
                msg = Message(conversation_id=conversation.id, role=msg_data['role'], content=msg_data['content'])
                db.session.add(msg)
        db.session.commit()
        conversation.title = auto_title(conversation.id)
        db.session.commit()
    else:
        messages_data = data.get('messages', [])
        for msg_data in messages_data:
            msg = Message(conversation_id=conversation.id, role=msg_data['role'], content=msg_data['content'])
            db.session.add(msg)
        db.session.commit()
    return jsonify(conversation.to_dict(include_messages=True)), 201

@conversations_bp.route('/search', methods=['POST'])
def search():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400
    data = request.get_json() or {}
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    results = search_conversations(user_id, query)
    return jsonify([conv.to_dict() for conv in results])

@conversations_bp.route('/<int:conversation_id>/archive', methods=['PATCH'])
def archive(conversation_id):
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400
    conv = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
    conv.archived = True
    db.session.commit()
    return jsonify(conv.to_dict())

@conversations_bp.route('/<int:conversation_id>/unarchive', methods=['PATCH'])
def unarchive(conversation_id):
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400
    conv = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
    conv.archived = False
    db.session.commit()
    return jsonify(conv.to_dict())

@conversations_bp.route('/<int:conversation_id>/export', methods=['GET'])
def export(conversation_id):
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400
    conv = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
    export_data = export_conversation(conv)
    return jsonify(export_data)

@conversations_bp.route('/import', methods=['POST'])
def import_conv():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Missing X-User-Id header'}), 400
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    conv = import_conversation(user_id, data)
    if not conv:
        return jsonify({'error': 'Import failed'}), 400
    return jsonify(conv.to_dict(include_messages=True)), 201
