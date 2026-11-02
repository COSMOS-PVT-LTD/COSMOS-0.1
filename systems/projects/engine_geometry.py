"""Immutable engineering intent capture, separate from qualified native fixtures."""

from systems.geometry.engine_intent import validate
from systems.projects.pressure_fed import ManagedPressureFed


class ManagedEngineGeometry(ManagedPressureFed):
    domain = "engine-geometry-intent"
    inputs_domain = "engine-geometry-intent-inputs"
    schema = "cosmos.managed-engine-geometry-intent.v1"
    input_schema = "cosmos.managed-engine-geometry-intent-input.v1"
    operation_prefix = "engine-geometry-intent"
    validate_specification = staticmethod(validate)
