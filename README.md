# Attachment Handling Module

This module provides a simple `Attachment` class for handling image and text file attachments.

## Supported File Types

- **Images**: PNG, JPEG, GIF
- **Text**: Plain text (`.txt`), CSV (`.csv`), HTML (`.html`)

## Usage

```python
from src.attachment import Attachment

# Create an attachment from a file path
att = Attachment('path/to/file.txt')

# Get metadata
print(att.filename)        # 'file.txt'
print(att.mime_type)       # 'text/plain'
print(att.size)            # file size in bytes
print(att.is_image)        # False
print(att.is_text)         # True

# Read content
content = att.read_content()  # returns str for text, bytes for images

# Get all metadata as dict
meta = att.get_metadata()
```

## Error Handling

- `FileNotFoundError` if the file does not exist.
- `IsADirectoryError` if the path is a directory.
- `ValueError` if the file type is not supported.

## Testing

Run tests with pytest:

```bash
pytest tests/test_attachment.py -v
```
