"""Pinned OCP nozzle profile/wall/revolve child; no store, GUI or fallback."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from plugins.geometry.nozzle_protocol import VERSION, validate
from plugins.geometry.protocol import PROTOCOL, parse_request
from systems.contracts.geometry import GeometryContractError
from systems.contracts.geometry._wire import MAX_WIRE_BYTES, require


def main() -> int:
    output = os.fdopen(os.dup(1), "w", buffering=1)
    os.dup2(2, 1)
    job = correlation = ""

    def emit(value):
        print(json.dumps(value, allow_nan=False, separators=(",", ":")), file=output, flush=True)

    try:
        require(len(sys.argv) == 2 and Path(sys.argv[1]).is_absolute(), "WORKER_CONFIG", "Pass exactly one private output directory")
        directory = Path(sys.argv[1])
        require(directory.is_dir() and not directory.is_symlink(), "WORKER_CONFIG", "Trusted existing private directory required")
        job, action, request, snapshot, graph = parse_request(sys.stdin.buffer.read(MAX_WIRE_BYTES + 1))
        correlation = request.correlation_id
        profile = validate(request, snapshot, graph)
        import OCP  # type: ignore[import-not-found]
        from OCP.BRepBuilderAPI import (  # type: ignore[import-not-found]
            BRepBuilderAPI_MakeFace,
            BRepBuilderAPI_MakePolygon,
        )
        from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore[import-not-found]
        from OCP.BRepGProp import BRepGProp  # type: ignore[import-not-found]
        from OCP.BRepMesh import (
            BRepMesh_IncrementalMesh,  # type: ignore[import-not-found]
        )
        from OCP.BRepPrimAPI import (
            BRepPrimAPI_MakeRevol,  # type: ignore[import-not-found]
        )
        from OCP.BRepTools import BRepTools  # type: ignore[import-not-found]
        from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt  # type: ignore[import-not-found]
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
        require(OCP.__version__ == "7.8.1.1", "BACKEND_VERSION", "Nozzle worker requires pinned OCP 7.8.1.1")
        header = {"protocol": PROTOCOL, "job_id": job, "correlation_id": correlation, "backend_version": VERSION}
        if action == "health":
            emit({**header, "event_type": "health", "native_version": OCP.__version__})
            return 0
        emit({**header, "event_type": "started"})
        polygon = BRepBuilderAPI_MakePolygon()
        for x, radius in (*profile.points, *((x, r + profile.radial_thickness_m) for x, r in reversed(profile.points))):
            polygon.Add(gp_Pnt(x * 1000, radius * 1000, 0.))
        polygon.Close()
        require(polygon.IsDone(), "PROFILE_FAILED", "Closed radial-wall profile failed; no repair")
        face = BRepBuilderAPI_MakeFace(polygon.Wire(), True)
        require(face.IsDone(), "PROFILE_FAILED", "Planar wall face failed; no healing")
        revolver = BRepPrimAPI_MakeRevol(face.Face(), gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), True)
        require(revolver.IsDone(), "REVOLVE_FAILED", "X-axis wall revolve did not complete")
        shape = revolver.Shape()
        explorer, solids = TopExp_Explorer(shape, TopAbs_SOLID), 0
        while explorer.More():
            solids += 1; explorer.Next()
        require(not shape.IsNull() and solids == 1 and BRepCheck_Analyzer(shape, True).IsValid(), "INVALID_TOPOLOGY", "Nozzle source must be one valid solid; no sewing/healing/repair")
        source = directory / "source.brep"
        require(not source.exists() and BRepTools.Write_s(shape, str(source)), "EXPORT_FAILURE", "Cannot create immutable native B-rep")
        exports, encoding = [], {}
        for format_ in request.output_formats:
            target = directory / ("export." + format_.value)
            require(not target.exists(), "ARTIFACT_EXISTS", "Refuse export overwrite")
            if format_.value == "step":
                STEPControl_Controller.Init_s()
                require(Interface_Static.SetCVal_s("write.step.unit", "M"), "EXPORT_FAILURE", "Cannot declare metre STEP units")
                writer = STEPControl_Writer()
                writer.Model().SetLocalLengthUnit(1)
                writer.Model().SetWriteLengthUnit(1000)
                Interface_Static.SetIVal_s("write.precision.mode", 1)
                Interface_Static.SetRVal_s("write.precision.val", request.export_tolerance_m * 1000)
                require(writer.Transfer(shape, STEPControl_AsIs) == IFSelect_RetDone and writer.Write(str(target)) == IFSelect_RetDone, "EXPORT_FAILURE", "STEP writer failed")
            else:
                mesh = BRepMesh_IncrementalMesh(shape, request.export_tolerance_m * 1000 * .6, False, .05, False)
                require(mesh.IsDone(), "EXPORT_FAILURE", "Nozzle STL tessellation failed")
                native = directory / "native-mm.stl"
                require(not native.exists(), "ARTIFACT_EXISTS", "Refuse scratch overwrite")
                writer_stl = StlAPI_Writer(); writer_stl.ASCIIMode = False
                from plugins.geometry.workers.stl_encoding import encode_si_stl
                try:
                    require(writer_stl.Write(shape, str(native)), "EXPORT_FAILURE", "Native STL export failed")
                    encoding = encode_si_stl(native, target)
                finally:
                    native.unlink(missing_ok=True)
            exports.append({"name": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "format": format_.value, "file_unit": "m"})
        properties = GProp_GProps(); BRepGProp.VolumeProperties_s(shape, properties)
        center = properties.CentreOfMass()
        require(properties.Mass() > 0, "INVALID_ORIENTATION", "Nozzle has no positive signed material volume")
        emit({**header, "event_type": "completed", "source_name": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "exports": exports,
              "metrics": {"volume_m3": properties.Mass() * 1e-9, "centroid_m": [center.X() * .001, center.Y() * .001, center.Z() * .001], "solid_count": solids, "kernel_unit": "mm", "input_unit": "m", "profile_station_count": len(profile.points), "radial_thickness_m": profile.radial_thickness_m, **encoding}})
        return 0
    except Exception as error:  # noqa: BLE001 - isolated native boundary retains typed terminal diagnostic
        emit({"protocol": PROTOCOL, "job_id": job, "correlation_id": correlation, "backend_version": VERSION, "event_type": "failed", "code": error.code if isinstance(error, GeometryContractError) else "WORKER_FAILURE", "message": str(error)[:1024]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
