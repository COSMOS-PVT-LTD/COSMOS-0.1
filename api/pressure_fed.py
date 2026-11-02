"""In-process read-only pressure-fed API; no HTTP authority or GUI equations."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from core.exceptions import InvalidInputError
from systems.cycle.pressure_fed import assess
from systems.projects.models import PropulsionDesign

__all__ = ("assess_pressure_fed",)


def _methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    paths = {
        path
        for directory in (
            "core",
            "physics/feed",
            "systems/cycle",
            "systems/contracts",
            "systems/operating_point",
            "systems/propellants",
            "systems/requirements",
            "systems/workflow",
        )
        for path in (root / directory).rglob("*.py")
    }
    paths.update(
        root / name
        for name in (
            "api/pressure_fed.py",
            "physics/feed/pressure_fed.py",
            "physics/model.py",
            "physics/exceptions.py",
            "physics/validity.py",
            "physics/quantities.py",
            "physics/injectors/orifice.py",
            "systems/projects/models.py",
        )
    )
    return {
        str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


_LOADED_METHODS = _methods()


def assess_pressure_fed(
    design: PropulsionDesign, specification: dict[str, Any]
) -> dict[str, Any]:
    """Return a detached supplemental result; original design is never modified.

    Persistence/HTTP publication is deliberately deferred until the managed
    assessment adapter captures inputs under the accepted project authority.
    """
    if _methods() != _LOADED_METHODS:
        raise InvalidInputError(
            "Pressure-fed method sources changed after loading; restart before evaluation."
        )
    result = assess(design, specification).to_canonical_dict()
    if _methods() != _LOADED_METHODS:
        raise InvalidInputError(
            "Pressure-fed method sources changed during evaluation; result not returned."
        )
    return {
        "result": result,
        "method_sources": dict(_LOADED_METHODS),
        "scope": "READ_ONLY_SUPPLEMENTAL_ASSESSMENT_NOT_WORKFLOW_CYCLE_CLOSURE",
    }
