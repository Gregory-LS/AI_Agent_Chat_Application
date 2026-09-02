import pytest
import tempfile
import os
from pathlib import Path
from attachments import AttachmentHandler


class TestAttachmentHandler:
    @pytest.fixture
    def handler(self):
        tmpdir = tempfile.mkdtemp()
        yield AttachmentHandler(base_dir=tmpdir)
        # Cleanup
        import shutil
        shutil.rmtree(tmpdir)

    def test_upload_and_download(self, handler):
        content = b"hello world"
        filename = handler.upload("issue-1", "test.txt", content)
        assert filename == "test.txt"
        downloaded = handler.download("issue-1", "test.txt")
        assert downloaded == content

    def test_upload_duplicate_renames(self, handler):
        content1 = b"first"
        content2 = b"second"
        f1 = handler.upload("issue-1", "file.txt", content1)
        assert f1 == "file.txt"
        f2 = handler.upload("issue-1", "file.txt", content2)
        assert f2 == "file_1.txt"
        # Ensure both files exist
        assert handler.download("issue-1", "file.txt") == content1
        assert handler.download("issue-1", "file_1.txt") == content2

    def test_list_attachments_empty(self, handler):
        assert handler.list_attachments("issue-2") == []

    def test_list_attachments(self, handler):
        handler.upload("issue-3", "a.txt", b"a")
        handler.upload("issue-3", "b.txt", b"b")
        assert handler.list_attachments("issue-3") == ["a.txt", "b.txt"]

    def test_download_nonexistent(self, handler):
        with pytest.raises(FileNotFoundError):
            handler.download("nonexistent", "no.txt")

    def test_delete_attachment(self, handler):
        handler.upload("issue-4", "del.txt", b"delete me")
        assert handler.delete_attachment("issue-4", "del.txt") == True
        assert handler.list_attachments("issue-4") == []

    def test_delete_nonexistent(self, handler):
        assert handler.delete_attachment("issue-5", "nothing.txt") == False

    def test_delete_all_for_resource(self, handler):
        handler.upload("issue-6", "a.txt", b"a")
        handler.upload("issue-6", "b.txt", b"b")
        assert handler.delete_all_for_resource("issue-6") == 2
        assert handler.list_attachments("issue-6") == []

    def test_delete_all_empty(self, handler):
        assert handler.delete_all_for_resource("no-resource") == 0

    def test_upload_empty_resource_id(self, handler):
        with pytest.raises(ValueError):
            handler.upload("", "f.txt", b"data")

    def test_upload_empty_filename(self, handler):
        with pytest.raises(ValueError):
            handler.upload("res", "", b"data")

    def test_download_empty_resource_id(self, handler):
        with pytest.raises(ValueError):
            handler.download("", "f.txt")

    def test_list_empty_resource_id(self, handler):
        with pytest.raises(ValueError):
            handler.list_attachments("")

    def test_delete_empty_resource_id(self, handler):
        with pytest.raises(ValueError):
            handler.delete_attachment("", "f.txt")

    def test_delete_all_empty_resource_id(self, handler):
        with pytest.raises(ValueError):
            handler.delete_all_for_resource("")

    def test_upload_with_path_traversal(self, handler):
        # Simulate a filename with path components
        content = b"safe"
        filename = handler.upload("issue-7", "../evil.txt", content)
        # Should store only basename
        assert filename == "evil.txt"
        # Should not have created a file outside base_dir
        from pathlib import Path
        assert not (handler.base_dir / "../evil.txt").resolve().exists()

    def test_upload_and_download_binary(self, handler):
        content = bytes(range(256))
        filename = handler.upload("issue-8", "binary.bin", content)
        assert handler.download("issue-8", filename) == content
