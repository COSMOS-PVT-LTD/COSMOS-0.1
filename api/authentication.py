"""Local user accounts, sessions, and login for the COSMOS desktop application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
import hashlib
import hmac
import json
import secrets
import sqlite3
import threading

__all__ = (
    "AuthenticationError",
    "AuthService",
    "SessionRecord",
    "UserAccount",
    "UserRole",
)


class AuthenticationError(ValueError):
    """Login or session validation failed."""


class UserRole(Enum):
    VIEWER = "VIEWER"
    ENGINEER = "ENGINEER"
    REVIEWER = "REVIEWER"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"


@dataclass(frozen=True, slots=True, kw_only=True)
class UserAccount:
    user_id: str
    login_id: str
    display_name: str
    designation: str
    employee_id: str
    team: str
    role: UserRole
    active: bool
    bio: str = ""
    profile_photo: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionRecord:
    session_id: str
    token: str
    user: UserAccount
    expires_at: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return digest.hex()


class AuthService:
    """Company-local credential store. Not a cloud identity provider."""

    def __init__(self, root: Path | str, *, secret: str | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "users.sqlite"
        self._secret = secret or self._load_or_create_secret()
        self._lock = threading.Lock()
        self._migrate()
        self._ensure_bootstrap_admin()

    def _load_or_create_secret(self) -> str:
        path = self.root / "session.secret"
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
        value = secrets.token_hex(32)
        path.write_text(value, encoding="utf-8")
        return value

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
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        login_id TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        password_salt TEXT NOT NULL,
                        display_name TEXT NOT NULL,
                        designation TEXT NOT NULL,
                        employee_id TEXT NOT NULL,
                        team TEXT NOT NULL,
                        role TEXT NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        token_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        client_info TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    );
                    """,
                )
                connection.commit()
                self._ensure_profile_columns(connection)
            finally:
                connection.close()

    def _ensure_profile_columns(self, connection: sqlite3.Connection) -> None:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "bio" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN bio TEXT NOT NULL DEFAULT ''")
        if "profile_photo" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT NOT NULL DEFAULT ''")
        connection.commit()

    def _ensure_bootstrap_admin(self) -> None:
        if self._get_user_by_login("cosmos-admin") is not None:
            return
        self.register_user(
            login_id="cosmos-admin",
            password="COSMOS-Dev-2026!",
            display_name="COSMOS Administrator",
            designation="System Administrator",
            employee_id="COSMOS-001",
            team="Platform",
            role=UserRole.ADMIN,
        )

    def register_user(
        self,
        *,
        login_id: str,
        password: str,
        display_name: str,
        designation: str,
        employee_id: str,
        team: str,
        role: UserRole,
    ) -> UserAccount:
        cleaned_login = login_id.strip().lower()
        if not cleaned_login or not password:
            raise AuthenticationError("login_id and password are required.")
        if self._get_user_by_login(cleaned_login) is not None:
            raise AuthenticationError(f"login_id '{cleaned_login}' already exists.")
        salt = secrets.token_bytes(16)
        user_id = f"USR-{secrets.token_hex(8)}"
        stamp = _utc_now().isoformat()
        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    """
                    INSERT INTO users(
                        user_id, login_id, password_hash, password_salt, display_name,
                        designation, employee_id, team, role, active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        user_id,
                        cleaned_login,
                        _hash_password(password, salt),
                        salt.hex(),
                        display_name.strip(),
                        designation.strip(),
                        employee_id.strip(),
                        team.strip(),
                        role.value,
                        stamp,
                    ),
                )
                connection.commit()
            finally:
                connection.close()
        account = self._get_user_by_login(cleaned_login)
        if account is None:
            raise AuthenticationError("user registration failed.")
        return account

    def login(
        self,
        login_id: str,
        password: str,
        *,
        client_info: str = "cosmos-desktop",
        ttl_hours: int = 12,
    ) -> SessionRecord:
        account = self._get_user_by_login(login_id.strip().lower())
        if account is None or not account.active:
            raise AuthenticationError("Invalid login credentials.")
        row = self._fetch_user_row(login_id.strip().lower())
        if row is None:
            raise AuthenticationError("Invalid login credentials.")
        salt = bytes.fromhex(str(row["password_salt"]))
        if not hmac.compare_digest(_hash_password(password, salt), str(row["password_hash"])):
            raise AuthenticationError("Invalid login credentials.")
        token = secrets.token_urlsafe(32)
        session_id = f"SES-{secrets.token_hex(8)}"
        token_hash = hashlib.sha256(f"{self._secret}:{token}".encode("utf-8")).hexdigest()
        created = _utc_now()
        expires = created + timedelta(hours=ttl_hours)
        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    """
                    INSERT INTO sessions(session_id, user_id, token_hash, created_at, expires_at, client_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        account.user_id,
                        token_hash,
                        created.isoformat(),
                        expires.isoformat(),
                        client_info,
                    ),
                )
                connection.commit()
            finally:
                connection.close()
        return SessionRecord(
            session_id=session_id,
            token=token,
            user=account,
            expires_at=expires.isoformat(),
        )

    def validate_token(self, token: str) -> SessionRecord | None:
        if not token:
            return None
        token_hash = hashlib.sha256(f"{self._secret}:{token}".encode("utf-8")).hexdigest()
        with self._lock:
            connection = self._connect()
            try:
                row = connection.execute(
                    """
                    SELECT s.session_id, s.user_id, s.expires_at, u.login_id, u.display_name,
                           u.designation, u.employee_id, u.team, u.role, u.active,
                           u.bio, u.profile_photo
                    FROM sessions s
                    JOIN users u ON u.user_id = s.user_id
                    WHERE s.token_hash = ?
                    """,
                    (token_hash,),
                ).fetchone()
            finally:
                connection.close()
        if row is None:
            return None
        expires = datetime.fromisoformat(str(row["expires_at"]))
        if expires < _utc_now():
            return None
        if not int(row["active"]):
            return None
        account = UserAccount(
            user_id=str(row["user_id"]),
            login_id=str(row["login_id"]),
            display_name=str(row["display_name"]),
            designation=str(row["designation"]),
            employee_id=str(row["employee_id"]),
            team=str(row["team"]),
            role=UserRole(str(row["role"])),
            active=True,
            bio=str(row["bio"] if "bio" in row.keys() else ""),
            profile_photo=str(row["profile_photo"] if "profile_photo" in row.keys() else ""),
        )
        return SessionRecord(
            session_id=str(row["session_id"]),
            token=token,
            user=account,
            expires_at=str(row["expires_at"]),
        )

    def logout(self, token: str) -> None:
        if not token:
            return
        token_hash = hashlib.sha256(f"{self._secret}:{token}".encode("utf-8")).hexdigest()
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
                connection.commit()
            finally:
                connection.close()

    def list_users(self) -> tuple[UserAccount, ...]:
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    "SELECT user_id, login_id, display_name, designation, employee_id, team, role, active FROM users ORDER BY login_id",
                ).fetchall()
            finally:
                connection.close()
        return tuple(self._row_to_account(row) for row in rows)

    def _fetch_user_row(self, login_id: str) -> sqlite3.Row | None:
        with self._lock:
            connection = self._connect()
            try:
                return connection.execute(
                    "SELECT * FROM users WHERE login_id = ?",
                    (login_id,),
                ).fetchone()
            finally:
                connection.close()

    def _get_user_by_login(self, login_id: str) -> UserAccount | None:
        row = self._fetch_user_row(login_id)
        if row is None:
            return None
        return self._row_to_account(row)

    @staticmethod
    def _row_to_account(row: sqlite3.Row) -> UserAccount:
        return UserAccount(
            user_id=str(row["user_id"]),
            login_id=str(row["login_id"]),
            display_name=str(row["display_name"]),
            designation=str(row["designation"]),
            employee_id=str(row["employee_id"]),
            team=str(row["team"]),
            role=UserRole(str(row["role"])),
            active=bool(int(row["active"])),
            bio=str(row["bio"] if "bio" in row.keys() else ""),
            profile_photo=str(row["profile_photo"] if "profile_photo" in row.keys() else ""),
        )

    def get_user_by_id(self, user_id: str) -> UserAccount | None:
        with self._lock:
            connection = self._connect()
            try:
                row = connection.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            finally:
                connection.close()
        if row is None:
            return None
        return self._row_to_account(row)

    def update_user_profile(
        self,
        user_id: str,
        *,
        display_name: str | None = None,
        designation: str | None = None,
        team: str | None = None,
        bio: str | None = None,
    ) -> UserAccount:
        assignments: list[str] = []
        values: list[str] = []
        if display_name is not None:
            assignments.append("display_name = ?")
            values.append(display_name.strip())
        if designation is not None:
            assignments.append("designation = ?")
            values.append(designation.strip())
        if team is not None:
            assignments.append("team = ?")
            values.append(team.strip())
        if bio is not None:
            assignments.append("bio = ?")
            values.append(bio.strip()[:500])
        if not assignments:
            raise AuthenticationError("No profile fields supplied.")
        values.append(user_id)
        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    f"UPDATE users SET {', '.join(assignments)} WHERE user_id = ?",
                    values,
                )
                connection.commit()
            finally:
                connection.close()
        account = self.get_user_by_id(user_id)
        if account is None:
            raise AuthenticationError("User not found.")
        return account

    def set_profile_photo(self, user_id: str, filename: str) -> None:
        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    "UPDATE users SET profile_photo = ? WHERE user_id = ?",
                    (filename, user_id),
                )
                connection.commit()
            finally:
                connection.close()

    def user_to_mapping(self, user: UserAccount) -> dict[str, object]:
        return {
            "user_id": user.user_id,
            "login_id": user.login_id,
            "display_name": user.display_name,
            "designation": user.designation,
            "employee_id": user.employee_id,
            "team": user.team,
            "role": user.role.value,
        }
