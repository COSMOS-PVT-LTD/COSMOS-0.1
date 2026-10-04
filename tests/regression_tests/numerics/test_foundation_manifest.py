"""Frozen file contract and explicit advanced-capability non-operational state."""

import ast
import importlib
import json
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]


def test_deferred_slots_export_no_operational_api():
    manifest = json.loads(
        (
            REPOSITORY / "documentation/development/cosmos_numerics_foundation_001.json"
        ).read_text()
    )
    assert len(manifest["deferred_capabilities"]) == 13
    for entry in manifest["deferred_capabilities"]:
        assert entry["status"] == "DEFERRED"
        assert entry["operational_api"] is False
        module = importlib.import_module(
            "numerics." + entry["capability"].replace("/", ".")
        )
        assert module.CAPABILITY_STATE == "DEFERRED"
        assert module.__all__ == ()
        tree = ast.parse(Path(module.__file__).read_text())
        assert not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for node in ast.walk(tree)
        )


def test_frozen_numerics_files_present():
    manifest = json.loads(
        (
            REPOSITORY / "documentation/development/cosmos_numerics_foundation_001.json"
        ).read_text()
    )
    for path in manifest["files"]:
        assert (REPOSITORY / path).is_file()
    for path in (REPOSITORY / "numerics").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Raise)
                and isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
            ):
                assert node.exc.func.id != "NotImplementedError"
