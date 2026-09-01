import pytest
import tempfile
import os
from pathlib import Path
from src.attachment import Attachment


@pytest.fixture
def text_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('Hello, world!')
        f.flush()
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def image_file():
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 10)
        f.flush()
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def csv_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('a,b,c\n1,2,3')
        f.flush()
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def unsupported_file():
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
        f.write(b'\x00\x01\x02')
        f.flush()
        yield Path(f.name)
    os.unlink(f.name)


class TestAttachment:
    def test_text_file_creation(self, text_file):
        att = Attachment(text_file)
        assert att.filename == text_file.name
        assert att.mime_type == 'text/plain'
        assert att.is_text
        assert not att.is_image
        assert att.size > 0

    def test_image_file_creation(self, image_file):
        att = Attachment(image_file)
        assert att.filename == image_file.name
        assert att.mime_type == 'image/png'
        assert att.is_image
        assert not att.is_text

    def test_csv_file_creation(self, csv_file):
        att = Attachment(csv_file)
        assert att.mime_type == 'text/csv'
        assert att.is_text
        assert not att.is_image

    def test_unsupported_file_raises(self, unsupported_file):
        with pytest.raises(ValueError, match='Unsupported file type'):
            Attachment(unsupported_file)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            Attachment('/nonexistent/path/file.txt')

    def test_directory_raises(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            Attachment(tmp_path)

    def test_read_text_content(self, text_file):
        att = Attachment(text_file)
        content = att.read_content()
        assert isinstance(content, str)
        assert content == 'Hello, world!'

    def test_read_image_content(self, image_file):
        att = Attachment(image_file)
        content = att.read_content()
        assert isinstance(content, bytes)
        assert len(content) > 0

    def test_metadata(self, text_file):
        att = Attachment(text_file)
        meta = att.get_metadata()
        assert meta['filename'] == text_file.name
        assert meta['mime_type'] == 'text/plain'
        assert meta['size'] > 0
        assert meta['is_image'] is False
        assert meta['is_text'] is True

    def test_read_content_caching(self, text_file):
        att = Attachment(text_file)
        first = att.read_content()
        second = att.read_content()
        assert first == second

    def test_mime_type_fallback(self):
        # .dat file with no mime type -> fallback to application/octet-stream
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as f:
            f.write(b'test')
            f.flush()
            path = Path(f.name)
        try:
            with pytest.raises(ValueError, match='Unsupported file type'):
                Attachment(path)
        finally:
            os.unlink(path)
