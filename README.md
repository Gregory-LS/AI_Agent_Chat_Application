# Attachments Handling

This module provides a generic file-based attachment handler for managing file uploads, downloads, and deletions associated with resources (e.g., issues, tasks).

## Features

- Upload attachments with automatic deduplication (appends counter to duplicate filenames)
- Download attachments by resource ID and filename
- List all attachments for a resource
- Delete individual attachments or all attachments for a resource
- Sanitizes filenames to prevent directory traversal

## Usage

```python
from attachments import AttachmentHandler

# Initialize handler (default storage path: ./attachments)
handler = AttachmentHandler(base_dir="./my_attachments")

# Upload a file
content = b"Hello, World!"
stored_name = handler.upload("issue-123", "report.txt", content)
print(f"Stored as: {stored_name}")

# Download a file
downloaded = handler.download("issue-123", "report.txt")
print(f"Content: {downloaded.decode()}")

# List attachments
files = handler.list_attachments("issue-123")
print(f"Files: {files}")

# Delete an attachment
handler.delete_attachment("issue-123", "report.txt")

# Delete all attachments for a resource
handler.delete_all_for_resource("issue-123")
```

## Installation

No external dependencies required. The module uses Python standard library only.

## Testing

Run tests with pytest:

```bash
pytest tests/test_attachments.py -v
```

## API Reference

### `AttachmentHandler(base_dir="./attachments")`

- `upload(resource_id, filename, file_content) -> str`
- `download(resource_id, filename) -> bytes`
- `list_attachments(resource_id) -> List[str]`
- `delete_attachment(resource_id, filename) -> bool`
- `delete_all_for_resource(resource_id) -> int`

See docstrings for detailed parameter and exception information.
