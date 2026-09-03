"""Architecture tests for Systems layer boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def _forbidden_imports(path: Path, forbidden_roots: tuple[str, ...]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for root in forbidden_roots:
                    if alias.name == root or alias.name.startswith(root + "."):
                        hits.append(f"{path.relative_to(REPO)}:{node.lineno} import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            for root in forbidden_roots:
                if node.module == root or node.module.startswith(root + "."):
                    hits.append(
                        f"{path.relative_to(REPO)}:{node.lineno} from {node.module}"
                    )
    return hits


def test_core_does_not_import_systems_or_physics() -> None:
    hits: list[str] = []
    for path in (REPO / "core").rglob("*.py"):
        hits.extend(_forbidden_imports(path, ("physics", "systems", "gui", "api")))
    assert hits == []


def test_gui_does_not_import_physics_or_systems_internals() -> None:
    hits: list[str] = []
    for path in (REPO / "gui").rglob("*.py"):
        # server may import api + DesignStore for wiring only — forbid physics and deep systems.
        text_hits = _forbidden_imports(path, ("physics",))
        hits.extend(text_hits)
        deep = _forbidden_imports(
            path,
            (
                "systems.calculations",
                "systems.workflow",
                "systems.projects",
                "systems.contracts",
            ),
        )
        # Allow systems.persistence.design_store on server as app-owned store handle.
        hits.extend(deep)
    assert hits == []


def test_api_propulsion_workflow_has_no_anderson_equations() -> None:
    text = (REPO / "api" / "propulsion_workflow.py").read_text(encoding="utf-8")
    for token in ("((gamma-1)/2)", "stagnation_temperature_ratio", "gamma/(gamma-1)"):
        assert token not in text


def test_systems_may_import_physics() -> None:
    text = (REPO / "systems" / "calculations" / "isentropic.py").read_text(encoding="utf-8")
    assert "from physics.compressible_flow.isentropic" in text
