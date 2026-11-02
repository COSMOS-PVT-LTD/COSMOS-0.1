"""Collect a local environment SBOM and explicit license/distribution gaps."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import sysconfig
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.release.inventory import (
    canonical,
    contract_registry,
    python_inventory,
    save_new,
    sha,
)


def collect(output: Path, extra: list[Path], runtime: Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    output.mkdir(parents=True, exist_ok=False)
    components, installed = python_inventory([Path(sysconfig.get_paths()["purelib"]), *extra], output / "notices/python")
    predecessor = root / "docs/implementation/evidence"
    p02 = json.loads((predecessor / "P02_2026-10-08/dependency_manifest.json").read_text())
    native = json.loads(runtime.read_text())
    native_files = {}
    for name, expected in native["sha256"].items():
        path = Path(name)
        if sha(path) != expected:
            raise ValueError("Native inventory drift: " + name)
        native_files[name] = expected
        if path.suffix in {".dll", ".dylib"} or path.name == "dotnet":
            components.append({"type": "file", "bom-ref": "native-" + hashlib.sha256(name.encode()).hexdigest(), "name": path.name,
                               "hashes": [{"alg": "SHA-256", "content": expected}],
                               "properties": [{"name": "cosmos:scope", "value": "External qualified local runtime; not bundled or approved for redistribution"},
                                              {"name": "cosmos:source-path", "value": name}]})
    for item in p02["sourcePins"]:
        components.append({"type": "library", "bom-ref": "source-" + item["name"], "name": item["name"], "version": item["commit"],
                           "licenses": [{"license": {"name": item["licenseAtPin"]}}],
                           "properties": [{"name": "cosmos:scope", "value": "Pinned predecessor source evidence, not binary source-closure approval"}]})
    for item in p02["nugetPackages"]:
        components.append({"type": "library", "bom-ref": "nuget-" + item["id"], "name": item["id"], "version": item["version"],
                           "purl": "pkg:nuget/" + item["id"] + "@" + item["version"],
                           "properties": [{"name": "cosmos:scope", "value": "Observed predecessor managed/build closure, not redistributed"}]})
    locks = {}
    for name in ("P02_2026-10-08/worker/packages.lock.json", "P03_2026-10-08/tooling/package-lock.json"):
        path = predecessor / name
        locks[name] = sha(path)
    npm = json.loads((predecessor / "P03_2026-10-08/tooling/package-lock.json").read_text())
    for name, item in npm["packages"].items():
        if name and item.get("version"):
            components.append({"type": "library", "bom-ref": "npm-" + name, "name": name.removeprefix("node_modules/"), "version": item["version"],
                               "properties": [{"name": "cosmos:scope", "value": "Pinned browser-test tooling; not application runtime"},
                                              {"name": "cosmos:npm-integrity", "value": item.get("integrity", "UNAVAILABLE")}]})
    retained = {}
    for phase in ("P02_2026-10-08", "P07_2026-10-09"):
        for source in (predecessor / phase / "licenses").rglob("*"):
            if source.is_file() and not source.is_symlink():
                name = str(source.relative_to(predecessor))
                target = output / "notices/predecessor" / name
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
                retained[name] = sha(target)
    sbom = {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
            "metadata": {"component": {"type": "application", "name": "COSMOS 0.1 local release preview", "version": "0.1.0"},
                         "properties": [{"name": "cosmos:scope", "value": "Local installed Python, qualified external native, pinned managed/source and browser tooling inventory; not a distribution approval"},
                                        {"name": "cosmos:platform", "value": platform.platform()}]},
            "components": sorted(components, key=lambda c: c["bom-ref"])}
    # Retain official frozen schema bytes; resolve only this allowlisted local closure.
    schemas = {}
    schema_dir = output / "schema"; schema_dir.mkdir()
    for name in ("bom-1.5.schema.json", "spdx.schema.json", "jsf-0.82.schema.json"):
        url = "https://raw.githubusercontent.com/CycloneDX/specification/1.5/schema/" + name
        with urllib.request.urlopen(url, timeout=20) as response:
            raw = response.read(1024**2)
        with (schema_dir / name).open("xb") as handle:
            handle.write(raw)
        schemas[name] = json.loads(raw)
    from jsonschema import Draft7Validator
    from referencing import Registry, Resource
    resources = [("http://cyclonedx.org/schema/" + name, Resource.from_contents(value)) for name, value in schemas.items()]
    resources += [("https://cyclonedx.org/schema/" + name, Resource.from_contents(value)) for name, value in schemas.items()]
    registry = Registry().with_resources(resources)
    Draft7Validator(schemas["bom-1.5.schema.json"], registry=registry).validate(sbom)
    save_new(output / "sbom.cdx.json", sbom)
    save_new(output / "installed-file-integrity.json", installed)
    save_new(output / "frozen-contract-registry.json", contract_registry(root))
    missing = [key for key, value in installed.items() if not value["license_files"] or value["missing_record_files"]]
    gaps = {"distribution_approved": False, "python_metadata_or_notice_gaps": missing,
            "native_and_embedded_asset_gaps": p02["distributionBlockers"],
            "additional_release_limits": ["OCCT LGPL exception and Gmsh GPL proprietary distribution need qualified legal review; native bytes excluded from bundle",
                                          "PDFium/Skia/VTK/transitive binary source/notice closure is not inferred from top-level metadata",
                                          "OS system libraries and Python interpreter have not been redistributed or given a complete release closure",
                                          "Environment inventory has hashes, not an authoritative exact native vulnerability database or legal clearance"]}
    save_new(output / "license-gaps.json", gaps)
    summary = {"sbom_schema_valid": True, "components": len(components), "python_distributions": len(installed),
               "native_files_verified": len(native_files), "predecessor_notices_retained": len(retained),
               "notice_sha256": retained, "lock_sha256": locks,
               "schema_sha256": {name: sha(schema_dir / name) for name in schemas},
               "sbom_sha256": hashlib.sha256(canonical(sbom)).hexdigest(), "distribution_approved": False}
    save_new(output / "inventory-summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extra-python", type=Path, action="append", default=[])
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    summary = collect(args.output.absolute(), args.extra_python, args.runtime)
    print(json.dumps({key: summary[key] for key in ("sbom_schema_valid", "components", "python_distributions", "native_files_verified", "distribution_approved")}))


if __name__ == "__main__":
    main()
