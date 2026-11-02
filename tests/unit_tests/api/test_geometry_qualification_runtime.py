import json
from hashlib import sha256
from pathlib import Path

import pytest

from api import geometry_qualification as api


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "ROOT", tmp_path)
    python = tmp_path / ".venv-release-p12/bin/python"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"Not executed: admission test fixture")
    python.chmod(0o700)
    venv = python.parent.parent / "pyvenv.cfg"
    venv.write_text("test fixture")
    method = tmp_path / "method.py"
    method.write_text("test method")
    digest = lambda p: sha256(p.read_bytes()).hexdigest()
    methods = {"method.py": digest(method)}
    monkeypatch.setattr(api, "methods", lambda: methods)
    hashes = {**methods, str(python): digest(python), str(venv): digest(venv)}
    reports = {}
    for role, n in (("unit", 10), ("native", 1), ("http", 1), ("families", 22)):
        path = tmp_path / (role + ".xml")
        path.write_text("Admission test report fixture, not executed qualification")
        reports[role] = {
            "tests": n,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "path": str(path),
            "sha256": digest(path),
        }
    proof = {
        "method_sources": methods,
        "sha256": hashes,
        "reports": reports,
        "physical_validation": "NOT_PERFORMED",
    }
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(proof))
    cfg = {
        "schema": api.RUNTIME_SCHEMA,
        "python": str(python),
        "sha256": hashes,
        "receipt": str(receipt),
        "receipt_sha256": digest(receipt),
    }
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(cfg))
    return path, cfg, proof, receipt


def test_r08_admits_only_current_separately_bound_profile(tmp_path, monkeypatch):
    path, *_ = fixture(tmp_path, monkeypatch)
    assert api.configuration(path)["schema"] == api.RUNTIME_SCHEMA


@pytest.mark.parametrize(
    "change",
    [
        "method",
        "python",
        "venv",
        "report",
        "receipt",
        "skip",
        "failed",
        "missing-native",
        "missing-families",
        "physical",
        "unknown-command",
    ],
)
def test_r08_refuses_stale_or_weakened_runtime_evidence(tmp_path, monkeypatch, change):
    path, cfg, proof, receipt = fixture(tmp_path, monkeypatch)
    if change in {"method", "python", "venv", "report", "receipt"}:
        file = {
            "method": tmp_path / "method.py",
            "python": Path(cfg["python"]),
            "venv": Path(cfg["python"]).parent.parent / "pyvenv.cfg",
            "report": tmp_path / "native.xml",
            "receipt": receipt,
        }[change]
        file.write_text("changed")
    elif change == "unknown-command":
        cfg["python"] = "/tmp/untrusted/python"
    else:
        if change == "skip":
            proof["reports"]["native"]["skipped"] = 1
        elif change == "failed":
            proof["reports"]["unit"]["failures"] = 1
        elif change == "missing-native":
            proof["reports"].pop("native")
        elif change == "missing-families":
            proof["reports"].pop("families")
        else:
            proof["physical_validation"] = "VALIDATED"
        receipt.write_text(json.dumps(proof))
        cfg["receipt_sha256"] = sha256(receipt.read_bytes()).hexdigest()
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError):
        api.configuration(path)
