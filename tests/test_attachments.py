import pytest
import os
import tempfile
from src.attachments import AttachmentManager


@pytest.fixture
def manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AttachmentManager(storage_dir=tmpdir)
        yield mgr


class TestAttachmentManager:
    def test_save_image(self, manager):
        data = b'fake image data'
        meta = manager.save_attachment(data, 'photo.png', 'image/png')
        assert 'id' in meta
        assert meta['original_name'] == 'photo.png'
        assert meta['type'] == 'image/png'
        assert meta['size'] == len(data)
        # verify file exists
        path = manager.get_file_path(meta['id'])
        assert os.path.isfile(path)

    def test_save_text(self, manager):
        data = b'Hello, world!'
        meta = manager.save_attachment(data, 'notes.txt', 'text/plain')
        assert meta['type'] == 'text/plain'
        path = manager.get_file_path(meta['id'])
        assert os.path.isfile(path)

    def test_invalid_type_raises(self, manager):
        with pytest.raises(ValueError, match='Unsupported file type'):
            manager.save_attachment(b'data', 'file.pdf', 'application/pdf')

    def test_list_attachments(self, manager):
        manager.save_attachment(b'img1', 'a.png', 'image/png')
        manager.save_attachment(b'text', 'b.txt', 'text/plain')
        lst = manager.list_attachments()
        assert len(lst) == 2

    def test_get_attachment_nonexistent(self, manager):
        assert manager.get_attachment('nonexistent') is None

    def test_get_file_path_missing(self, manager):
        # Remove file manually to simulate loss
        meta = manager.save_attachment(b'data', 'test.png', 'image/png')
        path = manager.get_file_path(meta['id'])
        os.remove(path)
        assert manager.get_file_path(meta['id']) is None
