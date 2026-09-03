"""Authoritative propulsion design aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from core.serialization import canonical_json_dumps
from core.version import COSMOS_VERSION

from systems import SYSTEMS_SCHEMA_VERSION
from systems.contracts.results import CalculationResult
from systems.cycle.models import CycleConfiguration
from systems.operating_point.models import OperatingPoint
from systems.propellants.models import PropellantConfiguration
from systems.requirements.models import DesignRequirements
from systems.workflow.state import WorkflowState

__all__ = ("DesignChangeEvent", "DesignStatus", "PropulsionDesign")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class DesignChangeEvent:
    field: str
    old_value: object
    new_value: object
    revision: int
    timestamp: str
    source: str = "systems"

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "new_value": self.new_value,
            "old_value": self.old_value,
            "revision": self.revision,
            "source": self.source,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> DesignChangeEvent:
        return cls(
            field=str(data["field"]),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            revision=int(data["revision"]),
            timestamp=str(data["timestamp"]),
            source=str(data.get("source") or "systems"),
        )


@dataclass(slots=True)
class DesignStatus:
    value: str = "draft"  # draft | active | archived

    def to_canonical_dict(self) -> dict[str, object]:
        return {"value": self.value}

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> DesignStatus:
        return cls(value=str(data.get("value") or "draft"))


@dataclass(slots=True)
class PropulsionDesign:
    """
    Root propulsion design object.

    Subsystem design slots (injector, chamber, …) remain None until later phases.
    """

    name: str
    design_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    revision: int = 0
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)
    software_version: str = COSMOS_VERSION
    status: DesignStatus = field(default_factory=DesignStatus)
    engineer: str | None = None
    requirements: DesignRequirements = field(default_factory=DesignRequirements)
    propellant_configuration: PropellantConfiguration = field(
        default_factory=PropellantConfiguration
    )
    cycle_configuration: CycleConfiguration = field(default_factory=CycleConfiguration)
    operating_point: OperatingPoint = field(default_factory=OperatingPoint)
    injector_design: dict[str, object] | None = None
    chamber_design: dict[str, object] | None = None
    thermal_design: dict[str, object] | None = None
    cooling_design: dict[str, object] | None = None
    nozzle_design: dict[str, object] | None = None
    structural_design: dict[str, object] | None = None
    material_selection: dict[str, object] | None = None
    workflow: WorkflowState = field(default_factory=WorkflowState)
    change_log: list[DesignChangeEvent] = field(default_factory=list)
    schema_version: str = SYSTEMS_SCHEMA_VERSION

    def bump_revision(self, field: str, old_value: object, new_value: object) -> int:
        self.revision += 1
        self.updated_at = _utc_now_iso()
        self.change_log.append(
            DesignChangeEvent(
                field=field,
                old_value=old_value,
                new_value=new_value,
                revision=self.revision,
                timestamp=self.updated_at,
            )
        )
        return self.revision

    def record_input_change(self, field: str, old_value: object, new_value: object) -> tuple[str, ...]:
        """Bump revision, log change, invalidate dependent workflow results."""

        self.bump_revision(field, old_value, new_value)
        return self.workflow.invalidate_field(field)

    def store_stage_result(self, stage_id: str, result: CalculationResult) -> None:
        result.design_revision = self.revision
        self.workflow.store_result(stage_id, result)
        self.updated_at = _utc_now_iso()

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "chamber_design": self.chamber_design,
            "change_log": [event.to_canonical_dict() for event in self.change_log],
            "cooling_design": self.cooling_design,
            "created_at": self.created_at,
            "cycle_configuration": self.cycle_configuration.to_canonical_dict(),
            "description": self.description,
            "design_id": self.design_id,
            "engineer": self.engineer,
            "injector_design": self.injector_design,
            "material_selection": self.material_selection,
            "name": self.name,
            "nozzle_design": self.nozzle_design,
            "operating_point": self.operating_point.to_canonical_dict(),
            "propellant_configuration": self.propellant_configuration.to_canonical_dict(),
            "requirements": self.requirements.to_canonical_dict(),
            "revision": self.revision,
            "schema_version": self.schema_version,
            "software_version": self.software_version,
            "status": self.status.to_canonical_dict(),
            "structural_design": self.structural_design,
            "thermal_design": self.thermal_design,
            "updated_at": self.updated_at,
            "workflow": self.workflow.to_canonical_dict(),
        }

    def to_canonical_json(self) -> str:
        return canonical_json_dumps(self.to_canonical_dict())

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> PropulsionDesign:
        return cls(
            design_id=str(data["design_id"]),
            name=str(data["name"]),
            description=str(data.get("description") or ""),
            revision=int(data.get("revision") or 0),
            created_at=str(data.get("created_at") or _utc_now_iso()),
            updated_at=str(data.get("updated_at") or _utc_now_iso()),
            software_version=str(data.get("software_version") or COSMOS_VERSION),
            status=DesignStatus.from_canonical_dict(dict(data.get("status") or {})),
            engineer=None if data.get("engineer") is None else str(data["engineer"]),
            requirements=DesignRequirements.from_canonical_dict(
                dict(data.get("requirements") or {})
            ),
            propellant_configuration=PropellantConfiguration.from_canonical_dict(
                dict(data.get("propellant_configuration") or {})
            ),
            cycle_configuration=CycleConfiguration.from_canonical_dict(
                dict(data.get("cycle_configuration") or {})
            ),
            operating_point=OperatingPoint.from_canonical_dict(
                dict(data.get("operating_point") or {})
            ),
            injector_design=(
                None if data.get("injector_design") is None else dict(data["injector_design"])
            ),
            chamber_design=(
                None if data.get("chamber_design") is None else dict(data["chamber_design"])
            ),
            thermal_design=(
                None if data.get("thermal_design") is None else dict(data["thermal_design"])
            ),
            cooling_design=(
                None if data.get("cooling_design") is None else dict(data["cooling_design"])
            ),
            nozzle_design=(
                None if data.get("nozzle_design") is None else dict(data["nozzle_design"])
            ),
            structural_design=(
                None
                if data.get("structural_design") is None
                else dict(data["structural_design"])
            ),
            material_selection=(
                None
                if data.get("material_selection") is None
                else dict(data["material_selection"])
            ),
            workflow=WorkflowState.from_canonical_dict(dict(data.get("workflow") or {})),
            change_log=[
                DesignChangeEvent.from_canonical_dict(dict(item))
                for item in (data.get("change_log") or [])
            ],
            schema_version=str(data.get("schema_version") or SYSTEMS_SCHEMA_VERSION),
        )
