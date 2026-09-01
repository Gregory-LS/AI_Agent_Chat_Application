# Project Management App

## Features

- Projects and Issues management
- Attachment handling: upload and delete attachments on issues
- User authentication for uploading/deleting
- AJAX-based UI for attachment operations

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start server: `python manage.py runserver`

## Usage

- Navigate to an issue detail page
- Upload files using the form
- Delete attachments with the delete button (only by uploader or superuser)

## Running Tests

```bash
python manage.py test tests/
```
