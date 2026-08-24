"""Persistence backend protocol. SQLite is a local/development boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
import json
import sqlite3
import threading

__all__ = (
    "InMemoryPersistenceBackend",
    "PersistenceBackend",
    "SQLitePersistenceBackend",
)


class PersistenceBackend(Protocol):
    name: str

    def migrate(self) -> int: ...

    def put(self, collection: str, record_id: str, payload: dict[str, object]) -> None: ...

    def get(self, collection: str, record_id: str) -> dict[str, object] | None: ...

    def list(self, collection: str) -> tuple[dict[str, object], ...]: ...

    def health(self) -> str: ...

    def export_bytes(self) -> bytes: ...

    def import_bytes(self, data: bytes) -> None: ...


class InMemoryPersistenceBackend:
    name = "memory"

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict[str, object]]] = {}

    def migrate(self) -> int:
        return 1

    def put(self, collection: str, record_id: str, payload: dict[str, object]) -> None:
        self._data.setdefault(collection, {})[record_id] = dict(payload)

    def get(self, collection: str, record_id: str) -> dict[str, object] | None:
        bucket = self._data.get(collection, {})
        item = bucket.get(record_id)
        return dict(item) if item is not None else None

    def list(self, collection: str) -> tuple[dict[str, object], ...]:
        bucket = self._data.get(collection, {})
        return tuple(dict(item) for item in bucket.values())

    def health(self) -> str:
        return "ok"

    def export_bytes(self) -> bytes:
        return json.dumps(self._data, sort_keys=True).encode("utf-8")

    def import_bytes(self, data: bytes) -> None:
        payload = json.loads(data.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Persistence export is not a mapping.")
        self._data = {
            str(collection): {
                str(record_id): dict(record)
                for record_id, record in records.items()
            }
            for collection, records in payload.items()
        }


class SQLitePersistenceBackend:
    """Generic local KV store. Not a production multi-node database."""

    name = "sqlite-local"

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._connection: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    def connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        self._connection = connection
        return connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def migrate(self) -> int:
        connection = self.connect()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_kv (
                collection TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (collection, record_id)
            )
            """,
        )
        connection.commit()
        return 1

    def put(self, collection: str, record_id: str, payload: dict[str, object]) -> None:
        connection = self.connect()
        stamp = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(payload, sort_keys=True)
        with self._lock:
            connection.execute(
                """
                INSERT INTO workspace_kv(collection, record_id, payload, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(collection, record_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
                """,
                (collection, record_id, encoded, stamp),
            )
            connection.commit()

    def get(self, collection: str, record_id: str) -> dict[str, object] | None:
        connection = self.connect()
        with self._lock:
            row = connection.execute(
                "SELECT payload FROM workspace_kv WHERE collection = ? AND record_id = ?",
                (collection, record_id),
            ).fetchone()
        if row is None:
            return None
        loaded = json.loads(row["payload"])
        return dict(loaded) if isinstance(loaded, dict) else None

    def list(self, collection: str) -> tuple[dict[str, object], ...]:
        connection = self.connect()
        with self._lock:
            rows = connection.execute(
                "SELECT payload FROM workspace_kv WHERE collection = ? ORDER BY record_id",
                (collection,),
            ).fetchall()
        items: list[dict[str, object]] = []
        for row in rows:
            loaded = json.loads(row["payload"])
            if isinstance(loaded, dict):
                items.append(dict(loaded))
        return tuple(items)

    def health(self) -> str:
        try:
            self.migrate()
            self.connect().execute("SELECT 1")
        except sqlite3.Error as exc:
            return f"unavailable:{exc}"
        return "ok"

    def export_bytes(self) -> bytes:
        return self.path.read_bytes() if self.path.is_file() else b""

    def import_bytes(self, data: bytes) -> None:
        self.close()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(data)
        self.migrate()
