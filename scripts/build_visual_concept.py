"""Build fixed, unitless display artwork using OCCT and a PicoGK marker.

This creates disconnected exterior surfaces and abstract markers only. It has no
engineering inputs, internal passages, dimensional interpretation or CAD export.
The target must not already exist; saved project data is never opened.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone, BRepPrimAPI_MakeCylinder
from OCP.GeomAbs import GeomAbs_Cone, GeomAbs_Cylinder
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS


def side_triangles(shape):
    BRepMesh_IncrementalMesh(shape, 1.5, False, 0.3, False)
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    result = []
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        if BRepAdaptor_Surface(face).GetType() in (GeomAbs_Cone, GeomAbs_Cylinder):
            location = TopLoc_Location()
            mesh = BRep_Tool.Triangulation_s(face, location)
            if mesh is None:
                raise ValueError("Missing display triangulation")
            for index in range(1, mesh.NbTriangles() + 1):
                nodes = list(mesh.Triangle(index).Get())
                if face.Orientation() == TopAbs_REVERSED:
                    nodes.reverse()
                for node in nodes:
                    point = mesh.Node(node).Transformed(location.Transformation())
                    result.extend(round(value / 100, 5) for value in point.Coord())
        explorer.Next()
    return result


def axis(z):
    return gp_Ax2(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))


def generate(dotnet, worker):
    # Fixed decorative proportions only; surfaces intentionally disconnected.
    parts = [
        (
            "lower silhouette",
            side_triangles(BRepPrimAPI_MakeCone(axis(-110), 45, 20, 60).Shape()),
        ),
        (
            "middle silhouette",
            side_triangles(BRepPrimAPI_MakeCylinder(axis(-42), 27, 75).Shape()),
        ),
        (
            "upper silhouette",
            side_triangles(BRepPrimAPI_MakeCylinder(axis(43), 34, 12).Shape()),
        ),
    ]
    proc = subprocess.run(
        [str(dotnet), str(worker)], check=True, capture_output=True, timeout=45
    )
    marker = json.loads(proc.stdout)
    if marker.get("backend") != "PicoGK" or not isinstance(
        marker.get("triangles"), list
    ):
        raise ValueError("PicoGK decorative marker was not returned")
    values = marker["triangles"]
    if (
        not 0 < len(values) <= 180000
        or len(values) % 9
        or not all(
            isinstance(v, (int, float)) and math.isfinite(v) and abs(v) < 1
            for v in values
        )
    ):
        raise ValueError("Invalid PicoGK marker")
    # Markers are purely visual annotation beads; they are not ports or fittings.
    for label, offset in (
        ("marker A", (-0.22, 0, 0.68)),
        ("marker B", (0.22, 0, 0.68)),
    ):
        parts.append(
            (label, [round(v + offset[i % 3], 5) for i, v in enumerate(values)])
        )
    return {
        "schema": "cosmos.visual-concept.v1",
        "scope": "UNIT_LESS_DISPLAY_ONLY",
        "kernels": ["OCCT", "PicoGK"],
        "parts": [{"name": name, "triangles": triangles} for name, triangles in parts],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--worker", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.dotnet.is_file() or not args.worker.is_file():
        parser.error("Existing dotnet runtime and fixed visual worker are required")
    data = generate(args.dotnet.resolve(), args.worker.resolve())
    text = (
        "/* Generated display artwork. No engineering units or physical geometry. */\n"
        + "globalThis.CosmosVisualConceptData = "
        + json.dumps(data, separators=(",", ":"), allow_nan=False)
        + ";\n"
    )
    with args.output.open("x", encoding="utf-8") as target:
        target.write(text)
    print(
        f"Visual concept generated: {len(data['parts'])} display parts; OCCT + PicoGK"
    )


if __name__ == "__main__":
    main()
