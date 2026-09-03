"""Architecture acceptance tests for Core layer independence."""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_PACKAGE = REPO_ROOT / "core"


def _physics_modules_loaded() -> list[str]:
    return sorted(name for name in sys.modules if name == "physics" or name.startswith("physics."))


def _clear_physics_modules() -> None:
    for name in list(sys.modules):
        if name == "physics" or name.startswith("physics."):
            del sys.modules[name]


def _core_python_files() -> list[Path]:
    return sorted(CORE_PACKAGE.rglob("*.py"))


def _find_physics_imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "physics" or alias.name.startswith("physics."):
                    hits.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module and (
                node.module == "physics" or node.module.startswith("physics.")
            ):
                hits.append((node.lineno, f"from {node.module} import ..."))

    return hits


@pytest.fixture(autouse=True)
def _isolate_core_imports() -> None:
    _clear_physics_modules()
    yield
    _clear_physics_modules()


def test_import_core_does_not_load_physics() -> None:
    import core  # noqa: F401

    assert _physics_modules_loaded() == []


def test_import_core_validation_does_not_load_physics() -> None:
    import core.validation  # noqa: F401

    assert _physics_modules_loaded() == []


def test_core_propulsion_wrappers_do_not_load_physics() -> None:
    from core.validation import validate_expansion_ratio, validate_mixture_ratio

    assert validate_mixture_ratio(2.5) == 2.5
    assert validate_expansion_ratio(40.0) == 40.0
    assert _physics_modules_loaded() == []


def test_core_package_has_no_physics_imports_in_source() -> None:
    violations: list[str] = []

    for path in _core_python_files():
        for lineno, statement in _find_physics_imports(path):
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel}:{lineno}: {statement}")

    assert violations == [], "Core must not import Physics:\n" + "\n".join(violations)


def test_physics_propulsion_validation_may_import_core_without_cycle() -> None:
    from physics.propulsion_validation import (
        validate_expansion_ratio,
        validate_mixture_ratio,
    )

    assert validate_mixture_ratio(3.5) == 3.5
    assert validate_expansion_ratio(25.0) == 25.0
    assert "core.validation" in sys.modules
