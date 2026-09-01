# Attachments Handling Module

This module provides functionality to process file attachments, specifically images and text files.

## Features

- Detect image files (PNG, JPEG, GIF, BMP) by reading magic bytes.
- Extract image dimensions (width, height) without heavy libraries.
- Read text files (UTF-8 encoded) and return their full content.
- Return file size in bytes.

## Usage

```python
from attachments import process_attachment

# Process a text file
result = process_attachment("example.txt")
print(result)
# {'type': 'text', 'size': 123, 'content': '...'}

# Process an image
result = process_attachment("image.png")
print(result)
# {'type': 'image', 'size': 45678, 'dimensions': (1920, 1080)}
```

## Error Handling

- `FileNotFoundError` if the file does not exist.
- `ValueError` if the file type is not supported (not an image and not valid UTF-8 text).
- `ValueError` for malformed image headers.

## Testing

Run tests with pytest:

```bash
pytest tests/test_attachments.py -v
```

## Requirements

- Python 3.7+
- No external dependencies (standard library only).
