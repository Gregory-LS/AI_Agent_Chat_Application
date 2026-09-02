import os
import tempfile
import pytest
from io import BytesIO
from pathlib import Path
from src.attachments import AttachmentHandler


@pytest.fixture
def handler():
    # Use a temporary directory for each test
    with tempfile.TemporaryDirectory() as tmpdir:
        yield AttachmentHandler(base_dir=tmpdir)


def test_save_and_retrieve(handler):
    data = b"hello world"
    handler.save("test.txt", BytesIO(data))
    result = handler.retrieve("test.txt")
    assert result == data


def test_save_creates_file(handler):
    handler.save("a.txt", BytesIO(b"content"))
    file_path = Path(handler.base_dir) / "a.txt"
    assert file_path.exists()


def test_retrieve_nonexistent(handler):
    result = handler.retrieve("nonexistent.txt")
    assert result is None


def test_list_files_empty(handler):
    assert handler.list_files() == []


def test_list_files(handler):
    handler.save("b.txt", BytesIO(b"1"))
    handler.save("a.txt", BytesIO(b"2"))
    assert handler.list_files() == ["a.txt", "b.txt"]


def test_delete_existing(handler):
    handler.save("del.txt", BytesIO(b"delete me"))
    assert handler.delete("del.txt") is True
    assert handler.retrieve("del.txt") is None


def test_delete_nonexistent(handler):
    assert handler.delete("ghost.txt") is False


def test_clear(handler):
    handler.save("x.txt", BytesIO(b"x"))
    handler.save("y.txt", BytesIO(b"y"))
    count = handler.clear()
    assert count == 2
    assert handler.list_files() == []


def test_save_empty_filename(handler):
    with pytest.raises(ValueError, match="Filename must not be empty"):
        handler.save("", BytesIO(b"data"))


def test_save_filename_with_slash(handler):
    with pytest.raises(ValueError, match="must not contain path separators"):
        handler.save("a/b.txt", BytesIO(b"data"))


def test_save_filename_with_backslash(handler):
    with pytest.raises(ValueError, match="must not contain path separators"):
        handler.save("a\\b.txt", BytesIO(b"data"))


def test_retrieve_after_clear(handler):
    handler.save("keep.txt", BytesIO(b"keep"))
    handler.clear()
    assert handler.retrieve("keep.txt") is None


def test_multiple_saves_same_name(handler):
    handler.save("dup.txt", BytesIO(b"first"))
    handler.save("dup.txt", BytesIO(b"second"))
    result = handler.retrieve("dup.txt")
    assert result == b"second"  # overwrites
