# Attachment Manager

Handles storage and metadata for image and text file attachments.

## Supported File Types

- Images: PNG, JPEG, GIF
- Text: Plain text (TXT)

## Usage

```python
from src.attachments import AttachmentManager

manager = AttachmentManager()

# Save an image
with open('photo.png', 'rb') as f:
    data = f.read()
meta = manager.save_attachment(data, 'photo.png', 'image/png')
print(meta['id'])

# List all attachments
attachments = manager.list_attachments()

# Get a specific attachment
attach = manager.get_attachment(meta['id'])

# Get the file path
path = manager.get_file_path(meta['id'])
```

## Running Tests

```bash
pytest tests/
```
