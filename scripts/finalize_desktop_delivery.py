"""Seal a locally tested package and retain a derived, explicit delivery receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--ui-report", type=Path)
    parser.add_argument(
        "--revision",
        default="",
        help="Append a new named delivery receipt without overwriting earlier evidence",
    )
    args = parser.parse_args()
    if args.revision and re.fullmatch(r"[a-z0-9-]{1,32}", args.revision) is None:
        raise ValueError("Bounded lower-case receipt revision required")
    suffix = "-" + args.revision if args.revision else ""
    repo = Path(__file__).resolve().parents[1]
    root = args.app / "Contents/Resources/app"
    source_reports = [
        repo / ("output/desktop-" + name + "-2026-10-28.xml")
        for name in (
            "final-lifecycle",
            "integration",
            "compatibility",
            "cea",
            "compact-native",
        )
    ]
    native_names = (
        "native-components",
        "component-http",
        "driving-constraints",
        "pico-unit",
        "pico-native",
        "pico-http",
        "pico-preview",
    )
    reports = [
        *(root / "desktop-qualification" / (name + ".xml") for name in native_names),
        *source_reports,
    ]
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    entries = []
    for path in reports:
        xml = ET.parse(path).getroot()
        counts = {
            key: sum(int(suite.get(key, 0)) for suite in xml.iter("testsuite"))
            for key in totals
        }
        for key in totals:
            totals[key] += counts[key]
        entries.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **counts,
            }
        )
    if totals["tests"] != 267 or any(
        totals[k] for k in ("failures", "errors", "skipped")
    ):
        raise ValueError(
            "Expected exact executed passing delivery scope, without skipped native tests"
        )
    ui_path = args.ui_report or args.evidence / "native-smoke-final.json"
    ui = json.loads(ui_path.read_text())
    if (
        not ui.get("pass")
        or ui.get("native_backend") != "webview.platforms.cocoa"
        or len(ui["routes"]) != 8
        or not ui.get("webgl2")
    ):
        raise ValueError("Actual packaged native UI evidence required")
    status = {
        "schema": "cosmos.desktop-delivery.v1",
        "status": "LOCAL_DESKTOP_DELIVERY_VERIFIED",
        "app": str(args.app),
        "desktop_shortcut": str(Path.home() / "Desktop/COSMOS Desktop.app"),
        "standalone_runtime": True,
        "external_python_or_venv_required": False,
        "external_development_server_required": False,
        "user_data_migrated": False,
        "tests": totals,
        "native_routes": len(ui["routes"]),
        "native_backend": ui["native_backend"],
        "native_ui_report": str(ui_path),
        "native_ui_sha256": hashlib.sha256(ui_path.read_bytes()).hexdigest(),
        "webgl2": ui["webgl2"],
        "reports": entries,
        "physical_validation": "NOT_PERFORMED",
        "full_engine_regeneration": "ON_HOLD",
        "r08": "ON_HOLD",
        "developer_id_signed": False,
        "notarized": False,
        "public_distribution_approved": False,
    }
    receipt = root / ("desktop-verified" + suffix + ".json")
    with receipt.open("x") as stream:
        json.dump(status, stream, indent=2)
    subprocess.run(
        [
            "/usr/bin/codesign",
            "--force",
            "--sign",
            "-",
            "--timestamp=none",
            str(args.app),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["/usr/bin/codesign", "--verify", "--strict", "--verbose=2", str(args.app)],
        check=True,
        capture_output=True,
    )
    status["local_ad_hoc_signature_verified"] = True
    status["launcher_sha256"] = hashlib.sha256(
        (args.app / "Contents/MacOS/cosmos-launcher").read_bytes()
    ).hexdigest()
    with (args.evidence / ("STATUS" + suffix + ".json")).open("x") as stream:
        json.dump(status, stream, indent=2)
    print(
        json.dumps(
            {
                "status": status["status"],
                "tests_passed": totals["tests"],
                "native_routes": len(ui["routes"]),
                "local_signature": "VERIFIED",
                "r08": "ON_HOLD",
            }
        )
    )


if __name__ == "__main__":
    main()
