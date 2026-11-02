"""One bounded retained-BREP inspection/drawing request per isolated process.

Native source is the component exporter's millimetre compound; direct children
are in its retained worker-observation order. Never infer BREP faces from STL.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def entities(shape, kind):
    from OCP.TopExp import TopExp_Explorer
    values = []; it = TopExp_Explorer(shape, kind)
    while it.More():
        values.append(it.Current()); it.Next()
    return values


def properties(shape):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(shape, p)
    return p.Mass() * 1e-9, [v * .001 for v in p.CentreOfMass().Coord()]


def load(request):
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.TopoDS import TopoDS_Shape, TopoDS_Iterator
    from OCP.TopAbs import TopAbs_SOLID
    source = Path("source.brep")
    require(source.is_file() and not source.is_symlink() and 0 < source.stat().st_size <= 64 * 1024**2, "Bounded private native artifact required")
    require(hashlib.sha256(source.read_bytes()).hexdigest() == request["source_sha256"], "Native source hash mismatch")
    root = TopoDS_Shape(); require(BRepTools.Read_s(root, str(source), BRep_Builder()), "Native BREP read failed")
    parts = request["parts"]
    require(type(parts) is list and 1 <= len(parts) <= 24 and len({p["part_id"] for p in parts}) == len(parts), "Bounded unique source part identities required")
    children = []; it = TopoDS_Iterator(root)
    while it.More():
        children.append(it.Value()); it.Next()
    require(len(children) == len(parts), "Native compound child count differs from exporter mapping")
    result = {}
    for part, shape in zip(parts, children, strict=True):
        require(len(entities(shape, TopAbs_SOLID)) == 1 and BRepCheck_Analyzer(shape, True).IsValid(), "Exactly one valid solid per retained output required")
        volume, center = properties(shape)
        require(volume > 0 and abs(volume - part["volume_m3"]) <= part["volume_m3"] * 1e-8 and math.dist(center, part["centroid_m"]) <= 1e-8,
                "Retained native child properties differ from explicit exporter part order")
        result[part["part_id"]] = shape
    return result


def clearance(shapes, request):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.TopAbs import TopAbs_SOLID
    a, b = request["pair"]
    require(a != b and a in shapes and b in shapes, "Two distinct exact source solids required")
    tolerance = request["linear_tolerance_m"]; resolution = request["volume_resolution_m3"]; required = request["required_clearance_m"]
    common = BRepAlgoAPI_Common(shapes[a], shapes[b]); common.SetFuzzyValue(0.); common.Build()
    require(common.IsDone(), "Solid intersection failed; no clearance result may be accepted")
    solids = entities(common.Shape(), TopAbs_SOLID)
    require(all(BRepCheck_Analyzer(s, True).IsValid() for s in solids), "Invalid intersection topology")
    volume = sum(abs(properties(s)[0]) for s in solids)
    distance = BRepExtrema_DistShapeShape(); distance.LoadS1(shapes[a]); distance.LoadS2(shapes[b]); distance.SetDeflection(tolerance * 1000); distance.Perform()
    require(distance.IsDone() and distance.NbSolution() > 0, "Minimum-distance computation failed")
    d = distance.Value() * .001
    require(math.isfinite(d) and d >= 0 and math.isfinite(volume), "Nonfinite native result")
    if solids:
        relation = "INTERFERENCE" if volume > resolution else "UNRESOLVED_SMALL_INTERSECTION"
        status = "FAIL_INTERFERENCE" if volume > resolution else "INDETERMINATE"
    elif distance.InnerSolution():
        raise ValueError("Containment reported without Boolean common solids; inconsistent kernel result")
    elif d <= tolerance:
        relation, status = "WITHIN_NUMERICAL_CONTACT_BAND", "INDETERMINATE"
    else:
        relation = "DISJOINT"
        status = "SATISFIED" if d - required > tolerance else "BELOW_REQUIRED" if required - d > tolerance else "INDETERMINATE"
    witnesses = [{"a_m": [v * .001 for v in distance.PointOnShape1(i).Coord()], "b_m": [v * .001 for v in distance.PointOnShape2(i).Coord()]} for i in range(1, min(4, distance.NbSolution()) + 1)]
    return {"pair": [a, b], "relation": relation, "clearance_status": status, "minimum_distance_m": d,
            "intersection_volume_m3": volume, "intersection_solid_count": len(solids), "required_clearance_m": required,
            "linear_tolerance_m": tolerance, "volume_resolution_m3": resolution, "witnesses": witnesses,
            "method": "OCCT_BREP_BOOLEAN_COMMON_AND_DISTSHAPESHAPE", "fuzzy_tolerance_m": 0.,
            "scope": "Retained analytic BREP and explicit numerical limits; not tessellation/AABB distance, signed penetration depth, tolerance-stack acceptance or physical contact validation."}


def drawing(shapes, request):
    from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    from OCP.HLRAlgo import HLRAlgo_Projector
    from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_QuasiUniformDeflection
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    part = request["part_id"]; require(part in shapes, "Exact retained part required")
    views = []; total = 0
    for name, normal, right in (("FRONT (XY)", (0,0,1), (1,0,0)), ("TOP (XZ)", (0,-1,0), (1,0,0)), ("END (ZY)", (1,0,0), (0,0,-1))):
        algo = HLRBRep_Algo(); algo.Add(shapes[part]); algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(*normal), gp_Dir(*right)))); algo.Update(); algo.Hide()
        extract = HLRBRep_HLRToShape(algo); lines = []
        for hidden, types in ((False, ("VCompound", "OutLineVCompound")), (True, ("HCompound", "OutLineHCompound"))):
            for kind in types:
                compound = getattr(extract, kind)()
                if compound.IsNull():
                    continue
                for edge in entities(compound, TopAbs_EDGE):
                    curve = BRepAdaptor_Curve(TopoDS.Edge_s(edge))
                    sampler = GCPnts_QuasiUniformDeflection(curve, request["curve_deflection_m"] * 1000)
                    require(sampler.IsDone() and 2 <= sampler.NbPoints() <= 20000, "Projected edge sampling failed or exceeds bound")
                    points = [[sampler.Value(i).X() * .001, sampler.Value(i).Y() * .001] for i in range(1, sampler.NbPoints()+1)]
                    require(all(math.isfinite(v) for point in points for v in point), "Nonfinite projected edge")
                    total += len(points); require(total <= 120000, "Drawing exceeds120k projected points; select a part/simpler explicit detail")
                    lines.append({"hidden": hidden, "points_m": points})
        require(lines, "No projected source edges")
        views.append({"name": name, "normal": normal, "right": right, "lines": lines})
    box=Bnd_Box();BRepBndLib.AddOptimal_s(shapes[part],box,False,False)
    return {"part_id": part, "views": views, "bounds_m":[v*.001 for v in box.Get()], "curve_deflection_m": request["curve_deflection_m"], "method": "OCCT_HLRBREP_ORTHOGRAPHIC_THIRD_ANGLE", "scope": "Hidden-line classification from retained analytic BREP. Drawing curves discretized at the explicit deflection, not an analytic DXF/PMI export or manufacturing release."}


def main():
    try:
        raw = sys.stdin.buffer.read(65537); require(len(raw) <= 65536, "Inspection request exceeds64KiB")
        import importlib.metadata
        require(importlib.metadata.version("cadquery-ocp")=="7.8.1.1", "Pinned OCP7.8.1.1 required")
        request = json.loads(raw); shapes = load(request)
        result = clearance(shapes, request) if request["operation"] == "clearance" else drawing(shapes, request) if request["operation"] == "drawing" else None
        require(result is not None, "Unsupported native inspection operation")
        if request["operation"] == "drawing" and request["format"] in {"pdf","svg"}:
            from systems.geometry import manufacturing_drawing as sheet
            content=getattr(sheet,request["format"])(result,request["metadata"])
            target=Path("drawing."+request["format"])
            require(not target.exists() and len(content)<=16*1024**2,"Drawing output exists or exceeds16MiB")
            with target.open("xb") as stream:stream.write(content)
            result={"part_id":request["part_id"],"output_name":target.name,"output_sha256":hashlib.sha256(content).hexdigest(),"method":result["method"],"curve_deflection_m":request["curve_deflection_m"],"manufacturing_acceptance":"NOT_PERFORMED"}
        print(json.dumps({"ok": True, "kernel": "OCCT7.8.1/OCP7.8.1.1", "source_sha256": request["source_sha256"], "result": result}, allow_nan=False))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)[:1024]})); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
