"""Seal a task-built development app with explicit bounded GD delivery evidence."""

import argparse
import hashlib
import json
import plistlib
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def report(path):
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    counts = {
        key: sum(int(s.get(key, 0)) for s in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    if not counts["tests"] or any(counts[k] for k in ("failures", "errors", "skipped")):
        raise ValueError("Passing executed non-skipped report required: " + str(path))
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        **counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    root = args.app / "Contents/Resources/app"
    identity = plistlib.loads((args.app / "Contents/Info.plist").read_bytes())[
        "CFBundleIdentifier"
    ]
    if (
        identity != "com.cosmos.engineering.guided-development"
        or args.app.is_symlink()
        or not (args.app / "Contents/Resources/desktop-stage.json").is_file()
        or list(root.glob("desktop-verified*.json"))
    ):
        raise ValueError(
            "Only the new, not-yet-sealed guided development app can be finalized"
        )
    source = [
        report(repo / "output" / n)
        for n in (
            "guided-development-ready-2026-10-29.xml",
            "guided-compatibility-2026-10-29.xml",
            "guided-cad-integration-2026-10-29.xml",
        )
    ]
    bundled = [
        report(root / "desktop-qualification" / (name + ".xml"))
        for name in (
            "native-components",
            "component-http",
            "driving-constraints",
            "pico-unit",
            "pico-native",
            "pico-http",
            "pico-preview",
        )
    ]
    bundled.append(report(repo / "output/guided-bundled-source-ready-2026-10-29.xml"))
    ui = json.loads((args.evidence / "native-menu-smoke.json").read_bytes())
    guided = json.loads((args.evidence / "native-guided-ready.json").read_bytes())
    audit = json.loads((args.evidence / "runtime-audit-ready.json").read_bytes())
    if not (
        ui.get("pass")
        and len(ui.get("routes", [])) == 8
        and ui.get("webgl2")
        and ui.get("native_backend") == "webview.platforms.cocoa"
        and guided.get("pass")
        and guided.get("history_reopened")
        and guided.get("expert_design_id")
        and audit.get("mach_o_files_checked", 0) > 1000
        and not audit.get("external_non_system_load_dependencies")
    ):
        raise ValueError("Actual native/menu/guided/closure evidence is required")
    # Confirm the executable entrypoint admits the NEW path-bound profiles.
    checked = subprocess.run(
        [str(args.app / "Contents/MacOS/cosmos-launcher"), "--check"],
        check=True,
        capture_output=True,
        text=True,
    )
    imported = json.loads(checked.stdout.strip().splitlines()[-1])
    if (
        imported.get("occt_profile") != "PASS"
        or imported.get("picogk_profile") != "PASS"
        or imported.get("user_data_opened") is not False
    ):
        raise ValueError("New bundle admission check failed")
    shortcut = Path.home() / "Desktop/COSMOS Guided Development.app"
    if shortcut.exists() or shortcut.is_symlink():
        raise ValueError(
            "New shortcut target required; existing icons are not overwritten"
        )
    status = {
        "schema": "cosmos.guided-development-delivery.v1",
        "status": "GUIDED_PRELIMINARY_DEVELOPMENT_SLICE_VERIFIED",
        "app": str(args.app),
        "desktop_shortcut": str(shortcut),
        "existing_app_replaced": False,
        "user_data_migrated": False,
        "user_data_bundled": False,
        "external_python_required": False,
        "source_tests": source,
        "source_python_passed": sum(r["tests"] for r in source),
        "bundled_tests": bundled,
        "bundled_python_passed": sum(r["tests"] for r in bundled),
        "test_counts_note": "Source and bundled environments overlap intentionally and are reported separately, not added as unique coverage.",
        "native_menu_routes": 8,
        "native_guided_workflow": "PASS",
        "webgl2": True,
        "phase_status": {
            "GD-00": "INITIAL_ROCKET_INPUT_INVENTORY_IMPLEMENTED",
            "GD-01": "BOUNDED_PROFILE_RESOLVER_IMPLEMENTED",
            "GD-02": "IDEAL_METHALOX_TARGET_SIZING_IMPLEMENTED",
            "GD-03": "PARTIAL_COLD_INJECTOR_AND_PRESSURE_SCREENING",
            "GD-04": "INITIAL_GUIDED_UI_IMPLEMENTED",
            "GD-05": "RETAINED_PROJECT_CAD_ACCESS_IMPLEMENTED",
            "GD-06": "AUTOMATED_SLICE_VERIFIED_HUMAN_OBSERVATIONS_PENDING",
        },
        "remaining": [
            "Broader sourced inlet/property packages and propellant/cycle coverage",
            "Matched cooling/material/operating-closure assistance and constrained candidate optimization",
            "Complete Expert-to-Guided advanced-override reconciliation",
            "Genuine human usability observations and acceptance",
        ],
        "full_engine_generation": "ON_HOLD",
        "r08": "ON_HOLD",
        "physical_validation": "NOT_PERFORMED",
        "developer_id_signed": False,
        "notarized": False,
        "public_distribution_approved": False,
    }
    with (root / "desktop-verified-guided.json").open("x") as stream:
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
    shortcut.symlink_to(args.app, target_is_directory=True)
    status["local_ad_hoc_signature_verified"] = True
    with (args.evidence / "STATUS.json").open("x") as stream:
        json.dump(status, stream, indent=2)
    print(
        json.dumps(
            {
                "status": status["status"],
                "source_python_passed": status["source_python_passed"],
                "bundled_python_passed": status["bundled_python_passed"],
                "desktop_shortcut": str(shortcut),
            }
        )
    )


if __name__ == "__main__":
    main()
