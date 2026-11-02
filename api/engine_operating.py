"""Exact-source engine operating candidate adapter and runtime fingerprints."""

from __future__ import annotations

from hashlib import sha256
from importlib import import_module
from pathlib import Path
from typing import Any

from api.pressure_fed import _methods
from core.exceptions import InvalidInputError
from systems.cycle.engine_operating import assess
from systems.projects.models import PropulsionDesign


def methods() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    result = _methods()
    for name in (
        "api/engine_operating.py", "api/engine_operating_projects.py", "systems/projects/engine_operating.py",
        "systems/projects/pressure_fed.py", "api/pressure_fed_projects.py", "api/cycle_projects.py",
        "physics/compressible_flow/heated_nozzle.py", "physics/heat_transfer/regenerative.py", "physics/heat_transfer/bartz.py",
        "physics/heat_transfer/pressure_cooling.py",
        "plugins/nasa_cea/chamber.py", "plugins/nasa_cea/engine.py", "plugins/nasa_cea/species_map.py",
        "numerics/nonlinear_solver/bounded.py", "systems/visualization/plots.py",
    ):
        result[name] = sha256((root / name).read_bytes()).hexdigest()
    try:
        cea = import_module("cea")
        result["runtime:cea-version"] = sha256(str(cea.__version__).encode()).hexdigest()
        if cea.__file__ is None:
            raise TypeError("CEA package path unavailable")
        directory = Path(cea.__file__).parent
        for path in [directory / "data/thermo.lib", directory / "data/trans.lib", *sorted((directory / "lib").glob("*.so"))]:
            result["runtime:cea/" + str(path.relative_to(directory))] = sha256(path.read_bytes()).hexdigest()
    except (ImportError, OSError, TypeError):
        result["runtime:cea-unavailable"] = sha256(b"unavailable-no-fallback").hexdigest()
    return result


_LOADED_METHODS = methods()


def evaluate(design: PropulsionDesign, specification: dict[str, Any]) -> dict[str, Any]:
    before = methods()
    if before != _LOADED_METHODS:
        raise InvalidInputError("Operating-point sources/runtime changed after loading; restart before evaluation.")
    result = assess(design, specification).to_canonical_dict()
    if before != methods():
        raise InvalidInputError("Operating-point methods/runtime changed during evaluation; no candidate published.")
    return {"result": result, "method_sources": before, "scope": "SELECTED_OPERATING_POINT_CANDIDATE_NOT_PHYSICAL_ACCEPTANCE"}
