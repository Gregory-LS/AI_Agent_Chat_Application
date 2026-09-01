import os
import mimetypes
from pathlib import Path
from typing import Optional, Union, Any


class Attachment:
    """Represents an attached file (image or text) with its metadata and content.

    Supported types: image/png, image/jpeg, image/gif, text/plain, text/csv, text/html
    """

    SUPPORTED_MIME_TYPES = {
        'image/png', 'image/jpeg', 'image/gif',
        'text/plain', 'text/csv', 'text/html',
    }

    def __init__(self, filepath: Union[str, Path]) -> None:
        self.filepath: Path = Path(filepath).resolve()
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        if not self.filepath.is_file():
            raise IsADirectoryError(f"Path is a directory: {self.filepath}")
        self._mime_type: Optional[str] = None
        self._content: Optional[Union[str, bytes]] = None
        self._detect_mime_type()
        if self.mime_type not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(f"Unsupported file type: {self.mime_type}")

    def _detect_mime_type(self) -> None:
        """Detect MIME type based on file extension and content."""
        mime_type, _ = mimetypes.guess_type(str(self.filepath))
        if mime_type is None:
            # fallback: use extension-based simple mapping
            ext = self.filepath.suffix.lower()
            mapping = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.html': 'text/html',
                '.htm': 'text/html',
            }
            mime_type = mapping.get(ext, 'application/octet-stream')
        self._mime_type = mime_type

    @property
    def mime_type(self) -> str:
        """Return the MIME type of the attachment."""
        return self._mime_type or 'application/octet-stream'

    @property
    def filename(self) -> str:
        """Return the filename (with extension)."""
        return self.filepath.name

    @property
    def size(self) -> int:
        """Return the file size in bytes."""
        return self.filepath.stat().st_size

    @property
    def is_image(self) -> bool:
        """Check if the attachment is an image."""
        return self.mime_type.startswith('image/')

    @property
    def is_text(self) -> bool:
        """Check if the attachment is a text file."""
        return self.mime_type.startswith('text/')

    def read_content(self) -> Union[str, bytes]:
        """Read and return the file content.

        For text files, returns a string (decoded as UTF-8).
        For image files, returns raw bytes.
        """
        if self._content is not None:
            return self._content
        mode = 'rb'
        if self.is_text:
            mode = 'r'
        with open(self.filepath, mode) as f:
            self._content = f.read()
        return self._content

    def get_metadata(self) -> dict:
        """Return a dictionary of attachment metadata."""
        return {
            'filename': self.filename,
            'mime_type': self.mime_type,
            'size': self.size,
            'is_image': self.is_image,
            'is_text': self.is_text,
        }
