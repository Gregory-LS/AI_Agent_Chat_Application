import os
import shutil
from pathlib import Path
from typing import List, Optional, BinaryIO


class AttachmentHandler:
    """
    Handles file attachments: save, retrieve, list, and delete.
    Files are stored under a base directory specified at initialization.
    """

    def __init__(self, base_dir: str = "./attachments"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: BinaryIO) -> str:
        """
        Save a file attachment.

        Args:
            filename: Name of the file (should be safe).
            data: Binary stream to write.

        Returns:
            The full path of the saved file.

        Raises:
            ValueError: If the filename is empty or contains path separators.
            IOError: If writing fails.
        """
        if not filename:
            raise ValueError("Filename must not be empty")
        if '/' in filename or '\\' in filename:
            raise ValueError("Filename must not contain path separators")
        file_path = self.base_dir / filename
        try:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(data, f)
        except OSError as e:
            raise IOError(f"Failed to save attachment: {e}") from e
        return str(file_path)

    def retrieve(self, filename: str) -> Optional[bytes]:
        """
        Retrieve the contents of an attachment.

        Args:
            filename: Name of the file.

        Returns:
            File contents as bytes, or None if file does not exist.
        """
        file_path = self.base_dir / filename
        if not file_path.exists() or not file_path.is_file():
            return None
        return file_path.read_bytes()

    def list_files(self) -> List[str]:
        """
        List all attachment filenames in the base directory.

        Returns:
            Sorted list of filenames.
        """
        return sorted([p.name for p in self.base_dir.iterdir() if p.is_file()])

    def delete(self, filename: str) -> bool:
        """
        Delete an attachment.

        Args:
            filename: Name of the file to delete.

        Returns:
            True if deleted, False if file did not exist.
        """
        file_path = self.base_dir / filename
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def clear(self) -> int:
        """
        Remove all attachments.

        Returns:
            Number of files removed.
        """
        count = 0
        for p in self.base_dir.iterdir():
            if p.is_file():
                p.unlink()
                count += 1
        return count
