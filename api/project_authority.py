"""Authenticated project-scoped application API, with no engineering equations."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from api.authentication import AuthService, UserAccount
from api.cycle_assessment import evaluate as cycle_evaluate
from api.cycle_assessment import methods as cycle_methods
from api.cycle_projects import CycleAssessmentAPI
from api.engine_operating import evaluate as operating_evaluate
from api.engine_operating import methods as operating_methods
from api.engine_operating_projects import EngineOperatingAPI
from api.engineering_extensions import (
    EngineGeometryAPI,
    OperatingSensitivityAPI,
    evaluate_geometry,
    evaluate_sensitivity,
)
from api.engineering_extensions import (
    methods as extension_methods,
)
from api.evidence_projects import EvidenceProjectAPI
from api.geometry_projects import BinarySource, GeometryProjectAPI
from api.pressure_fed import assess_pressure_fed
from api.pressure_fed_projects import PressureFedAPI
from api.pressure_fed_projects import methods as pressure_fed_methods
from api.propulsion_validation import PropulsionValidationAPI
from api.propulsion_validation import methods as validation_methods
from api.propulsion_workflow import (
    apply_design_edits,
    create_design,
    export_design,
    get_stage_result_payload,
    get_workflow_payload,
    run_design_workflow,
    run_isentropic,
    run_phase3,
    run_phase4,
    run_phase6,
    run_subsystems,
    update_cycle,
    update_propellants,
    update_requirements,
)
from api.sensitivity_projects import SensitivityAPI
from api.sensitivity_projects import evaluate as sensitivity_evaluate
from api.sensitivity_projects import methods as sensitivity_methods
from api.study_projects import StudyProjectAPI
from systems.geometry.authority import ManagedGeometry
from systems.persistence.job_repository import JobRepository
from systems.persistence.project_repository import ProjectRepository
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    IntegrityFailure,
    InvalidRecord,
    Lifecycle,
    Membership,
    OperationConflict,
    Principal,
    ProjectStoreError,
    QuotaExceeded,
    RecordNotFound,
    SavedSnapshot,
    SchemaMismatch,
    StoreUnavailable,
    identity,
)
from systems.projects.cycle_assessment import ManagedCycleAssessment
from systems.projects.engine_geometry import ManagedEngineGeometry
from systems.projects.engine_operating import ManagedEngineOperating
from systems.projects.evidence_authority import ManagedEvidence
from systems.projects.operating_sensitivity import ManagedOperatingSensitivity
from systems.projects.pressure_fed import ManagedPressureFed
from systems.projects.propulsion_authority import (
    DOMAIN,
    PropulsionProjectService,
    decode_design,
)
from systems.projects.propulsion_validation import PropulsionValidation
from systems.projects.sensitivity import ManagedSensitivity
from systems.projects.study_authority import ManagedStudies


def principal(user: UserAccount) -> Principal:
    return Principal(user.user_id, user.role.value, user.active)


def expected_head(value: object) -> Head:
    if not isinstance(value, dict) or set(value) != {"version", "content_hash"}:
        raise InvalidRecord(
            "Both expected saved version and content hash are required."
        )
    return Head(value["version"], value["content_hash"])


def project_error(error: Exception) -> tuple[int, dict[str, object]] | None:
    """Translate authority failures at the API boundary, not in the GUI layer."""
    if not isinstance(error, ProjectStoreError):
        return None
    from systems.persistence.design_store import ManagedDesignAccess

    status = (
        409
        if isinstance(error, (HeadConflict, OperationConflict, ManagedDesignAccess))
        else (
            403
            if isinstance(error, AccessDenied)
            else 404
            if isinstance(error, RecordNotFound)
            else 413
            if isinstance(error, QuotaExceeded)
            else 503
            if isinstance(error, (IntegrityFailure, SchemaMismatch, StoreUnavailable))
            else 400
        )
    )
    detail: dict[str, object] = {
        "code": type(error).__name__,
        "message": str(error),
        "action": "Retain drafts. Reload/reconcile an exact authorized head; do not overwrite or reset storage.",
    }
    if isinstance(error, HeadConflict):
        detail["current_head"] = asdict(error.current)
    return status, {"ok": False, "error": detail}


def _allowed(body: dict[str, Any], keys: set[str]) -> None:
    if body.keys() - keys:
        raise InvalidRecord(
            "Unsupported request fields; identities/roles/results cannot be posted as authority."
        )


class ProjectAPI:
    def __init__(self, repository: ProjectRepository, auth: AuthService, *, jobs: JobRepository | None = None,
                 geometry_services: Callable[[], Any] | None = None, study_materializer: Callable[..., Any] | None = None,
                 knowledge_workspace: Callable[[UserAccount], Any] | None = None, portability: Any = None,
                 nozzle_workspace: Callable[[], Any] | None = None, component_workspace: Callable[[], Any] | None = None,
                 pico_component_workspace: Callable[[], Any] | None = None) -> None:
        self.repository = repository
        self.auth = auth
        self.guided = None
        self.guided_jobs = jobs
        self.guided_lock = threading.Lock()
        self.portability = portability
        self.service = PropulsionProjectService(repository)
        self.sensitivity = SensitivityAPI(ManagedSensitivity(repository, sensitivity_evaluate, sensitivity_methods)) if repository.supports_dependencies else None
        self.pressure_fed = PressureFedAPI(ManagedPressureFed(repository, assess_pressure_fed, pressure_fed_methods)) if repository.supports_dependencies else None
        self.cycle_assessments = CycleAssessmentAPI(ManagedCycleAssessment(repository, cycle_evaluate, cycle_methods)) if repository.supports_dependencies else None
        self.engine_operating = EngineOperatingAPI(ManagedEngineOperating(repository, operating_evaluate, operating_methods)) if repository.supports_dependencies else None
        self.operating_sensitivity = OperatingSensitivityAPI(ManagedOperatingSensitivity(repository, evaluate_sensitivity, extension_methods)) if repository.supports_dependencies else None
        self.engine_geometry = EngineGeometryAPI(ManagedEngineGeometry(repository, evaluate_geometry, extension_methods)) if repository.supports_dependencies else None
        self.propulsion_validation = PropulsionValidationAPI(PropulsionValidation(repository, validation_methods, lambda actor, source: self.engine_operating is not None and self.engine_operating.service.read(actor, source)["usable_current_solved_candidate"])) if repository.supports_dependencies else None
        def resolve_actor(user_id: str) -> Principal:
            user = auth.get_user_by_id(user_id)
            return principal(user) if user is not None else Principal(user_id, "ENGINEER", False)
        self.geometry = GeometryProjectAPI(ManagedGeometry(repository, jobs, geometry_services, resolve_actor)) if jobs is not None and geometry_services is not None else None
        from api.nozzle_geometry import EngineBuildsAPI
        from systems.geometry.engine_builds import EngineBuildCoordinator
        self.engine_builds = EngineBuildsAPI(EngineBuildCoordinator(repository, jobs, nozzle_workspace, resolve_actor, self.engine_geometry.service)) if jobs is not None and nozzle_workspace is not None and self.engine_geometry is not None else None
        from api.component_geometry import ComponentGeometryAPI
        self.components = ComponentGeometryAPI(repository,jobs,component_workspace,resolve_actor) if jobs is not None and component_workspace is not None and repository.supports_dependencies else None
        from systems.geometry.cad_tools import CadTools
        self.cad_tools = CadTools(self.components) if self.components is not None else None
        from api.pico_components import PicoComponentsAPI
        self.pico_components=PicoComponentsAPI(repository,jobs,pico_component_workspace,resolve_actor,self.components.models) if self.components is not None and pico_component_workspace is not None else None
        from api.geometry_qualification import GeometryQualificationAPI
        self.geometry_qualification=GeometryQualificationAPI(repository,jobs,self.components,self.pico_components,resolve_actor) if self.components is not None else None
        self.studies = StudyProjectAPI(ManagedStudies(repository, jobs, study_materializer, resolve_actor)) if jobs is not None and repository.supports_dependencies and study_materializer is not None else None
        def claim_reader(actor: Principal, claim_id: str) -> tuple[dict[str, Any], bytes]:
            from knowledge.workspace.evidence_navigation import EvidenceNavigation
            user = auth.get_user_by_id(actor.user_id)
            if user is None or principal(user) != actor or knowledge_workspace is None:
                raise AccessDenied("Exact active authenticated knowledge principal required.")
            with knowledge_workspace(user) as workspace:
                value = EvidenceNavigation(workspace).claim(claim_id)
                source = value["claim"]["source"]
                if source is None or not source["original_available"]:
                    raise RecordNotFound("Hash-checked original knowledge source required.")
                return value, workspace.vault.retrieve_original(source["source_id"])
        self.evidence = EvidenceProjectAPI(ManagedEvidence(repository, jobs, study_materializer, claim_reader)) if self.studies is not None and jobs is not None and study_materializer is not None else None

    def close(self) -> None:
        if self.guided is not None:
            self.guided.service.close()
        if self.geometry_qualification is not None:
            self.geometry_qualification.close()
        if self.pico_components is not None:
            self.pico_components.coordinator.close()
        if self.cad_tools is not None:
            self.cad_tools.close()
        if self.components is not None:
            self.components.builds.coordinator.close()
        if self.engine_builds is not None:
            self.engine_builds.coordinator.close()
        if self.studies is not None:
            self.studies.coordinator.close()
        if self.geometry is not None:
            self.geometry.coordinator.close()

    def envelope(self, actor: Principal, saved: SavedSnapshot) -> dict[str, Any]:
        current = self.repository.get_snapshot(
            actor, saved.project_id, domain=DOMAIN, object_id=saved.object_id
        )
        return {
            "ok": True,
            "design": json.loads(saved.payload),
            "source_canonical_json": saved.payload.decode("utf-8"),
            "authority": {
                "project_id": saved.project_id,
                "object_id": saved.object_id,
                "commit_id": saved.commit_id,
                "head": asdict(saved.head),
                "input_revision": saved.input_revision,
                "source_commit_id": saved.source_commit_id,
                "input_commit_id": saved.input_commit_id,
                "purpose": saved.purpose,
                "selected_at_commit": saved.selected_at_commit,
                "is_current": current.commit_id == saved.commit_id,
                "current_commit_id": current.commit_id,
                "current_head": asdict(current.head),
            },
        }

    def handle(
        self,
        user: UserAccount,
        method: str,
        parts: list[str],
        query: dict[str, list[str]],
        body: dict[str, Any],
    ) -> dict[str, Any] | BinarySource:
        actor = principal(user)
        actor.require(write=method != "GET")
        if any(len(values) != 1 for values in query.values()):
            raise InvalidRecord("Duplicate query fields are ambiguous.")
        if method != "GET" and query:
            raise InvalidRecord("Managed mutations require exact body/path identities, not historical or ignored query overrides.")
        limit = int(query.get("limit", ["20"])[0])
        if len(parts) == 1 and parts[0] in {"import-preview", "import"} and method == "POST":
            from api.portability_projects import handle_import
            return handle_import(self, user, parts[0], body)
        if not parts:
            if method == "GET":
                return {
                    "ok": True,
                    "projects": [
                        asdict(item)
                        for item in self.repository.list_projects(
                            actor, limit=limit, after_id=query.get("after", [""])[0]
                        )
                    ],
                }
            _allowed(body, {"title", "mission", "operation_id"})
            return {
                "ok": True,
                "project": asdict(
                    self.repository.create_project(
                        actor,
                        title=body["title"],
                        mission=body.get("mission", ""),
                        operation_id=body["operation_id"],
                    )
                ),
            }
        project_id = parts[0]
        project = self.repository.get_project(actor, project_id)
        if len(parts) >= 2 and parts[1] == "guided-engine":
            if self.guided_jobs is None or not self.repository.supports_dependencies:
                raise SchemaMismatch("Guided design requires existing durable authority; no store was migrated.")
            with self.guided_lock:
                if self.guided is None:
                    from api.guided_engine import GuidedAPI

                    def guided_actor(user_id):
                        account = self.auth.get_user_by_id(user_id)
                        return principal(account) if account is not None else Principal(user_id, "ENGINEER", False)

                    self.guided = GuidedAPI(self, self.guided_jobs, guided_actor)
            return self.guided.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] in {"operating-sensitivity", "engine-geometry-intent"}:
            extension = self.operating_sensitivity if parts[1] == "operating-sensitivity" else self.engine_geometry
            if extension is None:
                raise SchemaMismatch("Engineering extensions require dependency-capable managed authority; no migration performed.")
            return extension.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "engine-operating":
            if self.engine_operating is None:
                raise SchemaMismatch("Operating-point candidates require dependency-capable managed authority; no migration performed.")
            return self.engine_operating.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "propulsion-validation":
            if self.propulsion_validation is None:
                raise SchemaMismatch("Propulsion validation requires dependency-capable managed authority; no storage migration was performed.")
            return self.propulsion_validation.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "cycle-assessments":
            if self.cycle_assessments is None:
                raise SchemaMismatch("Coupled cycle assessments require dependency-capable managed authority; no existing storage was upgraded.")
            return self.cycle_assessments.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "pressure-fed":
            if self.pressure_fed is None:
                raise SchemaMismatch("Pressure-fed assessments require dependency-capable managed authority; existing storage was not upgraded.")
            return self.pressure_fed.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "sensitivity":
            if self.sensitivity is None:
                raise SchemaMismatch("Sensitivity requires dependency-capable managed authority; no existing storage was upgraded.")
            return self.sensitivity.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "transfers" and method == "GET":
            if self.portability is None:
                raise SchemaMismatch("Transfer originals require explicit schema6 composition.")
            if len(parts) == 2:
                return {"ok": True, "transfers": self.portability.transfers(actor, project_id, limit=limit, after=query.get("after", [""])[0])}
            if len(parts) == 3:
                name, raw = self.portability.original(actor, project_id, parts[2])
                return BinarySource(name, raw, sha256(raw).hexdigest())
        if parts[1:] == ["clone"] and method == "POST":
            _allowed(body, {"title", "expected", "operation_id"})
            if self.portability is None:
                raise SchemaMismatch("Project clone requires an explicit schema6 origin archive.")
            from systems.projects.clone_inputs import clone_input
            return {"ok": True, "project": asdict(self.portability.clone(actor, project_id, expected_head(body["expected"]),
                title=body["title"], operation_id=body["operation_id"], cloner=clone_input))}
        if len(parts) >= 2 and parts[1] in {"domains", "context", "timeline", "records", "jobs", "requirements", "objects"}:
            from api.context_projects import handle as project_context
            return project_context(self, actor, method, project_id, parts[1:], query, body)
        if parts[1:] == ["package"] and method == "GET":
            if self.portability is None:
                raise SchemaMismatch("Project package export requires schema6 composition.")
            raw = self.portability.export(actor, project_id, Head(int(query["version"][0]), query["hash"][0]))
            return BinarySource("project.zip", raw, sha256(raw).hexdigest())
        if len(parts) >= 2 and parts[1] in {"evidence", "reports"}:
            if self.evidence is None:
                raise SchemaMismatch("Managed evidence requires schema5; existing storage was not upgraded.")
            return self.evidence.handle(actor, method, project_id, parts[1], parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "studies":
            if self.studies is None:
                raise SchemaMismatch("Managed studies require schema5 composition; no existing storage was upgraded.")
            return self.studies.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "engine-redesign":
            if self.components is None:
                raise SchemaMismatch("Redesign requires existing dependency-capable component authority; no migration")
            from api.engine_redesign import handle as engine_redesign
            return engine_redesign(self.components, actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "component-cooling":
            if self.components is None:
                raise SchemaMismatch("Component cooling inspection requires existing dependency-capable component authority; no migration")
            from api.component_cooling import handle as component_cooling
            return component_cooling(self.components, actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "component-interfaces":
            if self.components is None:
                raise SchemaMismatch("Interface inspection requires existing dependency-capable component authority; no migration")
            from api.component_interfaces import handle as component_interfaces
            return component_interfaces(self.components, actor, method, project_id, parts[2:], query, body)
        if len(parts)>=2 and parts[1]=="cad-tools":
            if self.cad_tools is None:raise SchemaMismatch("CAD tools require existing authorized component-project composition")
            from api.cad_tools import handle as cad_tools
            return cad_tools(self,actor,method,project_id,parts[2:],query,body)
        if len(parts)>=2 and parts[1]=="geometry-qualifications":
            if self.geometry_qualification is None:raise SchemaMismatch("R08 requires existing dependency-capable component authority; no store migration")
            return self.geometry_qualification.handle(actor,method,project_id,parts[2:],query,body)
        if len(parts)>=2 and parts[1]=="picogk-component-builds":
            if self.pico_components is None:raise SchemaMismatch("PicoGK components require explicit dependency-capable project composition; no store was migrated")
            return self.pico_components.handle(actor,method,project_id,parts[2:],query,body)
        if len(parts)>=2 and parts[1] in {"component-geometry","component-geometry-builds","component-geometry-reviews","component-studies"}:
            if self.components is None: raise SchemaMismatch("Component editor/build/review/study setup requires reviewed durable-project composition; no existing store was migrated")
            return self.components.handle(actor,method,project_id,parts[1],parts[2:],query,body)
        if len(parts) >= 2 and parts[1] == "engine-geometry-builds":
            if self.engine_builds is None:
                raise SchemaMismatch("Native engine builds require reviewed durable project composition; no store was migrated.")
            return self.engine_builds.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) >= 2 and parts[1] == "geometry":
            if self.geometry is None:
                raise SchemaMismatch("Managed geometry requires schema3 composition; no existing data was upgraded.")
            return self.geometry.handle(actor, method, project_id, parts[2:], query, body)
        if len(parts) == 1:
            if method == "GET":
                return {"ok": True, "project": asdict(project)}
            _allowed(
                body,
                {
                    "title",
                    "mission",
                    "lifecycle",
                    "confirmation_project_id",
                    "expected",
                    "operation_id",
                },
            )
            return {
                "ok": True,
                "project": asdict(
                    self.repository.change_project(
                        actor,
                        project_id,
                        expected=expected_head(body.get("expected")),
                        operation_id=body["operation_id"],
                        title=body.get("title"),
                        mission=body.get("mission"),
                        lifecycle=Lifecycle(body["lifecycle"])
                        if "lifecycle" in body
                        else None,
                        confirmation_project_id=body.get("confirmation_project_id"),
                    )
                ),
            }
        if parts[1:] == ["members"] and method == "POST":
            if actor.user_id != project.owner_user_id:
                raise AccessDenied("Only the project owner may manage membership.")
            _allowed(body, {"user_id", "capability", "expected", "operation_id"})
            # Resolve the real stable account; posted display names/roles are not authority.
            member = self.auth.get_user_by_id(body["user_id"])
            if member is None:
                raise RecordNotFound("Target account not found.")
            return {
                "ok": True,
                "project": asdict(
                    self.repository.set_member(
                        actor,
                        project_id,
                        member=principal(member),
                        capability=Membership(body["capability"])
                        if body.get("capability") is not None
                        else None,
                        expected=expected_head(body.get("expected")),
                        operation_id=body["operation_id"],
                    )
                ),
            }
        if parts[1] != "designs":
            raise RecordNotFound("Project route not found.")
        if len(parts) == 2 and method == "GET":
            rows = []
            for item in self.repository.list_objects(
                actor,
                project_id,
                domain=DOMAIN,
                limit=limit,
                after_id=query.get("after", [""])[0],
            ):
                saved = self.repository.get_snapshot(
                    actor,
                    project_id,
                    domain=DOMAIN,
                    object_id=item.object_id,
                    commit_id=item.commit_id,
                )
                design = decode_design(saved)
                rows.append(
                    {
                        "design_id": item.object_id,
                        "name": design.name,
                        "revision": design.revision,
                        "state": design.status.value,
                        "updated_at": design.updated_at,
                        "engineer": design.engineer,
                        "saved_version": item.head.version,
                        "commit_id": item.commit_id,
                        "project_id": project_id,
                    }
                )
            return {"ok": True, "designs": rows}
        if method == "GET":
            object_id = parts[2]
            if parts[3:] == ["history"]:
                before = int(query["before"][0]) if "before" in query else None
                commits = []
                for commit_id in self.repository.list_commit_ids(
                    actor,
                    project_id,
                    domain=DOMAIN,
                    object_id=object_id,
                    limit=limit,
                    before_version=before,
                ):
                    historical = self.repository.get_snapshot(
                        actor,
                        project_id,
                        domain=DOMAIN,
                        object_id=object_id,
                        commit_id=commit_id,
                    )
                    commits.append(
                        {
                            "commit_id": historical.commit_id,
                            "head": asdict(historical.head),
                            "input_revision": historical.input_revision,
                            "created_at": historical.created_at,
                            "purpose": historical.purpose,
                            "source_commit_id": historical.source_commit_id,
                            "input_commit_id": historical.input_commit_id,
                            "selected_at_commit": historical.selected_at_commit,
                        }
                    )
                return {"ok": True, "commits": commits}
            saved = self.repository.get_snapshot(
                actor,
                project_id,
                domain=DOMAIN,
                object_id=object_id,
                commit_id=query.get("commit", [None])[0],
            )
            design = decode_design(saved)
            if len(parts) == 3:
                return self.envelope(actor, saved)
            if parts[3:] == ["workflow"]:
                return {"ok": True, "workflow": get_workflow_payload(design)}
            if parts[3:] == ["export"]:
                return {"ok": True, "package": export_design(design)}
            if len(parts) == 5 and parts[3] == "stages":
                result = get_stage_result_payload(
                    design,
                    parts[4],
                    allow_stale=query.get("allow_stale", ["false"])[0]
                    in {"1", "true", "True"},
                )
                current = self.repository.get_snapshot(
                    actor, project_id, domain=DOMAIN, object_id=object_id
                )
                if current.commit_id != saved.commit_id:
                    result["displayable_as_current"] = False
                    result["snapshot_scope"] = "HISTORICAL_READ_ONLY"
                return result
            raise RecordNotFound("Exact project design route not found.")
        raw_operation = body.get("operation_id")
        if not isinstance(raw_operation, str):
            raise InvalidRecord("A bounded operation ID is required.")
        operation_id = identity(raw_operation, "operation ID")
        expected = (
            expected_head(body.get("expected")) if len(parts) > 2 else Head.absent()
        )
        action = "/".join(parts[3:])
        command_hash = sha256(
            json.dumps(
                {"route": parts, "body": body},
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest()
        if len(parts) == 2:
            _allowed(body, {"name", "description", "operation_id"})
            name = body.get("name", "Rocket Engine Analysis")
            if not isinstance(name, str) or not name.strip() or len(name) > 200:
                raise InvalidRecord("Design name must contain 1–200 characters.")
            description = body.get("description", "")
            if not isinstance(description, str) or len(description) > 8192:
                raise InvalidRecord("Invalid design description.")
            saved = self.service.create(
                actor,
                project_id,
                design=create_design(
                    name=name, description=description, engineer=user.login_id
                ),
                operation_id=operation_id,
                command_hash=command_hash,
            )
        elif action in {"activate", "branch", "clone"}:
            _allowed(body, {"expected", "operation_id", "source_commit_id", "name"})
            name = body.get("name")
            if name is not None and (
                not isinstance(name, str) or not name.strip() or len(name) > 200
            ):
                raise InvalidRecord("Branch name must contain 1–200 characters.")
            saved = self.service.historical(
                actor,
                project_id,
                parts[2],
                expected=expected,
                operation_id=operation_id,
                command_hash=command_hash,
                source_commit_id=body["source_commit_id"],
                branch=action != "activate",
                name=name,
            )
        elif action.startswith("run/"):
            runners: dict[str, Callable[..., Any]] = {
                "run/phase3": run_phase3,
                "run/phase4": run_phase4,
                "run/phase6": run_phase6,
                "run/analysis": run_design_workflow,
                "run/subsystems": run_subsystems,
                "run/isentropic": run_isentropic,
            }
            runner = runners.get(action)
            if runner is None:
                raise RecordNotFound("Supported calculation route not found.")
            import inspect

            keys = set(inspect.signature(runner).parameters) - {"design", "store"}
            _allowed(body, keys | {"expected", "operation_id"})
            kwargs = {key: value for key, value in body.items() if key in keys}
            if "stages" in kwargs:
                if not isinstance(kwargs["stages"], list) or len(kwargs["stages"]) > 3:
                    raise InvalidRecord("Invalid subsystem stage selection.")
                kwargs["stages"] = tuple(kwargs["stages"])

            def evaluate(design):
                result = runner(design, **kwargs)
                return (
                    result.to_canonical_dict()
                    if hasattr(result, "to_canonical_dict")
                    else result
                )

            saved = self.service.calculate(
                actor,
                project_id,
                parts[2],
                expected=expected,
                operation_id=operation_id,
                command_hash=command_hash,
                parameters={"action": action, "inputs": kwargs},
                evaluate=evaluate,
            )
        else:
            common = {"expected", "operation_id"}
            if action == "save":
                _allowed(
                    body,
                    common
                    | {
                        "name",
                        "base_revision",
                        "editor_drafts",
                        "requirements",
                        "propellants",
                        "cycle_type",
                        "subsystem_inputs",
                        "thermochemistry_configuration",
                    },
                )
                edits = {key: value for key, value in body.items() if key not in common}

                def mutate(design):
                    apply_design_edits(design, edits=edits)
            elif action == "requirements":
                _allowed(body, common | {"updates"})

                def mutate(design):
                    update_requirements(design, body["updates"])
            elif action == "propellants":
                _allowed(body, common | {"oxidizer_id", "fuel_id", "mixture_ratio"})

                def mutate(design):
                    update_propellants(
                        design,
                        **{
                            key: value
                            for key, value in body.items()
                            if key not in common
                        },
                    )
            elif action == "cycle":
                _allowed(body, common | {"cycle_type"})

                def mutate(design):
                    update_cycle(design, body["cycle_type"])
            else:
                raise RecordNotFound("Supported project mutation route not found.")
            saved = self.service.edit(
                actor,
                project_id,
                parts[2],
                expected=expected,
                operation_id=operation_id,
                command_hash=command_hash,
                mutate=mutate,
            )
        result = json.loads(saved.response_payload) if saved.response_payload else {}
        # ok here means durable command acceptance, not a successful physical solve.
        envelope = self.envelope(actor, saved)
        envelope["calculation"] = result or None
        if result:
            envelope.update(result)
            envelope.update(
                design=json.loads(saved.payload),
                authority=self.envelope(actor, saved)["authority"],
            )
            envelope["command_retained"] = True
        return envelope
