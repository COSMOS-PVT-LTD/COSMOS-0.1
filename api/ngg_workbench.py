"""Default-off authenticated loopback bridge to optional software fixtures.

No native auto-install, client worker paths or engineering publication authority.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from api.authentication import UserRole
from systems.contracts.geometry import GeometryContractError
from systems.contracts.geometry._wire import require

ASSETS = frozenset({"model.js", "viewport.js", "view.js", "styles.css"})
CATALOG_ITEM = {"workbench_id": "native-geometry", "title": "Native Geometry · software fixtures", "status": "active",
                "route": "/app/workbench/native-geometry", "page": 1, "description": "Optional local qualified fixtures; no engineering publication",
                "modules": ["Fixture tree", "Viewport", "Independent QA"], "validation_state": "SOFTWARE_FIXTURES_ONLY"}


def runtime_config(path: Path) -> dict[str, Any]:
    require(path.is_absolute() and path.is_file() and not path.is_symlink() and path.stat().st_size < 64 * 1024,
            "NATIVE_CONFIG_REQUIRED", "Provide an explicit bounded absolute local runtime manifest")
    config = json.loads(path.read_text())
    require(config.get("qualification") == "local-software-fixtures-only" and config.get("production_enabled") is False,
            "UNAPPROVED_RUNTIME", "Only explicit local software qualification is available")
    receipt = Path(config.get("g5_receipt", ""))
    require(receipt.is_absolute() and receipt.is_file() and not receipt.is_symlink()
            and hashlib.sha256(receipt.read_bytes()).hexdigest() == config.get("g5_receipt_sha256"),
            "G5_REQUIRED", "Hash-checked G5 closure receipt is required")
    decision = json.loads(receipt.read_text())
    require(decision.get("software_g5_pass") is True and decision.get("p08_may_begin") is True, "G5_REQUIRED", "Software G5 must pass before P08")
    hashes = config.get("sha256")
    require(type(hashes) is dict and 4 <= len(hashes) <= 256, "UNAPPROVED_RUNTIME", "Bounded runtime hash manifest required")
    for name, expected in hashes.items():
        file = Path(name)
        require(file.is_absolute() and file.is_file() and not file.is_symlink()
                and hashlib.sha256(file.read_bytes()).hexdigest() == expected, "RUNTIME_HASH_MISMATCH", "Native/runtime source hash mismatch")
    root = Path(__file__).resolve().parents[1]
    required = {str(root / name) for name in ("plugins/geometry/workers/occt_worker.py", "plugins/geometry/workers/step_reader.py",
                                             "plugins/geometry/workers/preview_reader.py", "systems/geometry/workbench.py")}
    require(required <= set(hashes), "UNAPPROVED_RUNTIME", "Workbench/worker hashes must be in manifest")
    return config


def transport_guard(handler: Any, *, mutation: bool) -> None:
    host, port = handler.server.server_address[:2]
    require(host == "127.0.0.1" and handler.client_address[0] == "127.0.0.1", "LOOPBACK_REQUIRED", "Native fixtures require IPv4 loopback")
    authority = handler.headers.get("Host")
    require(authority in {f"127.0.0.1:{port}", f"localhost:{port}"}, "INVALID_HOST", "Host must match exact loopback server")
    if mutation:
        require(handler.headers.get("Origin") == "http://" + str(authority), "INVALID_ORIGIN", "Same-origin fixture mutations required")
        require(handler.headers.get("Content-Type") == "application/json" and not handler.headers.get("Transfer-Encoding"),
                "INVALID_CONTENT_TYPE", "Bounded JSON with explicit length required")


def read_payload(handler: Any) -> dict[str, Any]:
    lengths = handler.headers.get_all("Content-Length", [])
    require(len(lengths) == 1 and not handler.headers.get_all("Transfer-Encoding", []),
            "INVALID_FRAMING", "One explicit unambiguous JSON length is required")
    length = handler.headers.get("Content-Length", "")
    require(len(length) <= 8 and length.isascii() and length.isdecimal() and 0 < int(length) <= 16 * 1024**2, "REQUEST_TOO_LARGE", "JSON body limit is 16MiB")
    if hasattr(handler, "connection"):
        handler.connection.settimeout(10)
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len({key for key, _ in items}) == len(items), "DUPLICATE_FIELD", "Duplicate JSON fields forbidden")
        return dict(items)
    def finite_float(raw: str) -> float:
        value = float(raw)
        require(math.isfinite(value), "INVALID_REQUEST", "Overflowing JSON numbers are refused")
        return value
    raw = handler.rfile.read(int(length))
    require(len(raw) == int(length), "INVALID_FRAMING", "Incomplete JSON body")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_float=finite_float,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds the supported parser depth") from error
    require(type(value) is dict, "INVALID_REQUEST", "Expected one JSON object")
    return value


def dispatch(handler: Any, path: str, session: Any, *, mutation: bool) -> None:
    app = handler.application
    if not app.ngg_enabled:
        return handler._json(404, {"error": "ngg_disabled"})
    if session is None:
        return handler._json(401, {"error": "authentication_required"})
    if getattr(app,"component_only_runtime",False):
        return handler._json(404,{"error":{"code":"FIXTURE_PROFILE_DISABLED","message":"OCCT-only component runtime; combined reference fixtures and PicoGK are deliberately disabled."}})
    try:
        transport_guard(handler, mutation=mutation)
        require(not mutation or path == "/api/ngg/measure" or session.user.role in {UserRole.ENGINEER, UserRole.ADMIN},
                "FORBIDDEN_ROLE", "Native fixture mutations require Engineer or Admin; review roles cannot become engineering publication authority")
        manager = app.ngg_workspace()
        actor = session.user.login_id
        if not mutation:
            query = parse_qs(urlparse(handler.path).query, keep_blank_values=True)
            require(all(len(v) == 1 for v in query.values()), "INVALID_REQUEST", "Duplicate query fields forbidden")
            if path == "/api/ngg/context" and not query:
                return handler._json(200, manager.context(actor))
            parts = path.removeprefix("/api/ngg/").split("/")
            if len(parts) == 2 and parts[0] == "reimports" and not query:
                return handler._json(200, manager.reimport_status(actor, parts[1]))
            require(len(parts) in (2, 3) and parts[0] == "jobs", "UNKNOWN_ROUTE", "Unknown fixture route")
            job = parts[1]
            if len(parts) == 2 and not query:
                return handler._json(200, manager.status(actor, job))
            require(len(parts) == 3 and set(query) == {"snapshot_id"}, "INVALID_REQUEST", "Exact snapshot ID required")
            snapshot = query["snapshot_id"][0]
            if parts[2] == "fixture":
                filename, data, digest = manager.fixture_bytes(actor, job, snapshot)
                handler.send_response(200)
                handler.send_header("Content-Type", "application/octet-stream")
                handler.send_header("Content-Disposition", 'attachment; filename="' + filename + '"')
                handler.send_header("X-COSMOS-SHA256", digest)
                handler.send_header("X-COSMOS-Scope", "software-fixture-not-engineering-publication")
            elif parts[2] == "preview":
                data = manager.preview(actor, job, snapshot)
                handler.send_response(200)
                handler.send_header("Content-Type", "application/octet-stream")
                handler.send_header("X-COSMOS-Scope", "display-only-si-triangles-not-export")
            else:
                raise GeometryContractError("UNKNOWN_ROUTE", "Unknown artifact route")
            handler.send_header("Content-Length", str(len(data)))
            handler.send_header("Cache-Control", "no-store")
            handler.send_header("X-Content-Type-Options", "nosniff")
            handler.end_headers(); handler.wfile.write(data)
            return
        payload = read_payload(handler)
        action = path.removeprefix("/api/ngg/")
        schemas = {"settings": {"snapshot_id", "settings"}, "activate": {"snapshot_id"}, "build": {"snapshot_id"},
                   "cancel": {"job_id"}, "measure": {"job_id", "snapshot_id", "vertex_indices"}, "reimport": {"job_id", "snapshot_id", "content_base64"}}
        require(action in schemas and set(payload) == schemas[action], "INVALID_REQUEST", "Exact fields required; no paths, commands or geometry parameters accepted")
        for key in {"snapshot_id", "job_id"} & set(payload):
            require(type(payload[key]) is str and 0 < len(payload[key]) <= 128, "INVALID_REQUEST", "Invalid bounded lineage identifier")
        if action == "settings":
            value = manager.change(actor, payload["snapshot_id"], payload["settings"])
        elif action == "activate":
            value = manager.activate(actor, payload["snapshot_id"])
        elif action == "build":
            value = manager.build(actor, payload["snapshot_id"])
        elif action == "cancel":
            value = manager.cancel(actor, payload["job_id"])
        elif action == "measure":
            value = manager.measure(actor, payload["job_id"], payload["snapshot_id"], payload["vertex_indices"])
        else:
            require(type(payload["content_base64"]) is str and len(payload["content_base64"]) <= 16 * 1024**2, "REQUEST_TOO_LARGE", "Reimport payload bounded")
            value = manager.reimport(actor, payload["job_id"], payload["snapshot_id"], base64.b64decode(payload["content_base64"], validate=True))
        handler._audit_request(session, path)
        return handler._json(200, value)
    except (GeometryContractError, ValueError, KeyError, TypeError, OSError) as error:
        handler.close_connection = True
        code = error.code if isinstance(error, GeometryContractError) else "INVALID_REQUEST"
        return handler._json(403 if code == "FORBIDDEN_ROLE" else 409 if code.startswith("STALE") else 400, {"ok": False, "error": {"code": code, "message": str(error)[:1024],
            "action": "Inspect exact snapshot, correct request or retry; engineering publication remains blocked."}})


def create_workspace(root: Path, config_path: Path | None):
    from systems.geometry.workbench import GeometryWorkbench
    require(config_path is not None, "NATIVE_CONFIG_REQUIRED", "Provide an explicit qualified local runtime config")
    assert config_path is not None
    config = runtime_config(config_path)
    candidate_root = root.resolve() / "ngg_software_candidates"
    candidate_root.mkdir(mode=0o700, exist_ok=True)
    return GeometryWorkbench(candidate_root, config)
