# Attachment Handling Module

This module provides a simple file attachment handler for storing, retrieving, listing, and deleting files.

## Usage

```python
from src.attachments import AttachmentHandler
from io import BytesIO

# Initialize with a base directory (defaults to './attachments')
handler = AttachmentHandler(base_dir="/path/to/attachments")

# Save an attachment
handler.save("report.pdf", open("report.pdf", "rb"))

# Retrieve as bytes
content = handler.retrieve("report.pdf")

# List all attachments
files = handler.list_files()

# Delete an attachment
handler.delete("old.txt")

# Clear all attachments
handler.clear()
```

## Running Tests

```bash
pytest tests/test_attachments.py -v
```

## API Reference

- `AttachmentHandler(base_dir)` – Constructor. Creates base directory if it doesn't exist.
- `save(filename, data)` – Save binary data from a file-like object. Raises `ValueError` for invalid filenames.
- `retrieve(filename)` – Return file contents as bytes, or `None` if missing.
- `list_files()` – Return sorted list of filenames.
- `delete(filename)` – Delete a file. Returns `True` if deleted, `False` if not found.
- `clear()` – Remove all attachments. Returns number of files removed.
