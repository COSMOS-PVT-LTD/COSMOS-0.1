"""Exact-source in-process selected-cycle assessment; never a fallback solver."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from api.pressure_fed import _methods
from core.exceptions import InvalidInputError
from systems.cycle.coupled import assess
from systems.projects.models import PropulsionDesign


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {
        **_methods(),
        **{
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "api/cycle_assessment.py",
                "api/cycle_projects.py",
                "systems/projects/cycle_assessment.py",
                "systems/projects/pressure_fed.py",
                "api/pressure_fed_projects.py",
                "systems/stages/subsystems.py",
                "physics/heat_transfer/regenerative.py",
            )
        },
    }


_LOADED_METHODS = methods()


def evaluate(design: PropulsionDesign, specification: dict[str, Any]) -> dict[str, Any]:
    before = methods()
    if before != _LOADED_METHODS:
        raise InvalidInputError(
            "Cycle sources changed after loading; restart before evaluation."
        )
    result = assess(design, specification).to_canonical_dict()
    if before != methods():
        raise InvalidInputError(
            "Cycle sources changed during evaluation; no answer published."
        )
    return {
        "result": result,
        "method_sources": before,
        "scope": "SELECTED_STEADY_COMPONENT_BOUNDARY_ASSESSMENT_NOT_HARDWARE_VALIDATION",
    }
