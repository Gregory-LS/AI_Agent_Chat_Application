import os
import uuid
from pathlib import Path

ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/gif'}
ALLOWED_TEXT_TYPES = {'text/plain'}


class AttachmentManager:
    """Manage file attachments (images and text files).

    Saves attachments to a specified directory and maintains metadata.
    """

    def __init__(self, storage_dir: str = 'attachments'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self._metadata = {}  # id -> {'filename': ..., 'original_name': ..., 'type': ..., 'size': ...}

    def save_attachment(self, file_data: bytes, original_name: str, file_type: str) -> dict:
        """Save an attachment after validating its type.

        Args:
            file_data: Raw bytes of the file.
            original_name: Original filename provided by the client.
            file_type: MIME type string (e.g., 'image/png', 'text/plain').

        Returns:
            dict: Metadata of the saved attachment.

        Raises:
            ValueError: If file_type is not allowed.
        """
        if file_type not in ALLOWED_IMAGE_TYPES and file_type not in ALLOWED_TEXT_TYPES:
            raise ValueError(f"Unsupported file type: {file_type}. Allowed: {ALLOWED_IMAGE_TYPES | ALLOWED_TEXT_TYPES}")

        attachment_id = str(uuid.uuid4())
        # Determine extension from original name or use a generic one
        ext = Path(original_name).suffix or '.bin'
        stored_name = f"{attachment_id}{ext}"
        file_path = self.storage_dir / stored_name

        with open(file_path, 'wb') as f:
            f.write(file_data)

        metadata = {
            'id': attachment_id,
            'filename': stored_name,
            'original_name': original_name,
            'type': file_type,
            'size': len(file_data)
        }
        self._metadata[attachment_id] = metadata
        return metadata

    def list_attachments(self) -> list:
        """Return list of all attachment metadata."""
        return list(self._metadata.values())

    def get_attachment(self, attachment_id: str) -> dict | None:
        """Retrieve metadata for a given attachment ID.

        Returns None if not found.
        """
        return self._metadata.get(attachment_id)

    def get_file_path(self, attachment_id: str) -> str | None:
        """Return the full path of the stored file, or None if missing."""
        meta = self._metadata.get(attachment_id)
        if meta is None:
            return None
        path = self.storage_dir / meta['filename']
        return str(path) if path.exists() else None
