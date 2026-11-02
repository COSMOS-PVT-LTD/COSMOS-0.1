"""Run an exact-candidate thermal/feed applicability assessment, not a fake solve.

Verify retained raw source bytes before pure Systems diagnostics. Existing source
properties are never extrapolated, repaired or replaced with artificial fixtures.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from scripts.generate_engine_redesign import load_candidate, unique
from scripts.prepare_methalox_thermal_envelope import saturation_states
from systems.geometry.compact_analysis import assess_readiness, record_sha256
from systems.materials.research import stage_conductivity
from systems.propellants.nist_liquid import liquid_table


def load(path):
    return json.loads(path.read_text(), object_pairs_hook=unique)


def verified(path, expected):
    if (
        path.is_symlink()
        or not path.is_file()
        or sha256(path.read_bytes()).hexdigest() != expected
    ):
        raise ValueError("Raw scientific source missing/changed: " + str(path))
    return {"path": str(path), "sha256": expected, "verified": True}


def assess(campaign, liquid_dir, saturation_file, material_dir, output):
    if (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
    ):
        raise ValueError("New absolute assessment report required; no overwrite")
    candidate, research, input_hash = load_candidate(campaign / "research-input.json")
    preflight = load(campaign / "preflight.json")
    baseline = campaign / "bound-propulsion-baseline.json"
    # Export is indented JSON, while baseline_sha256 binds exact source canonical
    # bytes. The Core serializer reconstructs the same retained canonical form.
    from core.serialization import canonical_json_dumps

    baseline_record = load(baseline)
    if (
        sha256(canonical_json_dumps(baseline_record).encode()).hexdigest()
        != preflight["baseline_sha256"]
    ):
        raise ValueError("Bound propulsion baseline identity changed")
    if (
        preflight["recipe_sha256"] != research["recipe_sha256"]
        or preflight["component_source_commit_id"] != research["source_commit_id"]
    ):
        raise ValueError("Assessment cannot borrow another geometry/source")
    liquid = load(liquid_dir / "liquid-table.json")
    sources = load(liquid_dir / "source-manifest.json")
    raw = []
    for row in sources["isobars"]:
        name = row["raw_file"]
        if Path(name).name != name:
            raise ValueError("Retained source filename must not traverse directories")
        raw.append(verified(liquid_dir / name, row["sha256"]))
    raw.append(verified(saturation_file, sources["saturation"]["sha256"]))
    if not set(liquid["raw_sha256"]) <= {record["sha256"] for record in raw}:
        raise ValueError("Not every liquid-table source hash has verified raw bytes")
    rebuilt = liquid_table(
        fluid_id=liquid["fluid_id"],
        temperatures_k=tuple(liquid["temperatures_k"]),
        pressures_pa=tuple(liquid["pressures_pa"]),
        responses=tuple(
            (row["url"], (liquid_dir / row["raw_file"]).read_bytes())
            for row in sources["isobars"]
            if row["kind"] == "grid"
        ),
        lowest_saturation_temperature_k=min(
            row["temperature_k"]
            for row in saturation_states(saturation_file.read_bytes())
        ),
        saturation_sha256=sources["saturation"]["sha256"],
    )
    if record_sha256(asdict(rebuilt)) != record_sha256(liquid):
        raise ValueError(
            "Liquid-table values differ from a fresh retained-TSV reconstruction"
        )
    materials = load(material_dir / "staged-records.json")
    material_sources = load(material_dir / "source-manifest.json")
    pdf_hash = material_sources["source_pdf_sha256"]
    raw.append(verified(material_dir / "source.pdf", pdf_hash))
    raw.append(
        verified(
            material_dir / "original-transcriptions.json",
            material_sources["original_transcriptions_sha256"],
        )
    )
    if any(record["curve"]["source_sha256"] != pdf_hash for record in materials):
        raise ValueError("Material curves do not match the retained supplier source")
    restaged = [
        asdict(stage_conductivity(payload, (material_dir / "source.pdf").read_bytes()))
        for payload in load(material_dir / "original-transcriptions.json")
    ]
    if record_sha256(restaged) != record_sha256(materials):
        raise ValueError(
            "Material curves differ from the verified original-unit transcription"
        )
    identity = {
        key: preflight[key]
        for key in (
            "baseline_sha256",
            "baseline_commit_id",
            "component_source_commit_id",
            "recipe_sha256",
        )
    }
    identity.update(
        liquid_table_sha256=record_sha256(liquid),
        material_records_sha256=record_sha256(materials),
    )
    report = assess_readiness(
        candidate,
        liquid_record=liquid,
        material_records=materials,
        physics_identity=identity,
    )
    report["provenance"].update(
        raw_source_verification="VERIFIED_RETAINED_BYTES",
        liquid_numeric_reconstruction="MATCHES_RETAINED_NIST_TSV_BYTES",
        material_numeric_reconstruction="MATCHES_VERIFIED_ORIGINAL_UNIT_TRANSCRIPTION",
        material_numeric_transcription="RETAINED_RESEARCH_TRANSCRIPTION_NOT_INDEPENDENTLY_REEXTRACTED_FROM_PDF",
        raw_sources=raw,
        research_input_sha256=input_hash,
        project_id=preflight["project_id"],
        candidate_commit_id=preflight["candidate_commit_id"],
        selection_commit_id=preflight["selection_commit_id"],
    )
    with output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(
        json.dumps(
            {
                "status": report["status"],
                "matched_thermal_feed_solved": False,
                "blocker_codes": sorted({row["code"] for row in report["blockers"]}),
                "output": str(output),
            }
        )
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--liquid-dir", type=Path, required=True)
    parser.add_argument("--saturation-file", type=Path, required=True)
    parser.add_argument("--material-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assess(
        args.campaign,
        args.liquid_dir,
        args.saturation_file,
        args.material_dir,
        args.output,
    )


if __name__ == "__main__":
    main()
