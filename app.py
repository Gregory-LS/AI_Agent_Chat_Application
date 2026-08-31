from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import models and routes after db init to avoid circular imports
from models import Conversation, Message
from routes.conversations import conversations_bp
app.register_blueprint(conversations_bp, url_prefix='/conversations')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
