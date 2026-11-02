"""COSMOS desktop application HTTP shell — login, workbenches, audit, knowledge."""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import threading
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from api.authentication import AuthenticationError, AuthService, UserRole
from api.authorization import (
    assert_login_profile,
    infrastructure_for_profile,
    map_user_role_to_workspace,
    redirect_for_profile,
    role_can_administer,
    role_can_audit,
    role_can_modify_design,
)
from api.catalogs import (
    list_material_catalog,
    list_propellant_catalog,
    list_workflow_catalog,
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
    clone_design,
    create_design,
    export_design,
    get_design_payload,
    get_stage_result_payload,
    get_workflow_payload,
    list_designs,
    load_design,
    map_systems_error,
    run_design_workflow,
    run_isentropic,
    run_phase3,
    run_phase4,
    run_phase6,
    run_subsystems,
    save_design,
    update_cycle,
    update_propellants,
    update_requirements,
)
from core.logger import get_logger
from gui.app_shell import (
    DESIGN_SYSTEM_ASSETS,
    ROCKET_WORKBENCH_ASSETS,
    SHELL_ASSETS,
    inject_shell,
    shell_flag,
    use_shell,
)
from gui.knowledge_proxy import dispatch_knowledge_request, is_knowledge_api_path
from gui.ngg import ASSETS as NGG_ASSETS
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

logger = get_logger(__name__)

__all__ = ("CosmosApplication", "serve_application")

SESSION_COOKIE = "cosmos_session"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
STATIC_ASSETS = {
    "guided-engine.js",
    "guided-engine.css",
    "cosmos-tokens.css",
    "cosmos-shell.css",
    "cosmos-background.css",
    "cosmos.css",
    "login.css",
    "login.js",
    "app.js",
    "cosmos-api.js",
    "rbac.js",
    "engineering-ux.js",
    "maharshi-popup.js",
    "maharshi.css",
    "maharshi.js",
    "physics-compressible.js",
    "propulsion-suite.js",
    "propulsion-suite.css",
    "projects.js",
    "managed-evidence.js",
    "managed-sensitivity.js",
    "managed-pressure-fed.js",
    "managed-pressure-fed.css",
    "managed-cycle.js",
    "managed-cycle.css",
    "managed-propulsion-validation.js",
    "managed-engine-operating.js",
    "managed-engine-extensions.js",
    "managed-engine-extensions.css",
    "managed-engine-builds.js",
    "component-geometry.js",
    "engine-redesign.js",
    "visual-concept.js",
    "visual-concept-data.js",
    "pico-components.js",
    "geometry-qualification.js",
    "component-geometry.css",
}


