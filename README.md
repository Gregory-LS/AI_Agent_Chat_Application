# Attachment Handling App

This is a simple web application for uploading and managing file attachments. It is built with Flask and SQLAlchemy.

## Features

- Upload files (allowed types: png, jpg, jpeg, gif, pdf, txt, zip, docx)
- View list of uploaded attachments
- Download files via direct link
- JSON endpoint for attachment metadata
- File type validation
- Size limit (16 MB)

## Installation

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

## Running

```bash
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

## Testing

Run tests with:

```bash
pytest tests/
```

## Project Structure

- `app.py` - Main Flask application
- `models.py` - Database model for attachments
- `templates/upload.html` - HTML template for upload/list UI
- `tests/test_attachments.py` - Unit tests
- `uploads/` - Directory where uploaded files are stored (created automatically)
- `requirements.txt` - Python dependencies