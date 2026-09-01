# Attachment Handling Module

This module provides a simple way to handle file attachments (images and text files) in a Python application.

## Features

- Validate image files (JPEG, PNG, GIF, BMP) using PIL
- Validate text files (TXT, MD, CSV, LOG) for UTF-8 encoding
- Configurable size limits (default: 5 MB for images, 1 MB for text)
- Automatic extension detection and handling
- Atomic file copy to a designated upload directory

## Usage

```python
from attachments import AttachmentHandler

handler = AttachmentHandler(upload_dir="./uploads")

# Handle an image
saved_path = handler.handle_image("photo.png")
print(f"Image saved to {saved_path}")

# Handle a text file
saved_path = handler.handle_text("notes.txt")
print(f"Text saved to {saved_path}")

# Automatically detect type
saved_path = handler.save_attachment("file.csv")
print(f"Attachment saved to {saved_path}")
```

## Error Handling

- `FileNotFoundError`: File does not exist.
- `ValueError`: Invalid extension, size limit exceeded, or corrupt file.

## Testing

Run tests with pytest:

```bash
pytest tests/test_attachments.py -v
```

## Dependencies

- Python 3.8+
- Pillow (for image validation)

Install with:

```bash
pip install Pillow
```
