"""Engine cycle configuration — extensible; Phase 2 has no cycle equations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = ("CycleConfiguration", "CycleImplementationStatus", "CycleType")


class CycleType(str, Enum):
    PRESSURE_FED = "PRESSURE_FED"
    GAS_GENERATOR = "GAS_GENERATOR"
    STAGED_COMBUSTION = "STAGED_COMBUSTION"
    EXPANDER = "EXPANDER"
    ELECTRIC_PUMP = "ELECTRIC_PUMP"
    UNSPECIFIED = "UNSPECIFIED"


class CycleImplementationStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    PARTIAL = "PARTIAL"
    IMPLEMENTED = "IMPLEMENTED"


# Phase 2: no cycle physics in frozen foundation → all NOT_IMPLEMENTED.
_CYCLE_STATUS: dict[CycleType, CycleImplementationStatus] = {
    CycleType.PRESSURE_FED: CycleImplementationStatus.NOT_IMPLEMENTED,
    CycleType.GAS_GENERATOR: CycleImplementationStatus.NOT_IMPLEMENTED,
    CycleType.STAGED_COMBUSTION: CycleImplementationStatus.NOT_IMPLEMENTED,
    CycleType.EXPANDER: CycleImplementationStatus.NOT_IMPLEMENTED,
    CycleType.ELECTRIC_PUMP: CycleImplementationStatus.NOT_IMPLEMENTED,
    CycleType.UNSPECIFIED: CycleImplementationStatus.NOT_IMPLEMENTED,
}


@dataclass(slots=True)
class CycleConfiguration:
    cycle_type: CycleType = CycleType.UNSPECIFIED
    implementation_status: CycleImplementationStatus = (
        CycleImplementationStatus.NOT_IMPLEMENTED
    )
    parameters: dict[str, object] = field(default_factory=dict)
    reason: str = "No validated cycle-power-balance implementation in COSMOS_0.1 Physics."

    @classmethod
    def for_type(cls, cycle_type: CycleType) -> CycleConfiguration:
        status = _CYCLE_STATUS.get(cycle_type, CycleImplementationStatus.NOT_IMPLEMENTED)
        return cls(cycle_type=cycle_type, implementation_status=status)

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "cycle_type": self.cycle_type.value,
            "implementation_status": self.implementation_status.value,
            "parameters": dict(self.parameters),
            "reason": self.reason,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> CycleConfiguration:
        cycle_type = CycleType(str(data.get("cycle_type", CycleType.UNSPECIFIED.value)))
        return cls(
            cycle_type=cycle_type,
            implementation_status=CycleImplementationStatus(
                str(
                    data.get(
                        "implementation_status",
                        CycleImplementationStatus.NOT_IMPLEMENTED.value,
                    )
                )
            ),
            parameters=dict(data.get("parameters") or {}),
            reason=str(
                data.get("reason")
                or "No validated cycle-power-balance implementation in COSMOS_0.1 Physics."
            ),
        )
