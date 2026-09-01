from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory conversation store
conversations = [
    {"id": 1, "title": "Project Discussion", "last_message": "Let's finalize the design", "updated_at": "2025-03-21T10:30:00Z"},
    {"id": 2, "title": "Bug Triage", "last_message": "Need to reproduce the issue", "updated_at": "2025-03-21T09:15:00Z"},
    {"id": 3, "title": "Team Standup", "last_message": "All good, moving forward", "updated_at": "2025-03-20T14:00:00Z"}
]
next_id = 4

@app.route('/')
def index():
    return render_template('sidebar.html')

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    search = request.args.get('search', '').lower()
    if search:
        filtered = [c for c in conversations if search in c['title'].lower() or search in c['last_message'].lower()]
        return jsonify(filtered)
    return jsonify(conversations)

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    global next_id
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400
    new_conv = {
        "id": next_id,
        "title": data['title'],
        "last_message": "",
        "updated_at": "2025-03-21T12:00:00Z"
    }
    conversations.append(new_conv)
    next_id += 1
    return jsonify(new_conv), 201

if __name__ == '__main__':
    app.run(debug=True)
