"""Build a NEW private Mac application, embedding runtime/source without user data.

Does not issue software qualifications, erase history, migrate roots or build an
engine. Native manifests must be qualified separately inside this exact bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
from pathlib import Path

PACKAGES = (
    "api",
    "core",
    "knowledge",
    "physics",
    "numerics",
    "systems",
    "simulation",
    "validation",
    "gui",
    "infrastructure",
    "plugins",
    "databases",
    "tests",
)
MAGIC = {
    b"\xcf\xfa\xed\xfe",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
}


def run(args):
    return subprocess.run(
        [str(a) for a in args], capture_output=True, text=True, check=True
    ).stdout


def files(root):
    return [
        p
        for p in root.rglob("*")
        if p.is_file()
        and not {"__pycache__", ".git", ".pytest_cache", "node_modules"}.intersection(
            p.parts
        )
        and p.suffix not in {".pyc", ".pyo", ".a"}
    ]


class Copier:
    def __init__(self):
        self.origins = {}

    def copy(self, source, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        self.origins[target] = source.resolve()

    def tree(self, source, target, *, stdlib=False):
        for file in files(source):
            relative = file.relative_to(source)
            if stdlib and (
                "site-packages" in relative.parts
                or "test" in relative.parts
                or relative.name.startswith(("_test", "_tkinter"))
            ):
                continue
            self.copy(file, target / relative)

    def relocate(self, bundle_root, framework):
        """Rebase only copied Mach-O dependencies; originals are never modified."""
        moved = {str(source): target for target, source in self.origins.items()}
        queue = list(self.origins)
        index = 0
        changed = []
        while index < len(queue):
            target = queue[index]
            index += 1
            with target.open("rb") as stream:
                if stream.read(4) not in MAGIC:
                    continue
            source = self.origins[target]
            edits = []
            seen = set()
            identities = {
                line.strip()
                for line in run(["/usr/bin/otool", "-D", target]).splitlines()[1:]
                if line.strip() and not line.rstrip().endswith(":")
            }
            for match in re.finditer(
                r"^\s+(/[^\n]+?) \(compatibility",
                run(["/usr/bin/otool", "-L", target]),
                re.MULTILINE,
            ):
                dependency = match.group(1)
                if dependency in seen:
                    continue
                seen.add(dependency)
                if dependency in identities:
                    edits.extend(["-id", "@loader_path/" + target.name])
                    continue
                if dependency.startswith(("/usr/lib/", "/System/Library/")):
                    continue
                original = Path(dependency).resolve()
                destination = moved.get(str(original))
                if destination is None:
                    if not original.is_file():
                        raise ValueError("Unresolved native dependency: " + dependency)
                    suffix = hashlib.sha256(str(original).encode()).hexdigest()[:12]
                    destination = (
                        bundle_root
                        / ".runtime-python/dependencies"
                        / suffix
                        / original.name
                    )
                    self.copy(original, destination)
                    moved[str(original)] = destination
                    queue.append(destination)
                replacement = "@loader_path/" + os.path.relpath(
                    destination, target.parent
                )
                if original == source:
                    edits.extend(["-id", "@loader_path/" + target.name])
                else:
                    edits.extend(["-change", dependency, replacement])
            if edits:
                # Original signatures become invalid after install-name changes.
                run(["/usr/bin/install_name_tool", *edits, target])
                run(["/usr/bin/codesign", "--force", "--sign", "-", target])
                changed.append(str(target.relative_to(bundle_root)))
        return changed


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def build(
    repo,
    app,
    python,
    cad,
    runtime,
    workspaces,
    *,
    resume=False,
    bundle_id="com.cosmos.engineering.desktop",
    display_name="COSMOS Desktop",
):
    if (
        re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]{2,120}", bundle_id) is None
        or not 1 <= len(display_name) <= 80
        or any(c in display_name for c in "\0/\n")
    ):
        raise ValueError("Bounded explicit application identity required")
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError(
            "This private package is scoped to this Mac's Darwin arm64 runtime"
        )
    marker = app / "Contents/Resources/desktop-stage.json"
    permitted_stage = (
        resume
        and marker.is_file()
        and json.loads(marker.read_text())
        == {"schema": "cosmos.desktop-stage.v1", "source_root": str(repo)}
        and not (app / "Contents/Info.plist").exists()
    )
    if (
        not app.is_absolute()
        or (app.exists() and not permitted_stage)
        or app.is_symlink()
        or app.suffix != ".app"
        or not app.parent.is_dir()
    ):
        raise ValueError(
            "Choose a NEW absolute .app path with an existing parent; nothing is overwritten"
        )
    for root in (python, cad, runtime):
        if not root.is_dir():
            raise ValueError("Missing explicit existing runtime: " + str(root))
    for workspace in workspaces:
        if not (Path(workspace["root"]) / "auth/users.sqlite").is_file():
            raise ValueError(
                "Existing workspace unavailable; no data will be initialized"
            )
    if shutil.disk_usage(app.parent).free < 3 * 1024**3:
        raise ValueError(
            "At least 3GiB free required for desktop packaging; no files removed"
        )
    base = Path(
        run([python / "bin/python", "-c", "import sys;print(sys.base_prefix)"]).strip()
    )
    version = "python3.11"
    source = app / "Contents/Resources/app"
    source.mkdir(parents=True, exist_ok=permitted_stage)
    if not permitted_stage:
        save(marker, {"schema": "cosmos.desktop-stage.v1", "source_root": str(repo)})
    copier = Copier()
    for package in PACKAGES:
        copier.tree(repo / package, source / package)
    for name in ("main.py", "LICENSE", "NOTICE"):
        copier.copy(repo / name, source / name)
    for file in (repo / "scripts").glob("*"):
        if file.is_file() and file.suffix in {".py", ".c"}:
            copier.copy(file, source / "scripts" / file.name)
    embedded = source / ".runtime-python"
    certificate_dir = embedded / "certs"
    certificate_dir.mkdir(parents=True, exist_ok=True)
    # Only public system root certificates, never user identities/private keys.
    roots = run(
        [
            "/usr/bin/security",
            "find-certificate",
            "-a",
            "-p",
            "/System/Library/Keychains/SystemRootCertificates.keychain",
        ]
    )
    if "-----BEGIN CERTIFICATE-----" not in roots:
        raise ValueError(
            "macOS system trust roots could not be bundled; TLS verification is never disabled"
        )
    (certificate_dir / "system-roots.pem").write_text(roots)
    # python.org's bin/python3.11 is a framework-app spawning stub, not the
    # interpreter. Embed the actual executable to avoid an external Python.app.
    copier.copy(
        base / "Resources/Python.app/Contents/MacOS/Python", embedded / "bin/python3.11"
    )
    copier.copy(base / "Python", embedded / "Python")
    copier.tree(base / "lib" / version, embedded / "lib" / version, stdlib=True)
    copier.tree(
        python / "lib" / version / "site-packages",
        embedded / "lib" / version / "site-packages",
    )
    copier.tree(
        cad / "lib" / version / "site-packages",
        source / ".venv-cad-inspection/lib" / version / "site-packages",
    )
    for library in (cad / "lib").glob("*.dylib"):
        copier.copy(library, source / ".venv-cad-inspection/lib" / library.name)
    # Compatibility location is retained for unchanged qualified worker policies,
    # but it contains a bundled-runtime launcher, not an external virtualenv.
    worker_python = source / ".venv-cad-inspection/bin/python"
    worker_python.parent.mkdir(parents=True, exist_ok=permitted_stage)
    with worker_python.open("w" if permitted_stage else "x") as stream:
        stream.write(
            '#!/bin/sh\nset -eu\ncosmos_root="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"\n'
        )
        stream.write(
            'export PYTHONHOME="$cosmos_root/.runtime-python"\nexport PYTHONNOUSERSITE=1\nexport PYTHONDONTWRITEBYTECODE=1\nexport PYTHONPATH="$cosmos_root/.venv-cad-inspection/lib/python3.11/site-packages:$cosmos_root"\nexec "$cosmos_root/.runtime-python/bin/python3.11" -s -B "$@"\n'
        )
    worker_python.chmod(0o755)
    (worker_python.parent.parent / "pyvenv.cfg").write_text(
        "# COSMOS bundled CAD worker closure; no external virtualenv\ninclude-system-site-packages = false\nversion = 3.11.4\n"
    )
    private = source / ".runtime-picogk/2026-10-24-v1"
    for folder in ("worker", "dotnet9/shared", "dotnet9/host"):
        copier.tree(runtime / folder, private / folder)
    copier.copy(runtime / "dotnet9/dotnet", private / "dotnet9/dotnet")
    copier.copy(
        runtime / "restoration-provenance.json", private / "restoration-provenance.json"
    )
    # Compact generator remains a separately unqualified research worker.
    compact = repo / "output/compact-engine-software-2026-10-28/worker"
    if compact.is_dir():
        copier.tree(compact, source / ".runtime-compact/worker")
    print(
        "Copied sources and runtime closures; rebasing private native dependencies",
        flush=True,
    )
    changes = copier.relocate(source, base)
    executable = app / "Contents/MacOS/cosmos-launcher"
    executable.parent.mkdir(parents=True)
    run(
        [
            "/usr/bin/clang",
            "-Os",
            "-arch",
            "arm64",
            repo / "scripts/desktop_launcher.c",
            "-o",
            executable,
        ]
    )
    icon = repo / "dist/COSMOS 0.1.app/Contents/Resources/cosmos_logo.icns"
    if icon.is_file():
        shutil.copy2(icon, app / "Contents/Resources/cosmos_logo.icns")
    with (app / "Contents/Info.plist").open("xb") as stream:
        plistlib.dump(
            {
                "CFBundleExecutable": "cosmos-launcher",
                "CFBundleIdentifier": bundle_id,
                "CFBundleName": display_name,
                "CFBundleDisplayName": display_name,
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": "0.1.0",
                "CFBundleVersion": "2026.10.28",
                "LSMinimumSystemVersion": "12.0",
                "NSHighResolutionCapable": True,
                "CFBundleIconFile": "cosmos_logo",
                "NSPrincipalClass": "NSApplication",
            },
            stream,
        )
    save(
        source / "desktop-profile.json",
        {
            "schema": "cosmos.desktop-profile.v1",
            "workspaces": workspaces,
            "runtimes": {
                "COSMOS_NGG_RUNTIME_CONFIG": "desktop-qualification/occt/runtime.json",
                "COSMOS_PICOGK_COMPONENT_CONFIG": "desktop-qualification/pico/runtime.json",
            },
        },
    )
    save(
        source / "desktop-build.json",
        {
            "schema": "cosmos.desktop-build.v1",
            "standalone_runtime": True,
            "runtime_dependency": "macOS system frameworks only",
            "platform": "Darwin-arm64",
            "user_data_bundled": False,
            "historical_profiles_modified": False,
            "native_relocations": changes,
            "qualification": "PENDING_NEW_EXECUTED_BUNDLE_TESTS",
            "distribution_approved": False,
            "notarized": False,
            "physical_validation": "NOT_PERFORMED",
            "r08": "ON_HOLD",
        },
    )
    print(
        json.dumps(
            {
                "app": str(app),
                "source": str(source),
                "qualification": "PENDING",
                "cad_python": str(worker_python),
                "helper_command": "PYTHONHOME="
                + shlex.quote(str(embedded))
                + " "
                + shlex.quote(str(embedded / "bin/python3.11")),
            }
        )
    )
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--python-env", type=Path, required=True)
    parser.add_argument("--cad-env", type=Path, required=True)
    parser.add_argument("--pico-runtime", type=Path, required=True)
    parser.add_argument("--bundle-id", default="com.cosmos.engineering.desktop")
    parser.add_argument("--display-name", default="COSMOS Desktop")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume only a marked unfinished app created by this builder",
    )
    parser.add_argument(
        "--workspace-profile",
        type=Path,
        required=True,
        help="Explicit array of existing key/label/root registrations; not account data",
    )
    args = parser.parse_args()
    build(
        Path(__file__).resolve().parents[1],
        args.app,
        args.python_env,
        args.cad_env,
        args.pico_runtime,
        json.loads(args.workspace_profile.read_text()),
        resume=args.resume,
        bundle_id=args.bundle_id,
        display_name=args.display_name,
    )


if __name__ == "__main__":
    main()
