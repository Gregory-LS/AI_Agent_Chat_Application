from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
import json

router = APIRouter()

# Mock conversation database - replace with actual data source
conversations_db = {
    "conv-1": {
        "id": "conv-1",
        "title": "Sample Conversation",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, how can I help?"},
            {"role": "user", "content": "What is the weather?"},
            {"role": "assistant", "content": "I'm not sure, but I can look it up."}
        ]
    }
}

@router.get("/conversations/{id}/export")
async def export_conversation(id: str, format: str = Query("json", regex="^(json|markdown)$")):
    conversation = conversations_db.get(id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if format == "json":
        return conversation
    elif format == "markdown":
        md_content = generate_markdown(conversation)
        return Response(content=md_content, media_type="text/markdown")
    else:
        raise HTTPException(status_code=400, detail="Invalid format")


def generate_markdown(conv: dict) -> str:
    lines = []
    lines.append(f"# {conv.get('title', 'Conversation')}")
    lines.append("")
    for msg in conv.get("messages", []):
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        lines.append(f"## {role}")
        lines.append(content)
        lines.append("")
    return "\n".join(lines)
