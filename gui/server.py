"""COSMOS desktop application HTTP shell — login, workbenches, audit, knowledge."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
from pathlib import Path
from urllib.parse import urlparse
import json
import mimetypes
import secrets
import threading

from api.authentication import AuthenticationError, AuthService, UserRole
from api.authorization import (
    assert_login_profile,
    infrastructure_for_profile,
    map_user_role_to_workspace,
    redirect_for_profile,
    role_can_administer,
    role_can_audit,
)
from api.physics_compressible import (
    evaluate_area_mach,
    evaluate_bartz_htc,
    evaluate_isentropic_stagnation,
    evaluate_thin_wall_stress,
    map_engineering_error,
)
from api.profile import ProfileService
from api.propulsion_workflow import (
    create_design,
    export_design,
    get_design_payload,
    get_stage_result_payload,
    get_workflow_payload,
    load_design,
    map_systems_error,
    run_isentropic,
    run_phase3,
    run_phase4,
    run_phase6,
    update_requirements,
)
from gui.knowledge_proxy import dispatch_knowledge_request, is_knowledge_api_path
from gui.workbenches.propulsion_suite import PROPULSION_SUITE_MODULES
from gui.workbenches.registry import WORKBENCH_PAGES, workbench_by_id
from systems.persistence.design_store import DesignStore


def _workbench_payload(item) -> dict[str, object]:
    return {
        "workbench_id": item.workbench_id,
        "title": item.title,
        "route": item.route,
        "status": item.status,
        "description": item.description,
        "design_type": item.design_type,
        "revision": item.revision,
        "validation_state": item.validation_state,
        "domain": item.domain,
    }


from infrastructure.security.audit import AppAuditLog
from infrastructure.security.credential_vault import (
    CredentialVault,
    generate_login_id,
    generate_password,
)
from knowledge.workspace.access import WorkspaceRole
from knowledge.workspace.server import STATIC_DIR as KNOWLEDGE_STATIC_DIR

__all__ = ("CosmosApplication", "serve_application")

SESSION_COOKIE = "cosmos_session"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
STATIC_ASSETS = {
    "cosmos-tokens.css",
    "cosmos-shell.css",
    "cosmos.css",
    "login.css",
    "login.js",
    "app.js",
    "rbac.js",
    "engineering-ux.js",
    "maharshi-popup.js",
    "maharshi.css",
    "maharshi.js",
    "physics-compressible.js",
    "propulsion-suite.js",
    "propulsion-suite.css",
}


class CosmosApplication:
    """Local desktop application state."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.auth = AuthService(self.root / "auth")
        self.profiles = ProfileService(self.auth)
        secret_path = self.auth.root / "session.secret"
        master_secret = secret_path.read_text(encoding="utf-8").strip() if secret_path.is_file() else "cosmos-bootstrap"
        self.credentials = CredentialVault(self.root / "credentials", master_secret=master_secret)
        self.audit = AppAuditLog(self.root / "audit" / "app_audit.sqlite")
        self.design_store = DesignStore(self.root / "propulsion_designs")
        self._knowledge_workspace = None
        self._workspace_lock = threading.RLock()

    def knowledge_workspace(self):
        if self._knowledge_workspace is None:
            from knowledge.workspace.session import KnowledgeWorkspace

            self._knowledge_workspace = KnowledgeWorkspace(
                self.root / "workspace_data",
                role=WorkspaceRole.ENGINEER,
                seed_corpus=False,
            )
        return self._knowledge_workspace

    def bind_session_to_workspace(self, session) -> None:
        workspace = self.knowledge_workspace()
        workspace.role = map_user_role_to_workspace(session.user.role)
        workspace.actor_id = session.user.login_id

    def audit_action(
        self,
        session,
        *,
        action: str,
        resource: str,
        detail: dict[str, object] | str = "",
        source_ip: str = "127.0.0.1",
        user_agent: str = "cosmos-desktop",
    ) -> None:
        if session is None:
            return
        self.audit.record(
            user_id=session.user.user_id,
            login_id=session.user.login_id,
            action=action,
            resource=resource,
            detail=detail,
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session.session_id,
        )


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    payload = json.loads(raw.decode("utf-8") or "{}")
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object.")
    return payload


