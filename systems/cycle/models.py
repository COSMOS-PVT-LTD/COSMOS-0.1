"""Cycle intent and current model scope; not a solved operating-point record."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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


# Selected R06 steady solvers exist; configuration is not successful execution.
_CYCLE_STATUS: dict[CycleType, CycleImplementationStatus] = {
    CycleType.PRESSURE_FED: CycleImplementationStatus.PARTIAL,
    CycleType.GAS_GENERATOR: CycleImplementationStatus.PARTIAL,
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
        reason = ("Selected steady PF/GG assessment and CEA HP operating solvers are available with explicit sourced inputs. Cycle selection does not run a feed/power balance; physical validation NOT_PERFORMED."
                  if status is CycleImplementationStatus.PARTIAL else "This selected cycle has no supported model. No implicit substitution of another cycle.")
        return cls(cycle_type=cycle_type, implementation_status=status, reason=reason)

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "cycle_type": self.cycle_type.value,
            "implementation_status": self.implementation_status.value,
            "parameters": dict(self.parameters),
            "reason": self.reason,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, Any]) -> CycleConfiguration:
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
