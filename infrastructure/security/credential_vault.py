"""Encrypted company credential vault — not exposed in application UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import re
import secrets
import sqlite3
import threading

__all__ = ("CredentialIssueService", "CredentialVault", "GeneratedCredentials")


@dataclass(frozen=True, slots=True, kw_only=True)
class GeneratedCredentials:
    login_id: str
    password: str
    user_id: str


class CredentialVault:
    """Append-only encrypted store for issued employee credentials."""

    def __init__(self, root: Path | str, *, master_secret: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "credential_vault.sqlite"
        self._key = hashlib.pbkdf2_hmac(
            "sha256",
            master_secret.encode("utf-8"),
            b"COSMOS-CREDENTIAL-VAULT",
            260_000,
            dklen=32,
        )
        self._lock = threading.Lock()
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _migrate(self) -> None:
        with self._lock:
            connection = self._connect()
            try:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS issued_credentials (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        login_id TEXT NOT NULL,
                        password_cipher TEXT NOT NULL,
                        issued_at TEXT NOT NULL,
                        issued_by TEXT NOT NULL,
                        employee_id TEXT NOT NULL,
                        display_name TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_cred_user ON issued_credentials(user_id);
                    """,
                )
                connection.commit()
            finally:
                connection.close()

    def _encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(16)
        data = plaintext.encode("utf-8")
        stream = hashlib.pbkdf2_hmac("sha256", self._key, nonce, 120_000, dklen=max(32, len(data)))
        masked = bytes(a ^ b for a, b in zip(data, stream))
        return base64.urlsafe_b64encode(nonce + masked).decode("ascii")

    def _decrypt(self, token: str) -> str:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        nonce, masked = raw[:16], raw[16:]
        stream = hashlib.pbkdf2_hmac("sha256", self._key, nonce, 120_000, dklen=max(32, len(masked)))
        plain = bytes(a ^ b for a, b in zip(masked, stream))
        return plain.decode("utf-8")

    def store_issued(
        self,
        *,
        user_id: str,
        login_id: str,
        password: str,
        issued_by: str,
        employee_id: str,
        display_name: str,
    ) -> int:
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        cipher = self._encrypt(password)
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO issued_credentials(
                        user_id, login_id, password_cipher, issued_at, issued_by,
                        employee_id, display_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, login_id, cipher, stamp, issued_by, employee_id, display_name),
                )
                connection.commit()
                return int(cursor.lastrowid)
            finally:
                connection.close()

    def export_for_authorized_admin(self) -> tuple[dict[str, object], ...]:
        """Offline/CLI retrieval only — never wired to public UI routes."""

        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    """
                    SELECT record_id, user_id, login_id, password_cipher, issued_at,
                           issued_by, employee_id, display_name
                    FROM issued_credentials
                    ORDER BY record_id DESC
                    """,
                ).fetchall()
            finally:
                connection.close()
        return tuple(
            {
                "record_id": int(row["record_id"]),
                "user_id": str(row["user_id"]),
                "login_id": str(row["login_id"]),
                "password": self._decrypt(str(row["password_cipher"])),
                "issued_at": str(row["issued_at"]),
                "issued_by": str(row["issued_by"]),
                "employee_id": str(row["employee_id"]),
                "display_name": str(row["display_name"]),
            }
            for row in rows
        )


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", ".", value.strip().lower()).strip(".")
    return cleaned or "employee"


def generate_login_id(*, display_name: str, employee_id: str) -> str:
    base = _slug(display_name.split()[0] if display_name else "employee")
    suffix = re.sub(r"[^a-z0-9]", "", employee_id.lower())[:8] or secrets.token_hex(2)
    candidate = f"{base}.{suffix}"
    return candidate[:48]


def generate_password() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(16))
        if (
            any(c.isupper() for c in value)
            and any(c.islower() for c in value)
            and any(c.isdigit() for c in value)
            and any(c in "!@#$%" for c in value)
        ):
            return value


class CredentialIssueService:
    def __init__(self, auth_root: Path | str, vault_root: Path | str, *, master_secret: str) -> None:
        self.vault = CredentialVault(vault_root, master_secret=master_secret)

    def issue(self, *, display_name: str, employee_id: str) -> GeneratedCredentials:
        from api.authentication import AuthService

        auth = AuthService(auth_root) if isinstance(auth_root, Path) else None
        del auth
        login_id = generate_login_id(display_name=display_name, employee_id=employee_id)
        password = generate_password()
        return GeneratedCredentials(login_id=login_id, password=password, user_id="")

    @staticmethod
    def write_export_file(records: tuple[dict[str, object], ...], destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(list(records), indent=2), encoding="utf-8")
        destination.chmod(0o600)
        return destination
