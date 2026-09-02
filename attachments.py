import os
import shutil
from pathlib import Path
from typing import List, Optional, BinaryIO


class AttachmentHandler:
    """Handles file attachments stored in a local directory.

    Each attachment is stored as a file under a base directory.
    The filename is uniquely identified by a combination of a
    parent resource identifier (e.g., issue ID) and the original
    filename. Duplicate filenames are resolved by appending a
    counter.

    Attributes:
        base_dir (Path): Root directory for storing attachments.
    """

    def __init__(self, base_dir: str = "./attachments"):
        """Initialize the handler with a base directory.

        Args:
            base_dir: Path to the directory where attachments are stored.
                      Created if it does not exist.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, resource_id: str, filename: str) -> Path:
        """Return the full path for an attachment.

        Args:
            resource_id: Identifier of the parent resource (e.g., issue ID).
            filename: Original filename of the attachment.

        Returns:
            Path to the stored file.
        """
        resource_dir = self.base_dir / resource_id
        resource_dir.mkdir(parents=True, exist_ok=True)
        return resource_dir / filename

    def upload(self, resource_id: str, filename: str, file_content: bytes) -> str:
        """Upload an attachment to a resource.

        If a file with the same name already exists, a counter is
        appended to the filename before the extension.

        Args:
            resource_id: Identifier of the parent resource.
            filename: Original filename (may include path components).
            file_content: Raw bytes of the file.

        Returns:
            The actual filename under which the attachment was stored.

        Raises:
            ValueError: If resource_id or filename is empty.
            IOError: If the file cannot be written.
        """
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        if not filename:
            raise ValueError("filename must not be empty")
        # Sanitize filename: keep only basename
        sanitized = Path(filename).name
        if not sanitized:
            raise ValueError("filename contains no valid basename")
        # Resolve path with potential deduplication
        resource_dir = self.base_dir / resource_id
        resource_dir.mkdir(parents=True, exist_ok=True)
        dest = resource_dir / sanitized
        if dest.exists():
            # Append counter before extension
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while True:
                new_name = f"{stem}_{counter}{suffix}"
                dest = resource_dir / new_name
                if not dest.exists():
                    break
                counter += 1
        try:
            dest.write_bytes(file_content)
        except OSError as e:
            raise IOError(f"Failed to write attachment {dest}: {e}") from e
        return dest.name

    def download(self, resource_id: str, filename: str) -> bytes:
        """Download an attachment's content.

        Args:
            resource_id: Identifier of the parent resource.
            filename: Exact filename (including any deduplication suffix).

        Returns:
            Raw bytes of the file.

        Raises:
            FileNotFoundError: If the attachment does not exist.
            ValueError: If resource_id or filename is empty.
        """
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        if not filename:
            raise ValueError("filename must not be empty")
        path = self._resolve_path(resource_id, filename)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {path}")
        return path.read_bytes()

    def list_attachments(self, resource_id: str) -> List[str]:
        """List all attachment filenames for a given resource.

        Args:
            resource_id: Identifier of the parent resource.

        Returns:
            List of filenames (sorted alphabetically).

        Raises:
            ValueError: If resource_id is empty.
        """
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        resource_dir = self.base_dir / resource_id
        if not resource_dir.exists():
            return []
        return sorted([f.name for f in resource_dir.iterdir() if f.is_file()])

    def delete_attachment(self, resource_id: str, filename: str) -> bool:
        """Delete an attachment.

        Args:
            resource_id: Identifier of the parent resource.
            filename: Exact filename to delete.

        Returns:
            True if the file was deleted, False if it did not exist.

        Raises:
            ValueError: If resource_id or filename is empty.
        """
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        if not filename:
            raise ValueError("filename must not be empty")
        path = self._resolve_path(resource_id, filename)
        if path.exists():
            path.unlink()
            return True
        return False

    def delete_all_for_resource(self, resource_id: str) -> int:
        """Delete all attachments for a given resource.

        Args:
            resource_id: Identifier of the parent resource.

        Returns:
            Number of deleted files.

        Raises:
            ValueError: If resource_id is empty.
        """
        if not resource_id:
            raise ValueError("resource_id must not be empty")
        resource_dir = self.base_dir / resource_id
        if not resource_dir.exists():
            return 0
        count = 0
        for f in resource_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        # Optionally remove empty directory
        try:
            resource_dir.rmdir()
        except OSError:
            pass  # Directory not empty or other error
        return count
