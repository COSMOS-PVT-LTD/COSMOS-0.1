"""Exact local source/dependency evidence, not distribution/license approval."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from importlib import metadata
from pathlib import Path
from typing import Any
from urllib.parse import quote

PACKAGES = ("api", "core", "knowledge", "physics", "numerics", "systems", "simulation", "validation", "gui", "infrastructure", "plugins", "databases")
CONTRACTS: tuple[str, ...] = ("systems/contracts/geometry", "simulation/contracts.py", "validation/contracts.py",
             "plugins/geometry/protocol.py", "api/ngg_workbench.py", "api/simulation_workbench.py",
             "api/comparison_workbench.py", "api/knowledge_reports.py", "gui/static/design-system/components.js",
             "gui/static/app-shell/model.js", "gui/static/knowledge-reports/model.js", "validation/reporting.py")
CONTRACTS += ("api/authentication.py", "gui/server.py", "gui/static/app.js", "gui/static/rbac.js", "infrastructure/release/security.py",
              "infrastructure/release/launch_preview.py", "requirements-release-macos.txt")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def source_files(root: Path) -> dict[str, str]:
    files = [root / "main.py", root / "LICENSE", root / "NOTICE"]
    for package in PACKAGES:
        files.extend(p for p in (root / package).rglob("*") if p.is_file() and p.suffix in {".py", ".js", ".css", ".html", ".json", ".svg", ".png", ".jpg", ".woff2"})
    result = {}
    for path in sorted(set(files)):
        if "__pycache__" in path.parts:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Source escaped release root: " + str(path))
        result[str(path.relative_to(root))] = sha(path)
    return result


def contract_registry(root: Path) -> dict[str, Any]:
    files = {}
    for name in CONTRACTS:
        path = root / name
        candidates = [path] if path.is_file() else list(path.rglob("*.py")) + list(path.rglob("*.json"))
        if not candidates:
            raise ValueError("Contract source is absent: " + name)
        for item in candidates:
            files[str(item.relative_to(root))] = sha(item)
    value = {"schema_version": "p12-frozen-registry-v1", "scope": "Exact local source/transport freeze; not human acceptance",
             "files": dict(sorted(files.items())), "wire_version": "NGG-json-v1 / geometry 1.0.0",
             "study_schema": "p09 steady-spherical-conduction-v1", "report_schema": "p11-engineering-report-v1",
             "flags_default_off": ["COSMOS_NEW_SHELL", "COSMOS_NGG", "COSMOS_NEW_SIM_UI", "COSMOS_NEW_VV_UI", "COSMOS_NEW_KNOWLEDGE_REPORTS_UI"],
             "release_profile": "local-preview only; no production profile", "approval": "unsigned automated freeze"}
    return {**value, "content_sha256": hashlib.sha256(canonical(value)).hexdigest()}


def verify_registry(root: Path, value: dict[str, Any]) -> None:
    body = {key: item for key, item in value.items() if key != "content_sha256"}
    if hashlib.sha256(canonical(body)).hexdigest() != value.get("content_sha256"):
        raise ValueError("Contract registry checksum mismatch")
    for name, expected in value["files"].items():
        path = root / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or sha(path) != expected:
            raise ValueError("Frozen contract changed or escaped root: " + name)


def python_inventory(paths: list[Path], notices: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Hash installed distributions, not an unverified original wheel archive."""
    notices.mkdir(parents=True, exist_ok=False)
    components = []
    entries = {}
    for index, location in enumerate(paths):
        for dist in sorted(metadata.distributions(path=[str(location)]), key=lambda d: str(d.metadata["Name"]).lower()):
            name, version = str(dist.metadata["Name"]), dist.version
            key = f"python-{index}-" + re.sub(r"[-_.]+", "-", name.lower()) + "-" + version
            hashed = {}
            licenses = []
            missing = []
            for file in dist.files or ():
                path = Path(str(dist.locate_file(file)))
                if path.suffix == ".pyc":
                    continue
                if not path.is_file():
                    missing.append(str(file))
                    continue
                hashed[str(file)] = sha(path)
                if re.search(r"(^|/)(licen[cs]e[^/]*|copying[^/]*|notice[^/]*)$", str(file), re.IGNORECASE):
                    safe_parts = [part if part not in {"/", ".."} else "_parent" for part in Path(str(file)).parts]
                    out = notices / key / Path(*safe_parts)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, out)
                    licenses.append({"path": str(out.relative_to(notices)), "sha256": sha(out)})
            classifiers = [v for v in dist.metadata.get_all("Classifier", []) if v.startswith("License ::")]
            declared = dist.metadata["License-Expression"] or "; ".join(classifiers) or dist.metadata["License"] or "UNKNOWN"
            components.append({"type": "library", "bom-ref": key, "name": name, "version": version,
                               "purl": f"pkg:pypi/{quote(re.sub(r'[-_.]+', '-', name.lower()))}@{quote(version)}",
                               "licenses": [{"license": {"name": declared[:512]}}],
                               "properties": [{"name": "cosmos:license-basis", "value": "Installed metadata plus retained files; not legal clearance"},
                                              {"name": "cosmos:installed-tree-sha256", "value": hashlib.sha256(canonical(hashed)).hexdigest()}]})
            entries[key] = {"environment": str(location), "files_sha256": hashed, "missing_record_files": missing,
                            "license_files": licenses, "declared_license": declared[:512], "requires_dist": dist.metadata.get_all("Requires-Dist", []),
                            "artifact_basis": "Actual installed files; original wheel archive is not asserted", "redistribution_approved": False}
    return components, entries


def save_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as output:
        output.write(json.dumps(value, indent=2) + "\n")
