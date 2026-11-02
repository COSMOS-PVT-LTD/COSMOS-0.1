"""Bundle entrypoint: exact checked local sources and external Python only."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import platform
import sys
from pathlib import Path


def main() -> None:
    resources = Path(__file__).resolve().parent
    value = json.loads((resources / "preview-manifest.json").read_text())
    if value.get("profile") != "local-preview" or value.get("standalone") is not False:
        raise SystemExit("Invalid local preview manifest; no production profile available")
    if platform.system() != "Darwin" or platform.machine() != "arm64" or value.get("platform") != "Darwin-arm64":
        raise SystemExit("This preview has only a local macOS arm64 support claim")
    if hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() != value.get("external_python_sha256"):
        raise SystemExit("External Python binary changed; rebuild and reverify the preview")
    root = Path(value["source_root"])
    for name, expected in value["source_files"].items():
        path = root / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit("Preview source changed/missing: " + name + "; rebuild and reverify rather than silently launching drifted code")
    parser = argparse.ArgumentParser(description="COSMOS private local preview; external runtime, no production acceptance")
    parser.add_argument("--root", type=Path, default=Path.home() / "Library/Application Support/COSMOS/ReleasePreview")
    parser.add_argument("--port", type=int, default=8840)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--modern", action="store_true", help="Explicit modern workbench preview; flags default off")
    parser.add_argument("--native-runtime", type=Path, help="Separately qualified existing local runtime; no native redistribution")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise SystemExit("Preview requires an unprivileged valid port")
    os.environ["COSMOS_RELEASE_PROFILE"] = "local-preview"
    flags = ("COSMOS_NEW_SHELL", "COSMOS_NGG", "COSMOS_NEW_SIM_UI", "COSMOS_NEW_VV_UI", "COSMOS_NEW_KNOWLEDGE_REPORTS_UI")
    for flag in flags:
        os.environ[flag] = "1" if args.modern else "0"
    if args.native_runtime:
        if not args.modern or not args.native_runtime.is_absolute():
            raise SystemExit("Native preview requires --modern and an explicit absolute qualified manifest")
        os.environ["COSMOS_NGG_RUNTIME_CONFIG"] = str(args.native_runtime)
    else:
        for flag in ("COSMOS_NGG", "COSMOS_NEW_SIM_UI", "COSMOS_NEW_VV_UI"):
            os.environ[flag] = "0"
        os.environ.pop("COSMOS_NGG_RUNTIME_CONFIG", None)
    # Ignore ambient PYTHONPATH for launch; dependencies must be in the selected environment.
    sys.path = [str(root), *[p for p in sys.path if p != ""]]
    os.chdir(root)
    # Fixed entrypoint, not an input-controlled import or a scientific fallback.
    application = importlib.import_module("gui.application")
    application.launch_desktop_application(root=args.root, host="127.0.0.1", port=args.port, headless=args.headless)


if __name__ == "__main__":
    main()
