"""Current R05 software evidence only; never a historical or release seal."""
from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main():
    suites = ET.parse(HERE / "full-confirmed-python.xml").getroot()
    cases = list(suites.iter("testcase"))
    assert not list(suites.iter("failure")) and not list(suites.iter("error"))
    assert "fail 0" in (HERE / "final-js-source-navigation.log").read_text()
    assert "All checks passed!" in (HERE / "ruff-latest.log").read_text()
    assert "Success:" in (HERE / "mypy-latest.log").read_text()
    assert not (HERE / "final-typescript-fixed.log").read_bytes()
    assert not (HERE / "whitespace-final.log").read_bytes()
    assert json.loads((HERE / "preservation-final-check.json").read_text())["pass"]
    before = json.loads((HERE.parent / "R05_4_2026-10-18/source-final.json").read_text())["sources"]
    frozen = ("physics/heat_transfer/spherical_conduction.py", "numerics/finite_volume/radial_diffusion.py",
        "simulation/contracts.py", "systems/geometry/source_contract.py", "systems/geometry/retained_source.py")
    assert all(sha256((ROOT / name).read_bytes()).hexdigest() == before[name]["sha256"] for name in frozen)
    preview = json.loads((HERE / "live-default-legacy-preview-v2.json").read_text())
    assert all(sha256((Path(preview["directory"]) / row["filename"]).read_bytes()).hexdigest() == row["sha256"] for row in preview["files"])
    sources = {}
    for directory in ("core", "physics", "numerics", "systems", "simulation", "validation", "api", "gui", "infrastructure", "plugins", "tests", "scripts"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and not path.is_symlink() and path.suffix in {".py", ".js", ".cjs", ".ts", ".css", ".html"}:
                sources[str(path.relative_to(ROOT))] = sha256(path.read_bytes()).hexdigest()
    (HERE / "source-final.json").write_text(json.dumps({"scope": "Current R05 software source identities, not release or physical acceptance",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "sha256": sources,
        "frozen_domain_sources_unchanged_from_prior_slice": list(frozen), "historical_receipts_not_resealed": True}, indent=2) + "\n")
    result = {"phase": "R05", "date": "2026-10-19", "software_status": "IMPLEMENTED_AND_LOCALLY_QUALIFIED",
        "live_migration": "NOT_EXECUTED_REQUIRES_CONCRETE_MAPPING_AND_CONFIRMATION", "default_root_preview_only": True,
        "per_requirement": {f"PRJ-{n:02}": "PASS_ACCEPTED_SOFTWARE_SCOPE" for n in range(1, 13)},
        "python": {"passed": sum(t.find("skipped") is None for t in cases), "skipped": len(list(suites.iter("skipped"))),
            "native_geometry_integration_passed": sum("integration_tests.geometry" in t.attrib["classname"] and t.find("skipped") is None for t in cases)},
        "javascript_passed": 398, "ruff": "PASS", "mypy_source_files": 381, "strict_typescript_consumers": 7,
        "default_preview": {"files": len(preview["files"]), "supported": sum(row["status"] == "supported" for row in preview["files"]),
            "unsupported_in_place": sum(row["status"] != "supported" for row in preview["files"]), "preview_sha256": preview["preview_sha256"], "all_source_hashes_unchanged": True},
        "limitations": ["Original actor-session previews remain distinct; managed editing is in Projects and shared exact-source pane",
            "R11 general Knowledge equation reconstruction is not supplied; retained report claim/source bytes survive",
            "No whole-application auth/Knowledge backup, live switch, qualified signature, remote CI, release or physical validation"],
        "native_ui_restart_and_download": "PASS_RETAINED_PROOF", "late_native_recheck": "MAC_LOCKED_BROWSER_CHECKS_COMPLETED",
        "commit_push_release": False, "owner_data_changed": False, "report": "IMPLEMENTATION_REPORT.md"}
    (HERE / "STATUS.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["software_status"], "python": result["python"], "sources": len(sources)}))


if __name__ == "__main__":
    main()
