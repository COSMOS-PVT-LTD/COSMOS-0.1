"""Reuse durable captured commands; keep the assumed-state study unchanged."""

from systems.cycle.operating_sensitivity import validate
from systems.projects.pressure_fed import ManagedPressureFed


class ManagedOperatingSensitivity(ManagedPressureFed):
    domain = "operating-sensitivity"
    inputs_domain = "operating-sensitivity-inputs"
    schema = "cosmos.managed-operating-sensitivity.v1"
    input_schema = "cosmos.managed-operating-sensitivity-input.v1"
    operation_prefix = "operating-sensitivity"
    validate_specification = staticmethod(validate)
