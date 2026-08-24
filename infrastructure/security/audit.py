"""Application-level audit trail. Separate from knowledge/foundation/audit.py."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import threading

__all__ = ("AppAuditEvent", "AppAuditLog")


@dataclass(frozen=True, slots=True, kw_only=True)
class AppAuditEvent:
    event_id: int
    timestamp: str
    user_id: str
    login_id: str
    action: str
    resource: str
    detail: str
    source_ip: str
    user_agent: str
    session_id: str | None


class AppAuditLog:
    """Append-only application audit store for company-wide action tracing."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _migrate(self) -> None:
        with self._lock:
            connection = self._connect()
            try:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS app_audit_events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        login_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource TEXT NOT NULL,
                        detail TEXT NOT NULL,
                        source_ip TEXT NOT NULL,
                        user_agent TEXT NOT NULL,
                        session_id TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_app_audit_user ON app_audit_events(user_id);
                    CREATE INDEX IF NOT EXISTS idx_app_audit_action ON app_audit_events(action);
                    CREATE INDEX IF NOT EXISTS idx_app_audit_ts ON app_audit_events(timestamp);
                    """,
                )
                connection.commit()
            finally:
                connection.close()

    def record(
        self,
        *,
        user_id: str,
        login_id: str,
        action: str,
        resource: str,
        detail: dict[str, object] | str = "",
        source_ip: str = "local",
        user_agent: str = "cosmos-desktop",
        session_id: str | None = None,
    ) -> AppAuditEvent:
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        encoded = detail if isinstance(detail, str) else json.dumps(detail, sort_keys=True)
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO app_audit_events(
                        timestamp, user_id, login_id, action, resource, detail,
                        source_ip, user_agent, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (stamp, user_id, login_id, action, resource, encoded, source_ip, user_agent, session_id),
                )
                connection.commit()
                event_id = int(cursor.lastrowid)
            finally:
                connection.close()
        return AppAuditEvent(
            event_id=event_id,
            timestamp=stamp,
            user_id=user_id,
            login_id=login_id,
            action=action,
            resource=resource,
            detail=encoded,
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
        )

    def list_events(self, *, limit: int = 200) -> tuple[AppAuditEvent, ...]:
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    """
                    SELECT event_id, timestamp, user_id, login_id, action, resource,
                           detail, source_ip, user_agent, session_id
                    FROM app_audit_events
                    ORDER BY event_id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            finally:
                connection.close()
        return tuple(
            AppAuditEvent(
                event_id=int(row["event_id"]),
                timestamp=str(row["timestamp"]),
                user_id=str(row["user_id"]),
                login_id=str(row["login_id"]),
                action=str(row["action"]),
                resource=str(row["resource"]),
                detail=str(row["detail"]),
                source_ip=str(row["source_ip"]),
                user_agent=str(row["user_agent"]),
                session_id=str(row["session_id"]) if row["session_id"] else None,
            )
            for row in rows
        )
