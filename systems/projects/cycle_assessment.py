"""Selected-cycle records reuse the qualified R05 downstream capture protocol."""

from typing import Any

from systems.cycle.coupled import validate
from systems.projects.authority import Principal, SavedSnapshot
from systems.projects.pressure_fed import ManagedPressureFed


class ManagedCycleAssessment(ManagedPressureFed):
    domain = "coupled-cycle-assessment"
    inputs_domain = "coupled-cycle-inputs"
    schema = "cosmos.managed-coupled-cycle.v1"
    input_schema = "cosmos.managed-coupled-cycle-input.v1"
    operation_prefix = "coupled-cycle"
    validate_specification = staticmethod(validate)

    def read(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        value = super().read(actor, source)
        record = value["record"]
        balanced = (
            record["status"] == "COMPLETED"
            and record["evaluation"]["result"]["outputs"][
                "assessment_balances_closed_within_declared_tolerances"
            ]
        )
        value["usable_current_balanced_assessment"] = (
            value["usable_current_assessment"] and balanced
        )
        return value
