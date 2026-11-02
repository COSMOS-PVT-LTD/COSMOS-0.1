"""Create a NEW R08 local software admission from executed unskipped evidence."""

import argparse
import importlib.metadata
import json
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from api.geometry_qualification import RUNTIME_SCHEMA, configuration
from systems.geometry.qualification import ROOT, methods

# These manufactured cases exercise the existing admitted component operations.
# This inventory does not claim all dimensions/assemblies are qualified.
FAMILIES = frozenset(
    {
        "profile.wall",
        "profile.solid",
        "cooling.axial_sector",
        "injector.showerhead",
        "injector.doublet",
        "injector.biprop_doublet",
        "injector.biprop_radial_doublet",
        "injector.triplet",
        "injector.coaxial",
        "injector.pintle",
        "manifold.dual_annular",
        "manifold.cooling_annular",
        "manifold.cooling_front_supply",
        "interface.bolted_flange",
        "interface.bolt_pattern",
        "interface.face_groove",
        "bolted-injector",
        "grooved-bolted-injector",
        "five-grooved-bolted-injector",
        "pipe.circular",
        "pipe.elbow",
        "placement.rigid",
    }
)


def family_campaigns(path):
    rows = []
    for prop in ET.parse(path).findall(
        ".//testcase/properties/property[@name='r08_family_campaign']"
    ):
        value = json.loads(prop.get("value"))
        policy = value["policy"]
        encoded = json.dumps(policy, sort_keys=True, allow_nan=False).encode()
        campaign = value["campaign"]
        if (
            value["kind"] not in FAMILIES
            or len(campaign) != 4
            or campaign[0]["voxel_resolution_m"] is not None
            or [c["voxel_resolution_m"] for c in campaign[1:]]
            != policy["refinement_resolutions_m"]
            or value["policy_sha256"] != sha256(encoded).hexdigest()
            or value["physical_validation"] != "NOT_PERFORMED"
            or not all(
                c["pass"] and all(p["pass"] for p in c["parts"]) for c in campaign
            )
        ):
            raise ValueError(
                "Complete passing source-bound four-row family evidence required"
            )
        rows.append(value["kind"])
    if len(rows) != len(FAMILIES) or set(rows) != FAMILIES:
        raise ValueError(
            "Exactly one executed campaign for every declared manufactured family required"
        )
    return sorted(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("unit", "native", "http", "families", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() or ROOT / "docs/implementation/evidence" not in out.parents:
        raise ValueError(
            "New repository evidence directory required; no historical reseal"
        )
    reports = {}
    for role, minimum in (("unit", 10), ("native", 1), ("http", 1), ("families", 22)):
        path = getattr(args, role).resolve()
        root = ET.parse(path).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        totals = {
            k: sum(int(s.get(k, "0")) for s in suites)
            for k in ("tests", "failures", "errors", "skipped")
        }
        if totals["tests"] < minimum or any(
            totals[k] for k in ("failures", "errors", "skipped")
        ):
            raise ValueError("Passing executed unskipped R08 evidence required")
        reports[role] = {
            **totals,
            "path": str(path),
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
    native = ET.parse(args.native).find(
        ".//testcase[@name='test_actual_r08_predeclaration_both_kernels_refinement_review_export_and_restart']/properties/property[@name='r08_real_campaign']"
    )
    if native is None:
        raise ValueError(
            "Actual two-kernel three-resolution R08 campaign property required; unrelated native reports do not qualify"
        )
    campaign = json.loads(native.get("value"))
    if (
        len(campaign.get("implicit_job_ids", [])) != 3
        or len(campaign.get("campaign", [])) != 4
        or not all(c["pass"] for c in campaign["campaign"])
    ):
        raise ValueError("Complete passing explicit refinement evidence required")
    qualified_families = family_campaigns(args.families)
    hashes = methods()
    python = ROOT / ".venv-release-p12/bin/python"
    files = [python.resolve(), python.parent.parent / "pyvenv.cfg"]
    distribution = importlib.metadata.distribution("numpy")
    numpy = Path(distribution.locate_file("numpy"))
    files.extend(
        p
        for p in numpy.rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".so", ".dylib"}
        and not {"tests", "test", "__pycache__"} & set(p.parts)
    )
    for p in files:
        if p.is_symlink():
            raise ValueError("Ambiguous runtime symlink")
        hashes[str(p)] = sha256(p.read_bytes()).hexdigest()
    proof = {
        "method_sources": methods(),
        "sha256": hashes,
        "reports": reports,
        "manufactured_family_cases": qualified_families,
        "physical_validation": "NOT_PERFORMED",
        "scope": "Local bounded sampled geometry software qualification; no genuine engine review or physical/manufacturing acceptance",
    }
    out.mkdir(parents=True)
    receipt = out / "software-receipt.json"
    with receipt.open("x") as f:
        json.dump(proof, f, indent=2)
    cfg = {
        "schema": RUNTIME_SCHEMA,
        "python": str(python),
        "sha256": hashes,
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt.read_bytes()).hexdigest(),
    }
    path = out / "runtime.json"
    with path.open("x") as f:
        json.dump(cfg, f, indent=2)
    configuration(path)
    print("Qualified R08 local software runtime:", path)


if __name__ == "__main__":
    main()
