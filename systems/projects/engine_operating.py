"""Additive solved candidate persistence reusing immutable R05 input captures."""

from systems.cycle.operating_contract import validate
from systems.projects.authority import Principal, SavedSnapshot
from systems.projects.pressure_fed import ManagedPressureFed


class ManagedEngineOperating(ManagedPressureFed):
    domain = "engine-operating-point"
    inputs_domain = "engine-operating-inputs"
    schema = "cosmos.managed-engine-operating.v1"
    input_schema = "cosmos.managed-engine-operating-input.v1"
    operation_prefix = "engine-operating"
    validate_specification = staticmethod(validate)

    def read(self, actor: Principal, source: SavedSnapshot):
        value = super().read(actor, source)
        record = value["record"]
        usable = record["status"] == "COMPLETED" and record["evaluation"]["result"]["outputs"]["solved_candidate_usable"]
        value["usable_current_solved_candidate"] = value["usable_current_assessment"] and usable
        value["usable_current_assessment"] = value["usable_current_solved_candidate"]
        return value
