"""Retain reproducible payload and local signing evidence without distribution claims."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from infrastructure.release.inventory import canonical, contract_registry, sha, source_files, verify_registry


def save(name, value):
    with (HERE / name).open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def tree(app):
    return {str(p.relative_to(app)): sha(p) for p in sorted(app.rglob("*")) if p.is_file()}


def main():
    app = ROOT / "dist/P12-release-preview/COSMOS 0.1 Release Preview.app"
    copy = ROOT / "dist/P12-release-preview-reproduction/COSMOS 0.1 Release Preview.app"
    unsigned = tree(app)
    assert unsigned == tree(copy)
    resources = app / "Contents/Resources"
    manifest = json.loads((resources / "preview-manifest.json").read_text())
    assert manifest["source_files"] == source_files(ROOT)
    assert sha(Path(manifest["external_python"])) == manifest["external_python_sha256"]
    registry = json.loads((resources / "frozen-contract-registry.json").read_text())
    verify_registry(ROOT, registry)
    assert registry == contract_registry(ROOT)
    save("frozen-contract-registry.json", registry)
    save("package-source-manifest.json", manifest)
    save("unsigned-payload.json", {"pass": True, "app": str(app), "reproduction": str(copy), "files": unsigned,
                                  "identical_unsigned_bytes": True, "scope": "Same absolute source/Python paths and source bytes on this Mac"})
    for name in ("package-build-final.log", "package-reproduction-final.log"):
        assert (HERE / name).is_file()
    commands = [
        ("codesign-adhoc.log", ["/usr/bin/codesign", "--force", "--sign", "-", "--timestamp=none", str(app)]),
        ("codesign-verify.log", ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app)]),
        ("codesign-display.log", ["/usr/bin/codesign", "--display", "--verbose=4", str(app)]),
        ("gatekeeper-assessment.log", ["/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose=4", str(app)]),
    ]
    results = []
    for name, command in commands:
        process = subprocess.run(command, capture_output=True, text=True)
        with (HERE / name).open("x") as handle:
            handle.write(process.stdout + process.stderr)
        results.append({"command": command, "exit_code": process.returncode, "log": name})
    assert results[0]["exit_code"] == results[1]["exit_code"] == results[2]["exit_code"] == 0
    # Do not equate ad-hoc checksum integrity with trusted release identity.
    signing = {"integrity_verification": True, "identity": "ad-hoc", "developer_id": False,
               "notarized": False, "production_distribution_approved": False, "commands": results}
    save("package-integrity.json", {"pass": True, "app": str(app), "source_files_verified": len(manifest["source_files"]),
                                    "external_runtime": True, "external_python_sha256": manifest["external_python_sha256"],
                                    "files": tree(app), "signing": signing})
    print(json.dumps({"unsigned_reproduction": True, "ad_hoc_integrity": True, "developer_id": False, "notarized": False,
                      "source_files": len(manifest["source_files"]), "gatekeeper_exit": results[-1]["exit_code"]}))


if __name__ == "__main__":
    main()
