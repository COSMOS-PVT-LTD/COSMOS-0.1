"""Architecture tests for GUI ↔ Physics integration boundary."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GUI = REPO / "gui"


def test_gui_python_does_not_import_physics_package() -> None:
    offenders: list[str] = []
    for path in GUI.rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped.startswith("import physics") or stripped.startswith("from physics"):
                offenders.append(f"{path.relative_to(REPO)}: {stripped}")
    assert offenders == []


def test_gui_static_js_does_not_embed_anderson_identities() -> None:
    markers = (
        "((gamma-1)/2)",
        "gamma/(gamma-1)",
        "stagnation_pressure_ratio",
        "mach_from_area_ratio",
    )
    hits: list[str] = []
    for path in (GUI / "static").rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                hits.append(f"{path.name}: {marker}")
    assert hits == []


def test_api_adapter_is_the_physics_boundary() -> None:
    adapter = (REPO / "api" / "physics_compressible.py").read_text(encoding="utf-8")
    assert "from physics.compressible_flow" in adapter
    assert "validation_status" in adapter
    assert "NOT_CLAIMED" in adapter
