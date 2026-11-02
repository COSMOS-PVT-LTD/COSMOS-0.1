"""Explicit, offline, unqualified compact CAD generation. Never edits app data.

Run from the checkout with PYTHONPATH=. and the appropriate native interpreter.
The GUI's research-input download is the sole accepted source format. A full
candidate build needs >=10GiB free; this is not an R08 qualification command.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from hashlib import sha256
from pathlib import Path

from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_model import from_contracts, keys
from systems.geometry.engine_redesign import compile_candidate


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate input JSON key")
        result[key] = value
    return result


def load_candidate(path):
    with path.open("rb") as stream:
        raw = stream.read(2097153)
    if len(raw) > 2097152:
        raise ValueError("Input exceeds 2MiB")
    value = json.loads(raw, object_pairs_hook=unique)
    keys(
        value,
        (
            "schema",
            "source_commit_id",
            "source_model",
            "specification",
            "recipe_sha256",
        ),
        "research input",
    )
    if value["schema"] != "cosmos.compact-engine-input.v1":
        raise ValueError("Explicit compact research input required")
    model = value["source_model"]
    keys(model, ("snapshot_json", "graph_json"), "source model")
    plan = from_contracts(
        DesignSnapshot.from_json(model["snapshot_json"]),
        GeometryFeatureGraph.from_json(model["graph_json"]),
    )
    candidate = compile_candidate(plan, value["specification"])
    if candidate.wire()["recipe_sha256"] != value["recipe_sha256"]:
        raise ValueError(
            "Research recipe hash mismatch; no silent recompilation with changed source"
        )
    return candidate, value, sha256(raw).hexdigest()


def preflight(directory):
    parent = directory.parent
    if (
        not directory.is_absolute()
        or directory.exists()
        or directory.is_symlink()
        or not parent.is_dir()
    ):
        raise ValueError(
            "A NEW absolute output folder with an existing parent is required; no overwrite"
        )
    if shutil.disk_usage(parent).free < 10 * 1024**3:
        raise ValueError(
            "Full engine generation held: at least 10GiB free required; no files deleted or build started"
        )


def occt_export(candidate, directory):
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.Interface import Interface_Static
    from OCP.STEPControl import (
        STEPControl_AsIs,
        STEPControl_Controller,
        STEPControl_Writer,
    )
    from OCP.TopoDS import TopoDS_Compound

    from plugins.geometry.compact_occt import Builder

    result = Builder(candidate.plan).build(candidate)
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    parts = []
    for name, shape, metrics in result:
        builder.Add(compound, shape)
        filename = directory / ("UNQUALIFIED-" + name + ".brep")
        if not BRepTools.Write_s(shape, str(filename)):
            raise ValueError("Compact BREP export failed")
        parts.append({"part_id": name, **metrics})
    STEPControl_Controller.Init_s()
    if not Interface_Static.SetCVal_s("write.step.unit", "MM"):
        raise ValueError("Explicit millimetre STEP file units could not be set")
    writer = STEPControl_Writer()
    if (
        writer.Transfer(compound, STEPControl_AsIs) != IFSelect_RetDone
        or writer.Write(str(directory / "UNQUALIFIED-assembly.step"))
        != IFSelect_RetDone
    ):
        raise ValueError("Compact STEP export failed")
    return {
        "ok": True,
        "backend": "occt",
        "parts": parts,
        "step_reimport": "NOT_PERFORMED",
        "step_file_unit": "mm",
        "qualification": "NOT_PERFORMED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("occt", "picogk"), required=True)
    parser.add_argument("--research-only", action="store_true", required=True)
    parser.add_argument("--voxel-m", type=float)
    parser.add_argument("--dotnet", type=Path)
    parser.add_argument("--picogk-worker", type=Path)
    args = parser.parse_args()
    candidate, value, checksum = load_candidate(args.input)
    preflight(args.output)
    wire = candidate.wire()
    if args.backend == "picogk":
        if args.dotnet is None or args.picogk_worker is None or args.voxel_m is None:
            raise ValueError(
                "PicoGK requires explicit new worker DLL, dotnet and voxel size; no old runtime is repurposed"
            )
        for path in (args.dotnet, args.picogk_worker):
            if not path.is_absolute() or not path.is_file():
                raise ValueError(
                    "Explicit existing absolute native command files required"
                )
        if not 2.5e-5 <= args.voxel_m <= 0.002:
            raise ValueError("Voxel size outside research envelope")
        cells = sum(
            math_product(
                (g["bounds_m"][i + 3] - g["bounds_m"][i]) / args.voxel_m + 5
                for i in range(3)
            )
            for g in wire["groups"]
        )
        if cells > 120_000_000:
            raise ValueError(
                "Declared PicoGK field exceeds 120M-cell envelope; no build started"
            )
    args.output.mkdir(mode=0o700)
    manifest = {
        "schema": "cosmos.compact-engine-build-evidence.v1",
        "complete": False,
        "input_sha256": checksum,
        "source_commit_id": value["source_commit_id"],
        "recipe_sha256": wire["recipe_sha256"],
        "qualification": "NOT_PERFORMED",
        "r08": "ON_HOLD",
        "physical_validation": "NOT_PERFORMED",
    }
    from systems.geometry.engine_redesign_authority import methods

    root = Path(__file__).resolve().parents[1]
    native_files = (
        "plugins/geometry/compact_occt.py",
        "plugins/geometry/workers/pico-compact/Program.cs",
        "plugins/geometry/workers/pico-compact/PicoCompact.csproj",
        "plugins/geometry/workers/pico-components/Program.cs",
        "scripts/generate_engine_redesign.py",
    )
    manifest["method_sources"] = {
        **methods(),
        **{
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in native_files
        },
    }
    if args.backend == "picogk":
        manifest["native_command_sha256"] = {
            str(path): sha256(path.read_bytes()).hexdigest()
            for path in (args.dotnet, args.picogk_worker)
        }

    # Artifact outputs (not production source edits); exclusive creation only.
    def artifact(name, content):
        with (args.output / name).open("x") as stream:
            json.dump(content, stream, allow_nan=False, indent=2)

    artifact("research-input.json", value)
    artifact("recipe.json", wire)
    if args.backend == "occt":
        result = occt_export(candidate, args.output)
    else:
        payload = json.dumps(
            {"research_only": True, "voxel_m": args.voxel_m, "recipe": wire},
            allow_nan=False,
        )
        worker = subprocess.run(
            [str(args.dotnet), str(args.picogk_worker), str(args.output)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=600,
            check=False,
        )
        result = json.loads(worker.stdout)
        if worker.returncode or not result.get("ok"):
            artifact(
                "failure.json",
                {**manifest, "error": result.get("error", "Native failure")},
            )
            raise ValueError(
                "Native compact build failed; partial unqualified artifacts retained"
            )
    artifacts = {
        p.name: sha256(p.read_bytes()).hexdigest()
        for p in args.output.iterdir()
        if p.is_file()
    }
    artifact(
        "manifest.json",
        {**manifest, "complete": True, "result": result, "artifacts": artifacts},
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(args.output),
                "backend": args.backend,
                "qualification": "NOT_PERFORMED",
            }
        )
    )


def math_product(values):
    import math

    return math.prod(values)


if __name__ == "__main__":
    main()
