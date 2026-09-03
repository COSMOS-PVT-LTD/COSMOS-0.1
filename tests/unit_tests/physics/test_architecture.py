"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_architecture
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Architecture-boundary audit for the physics package.
"""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_IMPORTS = (
    "gui",
    "ai",
    "api",
    "engineering",
    "simulation",
    "database",
)


def test_physics_does_not_import_forbidden_packages() -> None:
    root = Path(__file__).resolve().parents[3] / "physics"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for package in FORBIDDEN_IMPORTS:
                if stripped.startswith(f"import {package}") or stripped.startswith(
                    f"from {package}"
                ):
                    offenders.append(f"{path}: {stripped}")
    assert offenders == []


def test_physics_does_not_define_parallel_quantity_types() -> None:
    root = Path(__file__).resolve().parents[3] / "physics"
    banned = ("class PhysicsQuantity", "class ThermoQuantity", "class FluidUnit", "class RocketDimension")
    hits: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{path}: {token}")
    assert hits == []
