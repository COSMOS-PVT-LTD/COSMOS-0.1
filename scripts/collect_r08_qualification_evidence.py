"""Collect actual passing R08 family reports; never create acceptance records."""

import argparse
import json
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from scripts.qualify_geometry_qa import family_campaigns
from systems.geometry.qualification import ROOT, methods


def collect(path):
    raw = path.read_bytes()
    root = ET.fromstring(raw)
    cases = list(root.iter("testcase"))
    if any(
        t.find(k) is not None for t in cases for k in ("failure", "error", "skipped")
    ):
        raise ValueError("Only actual complete passing family reports may be collected")
    inventory = family_campaigns(path)
    rows = []
    for prop in root.findall(
        ".//testcase/properties/property[@name='r08_family_campaign']"
    ):
        original = json.loads(prop.get("value"))
        campaign = []
        for result in original["campaign"]:
            parts = result["parts"]
            distances = [
                x[direction]["maximum_m"]
                for p in parts
                if (x := p["direct_discrepancy"]) is not None
                for direction in ("reference_to_candidate", "candidate_to_reference")
            ]
            campaign.append(
                {
                    "voxel_resolution_m": result["voxel_resolution_m"],
                    "part_count": len(parts),
                    "pass": result["pass"],
                    "maximum_relative_volume_error": max(
                        p["dimensions"]["relative_volume"] for p in parts
                    ),
                    "maximum_relative_area_error": max(
                        p["dimensions"]["relative_area"] for p in parts
                    ),
                    "maximum_direct_sample_distance_m": max(distances)
                    if distances
                    else None,
                    "critical_witness_count": sum(
                        len(p["critical_features"]) for p in parts
                    ),
                    "critical_failures": sum(
                        not c["pass"] for p in parts for c in p["critical_features"]
                    ),
                    "comparison_process": result["process"],
                    "generation_process": result["generation_process"],
                    "reference_sha256": result["reference_sha256"],
                    "candidate_sha256": result["candidate_sha256"],
                }
            )
        rows.append(
            {
                "kind": original["kind"],
                "policy_sha256": original["policy_sha256"],
                "campaign": campaign,
            }
        )
    return {
        "schema": "cosmos.r08-software-family-summary.v1",
        "inventory": inventory,
        "source_report": str(path.resolve()),
        "source_report_sha256": sha256(raw).hexdigest(),
        "method_sources_at_collection": methods(),
        "cases": rows,
        "scope": "MANUFACTURED_CASE_SOFTWARE_QUALIFICATION_ONLY",
        "target_engine_acceptance": "NOT_PERFORMED",
        "physical_validation": "NOT_PERFORMED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or ROOT / "docs/implementation/evidence" not in output.parents:
        raise ValueError(
            "NEW repository evidence output required; no historical overwrite"
        )
    value = collect(args.input)
    if args.engine:
        raw = args.engine.read_bytes()
        tree = ET.fromstring(raw)
        if any(
            t.find(k) is not None
            for t in tree.iter("testcase")
            for k in ("failure", "error", "skipped")
        ):
            raise ValueError("Passing executed saved-engine diagnostic required")
        properties = tree.findall(
            ".//testcase/properties/property[@name='r08_saved_engine_nominal_diagnostic']"
        )
        if len(properties) != 1:
            raise ValueError("Exact executed saved-engine nominal diagnostic required")
        original = json.loads(properties[0].get("value"))
        value["saved_engine_diagnostic"] = {
            "source_report": str(args.engine.resolve()),
            "source_report_sha256": sha256(raw).hexdigest(),
            **{
                key: original[key]
                for key in (
                    "capture_sha256",
                    "model_commit_id",
                    "model_sha256",
                    "part_count",
                    "scope",
                    "engine_intended_use_policy",
                    "engineering_acceptance",
                    "whole_engine_implicit_refinement",
                    "physical_validation",
                )
            },
            "nominal_source_witness_count": sum(
                len(p["nominal_source_witnesses"]) for p in original["parts"]
            ),
            "maximum_relative_nominal_brep_area_error": max(
                abs(p["occt_area_m2"] - p["area_m2"]) / p["area_m2"]
                for p in original["parts"]
            ),
            "independent_step_pass": original["evidence"]["qa-step"]["pass"],
            "independent_stl_topology_pass": original["evidence"]["qa-stl"][
                "topology_pass"
            ],
        }
    with output.open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
    print(
        "Collected", len(value["cases"]), "actual manufactured-case campaigns:", output
    )


if __name__ == "__main__":
    main()
