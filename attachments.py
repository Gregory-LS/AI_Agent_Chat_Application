import os
import shutil
from pathlib import Path
from typing import Optional, Union

from PIL import Image


class AttachmentHandler:
    """Handles attachment uploads for images and text files.

    Attributes:
        upload_dir (Path): Directory where attachments are saved.
        max_image_size_mb (int): Maximum allowed image size in MB.
        max_text_size_mb (int): Maximum allowed text file size in MB.
        allowed_image_extensions (set): Allowed image file extensions.
        allowed_text_extensions (set): Allowed text file extensions.
    """

    def __init__(
        self,
        upload_dir: Union[str, Path] = "uploads",
        max_image_size_mb: int = 5,
        max_text_size_mb: int = 1,
    ):
        """Initialize the handler.

        Args:
            upload_dir: Directory to store uploaded files.
            max_image_size_mb: Maximum image file size in MB.
            max_text_size_mb: Maximum text file size in MB.
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_image_size_mb = max_image_size_mb
        self.max_text_size_mb = max_text_size_mb
        self.allowed_image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        self.allowed_text_extensions = {".txt", ".md", ".csv", ".log"}

    def handle_image(self, file: Union[str, Path]) -> Path:
        """Process and save an image file.

        Args:
            file: Path to the image file to be handled.

        Returns:
            Path to the saved image file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid image, has an unsupported
                extension, or exceeds the size limit.
        """
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in self.allowed_image_extensions:
            raise ValueError(
                f"Unsupported image extension '{ext}'. Allowed: {self.allowed_image_extensions}"
            )

        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_image_size_mb:
            raise ValueError(
                f"Image file size {size_mb:.2f} MB exceeds maximum of {self.max_image_size_mb} MB"
            )

        # Verify it's a valid image using PIL
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            raise ValueError(f"File is not a valid image: {e}")

        # Save to upload directory
        dest = self.upload_dir / file_path.name
        shutil.copy2(file_path, dest)
        return dest

    def handle_text(self, file: Union[str, Path]) -> Path:
        """Process and save a text file.

        Args:
            file: Path to the text file to be handled.

        Returns:
            Path to the saved text file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file has an unsupported extension, exceeds the
                size limit, or contains non-UTF-8 characters.
        """
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in self.allowed_text_extensions:
            raise ValueError(
                f"Unsupported text extension '{ext}'. Allowed: {self.allowed_text_extensions}"
            )

        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_text_size_mb:
            raise ValueError(
                f"Text file size {size_mb:.2f} MB exceeds maximum of {self.max_text_size_mb} MB"
            )

        # Check if file is valid UTF-8 text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read()
        except UnicodeDecodeError as e:
            raise ValueError(f"File is not valid UTF-8 text: {e}")

        # Save to upload directory
        dest = self.upload_dir / file_path.name
        shutil.copy2(file_path, dest)
        return dest

    def save_attachment(self, file: Union[str, Path]) -> Path:
        """Automatically detect file type and handle accordingly.

        Args:
            file: Path to the file.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If the file type cannot be determined.
        """
        ext = Path(file).suffix.lower()
        if ext in self.allowed_image_extensions:
            return self.handle_image(file)
        elif ext in self.allowed_text_extensions:
            return self.handle_text(file)
        else:
            raise ValueError(
                f"Unsupported file extension '{ext}'. Allowed image: {self.allowed_image_extensions}, "
                f"text: {self.allowed_text_extensions}"
            )
