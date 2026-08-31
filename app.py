import uuid
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory storage for imported conversations (a dict keyed by conversation id).
CONVERSATIONS = {}

REQUIRED_FIELDS = ("title", "messages")
MESSAGE_REQUIRED_FIELDS = ("role", "content")


def validate_conversation(payload):
    """Validate the imported conversation payload. Return a list of error messages."""
    errors = []

    if not isinstance(payload, dict):
        return ["Request body must be a JSON object."]

    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: '{field}'")
        elif field == "title" and not isinstance(payload[field], str):
            errors.append("Field 'title' must be a string.")
        elif field == "messages":
            messages = payload[field]
            if not isinstance(messages, list) or not messages:
                errors.append("Field 'messages' must be a non-empty list.")
            else:
                for idx, message in enumerate(messages):
                    if not isinstance(message, dict):
                        errors.append(f"messages[{idx}] must be an object.")
                        continue
                    for msg_field in MESSAGE_REQUIRED_FIELDS:
                        if msg_field not in message:
                            errors.append(f"messages[{idx}] missing required field: '{msg_field}'")
                    if "role" in message and message["role"] not in {"user", "assistant", "system"}:
                        errors.append(f"messages[{idx}].role must be one of: user, assistant, system")
    return errors


@app.post("/api/conversations/import")
def import_conversation():
    """Import a conversation from a JSON body."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    errors = validate_conversation(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 422

    conversation_id = payload.get("id") or str(uuid.uuid4())
    conversation = {
        "id": conversation_id,
        "title": payload["title"],
        "participants": payload.get("participants", []),
        "messages": payload["messages"],
        "metadata": payload.get("metadata", {}),
        "imported_at": datetime.utcnow().isoformat() + "Z",
    }
    CONVERSATIONS[conversation_id] = conversation

    return jsonify({
        "status": "imported",
        "id": conversation_id,
        "message_count": len(conversation["messages"]),
    }), 201


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
