from pathlib import Path

import pytest

from attachments import (
    Attachment,
    AttachmentNotFoundError,
    AttachmentStore,
    ValidationError,
)


@pytest.fixture()
def store(tmp_path: Path) -> AttachmentStore:
    return AttachmentStore(storage_dir=tmp_path / 'attachments')


def build_attachment(**overrides) -> Attachment:
    values = {
        'filename': 'notes.txt',
        'content_type': 'text/plain',
        'data': b'hello attachments',
    }
    values.update(overrides)
    return Attachment(**values)


def test_save_and_load_round_trip(store):
    original = build_attachment(metadata={'user_id': 42, 'labels': ['docs']})

    saved = store.save(original)

    loaded = store.load(saved.attachment_id)
    assert loaded.attachment_id == saved.attachment_id
    assert loaded.filename == original.filename
    assert loaded.content_type == original.content_type
    assert loaded.data == original.data
    assert loaded.metadata == original.metadata


def test_save_generates_valid_id(store):
    saved = store.save(build_attachment())

    assert len(saved.attachment_id) > 0
    assert all(c.isalnum() or c in '-_' for c in saved.attachment_id)


def test_save_preserves_provided_id(store):
    saved = store.save(build_attachment(attachment_id='my-file'))

    assert saved.attachment_id == 'my-file'
    assert store.load('my-file').filename == 'notes.txt'


def test_rejects_too_large(tmp_path):
    store = AttachmentStore(tmp_path / 'medium', max_size=4)

    with pytest.raises(ValidationError, match='maximum allowed'):
        store.save(build_attachment(data=b'12345'))


def test_rejects_disallowed_content_type(store):
    with pytest.raises(ValidationError, match='content type'):
        store.save(build_attachment(content_type='application/x-unknown'))


@pytest.mark.parametrize(
    'filename',
    ['', '.', '..', '../evil.sh', 'dir/evil.sh', 'evil.sh' + chr(92)],
)
def test_rejects_unsafe_filename(store, filename):
    with pytest.raises(ValidationError, match='filename'):
        store.save(build_attachment(filename=filename))


def test_load_rejects_invalid_id(store):
    with pytest.raises(ValueError):
        store.load('../bad')


def test_load_missing_attachment(store):
    with pytest.raises(AttachmentNotFoundError):
        store.load('doesnotexist')


def test_delete_removes_attachment(store):
    saved = store.save(build_attachment())

    assert store.exists(saved.attachment_id) is True
    assert store.delete(saved.attachment_id) is True
    assert store.exists(saved.attachment_id) is False
    assert store.delete(saved.attachment_id) is False


def test_list_attachments(store):
    first = store.save(build_attachment(filename='a.txt', data=b'a'))
    second = store.save(build_attachment(filename='b.txt', data=b'bb'))

    assert set(store.list_ids()) == {first.attachment_id, second.attachment_id}
    assert len(store.list_attachments()) == 2


def test_attachment_from_file(tmp_path):
    path = tmp_path / 'sample.bin'
    path.write_bytes(bytes([0, 1]))

    attachment = Attachment.from_file(path, content_type='application/octet-stream')

    assert attachment.filename == 'sample.bin'
    assert attachment.data == bytes([0, 1])
    assert attachment.size == 2
