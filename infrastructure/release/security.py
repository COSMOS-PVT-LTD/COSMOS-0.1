"""Opt-in local-preview transport and private bootstrap; legacy mode unchanged."""
from __future__ import annotations

import json
import math
import os
import secrets
import stat
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROFILE = "local-preview"
MAX_BODY = 16 * 1024**2


def add_preview_headers(handler: Any) -> None:
    for name, value in (
        ("X-Content-Type-Options", "nosniff"), ("Cache-Control", "no-store"),
        ("Referrer-Policy", "no-referrer"), ("Cross-Origin-Resource-Policy", "same-origin"),
        ("X-Frame-Options", "DENY"),
    ):
        handler.send_header(name, value)


class ReleaseProfileError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise ReleaseProfileError(code, message)


def preview_enabled(value: str | None) -> bool:
    require(value in {None, "", PROFILE}, "UNSUPPORTED_RELEASE_PROFILE", "Only explicit local-preview is supported; production is not authorized")
    return value == PROFILE


def private_bootstrap(root: Path) -> str:
    """Provision only an isolated root; never migrate/reset a legacy account."""
    require(not root.is_symlink(), "UNSAFE_DATA_ROOT", "Release preview root cannot be a symlink")
    credential = root / "first-login.json"
    database = root / "auth/users.sqlite"
    for path in (root / "auth", database, root / "auth/session.secret"):
        require(not path.is_symlink(), "UNSAFE_CREDENTIAL", "Preview authentication paths cannot be symlinks")
        require(not path.exists() or path.stat().st_uid == os.getuid(), "UNSAFE_CREDENTIAL", "Preview authentication paths must belong to the local user")
    require(not database.exists() or credential.is_file(), "LEGACY_DATA_ROOT", "Use a separate preview root; legacy accounts are not silently migrated")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    require(root.stat().st_uid == os.getuid(), "UNSAFE_DATA_ROOT", "Preview root must belong to the current local user")
    root.chmod(0o700)
    if credential.exists() or credential.is_symlink():
        require(not credential.is_symlink() and credential.is_file() and credential.stat().st_size < 4096,
                "UNSAFE_CREDENTIAL", "Private first-login record must be a bounded regular file")
        require(stat.S_IMODE(credential.stat().st_mode) == 0o600 and credential.stat().st_uid == os.getuid(),
                "UNSAFE_CREDENTIAL", "First-login record must be owned by the local user and mode 0600")
        value = json.loads(credential.read_text())
        require(type(value) is dict and set(value) == {"login_id", "password", "profile"}
                and value["profile"] == PROFILE and value["login_id"] == "cosmos-admin", "UNSAFE_CREDENTIAL", "Invalid private preview identity")
        password = value["password"]
        require(type(password) is str and 32 <= len(password) <= 128 and password != "COSMOS-Dev-2026!",
                "UNSAFE_CREDENTIAL", "A unique strong preview password is required")
        return password
    password = secrets.token_urlsafe(32)
    descriptor = os.open(credential, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump({"profile": PROFILE, "login_id": "cosmos-admin", "password": password}, output)
    return password


def private_auth_files(root: Path) -> None:
    for name in ("users.sqlite", "session.secret"):
        path = root / name
        require(not path.is_symlink() and path.is_file(), "UNSAFE_CREDENTIAL", "Authentication storage must be regular local files")
        path.chmod(0o600)
    root.chmod(0o700)


def strict_json(raw: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "INVALID_JSON", "Duplicate JSON fields are refused")
            result[key] = value
        return result
    def constant(_value: str) -> Any:
        raise ReleaseProfileError("INVALID_JSON", "Non-finite JSON constants are refused")
    def finite_float(raw: str) -> float:
        value = float(raw)
        require(math.isfinite(value), "INVALID_JSON", "Overflowing JSON numbers are refused")
        return value
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ReleaseProfileError("INVALID_JSON", "A bounded unambiguous UTF-8 JSON object is required") from error
    require(type(value) is dict, "INVALID_JSON", "JSON body must be an object")
    return value


def guard(handler: Any, method: str) -> None:
    host, port = handler.server.server_address[:2]
    require(host == "127.0.0.1" and handler.client_address[0] == "127.0.0.1", "LOOPBACK_REQUIRED", "Preview supports IPv4 loopback only")
    authorities = handler.headers.get_all("Host", [])
    require(len(authorities) == 1 and authorities[0] in {f"127.0.0.1:{port}", f"localhost:{port}"},
            "INVALID_HOST", "Exactly one matching loopback Host is required")
    require(not handler.headers.get_all("Transfer-Encoding", []), "INVALID_FRAMING", "Chunked or ambiguous request framing is unsupported")
    lengths = handler.headers.get_all("Content-Length", [])
    require(len(lengths) <= 1 and (not lengths or len(lengths[0]) <= 8 and lengths[0].isascii() and lengths[0].isdecimal()),
            "INVALID_FRAMING", "One decimal Content-Length is required")
    size = int(lengths[0]) if lengths else 0
    require(size <= MAX_BODY, "BODY_LIMIT", "Preview request exceeds the explicit 16MiB limit")
    require(method != "GET" or size == 0, "INVALID_FRAMING", "GET must not carry a body")
    require(handler.headers.get("Sec-Fetch-Site") != "cross-site", "INVALID_ORIGIN", "Cross-site requests are refused")
    if method != "GET":
        origins = handler.headers.get_all("Origin", [])
        require(origins == ["http://" + authorities[0]], "INVALID_ORIGIN", "Mutations require an exact same-origin header")
        require(method != "POST" or len(lengths) == 1 and size > 0, "INVALID_FRAMING", "POST requires a bounded explicit body")
        types = handler.headers.get_all("Content-Type", [])
        if size and method == "POST" and getattr(handler, "path", "").split("?", 1)[0] in {"/api/ingest", "/api/profile/photo"}:
            from infrastructure.transport.multipart import multipart_boundary
            require(len(types) == 1, "INVALID_CONTENT_TYPE", "One upload content type is required")
            try:
                multipart_boundary(types[0])
            except ValueError as error:
                raise ReleaseProfileError("INVALID_CONTENT_TYPE", str(error)) from error
        else:
            require(size == 0 or types == ["application/json"],
                    "INVALID_CONTENT_TYPE", "Mutations require JSON content except explicit upload routes")


class PreviewHTTPServer(ThreadingHTTPServer):
    """Bounded connections for the opt-in preview; no change to legacy server."""
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, address: tuple[str, int], handler: Any) -> None:
        require(address[0] == "127.0.0.1", "LOOPBACK_REQUIRED", "Release preview cannot bind to a public interface")
        self._slots = threading.BoundedSemaphore(8)
        super().__init__(address, handler)

    def process_request(self, request: Any, client_address: Any) -> None:
        # Brief bounded backpressure lets normal parallel page assets finish.
        # Sustained saturation still fails closed without unbounded threads.
        if not self._slots.acquire(timeout=1.0):
            try:
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()
