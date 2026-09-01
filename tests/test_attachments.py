import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from attachments import AttachmentHandler


@pytest.fixture
def handler(tmp_path):
    """Create an AttachmentHandler with a temporary upload directory."""
    upload_dir = tmp_path / "uploads"
    return AttachmentHandler(upload_dir=upload_dir)


@pytest.fixture
def sample_image(tmp_path):
    """Create a valid small PNG image."""
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_text(tmp_path):
    """Create a valid UTF-8 text file."""
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Hello, world!\n", encoding="utf-8")
    return txt_path


class TestHandleImage:
    def test_valid_image(self, handler, sample_image):
        dest = handler.handle_image(sample_image)
        assert dest.exists()
        assert dest.name == "test.png"

    def test_unsupported_extension(self, handler, tmp_path):
        fake = tmp_path / "image.pdf"
        fake.write_text("fake")
        with pytest.raises(ValueError, match="Unsupported image extension"):
            handler.handle_image(fake)

    def test_file_not_found(self, handler):
        with pytest.raises(FileNotFoundError):
            handler.handle_image("nonexistent.png")

    def test_oversized_image(self, handler, tmp_path):
        # Create a large file by writing garbage
        large = tmp_path / "large.jpg"
        size = (handler.max_image_size_mb + 1) * 1024 * 1024
        large.write_bytes(b"0" * size)
        with pytest.raises(ValueError, match="exceeds maximum"):
            handler.handle_image(large)

    def test_invalid_image_content(self, handler, tmp_path):
        fake = tmp_path / "fake.png"
        fake.write_bytes(b"not a real image")
        with pytest.raises(ValueError, match="not a valid image"):
            handler.handle_image(fake)


class TestHandleText:
    def test_valid_text(self, handler, sample_text):
        dest = handler.handle_text(sample_text)
        assert dest.exists()
        assert dest.name == "test.txt"

    def test_unsupported_extension(self, handler, tmp_path):
        fake = tmp_path / "data.bin"
        fake.write_text("binary")
        with pytest.raises(ValueError, match="Unsupported text extension"):
            handler.handle_text(fake)

    def test_file_not_found(self, handler):
        with pytest.raises(FileNotFoundError):
            handler.handle_text("nope.txt")

    def test_oversized_text(self, handler, tmp_path):
        large = tmp_path / "large.txt"
        size = (handler.max_text_size_mb + 1) * 1024 * 1024
        large.write_bytes(b"a" * size)
        with pytest.raises(ValueError, match="exceeds maximum"):
            handler.handle_text(large)

    def test_non_utf8_text(self, handler, tmp_path):
        bad = tmp_path / "bad.txt"
        bad.write_bytes(b"\xff\xfe")
        with pytest.raises(ValueError, match="not valid UTF-8"):
            handler.handle_text(bad)


class TestSaveAttachment:
    def test_image_detected(self, handler, sample_image):
        dest = handler.save_attachment(sample_image)
        assert dest.suffix == ".png"

    def test_text_detected(self, handler, sample_text):
        dest = handler.save_attachment(sample_text)
        assert dest.suffix == ".txt"

    def test_unsupported_type(self, handler, tmp_path):
        unknown = tmp_path / "file.xyz"
        unknown.write_text("unknown")
        with pytest.raises(ValueError, match="Unsupported file extension"):
            handler.save_attachment(unknown)


class TestEdgeCases:
    def test_empty_text_file(self, handler, tmp_path):
        empty = tmp_path / "empty.txt"
        empty.write_text("", encoding="utf-8")
        dest = handler.handle_text(empty)
        assert dest.exists()

    def test_empty_image_file(self, handler, tmp_path):
        # PIL cannot save an empty image, so we create a minimal valid PNG
        # Actually we can create a 1x1 pixel
        img = Image.new("RGB", (1, 1))
        empty_img = tmp_path / "tiny.png"
        img.save(empty_img)
        dest = handler.handle_image(empty_img)
        assert dest.exists()

    def test_filename_with_spaces(self, handler, tmp_path):
        img = Image.new("RGB", (10, 10))
        path = tmp_path / "my image.png"
        img.save(path)
        dest = handler.handle_image(path)
        assert dest.name == "my image.png"

    def test_case_insensitive_extension(self, handler, tmp_path):
        img = Image.new("RGB", (10, 10))
        path = tmp_path / "image.PNG"
        img.save(path)
        dest = handler.handle_image(path)
        assert dest.exists()
