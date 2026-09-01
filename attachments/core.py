from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

DEFAULT_ALLOWED_CONTENT_TYPES = frozenset({
    'text/plain',
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/json',
    'application/zip',
    'application/octet-stream',
})
ALLOWED_CONTENT_TYPES = DEFAULT_ALLOWED_CONTENT_TYPES

DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MiB

_ATTACHMENT_ID_RE = re.compile(r'^[A-Za-z0-9_-]{1,128}$')


class AttachmentError(Exception):
    '''Base exception for attachment handling errors.'''


class ValidationError(AttachmentError):
    '''Raised when an attachment does not pass validation.'''


class AttachmentNotFoundError(AttachmentError):
    '''Raised when an attachment ID cannot be found in the store.'''


@dataclass
class Attachment:
    '''Represents a file attachment.

    Attributes:
        filename: Plain file name, without any path separators.
        content_type: MIME type of the attachment.
        data: Raw file bytes.
        metadata: Arbitrary JSON-serializable metadata attached to the file.
        attachment_id: Stable, unique identifier. Leave empty to generate one on save.
    '''

    filename: str
    content_type: str
    data: bytes
    metadata: dict[str, Any] = field(default_factory=dict)
    attachment_id: str = ''

    @property
    def size(self) -> int:
        '''Return the size of the attachment data in bytes.'''
        return len(self.data)

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        content_type: str = 'application/octet-stream',
        metadata: dict[str, Any] | None = None,
    ) -> 'Attachment':
        '''Create an Attachment from a file on disk.'''
        path = Path(path)
        return cls(
            filename=path.name,
            content_type=content_type,
            data=path.read_bytes(),
            metadata=metadata or {},
        )


class AttachmentStore:
    '''Store, validate and retrieve attachments on the local filesystem.

    Each attachment is written as two files inside ``storage_dir``:

    - ``<attachment_id>.data``: the raw file bytes.
    - ``<attachment_id>.json``: sidecar metadata (filename, MIME type, metadata).
    '''

    def __init__(
        self,
        storage_dir: str | Path,
        allowed_types: Iterable[str] | None = None,
        max_size: int = DEFAULT_MAX_FILE_SIZE,
    ) -> None:
        self.storage_dir = Path(storage_dir).expanduser().resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_types = {
            item.lower()
            for item in (
                DEFAULT_ALLOWED_CONTENT_TYPES if allowed_types is None else allowed_types
            )
        }
        self.max_size = max_size

    @staticmethod
    def _validate_id(attachment_id: str) -> None:
        if not isinstance(attachment_id, str) or not _ATTACHMENT_ID_RE.match(attachment_id):
            raise ValueError('Invalid attachment ID')

    def validate(self, attachment: Attachment) -> None:
        '''Validate attachment data, content type and filename.

        Raises:
            ValidationError: If any validation rule is violated.
        '''
        if not isinstance(attachment.data, bytes):
            raise ValidationError('Attachment data must be bytes')
        if len(attachment.data) > self.max_size:
            raise ValidationError(
                f'Attachment is {len(attachment.data)} bytes; maximum allowed is {self.max_size} bytes'
            )
        if (
            not attachment.filename
            or attachment.filename in {'.', '..'}
            or '/' in attachment.filename
            or chr(92) in attachment.filename  # backslash
        ):
            raise ValidationError('Attachment filename must be a plain file name')
        if attachment.content_type.lower() not in self.allowed_types:
            raise ValidationError(
                f'Content type {attachment.content_type!r} is not allowed'
            )

    def save(self, attachment: Attachment) -> Attachment:
        '''Validate and persist an attachment.

        If the attachment has no ID, a random hex ID is generated.
        '''
        self.validate(attachment)
        if not attachment.attachment_id:
            attachment.attachment_id = uuid.uuid4().hex
        self._validate_id(attachment.attachment_id)

        data_path = self.storage_dir / f'{attachment.attachment_id}.data'
        metadata_path = self.storage_dir / f'{attachment.attachment_id}.json'

        data_path.write_bytes(attachment.data)
        payload = {
            'attachment_id': attachment.attachment_id,
            'filename': attachment.filename,
            'content_type': attachment.content_type,
            'metadata': attachment.metadata,
        }
        metadata_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + chr(10),
            encoding='utf-8',
        )
        return attachment

    def load(self, attachment_id: str) -> Attachment:
        '''Load an attachment from the store by its ID.'''
        self._validate_id(attachment_id)
        data_path = self.storage_dir / f'{attachment_id}.data'
        metadata_path = self.storage_dir / f'{attachment_id}.json'

        if not data_path.exists() or not metadata_path.exists():
            raise AttachmentNotFoundError(f'Attachment {attachment_id!r} not found')

        try:
            with metadata_path.open('r', encoding='utf-8') as metadata_file:
                payload = json.load(metadata_file)
            filename = str(payload['filename'])
            content_type = str(payload['content_type'])
            metadata = payload.get('metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise AttachmentError(
                f'Could not read attachment metadata for {attachment_id!r}'
            ) from exc

        attachment = Attachment(
            filename=filename,
            content_type=content_type,
            data=data_path.read_bytes(),
            metadata=metadata,
            attachment_id=attachment_id,
        )
        self.validate(attachment)
        return attachment

    def delete(self, attachment_id: str) -> bool:
        '''Delete an attachment. Returns True if any file was removed.'''
        self._validate_id(attachment_id)
        data_path = self.storage_dir / f'{attachment_id}.data'
        metadata_path = self.storage_dir / f'{attachment_id}.json'
        deleted = False
        for path in (data_path, metadata_path):
            if path.exists():
                path.unlink()
                deleted = True
        return deleted

    def exists(self, attachment_id: str) -> bool:
        '''Return True if an attachment with the given ID is stored.'''
        self._validate_id(attachment_id)
        return (self.storage_dir / f'{attachment_id}.data').exists()

    def list_ids(self) -> list[str]:
        '''Return all stored attachment IDs sorted alphabetically.'''
        return sorted(path.stem for path in self.storage_dir.glob('*.data'))

    def list_attachments(self) -> list[Attachment]:
        '''Load and return all stored attachments.'''
        return [self.load(attachment_id) for attachment_id in self.list_ids()]


def save_attachment(
    attachment: Attachment,
    storage_dir: str | Path = '.',
    **kwargs: Any,
) -> Attachment:
    '''Convenience function for saving an attachment to the default store.'''
    return AttachmentStore(storage_dir, **kwargs).save(attachment)


def load_attachment(attachment_id: str, storage_dir: str | Path = '.') -> Attachment:
    '''Convenience function for loading an attachment.'''
    return AttachmentStore(storage_dir).load(attachment_id)


def delete_attachment(attachment_id: str, storage_dir: str | Path = '.') -> bool:
    '''Convenience function for deleting an attachment.'''
    return AttachmentStore(storage_dir).delete(attachment_id)
