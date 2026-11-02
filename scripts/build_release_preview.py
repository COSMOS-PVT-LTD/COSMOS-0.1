"""Build a new checksum-pinned source-linked Mac preview; never overwrite an app."""
from __future__ import annotations

import argparse
import json
import platform
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.release.inventory import (
    contract_registry,
    save_new,
    sha,
    source_files,
)


def build(root: Path, output: Path, python: Path) -> Path:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("Only this macOS arm64 local source preview has a supported build claim")
    if output.exists() or output.is_symlink() or not python.is_file():
        raise ValueError("Provide a new output path and the explicit existing Python runtime")
    app = output / "COSMOS 0.1 Release Preview.app"
    resources = app / "Contents/Resources"
    executable = app / "Contents/MacOS/cosmos-launcher"
    resources.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    manifest = {"schema_version": "p12-local-preview-v1", "profile": "local-preview", "standalone": False,
                "source_root": str(root), "external_python": str(python), "external_python_sha256": sha(python),
                "platform": "Darwin-arm64", "source_files": source_files(root),
                "native_libraries_distributed": False, "default_flags_enabled": False, "production_handoff": False,
                "limits": "Private source-linked development preview; not Developer ID signed/notarized, portable or a distributable native runtime"}
    save_new(resources / "preview-manifest.json", manifest)
    save_new(resources / "frozen-contract-registry.json", contract_registry(root))
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(root / name, resources / name)
    shutil.copyfile(root / "infrastructure/release/launch_preview.py", resources / "launch_preview.py")
    icon = root / "gui/assets/cosmos_logo.png"
    if icon.is_file():
        shutil.copyfile(icon, resources / "cosmos_logo.png")
    with executable.open("x") as handle:
        handle.write('#!/bin/sh\nset -eu\ncosmos_resources="$(CDPATH= cd -- "$(dirname -- "$0")/../Resources" && pwd)"\n')
        handle.write("unset PYTHONPATH\nexec " + shlex.quote(str(python)) + ' "$cosmos_resources/launch_preview.py" "$@"\n')
    executable.chmod(0o755)
    with (app / "Contents/Info.plist").open("xb") as handle:
        plistlib.dump({"CFBundleExecutable": "cosmos-launcher", "CFBundleIdentifier": "com.cosmos.engineering.preview",
                      "CFBundleName": "COSMOS 0.1 Release Preview", "CFBundleDisplayName": "COSMOS 0.1 Release Preview",
                      "CFBundlePackageType": "APPL", "CFBundleShortVersionString": "0.1.0", "CFBundleVersion": "0.1.0",
                      "LSMinimumSystemVersion": "12.0", "NSHighResolutionCapable": True}, handle, sort_keys=True)
    subprocess.run(["/usr/bin/plutil", "-lint", str(app / "Contents/Info.plist")], check=True, capture_output=True)
    save_new(output / "build-receipt.json", {"profile": "local-preview", "os": platform.system(), "architecture": platform.machine(),
                                             "python": str(python), "signing": "unsigned", "notarized": False,
                                             "standalone": False, "distribution_approved": False, "source_files": len(manifest["source_files"]),
                                             "reproducible_payload": "Identical source root/bytes and Python path yield identical unsigned Contents bytes"})
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    app = build(root, args.output.absolute(), args.python.absolute())
    print(json.dumps({"app": str(app), "profile": "local-preview", "standalone": False, "production_release": False}))


if __name__ == "__main__":
    main()
