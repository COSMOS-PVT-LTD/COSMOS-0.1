"""Direct OCCT/OCP headless path; no CadQuery/VTK GUI import and no fallback.

P06/worker JSON uses metres. This adapter explicitly converts to/from kernel mm.
STEP writes a metre header; STL coordinates are converted to metres before export.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from plugins.geometry.protocol import (
    CAD_VERSION,
    PROTOCOL,
    parse_request,
    validate_slice,
)
from systems.contracts.geometry import GeometryContractError, Representation
from systems.contracts.geometry._wire import MAX_WIRE_BYTES, require

PROTOCOL_STREAM = sys.stdout


def emit(value):
    print(json.dumps(value, allow_nan=False, separators=(",", ":")), file=PROTOCOL_STREAM, flush=True)


def main() -> int:
    global PROTOCOL_STREAM
    PROTOCOL_STREAM = os.fdopen(os.dup(1), "w", buffering=1)
    os.dup2(2, 1)  # Redirect native OCCT fd-1 diagnostics, not just Python print.
    job = correlation = ""
    try:
        require(len(sys.argv) == 2 and Path(sys.argv[1]).is_absolute(), "WORKER_CONFIG", "Pass one private output directory")
        directory = Path(sys.argv[1])
        require(directory.is_dir(), "WORKER_CONFIG", "Output directory is missing")
        raw = sys.stdin.buffer.read(MAX_WIRE_BYTES + 1)
        job, action, request, snapshot, graph = parse_request(raw)
        correlation = request.correlation_id
        validate_slice(request, snapshot, graph, "occt")
        require(request.representation is Representation.ANALYTIC_BREP and all(f.representation == request.representation for f in graph.features), "REPRESENTATION_MISMATCH", "OCCT slice builds analytic B-rep only")
        require({f.value for f in request.output_formats} <= {"step", "stl"}, "UNSUPPORTED_FORMAT", "Qualified OCCT formats are STEP/STL")
        require(request.source_tolerance_m >= 1e-10, "UNSUPPORTED_TOLERANCE", "Requested source tolerance is below the declared kernel floor")
        # All native imports occur after bounded typed input validation, in this child.
        import OCP  # type: ignore[import-not-found]
        from OCP.BRep import BRep_Tool  # type: ignore[import-not-found]
        from OCP.BRepAlgoAPI import (  # type: ignore[import-not-found]
            BRepAlgoAPI_Common,
            BRepAlgoAPI_Cut,
            BRepAlgoAPI_Fuse,
        )
        from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore[import-not-found]
        from OCP.BRepGProp import BRepGProp  # type: ignore[import-not-found]
        from OCP.BRepMesh import (  # type: ignore[import-not-found]
            BRepMesh_IncrementalMesh,
        )
        from OCP.BRepPrimAPI import (  # type: ignore[import-not-found]
            BRepPrimAPI_MakeBox,
            BRepPrimAPI_MakeCylinder,
            BRepPrimAPI_MakeSphere,
        )
        from OCP.BRepTools import BRepTools  # type: ignore[import-not-found]
        from OCP.gp import (  # type: ignore[import-not-found]
            gp_Ax2,
            gp_Dir,
            gp_Pnt,
        )
        from OCP.GProp import GProp_GProps  # type: ignore[import-not-found]
        from OCP.IFSelect import IFSelect_RetDone  # type: ignore[import-not-found]
        from OCP.Interface import Interface_Static  # type: ignore[import-not-found]
        from OCP.STEPControl import (  # type: ignore[import-not-found]
            STEPControl_AsIs,
            STEPControl_Controller,
            STEPControl_Writer,
        )
        from OCP.StlAPI import StlAPI_Writer  # type: ignore[import-not-found]
        from OCP.TopAbs import TopAbs_SOLID  # type: ignore[import-not-found]
        from OCP.TopExp import TopExp_Explorer  # type: ignore[import-not-found]
        require(OCP.__version__ == "7.8.1.1", "BACKEND_VERSION", "OCP runtime version mismatch")
        header = {"protocol": PROTOCOL, "job_id": job, "correlation_id": correlation, "backend_version": CAD_VERSION}
        if action == "health":
            emit({**header, "event_type": "health", "native_version": OCP.__version__})
            return 0
        emit({**header, "event_type": "started"})
        values = {p.name: p.value_si * 1000 for p in snapshot.parameters_si}
        nodes: dict[str, Any] = {}
        for name in graph.topological_order():
            f = next(f for f in graph.features if f.feature_id == name)
            if f.operation.startswith("primitive."):
                p = {n.rsplit(".", 1)[-1]: values[n] for n in f.parameter_refs}
                center = gp_Pnt(p["x"], p["y"], p["z"])
                if f.operation == "primitive.sphere":
                    shape = BRepPrimAPI_MakeSphere(center, p["radius"]).Shape()
                elif f.operation == "primitive.cylinder":
                    shape = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(p["x"], p["y"], p["z"] - p["height"] / 2), gp_Dir(0, 0, 1)), p["radius"], p["height"]).Shape()
                else:
                    shape = BRepPrimAPI_MakeBox(gp_Pnt(p["x"] - p["width"] / 2, p["y"] - p["depth"] / 2, p["z"] - p["height"] / 2), p["width"], p["depth"], p["height"]).Shape()
            else:
                deps = f.dependency_ids
                if f.operation == "boolean.difference":
                    deps = (next(d for d in deps if d.endswith(".lhs")), next(d for d in deps if d.endswith(".rhs")))
                operation = {"boolean.union": BRepAlgoAPI_Fuse, "boolean.difference": BRepAlgoAPI_Cut, "boolean.intersection": BRepAlgoAPI_Common}[f.operation](nodes[deps[0]], nodes[deps[1]])
                operation.SetFuzzyValue(request.source_tolerance_m * 1000)
                operation.Build()
                require(operation.IsDone(), "KERNEL_FAILURE", "OCCT Boolean did not complete")
                shape = operation.Shape()
            nodes[name] = shape
        shape = nodes[graph.output_feature_ids[0]]
        solids = 0
        explorer = TopExp_Explorer(shape, TopAbs_SOLID)
        while explorer.More():
            solids += 1
            explorer.Next()
        require(not shape.IsNull() and solids > 0, "EMPTY_GEOMETRY", "Empty geometry has no accepted export")
        require(BRepCheck_Analyzer(shape, True).IsValid(), "INVALID_TOPOLOGY", "OCCT source topology check failed")
        source = directory / "source.brep"
        require(not source.exists(), "ARTIFACT_EXISTS", "Refusing source overwrite")
        require(BRepTools.Write_s(shape, str(source)), "EXPORT_FAILURE", "BREP writer failed")
        exports = []
        encoding = {}
        for output in request.output_formats:
            target = directory / ("export." + output.value)
            require(not target.exists(), "ARTIFACT_EXISTS", "Refusing export overwrite")
            if output.value == "step":
                STEPControl_Controller.Init_s()
                require(Interface_Static.SetCVal_s("write.step.unit", "M"), "EXPORT_FAILURE", "Cannot set explicit STEP output unit")
                writer = STEPControl_Writer()
                # Local kernel mm and the requested metre STEP unit are distinct.
                writer.Model().SetLocalLengthUnit(1)
                writer.Model().SetWriteLengthUnit(1000)
                Interface_Static.SetIVal_s("write.precision.mode", 1)
                Interface_Static.SetRVal_s("write.precision.val", request.export_tolerance_m * 1000)
                require(writer.Transfer(shape, STEPControl_AsIs) == IFSelect_RetDone and writer.Write(str(target)) == IFSelect_RetDone, "EXPORT_FAILURE", "STEP writer failed")
            else:
                # Reserve 40% of the requested chord budget for SI float32 encoding.
                mesh = BRepMesh_IncrementalMesh(shape, request.export_tolerance_m * 1000 * .6, False, .05, False)
                require(mesh.IsDone(), "EXPORT_FAILURE", "Explicit STL meshing failed")
                writer_stl = StlAPI_Writer(); writer_stl.ASCIIMode = False
                from plugins.geometry.workers.stl_encoding import encode_si_stl
                native_stl = directory / "native-mm.stl"
                require(not native_stl.exists(), "ARTIFACT_EXISTS", "Refusing native tessellation overwrite")
                try:
                    require(writer_stl.Write(shape, str(native_stl)), "EXPORT_FAILURE", "STL writer failed")
                    encoding = encode_si_stl(native_stl, target)
                finally:
                    native_stl.unlink(missing_ok=True)
            exports.append({"name": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "format": output.value, "file_unit": "m"})
        props = GProp_GProps(); BRepGProp.VolumeProperties_s(shape, props)
        center = props.CentreOfMass()
        emit({**header, "event_type": "completed", "source_name": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "exports": exports,
              "metrics": {"volume_m3": props.Mass() * 1e-9, "centroid_m": [center.X() * .001, center.Y() * .001, center.Z() * .001],
                          "solid_count": solids, "kernel_unit": "mm", "input_unit": "m", "occt_shape_closed_flag": BRep_Tool.IsClosed_s(shape), **encoding}})
        return 0
    except Exception as error:  # noqa: BLE001 - child boundary must emit a typed terminal diagnostic for native failures.
        code = error.code if isinstance(error, GeometryContractError) else "WORKER_FAILURE"
        emit({"protocol": PROTOCOL, "job_id": job, "correlation_id": correlation, "backend_version": CAD_VERSION,
              "event_type": "failed", "code": code, "message": str(error)[:1024]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
