"""Explicit persisted thermochemistry mode and reactant state (no equations)."""

from __future__ import annotations

import math
from typing import Any

from core.exceptions import InvalidInputError
from systems.projects.models import PropulsionDesign


def configure_thermochemistry(design: PropulsionDesign, data: dict[str, Any]) -> None:
    fields = {"mode", "fuel_temperature_k", "oxidizer_temperature_k"}
    if not isinstance(data, dict) or data.keys() - fields:
        raise InvalidInputError("Unknown or malformed thermochemistry configuration.")
    mode = data.get("mode")
    if mode not in {"nasa_cea", "assumed"}:
        raise InvalidInputError("Thermochemistry mode must be nasa_cea or assumed.")
    clean: dict[str, Any] = {"mode": mode}
    for key in fields - {"mode"}:
        value = data.get(key)
        if value is None:
            continue  # Drafts may be incomplete; execution requires both temperatures.
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise InvalidInputError(f"{key} must be a finite positive temperature in kelvin.")
        clean[key] = float(value)
    old = design.thermochemistry_configuration
    if old != clean:
        design.thermochemistry_configuration = clean
        design.record_input_change("thermochemistry_configuration", old, clean)