class CosmosApplication:
    """Local desktop application state."""

    def __init__(self, root: Path | str, *, new_shell: bool | None = None, ngg_enabled: bool | None = None, ngg_runtime: Path | None = None, simulation_enabled: bool | None = None, comparison_enabled: bool | None = None, knowledge_reports_enabled: bool | None = None, durable_projects: bool | None = None) -> None:
        self.shell_flag = shell_flag(os.environ.get("COSMOS_NEW_SHELL") if new_shell is None else str(new_shell))
        if self.shell_flag.diagnostic:
            logger.warning("%s: COSMOS_NEW_SHELL is invalid; legacy shell remains active", self.shell_flag.diagnostic)
        self.root = Path(root)
        from infrastructure.release.security import (
            preview_enabled,
            private_auth_files,
            private_bootstrap,
        )
        self.release_preview = preview_enabled(os.environ.get("COSMOS_RELEASE_PROFILE"))
        bootstrap_password = private_bootstrap(self.root) if self.release_preview else None
        self.root.mkdir(parents=True, exist_ok=True)
        self.auth = AuthService(self.root / "auth", bootstrap_password=bootstrap_password)
        if self.release_preview:
            private_auth_files(self.auth.root)
        self.profiles = ProfileService(self.auth)
        secret_path = self.auth.root / "session.secret"
        master_secret = secret_path.read_text(encoding="utf-8").strip() if secret_path.is_file() else "cosmos-bootstrap"
        self.credentials = CredentialVault(self.root / "credentials", master_secret=master_secret)
        self.audit = AppAuditLog(self.root / "audit" / "app_audit.sqlite")
        self.design_store = DesignStore(self.root / "propulsion_designs")
        self._knowledge_workspace = None
        self._workspace_lock = threading.RLock()
        from gui.ngg import enabled
        self.ngg_enabled = enabled(os.environ.get("COSMOS_NGG") if ngg_enabled is None else str(ngg_enabled), self.shell_flag.enabled)
        self.ngg_runtime = ngg_runtime or (Path(os.environ["COSMOS_NGG_RUNTIME_CONFIG"]) if os.environ.get("COSMOS_NGG_RUNTIME_CONFIG") else None)
        try:
            self.component_only_runtime = self.ngg_runtime is not None and json.loads(self.ngg_runtime.read_bytes()).get("schema") == "cosmos.occt-component-runtime.v1"
        except (OSError, ValueError):
            self.component_only_runtime = False
        self._ngg_workspace = None
        self._nozzle_workspace = None
        self._component_workspace = None
        self._pico_component_workspace = None
        from gui.simulation_ui import enabled as simulation_flag
        self.simulation_enabled = simulation_flag(os.environ.get("COSMOS_NEW_SIM_UI") if simulation_enabled is None else str(simulation_enabled), self.shell_flag.enabled)
        self._simulation_workspace = None
        from gui.comparison_ui import enabled as comparison_flag
        self.comparison_enabled = comparison_flag(os.environ.get("COSMOS_NEW_VV_UI") if comparison_enabled is None else str(comparison_enabled), self.shell_flag.enabled)
        self._comparison_workspace = None
        from gui.knowledge_reports_ui import enabled as knowledge_reports_flag
        self.knowledge_reports_enabled = knowledge_reports_flag(os.environ.get("COSMOS_NEW_KNOWLEDGE_REPORTS_UI") if knowledge_reports_enabled is None else str(knowledge_reports_enabled), self.shell_flag.enabled)
        self._reports_workspace = None
        self.durable_projects_flag = shell_flag(os.environ.get("COSMOS_DURABLE_PROJECTS") if durable_projects is None else str(durable_projects))
        self._project_authority = None
        self.project_api = None
        from infrastructure.persistence.application_authority import (
            ApplicationAuthority,
            authority_required,
        )
        if self.durable_projects_flag.enabled or authority_required(self.root):
            from api.project_authority import ProjectAPI
            from infrastructure.persistence.portability import ProjectPortability
            from infrastructure.persistence.study_runtime import materialize_fixture
            self._project_authority = ApplicationAuthority(self.root, enabled=self.durable_projects_flag.enabled)
            self.design_store.access_guard = self._project_authority.legacy_guard
            self.project_api = ProjectAPI(self._project_authority.repository, self.auth,
                jobs=self._project_authority.jobs if self._project_authority.repository.schema_version >= 3 else None,
                geometry_services=lambda: self.ngg_workspace().services, study_materializer=materialize_fixture,
                nozzle_workspace=self.nozzle_workspace,
                component_workspace=self.component_workspace,
                pico_component_workspace=self.pico_component_workspace,
                knowledge_workspace=lambda user: self.knowledge_workspace().as_principal(map_user_role_to_workspace(user.role), user.login_id),
                portability=ProjectPortability(self._project_authority.repository) if self._project_authority.repository.schema_version >= 6 else None)

    def close(self) -> None:
        """Release workers and the application-lifetime authority lease once."""
        for name in ("project_api", "_comparison_workspace", "_simulation_workspace", "_ngg_workspace", "_nozzle_workspace", "_component_workspace", "_pico_component_workspace", "_project_authority"):
            resource = getattr(self, name, None)
            if resource is not None:
                resource.close()
                setattr(self, name, None)

    def reports_workspace(self):
        from api.knowledge_reports import create_workspace
        with self._workspace_lock:
            if self._reports_workspace is None:
                self._reports_workspace = create_workspace()
            return self._reports_workspace

    def comparison_workspace(self):
        from api.comparison_workbench import create_workspace
        with self._workspace_lock:
            if self._comparison_workspace is None:
                self._comparison_workspace = create_workspace(self.root)
            return self._comparison_workspace

    def simulation_workspace(self):
        from api.simulation_workbench import create_workspace
        with self._workspace_lock:
            if self._simulation_workspace is None:
                self._simulation_workspace = create_workspace()
            return self._simulation_workspace

    def ngg_workspace(self):
        from api.ngg_workbench import create_workspace
        with self._workspace_lock:
            if self._ngg_workspace is None:
                self._ngg_workspace = create_workspace(self.root, self.ngg_runtime if self.ngg_enabled else None)
            return self._ngg_workspace

    def nozzle_workspace(self):
        from api.nozzle_geometry import create_workspace
        with self._workspace_lock:
            if self._nozzle_workspace is None:
                self._nozzle_workspace = create_workspace(self.root, self.ngg_runtime, enabled=self.ngg_enabled)
            return self._nozzle_workspace

    def component_workspace(self):
        from api.component_geometry import create_workspace
        with self._workspace_lock:
            if self._component_workspace is None:
                self._component_workspace=create_workspace(self.root,self.ngg_runtime,enabled=self.ngg_enabled)
            return self._component_workspace

    def pico_component_workspace(self):
        from api.pico_component_runtime import create_workspace
        with self._workspace_lock:
            if self._pico_component_workspace is None:
                value=os.environ.get("COSMOS_PICOGK_COMPONENT_CONFIG")
                self._pico_component_workspace=create_workspace(self.root,Path(value) if value else None,enabled=self.ngg_enabled)
            return self._pico_component_workspace

    def knowledge_workspace(self):
        with self._workspace_lock:
            if self._knowledge_workspace is None:
                from knowledge.workspace.session import KnowledgeWorkspace

                self._knowledge_workspace = KnowledgeWorkspace(
                    self.root / "workspace_data",
                    role=WorkspaceRole.VIEWER,
                    seed_corpus=False,
                )
            return self._knowledge_workspace

    def bind_session_to_workspace(self, session):
        """Return a scoped principal; never change the shared workspace identity."""
        workspace = self.knowledge_workspace()
        return workspace.as_principal(map_user_role_to_workspace(session.user.role), session.user.login_id)

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
    from infrastructure.release.security import MAX_BODY, strict_json
    lengths = handler.headers.get_all("Content-Length", [])
    if len(lengths) > 1 or handler.headers.get_all("Transfer-Encoding", []):
        raise ValueError("Ambiguous JSON framing")
    value = lengths[0] if lengths else "0"
    if len(value) > 8 or not value.isascii() or not value.isdecimal() or int(value) > MAX_BODY:
        raise ValueError("JSON exceeds the bounded request policy")
    length = int(value)
    raw = handler.rfile.read(length) if length else b"{}"
    if length and len(raw) != length:
        raise ValueError("Incomplete JSON body")
    return strict_json(raw)


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
        if urlparse(self.path).path == "/api/projects" or urlparse(self.path).path.startswith("/api/projects/"):
            self.send_header("Cache-Control", "no-store")
            self.send_header("Vary", "Cookie")
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
        if self.application.release_preview and "text/html" in mime:
            data = data.replace(b"Local development administrator:", b"Private local-preview administrator:")
            data = data.replace(b"COSMOS-Dev-2026!", b"[unique password in first-login.json]")
        if "text/html" in mime and urlparse(self.path).path.startswith("/app/"):
            if self.application.component_only_runtime:
                notice=b'Reference fixture laboratory disabled for this component profile. Separate PicoGK component availability is shown in the component editor.' if os.environ.get("COSMOS_PICOGK_COMPONENT_CONFIG") else b'Reference fixture laboratory / PicoGK disabled by the separately qualified OCCT-only component profile.'
                data = data.replace(b'<details class="ngg-fixture-lab">', b'<p>'+notice+b'</p><details class="ngg-fixture-lab" hidden inert>')
                data = data.replace(b'<script src="/assets/ngg/view.js"></script>', b'')
            data = inject_shell(data, enabled=use_shell(self.application.shell_flag, self.path))
            if self.application.project_api is not None:
                tag = b'<link rel="stylesheet" href="/assets/managed-pressure-fed.css"><link rel="stylesheet" href="/assets/managed-cycle.css"><script src="/assets/projects.js"></script><script src="/assets/managed-evidence.js"></script><script src="/assets/managed-sensitivity.js"></script><script src="/assets/managed-pressure-fed.js"></script><script src="/assets/managed-cycle.js"></script><script src="/assets/managed-propulsion-validation.js"></script>'
                tag += b'<script src="/assets/managed-engine-operating.js"></script>'
                tag += b'<script src="/assets/managed-engine-extensions.js"></script>'
                tag += b'<script src="/assets/ngg/model.js"></script><script src="/assets/ngg/viewport.js"></script>'
                tag += b'<script src="/assets/managed-engine-builds.js"></script>'
                tag += b'<script src="/assets/pico-components.js"></script><script src="/assets/geometry-qualification.js"></script><script src="/assets/component-geometry.js"></script><script src="/assets/engine-redesign.js"></script><link rel="stylesheet" href="/assets/component-geometry.css">'
                if urlparse(self.path).path == "/app/workbench/native-geometry":
                    tag += b'<script src="/assets/visual-concept-data.js"></script><script src="/assets/visual-concept.js"></script>'
                tag += b'<link rel="stylesheet" href="/assets/managed-engine-extensions.css">'
                anchor = b'<script src="/assets/cosmos-api.js"></script>'
                data = data.replace(anchor, anchor+tag, 1) if anchor in data else data.replace(b'</head>', tag+b'</head>', 1)
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_asset(self, name: str) -> None:
        from api.visualization_workbench import ASSETS as VISUALIZATION_ASSETS
        from api.visualization_workbench import VENDOR_ASSETS
        from gui.comparison_ui import ASSETS as COMPARISON_ASSETS
        from gui.knowledge_reports_ui import ASSETS as KNOWLEDGE_REPORTS_ASSETS
        from gui.simulation_ui import ASSETS as SIMULATION_ASSETS
        rel = _safe_asset_path(name)
        if rel is None:
            return self._json(404, {"error": "not_found"})
        if rel.name in STATIC_ASSETS:
            return self._send_file(STATIC_DIR / rel.name)
        if len(rel.parts) == 3 and rel.parts[0] == "vendor" and "/".join(rel.parts[1:]) in VENDOR_ASSETS:
            return self._send_file(STATIC_DIR / rel)
        if len(rel.parts) == 2 and (
            rel.parts[0] == "app-shell" and rel.name in SHELL_ASSETS
            or rel.parts[0] == "rocket-workbench" and rel.name in ROCKET_WORKBENCH_ASSETS
            or rel.parts[0] == "design-system" and rel.name in DESIGN_SYSTEM_ASSETS
            or rel.parts[0] == "ngg" and rel.name in NGG_ASSETS
            or rel.parts[0] == "simulation" and rel.name in SIMULATION_ASSETS
            or rel.parts[0] == "comparison" and rel.name in COMPARISON_ASSETS
            or rel.parts[0] == "knowledge-reports" and rel.name in KNOWLEDGE_REPORTS_ASSETS
            or rel.parts[0] == "visualization" and rel.name in VISUALIZATION_ASSETS
        ):
            return self._send_file(STATIC_DIR / rel)
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

    def _release_guard(self, method: str) -> bool:
        if not self.application.release_preview:
            return True
        from infrastructure.release.security import ReleaseProfileError, guard
        try:
            guard(self, method)
            return True
        except ReleaseProfileError as error:
            self.close_connection = True
            self._json(400, {"error": {"code": error.code, "message": str(error),
                                     "action": "Use the isolated local preview, exact loopback origin and bounded JSON request."}})
            return False

    def setup(self) -> None:
        if self.application.release_preview:
            self.request.settimeout(10)
        super().setup()

    def end_headers(self) -> None:
        if self.application.release_preview:
            from infrastructure.release.security import add_preview_headers
            add_preview_headers(self)
        super().end_headers()

    def do_GET(self) -> None:
        if not self._release_guard("GET"):
            return
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

    def do_POST(self) -> None:
        if not self._release_guard("POST"):
            return
        parsed = urlparse(self.path)
        path = parsed.path
        session = _session_from_handler(self, self.application)
        if path.startswith("/api/"):
            return self._dispatch_api_post(path, session)
        self._json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:
        if not self._release_guard("DELETE"):
            return
        parsed = urlparse(self.path)
        path = parsed.path
        session = _session_from_handler(self, self.application)
        if path.startswith("/api/"):
            return self._dispatch_api_delete(path, session)
        self._json(404, {"error": "not_found"})

    def _dispatch_app(self, path: str, session) -> None:
        if path == "/app/projects":
            if not use_shell(self.application.shell_flag, self.path):
                return self._redirect("/app/workbenches")
            return self._send_file(STATIC_DIR / "app-shell" / "dashboard.html", "text/html; charset=utf-8")
        if path in {"/app/help", "/app/help.html"}:
            return self._send_file(STATIC_DIR / "help.html", "text/html; charset=utf-8")
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
            return self._redirect("/app/workbench/rocket-engine?stage=nozzle&from=physics")
        if path.startswith("/app/workbench/"):
            workbench_id = path.removeprefix("/app/workbench/").strip("/")
            if self.application.knowledge_reports_enabled and (workbench_id == "reports" or workbench_id == "knowledge" and "knowledge=legacy" not in urlparse(self.path).query.split("&")):
                return self._send_file(STATIC_DIR / "workbench" / "knowledge-reports.html", "text/html; charset=utf-8")
            if workbench_id == "comparison" and self.application.comparison_enabled:
                return self._send_file(STATIC_DIR / "workbench" / "comparison.html", "text/html; charset=utf-8")
            if workbench_id == "native-geometry" and self.application.ngg_enabled:
                return self._send_file(STATIC_DIR / "workbench" / "native-geometry.html", "text/html; charset=utf-8")
            if workbench_id == "simulation" and self.application.simulation_enabled:
                return self._send_file(STATIC_DIR / "workbench" / "simulation.html", "text/html; charset=utf-8")
            if workbench_id == "knowledge":
                return self._send_file(STATIC_DIR / "workbench" / "knowledge.html", "text/html; charset=utf-8")
            if workbench_id == "visualization":
                return self._send_file(STATIC_DIR / "workbench" / "visualization.html", "text/html; charset=utf-8")
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
            body = inject_shell(html.encode("utf-8"), enabled=use_shell(self.application.shell_flag, self.path))
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
        subpath = urlparse(self.path).path.removeprefix("/knowledge") or "/"
        if subpath in {"/", "/index.html"}:
            return self._send_file(KNOWLEDGE_STATIC_DIR / "index.html", "text/html; charset=utf-8")
        return self._json(404, {"error": "not_found"})

    def _dispatch_knowledge_api(self, session, path: str) -> None:
        if session is None:
            return self._json(401, {"error": "authentication_required"})
        self._audit_request(session, path)
        with self.application._workspace_lock, self.application.bind_session_to_workspace(session):
            dispatch_knowledge_request(
                self,
                self.application.knowledge_workspace(),
                subpath=path,
                method=self.command,
            )

    def _dispatch_api_get(self, path: str, session) -> None:
        if path == "/api/projects" or path.startswith("/api/projects/"):
            return self._dispatch_project(path, session, mutation=False)
        if not self._legacy_project_guard(path, session):
            return
        if path.startswith("/api/knowledge-reports/"):
            from gui.knowledge_reports_ui import dispatch
            return dispatch(self, path, session, mutation=False)
        if path.startswith("/api/comparison/"):
            from gui.comparison_ui import dispatch
            return dispatch(self, path, session, mutation=False)
        if path.startswith("/api/simulation/"):
            from gui.simulation_ui import dispatch
            return dispatch(self, path, session, mutation=False)
        if path.startswith("/api/ngg/"):
            from gui.ngg import dispatch
            return dispatch(self, path, session, mutation=False)
        if path == "/api/ui/shell":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            return self._json(200, {"schemaVersion": 1, "enabled": self.application.shell_flag.enabled,
                "diagnostic": self.application.shell_flag.diagnostic, "historicalSnapshots": False,
                "projectContext": "UI preference, not authoritative Project storage",
                "jobDomain": "knowledge-ingestion", "scientificBackendActivated": False,
                "durableProjects": {"available": self.application.project_api is not None,
                    "enabled": self.application.durable_projects_flag.enabled,
                    "readOnly": not self.application.durable_projects_flag.enabled,
                    "geometrySnapshots": self.application.project_api is not None and self.application.project_api.geometry is not None,
                    "geometryStages": self.application._project_authority is not None and self.application._project_authority.jobs.supports_stages,
                    "managedStudies": self.application.project_api is not None and self.application.project_api.studies is not None,
                    "managedEvidence": self.application.project_api is not None and self.application.project_api.evidence is not None,
                    "managedSensitivity": self.application.project_api is not None and self.application.project_api.sensitivity is not None,
                    "managedPressureFed": self.application.project_api is not None and self.application.project_api.pressure_fed is not None,
                    "managedCycleAssessments": self.application.project_api is not None and self.application.project_api.cycle_assessments is not None,
                    "managedEngineOperating": self.application.project_api is not None and self.application.project_api.engine_operating is not None,
                    "managedEngineExtensions": self.application.project_api is not None and self.application.project_api.engine_geometry is not None,
                    "managedEngineBuilds": self.application.project_api is not None and self.application.project_api.engine_builds is not None,
                    "managedComponents": self.application.project_api is not None and self.application.project_api.components is not None,
                    "propulsionValidation": self.application.project_api is not None and self.application.project_api.propulsion_validation is not None,
                    "managedPackages": self.application.project_api is not None and self.application.project_api.portability is not None,
                    "nativeGeometryRequested": self.application.ngg_enabled and self.application.ngg_runtime is not None,
                    "diagnostic": self.application.durable_projects_flag.diagnostic}})
        if path.startswith("/api/visualization/"):
            from api.visualization_workbench import dispatch
            return dispatch(self, path, session)
        if is_knowledge_api_path(path):
            return self._dispatch_knowledge_api(session, path)
        if path == "/api/auth/session":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            return self._json(200, {"user": self.application.profiles.profile_mapping(session.user),
                "transport_limits": {"document_bytes": (15 if self.application.release_preview else 100) * 1024**2,
                                     "profile_photo_bytes": 2 * 1024**2,
                                     "request_bytes": (16 if self.application.release_preview else 101) * 1024**2}})
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
            if self.application.ngg_enabled:
                from gui.ngg import CATALOG_ITEM
                pages[0]["items"].append(dict(CATALOG_ITEM))
            if self.application.comparison_enabled:
                from gui.comparison_ui import CATALOG_ITEM as COMPARISON_ITEM
                pages[0]["items"].append(dict(COMPARISON_ITEM))
            if self.application.knowledge_reports_enabled:
                from gui.knowledge_reports_ui import CATALOG_ITEM as REPORTS_ITEM
                pages[0]["items"].append(dict(REPORTS_ITEM))
            if self.application.simulation_enabled:
                from gui.simulation_ui import catalog_item
                for page in pages:
                    page["items"] = [catalog_item(item) if item["workbench_id"] == "simulation" else item for item in page["items"]]
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
        if path == "/api/catalogs/propellants":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            try:
                return self._json(200, list_propellant_catalog())
            except Exception as exc:
                logger.exception("server: boundary operation failed")
                status, payload = map_systems_error(exc)
                return self._json(status, payload)
        if path == "/api/catalogs/materials":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            return self._json(200, list_material_catalog())
        if path == "/api/propulsion/workflow-catalog":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            return self._json(200, list_workflow_catalog())
        if path == "/api/propulsion/designs":
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            self._audit_request(session, path)
            return self._json(200, {"ok": True, "designs": list_designs(self.application.design_store)})
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
                    logger.exception("server: boundary operation failed")
                    status, payload = map_systems_error(exc)
                    return self._json(status, payload)
                return self._json(200, {"ok": True, "workflow": get_workflow_payload(design)})
            if remainder.endswith("/export"):
                design_id = remainder.removesuffix("/export").strip("/")
                try:
                    design = load_design(design_id, self.application.design_store)
                    package = export_design(design)
                except Exception as exc:
                    logger.exception("server: boundary operation failed")
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
                    logger.exception("server: boundary operation failed")
                    status, err = map_systems_error(exc)
                    return self._json(status, err)
                return self._json(200, payload)
            design_id = remainder
            try:
                design = load_design(design_id, self.application.design_store)
            except Exception as exc:
                logger.exception("server: boundary operation failed")
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

    def _legacy_project_guard(self, path: str, session) -> bool:
        if not (path == "/api/propulsion/designs" or path.startswith("/api/propulsion/designs/")):
            return True
        if session is None:
            self._json(401, {"error": "authentication_required"})
            return False
        from api.project_authority import project_error
        try:
            suffix = path.removeprefix("/api/propulsion/designs").strip("/")
            self.application.design_store.check_access(suffix.split("/")[0] if suffix else None)
            return True
        except Exception as error:
            translated = project_error(error)
            if translated is None:
                raise
            status, payload = translated
            self._json(status, payload)
            return False

    def _dispatch_project(self, path: str, session, *, mutation: bool) -> None:
        if session is None:
            return self._json(401, {"error": "authentication_required"})
        if self.application.project_api is None:
            return self._json(404, {"ok": False, "error": {"code": "PROJECT_AUTHORITY_DISABLED", "message": "Durable projects are not enabled; no migration occurred."}})
        if mutation and not self.application.durable_projects_flag.enabled:
            return self._json(403, {"ok": False, "error": {"code": "PROJECT_AUTHORITY_READ_ONLY", "message": "Managed authority is read-only while its feature flag is off."}})
        host = self.headers.get("Host", "")
        port = self.server.server_port
        if host not in {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}:
            return self._json(403, {"ok": False, "error": {"code": "PROJECT_LOCAL_ORIGIN_REQUIRED", "message": "Project authority requires the exact local application origin."}})
        if mutation and (self.headers.get_content_type() != "application/json" or
                self.headers.get("Origin") not in {None, "http://"+host}):
            return self._json(403, {"ok": False, "error": {"code": "PROJECT_JSON_ORIGIN_REQUIRED", "message": "Use bounded JSON from the same local application origin."}})
        from urllib.parse import parse_qs

        from api.project_authority import project_error
        try:
            parts = path.removeprefix("/api/projects").strip("/").split("/") if path != "/api/projects" else []
            body = _read_json(self) if mutation else {}
            result = self.application.project_api.handle(session.user, "POST" if mutation else "GET", parts,
                parse_qs(urlparse(self.path).query, keep_blank_values=True), body)
            from api.cad_tools import UnreleasedDrawingSource
            from api.component_geometry import (
                ComponentEvidenceSource,
                ReviewedAnalysisSource,
            )
            from api.engine_operating_projects import OperatingSource
            from api.engineering_extensions import GeometryIntentSource
            from api.geometry_projects import BinarySource
            from api.nozzle_geometry import EngineCandidateSource, EnginePreviewSource
            from api.propulsion_validation import PropulsionEvidenceSource
            if isinstance(result, BinarySource):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                evidence = isinstance(result, PropulsionEvidenceSource)
                operating = isinstance(result, OperatingSource)
                intent = isinstance(result, GeometryIntentSource)
                candidate = isinstance(result, EngineCandidateSource)
                display = isinstance(result, EnginePreviewSource)
                component_evidence=isinstance(result,ComponentEvidenceSource)
                reviewed=isinstance(result,ReviewedAnalysisSource)
                drawing=isinstance(result,UnreleasedDrawingSource)
                prefix = "COSMOS-source-bound-unreleased-" if drawing else "COSMOS-reviewed-analysis-not-manufacturing-" if reviewed else "COSMOS-component-evidence-" if component_evidence else "COSMOS-display-only-" if display else "COSMOS-unreviewed-engine-candidate-" if candidate else "COSMOS-unbuilt-engine-intent-" if intent else "COSMOS-preliminary-model-" if operating else "COSMOS-unreviewed-evidence-" if evidence else "COSMOS-software-fixture-"
                self.send_header("Content-Disposition", 'attachment; filename="' + prefix + result.name + '"')
                self.send_header("Content-Length", str(len(result.data)))
                self.send_header("X-COSMOS-SHA256", result.content_hash)
                self.send_header("X-COSMOS-Scope", "source-bound-unreleased-drawing-not-manufacturing-or-physical-acceptance" if drawing else "independently-reviewed-geometry-analysis-not-manufacturing-or-physical-acceptance" if reviewed else "original-component-evidence-may-be-historical-or-rejected-not-automatic-acceptance" if component_evidence else "display-only-not-metrology" if display else "unreviewed-engine-candidate-not-manufacturing-or-physical-acceptance" if candidate else "unbuilt-engine-geometry-intent-not-cad-acceptance" if intent else "selected-operating-model-not-physical-validation" if operating else "unreviewed-propulsion-evidence-not-physical-acceptance" if evidence else "immutable-software-fixture-source-not-engineering-publication")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Vary", "Cookie")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(result.data)
                return
            return self._json(200, result)
        except (ValueError, TypeError, KeyError, IndexError) as error:
            return self._json(400, {"ok": False, "error": {"code": "INVALID_PROJECT_REQUEST", "message": str(error)}})
        except Exception as error:
            translated = project_error(error)
            if translated is not None:
                status, result = translated
                return self._json(status, result)
            logger.exception("project authority boundary failed")
            status, result = map_systems_error(error)
            return self._json(status, result)

    def _dispatch_api_delete(self, path: str, session) -> None:
        if is_knowledge_api_path(path):
            return self._dispatch_knowledge_api(session, path)
        self._json(404, {"error": "not_found"})

    def _dispatch_api_post(self, path: str, session) -> None:
        if path == "/api/projects" or path.startswith("/api/projects/"):
            return self._dispatch_project(path, session, mutation=True)
        if not self._legacy_project_guard(path, session):
            return
        if path == "/api/propulsion" or path.startswith("/api/propulsion/"):
            if session is None:
                return self._json(401, {"error": "authentication_required"})
            if not role_can_modify_design(session.user.role):
                return self._json(403, {"error": {"code": "FORBIDDEN_ROLE",
                    "message": "Engineer or Admin required for persistent design mutations.",
                    "action": "Use a permitted engineering account; read-only results remain available."}})
        if path.startswith("/api/knowledge-reports/"):
            from gui.knowledge_reports_ui import dispatch
            return dispatch(self, path, session, mutation=True)
        if path.startswith("/api/comparison/"):
            from gui.comparison_ui import dispatch
            return dispatch(self, path, session, mutation=True)
        if path.startswith("/api/simulation/"):
            from gui.simulation_ui import dispatch
            return dispatch(self, path, session, mutation=True)
        if path.startswith("/api/ngg/"):
            from gui.ngg import dispatch
            return dispatch(self, path, session, mutation=True)
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
        if path.startswith("/api/propulsion/designs/") and path.endswith("/clone"):
            current = self._require_session()
            if current is None:
                return
            design_id = path.removeprefix("/api/propulsion/designs/").removesuffix("/clone").strip("/")
            try:
                payload = _read_json(self)
                source = load_design(design_id, self.application.design_store)
                cloned = clone_design(
                    source,
                    name=None if payload.get("name") is None else str(payload["name"]),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            return self._json(200, {"ok": True, "design": get_design_payload(cloned)})
        if path.startswith("/api/propulsion/designs/") and path.endswith("/save"):
            current = self._require_session()
            if current is None:
                return
            design_id = path.removeprefix("/api/propulsion/designs/").removesuffix("/save").strip("/")
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                save_design(design, self.application.design_store, edits=payload)
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            return self._json(200, {"ok": True, "design": get_design_payload(design)})
        if path.startswith("/api/propulsion/designs/") and path.endswith("/propellants"):
            current = self._require_session()
            if current is None:
                return
            design_id = (
                path.removeprefix("/api/propulsion/designs/").removesuffix("/propellants").strip("/")
            )
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                update_propellants(
                    design,
                    oxidizer_id=str(payload["oxidizer_id"]),
                    fuel_id=str(payload["fuel_id"]),
                    mixture_ratio=(
                        None
                        if payload.get("mixture_ratio") is None
                        else float(payload["mixture_ratio"])
                    ),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            return self._json(200, {"ok": True, "design": get_design_payload(design)})
        if path.startswith("/api/propulsion/designs/") and path.endswith("/cycle"):
            current = self._require_session()
            if current is None:
                return
            design_id = path.removeprefix("/api/propulsion/designs/").removesuffix("/cycle").strip("/")
            try:
                payload = _read_json(self)
                design = load_design(design_id, self.application.design_store)
                update_cycle(
                    design,
                    str(payload.get("cycle_type") or "UNSPECIFIED"),
                    store=self.application.design_store,
                )
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            return self._json(
                200,
                {
                    "ok": True,
                    "design": get_design_payload(design),
                    "implementation_status": design.cycle_configuration.implementation_status.value,
                    "reason": design.cycle_configuration.reason,
                },
            )
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
        if path.startswith("/api/propulsion/designs/") and path.endswith("/run/analysis"):
            current = self._require_session()
            if current is None:
                return
            design_id = path.removeprefix("/api/propulsion/designs/").removesuffix("/run/analysis").strip("/")
            try:
                payload = _read_json(self)
                if payload.keys() - {"phase3_inputs", "phase4_inputs"}:
                    raise ValueError("Unknown analysis command fields.")
                design = load_design(design_id, self.application.design_store)
                result = run_design_workflow(design, **payload, store=self.application.design_store)
                return self._json(200, result)
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
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
                    thermochemistry_configuration=payload.get("thermochemistry_configuration"),
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
                    material_id=None if payload.get("material_id") is None else str(payload["material_id"]),
                    external_pressure_pa=payload.get("external_pressure_pa"),
                    external_pressure_source=payload.get("external_pressure_source"),
                    material_temperature_k=payload.get("material_temperature_k"),
                    pressure_model=payload.get("pressure_model"),
                    gas_property_mode=payload.get("gas_property_mode"),
                    viscosity_pa_s=payload.get("viscosity_pa_s"),
                    conductivity_w_m_k=payload.get("conductivity_w_m_k"),
                    cp_j_kg_k=payload.get("cp_j_kg_k"),
                    wall_temperature_k=payload.get("wall_temperature_k"),
                    throat_curvature_radius_m=payload.get("throat_curvature_radius_m"),
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
        if path.startswith("/api/propulsion/designs/") and path.endswith("/run/subsystems"):
            current = self._require_session()
            if current is None:
                return
            design_id = path.removeprefix("/api/propulsion/designs/").removesuffix("/run/subsystems").strip("/")
            try:
                payload = _read_json(self)
                selected = payload.get("stages", ["injector", "nozzle", "cooling"])
                if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
                    from core.exceptions import InvalidInputError
                    raise InvalidInputError("stages must be a list of subsystem names.")
                design = load_design(design_id, self.application.design_store)
                summary = run_subsystems(design, inputs=payload.get("inputs"), stages=tuple(selected), store=self.application.design_store)
            except Exception as exc:
                status, error_payload = map_systems_error(exc)
                if status >= 500:
                    raise
                return self._json(status, error_payload)
            self.application.audit_action(current, action="PROPULSION_SUBSYSTEMS", resource=path,
                detail={"design_id": design_id, "stages": selected, "execution_ok": summary.get("execution_ok")},
                source_ip=self.client_address[0], user_agent=self.headers.get("User-Agent", "cosmos-desktop"))
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
            except AuthenticationError as exc:
                self.application.audit.record(
                    user_id="anonymous",
                    login_id=str(payload.get("login_id") or "unknown"),
                    action="LOGIN_FAILED",
                    resource="/api/auth/login",
                    detail={"reason": str(exc), "profile": payload.get("login_profile")},
                    source_ip=self.client_address[0],
                    user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
                )
                return self._json(
                    401,
                    {"error": str(exc), "error_code": "authentication_failed"},
                )
            except ValueError as exc:
                self.application.audit.record(
                    user_id="anonymous",
                    login_id=str(payload.get("login_id") or "unknown"),
                    action="LOGIN_FAILED",
                    resource="/api/auth/login",
                    detail={"reason": str(exc), "profile": payload.get("login_profile")},
                    source_ip=self.client_address[0],
                    user_agent=self.headers.get("User-Agent", "cosmos-desktop"),
                )
                return self._json(
                    401,
                    {"error": str(exc), "error_code": "profile_mismatch"},
                )
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
    from infrastructure.release.security import MAX_BODY
    from infrastructure.transport.multipart import (
        PREVIEW_FILE_LIMIT,
        read_multipart_upload,
    )
    if getattr(getattr(handler, "application", None), "release_preview", False):
        return read_multipart_upload(handler, max_body=MAX_BODY, max_file=PREVIEW_FILE_LIMIT)
    return read_multipart_upload(handler)


def serve_application(root: Path | str, *, host: str = "127.0.0.1", port: int = 8780) -> None:
    from infrastructure.release.security import PreviewHTTPServer, ReleaseProfileError
    application = CosmosApplication(root)

    class BoundHandler(CosmosApplicationHandler):
        pass

    BoundHandler.application = application
    try:
        server_class = PreviewHTTPServer if application.release_preview else ThreadingHTTPServer
        server = server_class((host, port), BoundHandler)
    except (OSError, ReleaseProfileError) as exc:
        application.close()
        raise SystemExit(
            f"Could not bind http://{host}:{port}: {exc}\n"
            "Try another port, e.g. --port 8781.",
        ) from exc

    identity = (f"  Private first-login record: {application.root / 'first-login.json'}\n"
                "  Local research preview only; not a production/hardware release.\n") if application.release_preview else "  Default admin: cosmos-admin / COSMOS-Dev-2026!\n"
    print(
        f"COSMOS 0.1 desktop shell listening on http://{host}:{port}\n"
        f"  data root={Path(root).resolve()}\n"
        f"{identity}"
        "  Press Ctrl+C to stop.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
    finally:
        server.server_close()
        application.close()
