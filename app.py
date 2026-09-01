import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from models import db, Attachment

app = Flask(__name__)
app.secret_key = 'change-this-to-a-random-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attachments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'zip', 'docx'}

db.init_app(app)

with app.app_context():
    db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    attachments = Attachment.query.order_by(Attachment.uploaded_at.desc()).all()
    return render_template('upload.html', attachments=attachments)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add a unique prefix to avoid overwrites
        unique_filename = str(uuid.uuid4()) + '_' + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        # Save metadata to database
        attachment = Attachment(
            original_filename=filename,
            stored_filename=unique_filename,
            file_size=os.path.getsize(file_path),
            content_type=file.content_type or 'application/octet-stream'
        )
        db.session.add(attachment)
        db.session.commit()
        flash('File uploaded successfully')
        return redirect(url_for('index'))
    else:
        flash('File type not allowed')
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/attachments')
def list_attachments():
    attachments = Attachment.query.order_by(Attachment.uploaded_at.desc()).all()
    return jsonify([{
        'id': a.id,
        'original_filename': a.original_filename,
        'file_size': a.file_size,
        'content_type': a.content_type,
        'uploaded_at': a.uploaded_at.isoformat(),
        'url': url_for('uploaded_file', filename=a.stored_filename)
    } for a in attachments])

if __name__ == '__main__':
    app.run(debug=True)