def _session_from_handler(handler: BaseHTTPRequestHandler, app: CosmosApplication):
    jar = cookies.SimpleCookie(handler.headers.get("Cookie", ""))
    if SESSION_COOKIE not in jar:
        return None
    return app.auth.validate_token(jar[SESSION_COOKIE].value)


def _set_session_cookie(handler: BaseHTTPRequestHandler, token: str) -> None:
    jar = cookies.SimpleCookie()
    jar[SESSION_COOKIE] = token
    jar[SESSION_COOKIE]["path"] = "/"
    jar[SESSION_COOKIE]["httponly"] = True
    jar[SESSION_COOKIE]["samesite"] = "Lax"
    handler.send_header("Set-Cookie", jar.output(header="").strip())


def _clear_session_cookie(handler: BaseHTTPRequestHandler) -> None:
    jar = cookies.SimpleCookie()
    jar[SESSION_COOKIE] = ""
    jar[SESSION_COOKIE]["path"] = "/"
    jar[SESSION_COOKIE]["max-age"] = "0"
    handler.send_header("Set-Cookie", jar.output(header="").strip())


def _safe_asset_path(raw: str) -> Path | None:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate


class CosmosApplicationHandler(BaseHTTPRequestHandler):
    application: CosmosApplication

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _client_meta(self) -> tuple[str, str]:
        return self.client_address[0], self.headers.get("User-Agent", "cosmos-desktop")

    def _audit_request(self, session, path: str) -> None:
        if session is None:
            return
        source_ip, user_agent = self._client_meta()
        self.application.audit_action(
            session,
            action=f"HTTP_{self.command}",
            resource=path,
            source_ip=source_ip,
            user_agent=user_agent,
        )

    def _json(
        self,
        status: int,
        payload: dict[str, object],
        *,
        clear_session: bool = False,
        set_token: str | None = None,
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if set_token:
            _set_session_cookie(self, set_token)
        if clear_session:
            _clear_session_cookie(self)
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.is_file():
            self._json(404, {"error": "not_found"})
            return
        data = path.read_bytes()
        mime = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_asset(self, name: str) -> None:
        rel = _safe_asset_path(name)
        if rel is None:
            return self._json(404, {"error": "not_found"})
        if rel.name in STATIC_ASSETS:
            return self._send_file(STATIC_DIR / rel.name)
        if rel.parts and rel.parts[0] == "profiles":
            resolved = self.application.profiles.resolve_photo_path(rel.name)
            if resolved is not None:
                return self._send_file(resolved)
            return self._json(404, {"error": "not_found"})
        return self._send_file(ASSETS_DIR / rel)

    def _require_session(self):
        session = _session_from_handler(self, self.application)
        if session is None:
            self._json(401, {"error": "authentication_required"})
            return None
        return session

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        session = _session_from_handler(self, self.application)

        if path.startswith("/assets/"):
            return self._send_asset(path.removeprefix("/assets/"))
        if path in {"/", "/login", "/login.html"}:
            if session is not None:
                return self._redirect("/app/workbenches")
            return self._send_file(STATIC_DIR / "login.html", "text/html; charset=utf-8")
        if path.startswith("/knowledge"):
            return self._dispatch_knowledge_page(session)
        if path.startswith("/app/"):
            if session is None:
                return self._redirect("/")
            self._audit_request(session, path)
            return self._dispatch_app(path, session)
        if path.startswith("/api/"):
            return self._dispatch_api_get(path, session)
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        session = _session_from_handler(self, self.application)
        if path.startswith("/api/"):
            return self._dispatch_api_post(path, session)
        self._json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        session = _session_from_handler(self, self.application)
        if path.startswith("/api/"):
            return self._dispatch_api_delete(path, session)
        self._json(404, {"error": "not_found"})

    def _dispatch_app(self, path: str, session) -> None:
        if path == "/app/workbenches":
            return self._send_file(STATIC_DIR / "workbenches.html", "text/html; charset=utf-8")
        if path == "/app/audit":
            if not role_can_audit(session.user.role):
                return self._json(403, {"error": "forbidden"})
            return self._send_file(STATIC_DIR / "audit.html", "text/html; charset=utf-8")
        if path == "/app/admin":
            if not role_can_administer(session.user.role):
                return self._json(403, {"error": "forbidden"})
            return self._send_file(STATIC_DIR / "admin.html", "text/html; charset=utf-8")
        if path == "/app/physics/compressible":
            # Deep link retained; primary UX lives in Rocket Engine propulsion suite.
            return self._redirect("/app/workbench/rocket-engine?module=nozzle-flow")
        if path.startswith("/app/workbench/"):
            workbench_id = path.removeprefix("/app/workbench/").strip("/")
            if workbench_id == "knowledge":
                self.application.bind_session_to_workspace(session)
                return self._send_file(STATIC_DIR / "workbench" / "knowledge.html", "text/html; charset=utf-8")
            if workbench_id == "rocket-engine":
                return self._send_file(
                    STATIC_DIR / "workbench" / "rocket-engine.html",
                    "text/html; charset=utf-8",
                )
            item = workbench_by_id(workbench_id)
            if item is None:
                return self._json(404, {"error": "workbench_not_found"})
            html = (STATIC_DIR / "workbench" / "detail.html").read_text(encoding="utf-8")
            html = html.replace("__WORKBENCH_ID__", workbench_id)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"error": "not_found"})

    def _dispatch_knowledge_page(self, session) -> None:
        if session is None:
            return self._redirect("/")
        self._audit_request(session, self.path)
        self.application.bind_session_to_workspace(session)
        subpath = urlparse(self.path).path.removeprefix("/knowledge") or "/"
        if subpath in {"/", "/index.html"}:
            return self._send_file(KNOWLEDGE_STATIC_DIR / "index.html", "text/html; charset=utf-8")
        return self._json(404, {"error": "not_found"})

    def _dispatch_knowledge_api(self, session, path: str) -> None:
        if session is None:
            return self._json(401, {"error": "authentication_required"})
        self._audit_request(session, path)
        with self.application._workspace_lock:
            self.application.bind_session_to_workspace(session)
            dispatch_knowledge_request(
                self,
                self.application.knowledge_workspace(),
                subpath=path,
                method=self.command,
            )

    def _dispatch_api_get(self, path: str, session) -> None:
        if is_knowledge_api_path(path):
            return self._dispatch_knowledge_api(session, path)
        if path == "/api/auth/session":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            return self._json(200, {"user": self.application.profiles.profile_mapping(session.user)})
        if path == "/api/profile":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            return self._json(200, {"user": self.application.profiles.profile_mapping(session.user)})
        if path == "/api/workbenches":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            self._audit_request(session, path)
            pages = []
            for index, page in enumerate(WORKBENCH_PAGES, start=1):
                pages.append(
                    {
                        "page": index,
                        "items": [_workbench_payload(item) for item in page],
                    },
                )
            return self._json(200, {"pages": pages})
        if path == "/api/workbenches/rocket-engine/suite":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            self._audit_request(session, path)
            modules = [
                {
                    "module_id": item.module_id,
                    "title": item.title,
                    "group": item.group,
                    "description": item.description,
                    "status": item.status,
                    "physics_ops": list(item.physics_ops),
                    "reference_note": item.reference_note,
                }
                for item in PROPULSION_SUITE_MODULES
            ]
            return self._json(200, {"workbench_id": "rocket-engine", "modules": modules})
        if path.startswith("/api/propulsion/designs/"):
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            self._audit_request(session, path)
            remainder = path.removeprefix("/api/propulsion/designs/").strip("/")
            if remainder.endswith("/workflow"):
                design_id = remainder.removesuffix("/workflow").strip("/")
                try:
                    design = load_design(design_id, self.application.design_store)
                except Exception as exc:
                    status, payload = map_systems_error(exc)
                    return self._json(status, payload)
                return self._json(200, {"ok": True, "workflow": get_workflow_payload(design)})
            if remainder.endswith("/export"):
                design_id = remainder.removesuffix("/export").strip("/")
                try:
                    design = load_design(design_id, self.application.design_store)
                    package = export_design(design)
                except Exception as exc:
                    status, payload = map_systems_error(exc)
                    return self._json(status, payload)
                return self._json(200, {"ok": True, "package": package})
            if "/stages/" in remainder:
                design_id, _, stage_part = remainder.partition("/stages/")
                stage_id = stage_part.strip("/")
                allow_stale = False
                try:
                    from urllib.parse import parse_qs

                    query = parse_qs(urlparse(self.path).query)
                    allow_stale = str(query.get("allow_stale", ["0"])[0]) in {
                        "1",
                        "true",
                        "True",
                    }
                    design = load_design(design_id, self.application.design_store)
                    payload = get_stage_result_payload(
                        design, stage_id, allow_stale=allow_stale
                    )
                except Exception as exc:
                    status, err = map_systems_error(exc)
                    return self._json(status, err)
                return self._json(200, payload)
            design_id = remainder
            try:
                design = load_design(design_id, self.application.design_store)
            except Exception as exc:
                status, payload = map_systems_error(exc)
                return self._json(status, payload)
            return self._json(200, {"ok": True, "design": get_design_payload(design)})
        if path.startswith("/api/workbenches/"):
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            self._audit_request(session, path)
            workbench_id = path.removeprefix("/api/workbenches/").strip("/")
            item = workbench_by_id(workbench_id)
            if item is None:
                return self._json(404, {"error": "workbench_not_found"})
            return self._json(
                200,
                {
                    "workbench_id": item.workbench_id,
                    "title": item.title,
                    "route": item.route,
                    "status": item.status,
                    "description": item.description,
                    "modules": list(item.modules),
                },
            )
        if path == "/api/audit/events":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            if not role_can_audit(session.user.role):
                return self._json(403, {"error": "forbidden"})
            self._audit_request(session, path)
            events = [
                {
                    "timestamp": event.timestamp,
                    "login_id": event.login_id,
                    "action": event.action,
                    "resource": event.resource,
                    "detail": event.detail,
                }
                for event in self.application.audit.list_events()
            ]
            return self._json(200, {"events": events})
        if path == "/api/admin/users":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            if not role_can_administer(session.user.role):
                return self._json(403, {"error": "forbidden"})
            self._audit_request(session, path)
            users = [
                self.application.auth.user_to_mapping(user)
                for user in self.application.auth.list_users()
            ]
            return self._json(200, {"users": users})
        self._json(404, {"error": "not_found"})

    def _dispatch_api_delete(self, path: str, session) -> None:
        if is_knowledge_api_path(path):
            return self._dispatch_knowledge_api(session, path)
        self._json(404, {"error": "not_found"})

    def _dispatch_api_post(self, path: str, session) -> None:
        if is_knowledge_api_path(path):
            return self._dispatch_knowledge_api(session, path)
        if path in {
            "/api/physics/compressible/isentropic",
            "/api/physics/compressible/area-mach",
            "/api/physics/heat-transfer/bartz",
            "/api/physics/structures/thin-wall",
        }:
            current = self._require_session()
            if current is None:
                return
            try:
                payload = _read_json(self)
                if path.endswith("/isentropic"):
                    result = evaluate_isentropic_stagnation(
                        float(payload["mach"]),
                        float(payload["gamma"]),
                    )
                elif path.endswith("/area-mach"):
                    result = evaluate_area_mach(
                        mode=str(payload.get("mode") or "forward"),
                        gamma=float(payload["gamma"]),
                        mach=None if payload.get("mach") is None else float(payload["mach"]),
                        area_ratio_value=(
                            None
                            if payload.get("area_ratio") is None
                            else float(payload["area_ratio"])
                        ),
                        branch=str(payload.get("branch") or "supersonic"),
                    )
                elif path.endswith("/bartz"):
                    result = evaluate_bartz_htc(payload)
                else:
                    result = evaluate_thin_wall_stress(payload)
            except Exception as exc:
                status, error_payload = map_engineering_error(exc)
                # Unexpected non-engineering failures must not be converted into
                # plausible calculation responses.
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(
                current,
                action="PHYSICS_EVAL",
                resource=path,
                detail={"operation": result.get("operation")},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, result)
        if path == "/api/propulsion/designs":
            current = self._require_session()
            if current is None:
                return
            try:
                payload = _read_json(self)
                design = create_design(
                    name=str(payload.get("name") or "Untitled Propulsion Design"),
                    description=str(payload.get("description") or ""),
                    engineer=(
                        None
                        if payload.get("engineer") is None
                        else str(payload["engineer"])
                    ),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(
                current,
                action="PROPULSION_DESIGN_CREATE",
                resource=path,
                detail={"design_id": design.design_id},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, {"ok": True, "design": get_design_payload(design)})
        if path.startswith("/api/propulsion/designs/") and path.endswith("/requirements"):
            current = self._require_session()
            if current is None:
                return
            design_id = path.removeprefix("/api/propulsion/designs/").removesuffix(
                "/requirements"
            ).strip("/")
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                update_requirements(
                    design,
                    dict(payload.get("updates") or payload),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            return self._json(200, {"ok": True, "design": get_design_payload(design)})
        if path.startswith("/api/propulsion/designs/") and path.endswith(
            "/calculate/isentropic"
        ):
            current = self._require_session()
            if current is None:
                return
            design_id = (
                path.removeprefix("/api/propulsion/designs/")
                .removesuffix("/calculate/isentropic")
                .strip("/")
            )
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                result = run_isentropic(
                    design,
                    mach=float(payload["mach"]),
                    gamma=None if payload.get("gamma") is None else float(payload["gamma"]),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(
                current,
                action="PROPULSION_ISENTROPIC",
                resource=path,
                detail={"design_id": design_id, "status": result.status.value},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(
                200,
                {
                    "ok": True,
                    "result": result.to_canonical_dict(),
                    "workflow": get_workflow_payload(design),
                },
            )
        if path.startswith("/api/propulsion/designs/") and path.endswith("/run/phase3"):
            current = self._require_session()
            if current is None:
                return
            design_id = (
                path.removeprefix("/api/propulsion/designs/")
                .removesuffix("/run/phase3")
                .strip("/")
            )
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                summary = run_phase3(
                    design,
                    chamber_temperature_k=(
                        None
                        if payload.get("chamber_temperature_k") is None
                        else float(payload["chamber_temperature_k"])
                    ),
                    gamma=None if payload.get("gamma") is None else float(payload["gamma"]),
                    molecular_weight_kg_per_mol=(
                        None
                        if payload.get("molecular_weight_kg_per_mol") is None
                        else float(payload["molecular_weight_kg_per_mol"])
                    ),
                    throat_area_m2=(
                        None
                        if payload.get("throat_area_m2") is None
                        else float(payload["throat_area_m2"])
                    ),
                    expansion_ratio=(
                        None
                        if payload.get("expansion_ratio") is None
                        else float(payload["expansion_ratio"])
                    ),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(
                current,
                action="PROPULSION_PHASE3",
                resource=path,
                detail={"design_id": design_id, "ok": summary.get("ok")},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, summary)
        if path.startswith("/api/propulsion/designs/") and path.endswith("/run/phase4"):
            current = self._require_session()
            if current is None:
                return
            design_id = (
                path.removeprefix("/api/propulsion/designs/")
                .removesuffix("/run/phase4")
                .strip("/")
            )
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                summary = run_phase4(
                    design,
                    characteristic_length_m=(
                        None
                        if payload.get("characteristic_length_m") is None
                        else float(payload["characteristic_length_m"])
                    ),
                    contraction_ratio=(
                        None
                        if payload.get("contraction_ratio") is None
                        else float(payload["contraction_ratio"])
                    ),
                    wall_thickness_m=(
                        None
                        if payload.get("wall_thickness_m") is None
                        else float(payload["wall_thickness_m"])
                    ),
                    material_id=str(payload.get("material_id") or "stainless_304"),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(
                current,
                action="PROPULSION_PHASE4",
                resource=path,
                detail={"design_id": design_id, "ok": summary.get("ok")},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, summary)
        if path.startswith("/api/propulsion/designs/") and path.endswith("/run/phase6"):
            current = self._require_session()
            if current is None:
                return
            design_id = (
                path.removeprefix("/api/propulsion/designs/")
                .removesuffix("/run/phase6")
                .strip("/")
            )
            try:
                design = load_design(design_id, self.application.design_store)
                summary = run_phase6(design, store=self.application.design_store)
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(
                current,
                action="PROPULSION_PHASE6",
                resource=path,
                detail={"design_id": design_id, "ok": summary.get("ok")},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, summary)
        if path == "/api/auth/login":
            payload: dict[str, object] = {}
            try:
                payload = _read_json(self)
                record = self.application.auth.login(
                    str(payload.get("login_id") or ""),
                    str(payload.get("password") or ""),
                    client_info=self.headers.get("User-Agent", "cosmos-desktop"),
                )
                login_profile = assert_login_profile(
                    record.user.role,
                    str(payload.get("login_profile") or "ENGINEER"),
                )
            except (AuthenticationError, ValueError) as exc:
                self.application.audit.record(
                    user_id="anonymous",
                    login_id=str(payload.get("login_id") or "unknown"),
                    action="LOGIN_FAILED",
                    resource="/api/auth/login",
                    detail={"reason": str(exc), "profile": payload.get("login_profile")},
                    source_ip=self.client_address[0],
                    user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
                )
                return self._json(401, {"error": str(exc)})
            self.application.audit_action(
                record,
                action="LOGIN",
                resource="/api/auth/login",
                detail={"role": record.user.role.value, "login_profile": login_profile},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(
                200,
                {
                    "user": self.application.profiles.profile_mapping(record.user),
                    "login_profile": login_profile,
                    "infrastructure": infrastructure_for_profile(login_profile),
                    "redirect": redirect_for_profile(login_profile),
                },
                set_token=record.token,
            )

        if path == "/api/profile":
            current = self._require_session()
            if current is None:
                return
            try:
                payload = _read_json(self)
                if path.endswith("/photo"):
                    return
                updated = self.application.profiles.update_profile(
                    current.user.user_id,
                    display_name=str(payload["display_name"]) if "display_name" in payload else None,
                    designation=str(payload["designation"]) if "designation" in payload else None,
                    team=str(payload["team"]) if "team" in payload else None,
                    bio=str(payload["bio"]) if "bio" in payload else None,
                )
            except (AuthenticationError, ValueError) as exc:
                return self._json(400, {"error": str(exc)})
            self.application.audit_action(
                current,
                action="PROFILE_UPDATE",
                resource="/api/profile",
                detail={"login_id": updated.login_id},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, {"user": self.application.profiles.profile_mapping(updated)})

        if path == "/api/profile/photo":
            current = self._require_session()
            if current is None:
                return
            try:
                filename, content, _fields = _read_multipart_upload(self)
                del filename
                photo_url = self.application.profiles.save_photo(current.user.user_id, content)
            except (AuthenticationError, ValueError) as exc:
                return self._json(400, {"error": str(exc)})
            self.application.audit_action(
                current,
                action="PROFILE_PHOTO_UPDATE",
                resource="/api/profile/photo",
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(200, {"profile_photo_url": photo_url})

        if path == "/api/auth/logout":
            if session is not None:
                self.application.audit_action(
                    session,
                    action="LOGOUT",
                    resource="/api/auth/logout",
                    source_ip=self.client_address[0],
                    user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
                )
                jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
                if SESSION_COOKIE in jar:
                    self.application.auth.logout(jar[SESSION_COOKIE].value)
            return self._json(200, {"ok": True}, clear_session=True)

        if path == "/api/admin/users":
            current = self._require_session()
            if current is None:
                return
            if not role_can_administer(current.user.role):
                return self._json(403, {"error": "forbidden"})
            try:
                payload = _read_json(self)
                display_name = str(payload.get("display_name") or "Employee")
                employee_id = str(payload.get("employee_id") or f"EMP-{secrets.token_hex(3).upper()}")
                auto_generate = payload.get("auto_generate", True) is not False
                if auto_generate:
                    login_id = generate_login_id(display_name=display_name, employee_id=employee_id)
                    password = generate_password()
                else:
                    login_id = str(payload["login_id"])
                    password = str(payload["password"])
                user = self.application.auth.register_user(
                    login_id=login_id,
                    password=password,
                    display_name=display_name,
                    designation=str(payload.get("designation") or "Engineer"),
                    employee_id=employee_id,
                    team=str(payload.get("team") or "Engineering"),
                    role=UserRole(str(payload.get("role") or UserRole.ENGINEER.value)),
                )
                self.application.credentials.store_issued(
                    user_id=user.user_id,
                    login_id=user.login_id,
                    password=password,
                    issued_by=current.user.login_id,
                    employee_id=user.employee_id,
                    display_name=user.display_name,
                )
            except (AuthenticationError, KeyError, ValueError) as exc:
                return self._json(400, {"error": str(exc)})
            self.application.audit_action(
                current,
                action="USER_REGISTER",
                resource="/api/admin/users",
                detail={"created_login_id": user.login_id, "role": user.role.value, "vault_stored": True},
                source_ip=self.client_address[0],
                user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
            )
            return self._json(
                201,
                {
                    "user": self.application.auth.user_to_mapping(user),
                    "credentials_secured": True,
                    "one_time_credentials": {
                        "login_id": user.login_id,
                        "password": password,
                    },
                    "message": "User registered. Copy the credentials below now — they will not be shown again.",
                },
            )

        if session is None:
            return self._json(401, {"error": "authentication_required"})
        self._json(404, {"error": "not_found"})


def _read_multipart_upload(handler: BaseHTTPRequestHandler) -> tuple[str, bytes, dict[str, str]]:
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length)
    if "multipart/form-data" not in content_type:
        raise ValueError("upload requires multipart/form-data")
    boundary = ""
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("boundary="):
            boundary = part.split("=", 1)[1].strip().strip('"')
    if not boundary:
        raise ValueError("multipart boundary missing")
    marker = b"--" + boundary.encode("utf-8")
    fields: dict[str, str] = {}
    filename = "upload.bin"
    content = b""
    for chunk in body.split(marker):
        chunk = chunk.lstrip(b"\r\n")
        if not chunk or chunk in {b"--", b"--\r\n"}:
            continue
        header_blob, _, data = chunk.partition(b"\r\n\r\n")
        data = data.rstrip(b"\r\n")
        headers = header_blob.decode("utf-8", errors="replace")
        name = ""
        part_filename = ""
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                for token in line.split(";"):
                    token = token.strip()
                    if token.startswith("name="):
                        name = token.split("=", 1)[1].strip().strip('"')
                    if token.startswith("filename="):
                        part_filename = token.split("=", 1)[1].strip().strip('"')
        if part_filename:
            filename = part_filename
            content = data
        elif name:
            fields[name] = data.decode("utf-8")
    if not content:
        raise ValueError("file field missing")
    return filename, content, fields


def serve_application(root: Path | str, *, host: str = "127.0.0.1", port: int = 8780) -> None:
    application = CosmosApplication(root)

    class BoundHandler(CosmosApplicationHandler):
        pass

    BoundHandler.application = application
    try:
        server = ThreadingHTTPServer((host, port), BoundHandler)
    except OSError as exc:
        raise SystemExit(
            f"Could not bind http://{host}:{port}: {exc}\n"
            "Try another port, e.g. --port 8781.",
        ) from exc

    print(
        f"COSMOS 0.1 desktop shell listening on http://{host}:{port}\n"
        f"  data root={Path(root).resolve()}\n"
        "  Default admin: cosmos-admin / COSMOS-Dev-2026!\n"
        "  Press Ctrl+C to stop.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
        server.server_close()
