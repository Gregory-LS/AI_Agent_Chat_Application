'''SQLite-backed persistence for OpenRouter response metadata.'''

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .capture import extract_metadata


class MetadataStore:
    '''Store extracted OpenRouter metadata in SQLite.'''

    def __init__(self, db_path: Union[str, Path] = ':memory:') -> None:
        self.db_path = str(db_path)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self.connection: Optional[sqlite3.Connection] = conn
        self._create_schema()

    def _conn(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError('MetadataStore instance is closed')
        return self.connection

    def _create_schema(self) -> None:
        conn = self._conn()
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS openrouter_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT,
                model TEXT,
                provider TEXT,
                created INTEGER,
                total_tokens INTEGER,
                metadata_json TEXT NOT NULL,
                captured_at TEXT NOT NULL
            )
            '''
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_openrouter_metadata_model ON openrouter_metadata(model)'
        )
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_openrouter_metadata_created ON openrouter_metadata(created)'
        )
        conn.commit()

    def store_response(self, response: Union[Dict[str, Any], str, bytes]) -> int:
        '''Extract metadata from a response and store it.'''
        metadata = extract_metadata(response)
        return self.insert_metadata(metadata)

    def insert_metadata(self, metadata: Dict[str, Any]) -> int:
        '''Insert a metadata dictionary and return the new record id.'''
        conn = self._conn()
        metadata_json = json.dumps(metadata, ensure_ascii=False, default=str)
        response_id = metadata.get('id') or metadata.get('response_id')
        model = metadata.get('model')
        provider = metadata.get('provider')
        created = metadata.get('created')
        usage = metadata.get('usage')
        if isinstance(usage, dict):
            total_tokens = usage.get('total_tokens')
        else:
            total_tokens = None
        captured_at = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            '''
            INSERT INTO openrouter_metadata
                (response_id, model, provider, created, total_tokens, metadata_json, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                response_id,
                model,
                provider,
                created,
                total_tokens,
                metadata_json,
                captured_at,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)

    def list_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        '''Return stored records with parsed metadata dictionaries.'''
        if limit < 0:
            raise ValueError('limit must be non-negative')
        conn = self._conn()
        cursor = conn.execute(
            '''
            SELECT id, response_id, model, provider, created, total_tokens, metadata_json, captured_at
            FROM openrouter_metadata
            ORDER BY id DESC
            LIMIT ?
            ''',
            (limit,),
        )
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            record['metadata'] = json.loads(record.pop('metadata_json'))
            records.append(record)
        return records

    def count(self) -> int:
        '''Return the number of stored metadata records.'''
        conn = self._conn()
        row = conn.execute('SELECT COUNT(*) AS count FROM openrouter_metadata').fetchone()
        return int(row['count'])

    def close(self) -> None:
        '''Close the underlying SQLite connection.'''
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __enter__(self) -> 'MetadataStore':
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()


def store_response(
    response: Union[Dict[str, Any], str, bytes],
    db_path: Union[str, Path] = ':memory:',
) -> int:
    '''Convenience function that stores a response in a new MetadataStore.'''
    with MetadataStore(db_path) as store:
        return store.store_response(response)
