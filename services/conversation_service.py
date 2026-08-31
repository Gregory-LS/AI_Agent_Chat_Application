from app import db
from models import Conversation, Message

def auto_title(conversation_id):
    """Generate a title from the first user message."""
    first_user_msg = Message.query.filter_by(
        conversation_id=conversation_id,
        role='user'
    ).order_by(Message.timestamp).first()
    if first_user_msg:
        content = first_user_msg.content.strip()
        if len(content) > 50:
            content = content[:50] + '...'
        return content
    return 'New Conversation'

def search_conversations(user_id, query):
    """Search conversations by title or message content."""
    # Use LIKE for simplicity; can be upgraded to full-text search
    like_query = f'%{query}%'
    # Get conversation ids that have matching messages
    matching_msg_ids = db.session.query(Message.conversation_id).filter(
        Message.content.ilike(like_query)
    ).distinct().subquery()
    # Also search by title
    convs = Conversation.query.filter(
        Conversation.user_id == user_id,
        (Conversation.title.ilike(like_query)) | (Conversation.id.in_(matching_msg_ids))
    ).order_by(Conversation.updated_at.desc()).all()
    return convs

def export_conversation(conversation):
    """Export conversation as a dict with metadata and messages."""
    return {
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat(),
        'messages': [
            {'role': msg.role, 'content': msg.content, 'timestamp': msg.timestamp.isoformat()}
            for msg in conversation.messages.order_by(Message.timestamp).all()
        ]
    }

def import_conversation(user_id, data):
    """Import a conversation from a dict (export format)."""
    title = data.get('title', 'Imported Conversation')
    messages_data = data.get('messages', [])
    if not isinstance(messages_data, list):
        return None
    conv = Conversation(user_id=user_id, title=title)
    db.session.add(conv)
    db.session.flush()
    for msg_data in messages_data:
        role = msg_data.get('role')
        content = msg_data.get('content')
        if role not in ('user', 'assistant') or not content:
            db.session.rollback()
            return None
        msg = Message(
            conversation_id=conv.id,
            role=role,
            content=content
        )
        db.session.add(msg)
    db.session.commit()
    return conv
