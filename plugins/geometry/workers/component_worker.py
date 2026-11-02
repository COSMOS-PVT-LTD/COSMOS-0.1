"""Pinned native component construction; no store/GUI access or engineering signoff."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

from plugins.geometry.component_protocol import validate
from plugins.geometry.protocol import PROTOCOL, parse_request
from systems.contracts.geometry import GeometryContractError
from systems.contracts.geometry._wire import MAX_WIRE_BYTES, require
from systems.geometry.component_model import VERSION


def main():
    output = os.fdopen(os.dup(1),"w",buffering=1)
    os.dup2(2,1)
    job=correlation=""
    def emit(value):
        print(json.dumps(value,allow_nan=False,separators=(",",":")),file=output,flush=True)
    try:
        require(len(sys.argv)==2,"WORKER_CONFIG","One trusted private output directory required")
        directory=Path(sys.argv[1])
        require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink(),"WORKER_CONFIG","Existing private absolute output directory required")
        job,action,request,snapshot,graph=parse_request(sys.stdin.buffer.read(MAX_WIRE_BYTES+1))
        correlation=request.correlation_id
        plan=validate(request,snapshot,graph)
        import numpy as np
        import OCP  # type: ignore[import-not-found]
        from OCP.Bnd import Bnd_Box  # type: ignore[import-not-found]
        from OCP.BRep import BRep_Builder, BRep_Tool  # type: ignore[import-not-found]
        from OCP.BRepAdaptor import BRepAdaptor_Curve  # type: ignore[import-not-found]
        from OCP.BRepAlgoAPI import (  # type: ignore[import-not-found]
            BRepAlgoAPI_Common,
            BRepAlgoAPI_Cut,
        )
        from OCP.BRepBndLib import BRepBndLib  # type: ignore[import-not-found]
        from OCP.BRepBuilderAPI import (  # type: ignore[import-not-found]
            BRepBuilderAPI_MakeEdge,
            BRepBuilderAPI_MakeFace,
            BRepBuilderAPI_MakeWire,
            BRepBuilderAPI_Transform,
        )
        from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore[import-not-found]
        from OCP.BRepGProp import BRepGProp  # type: ignore[import-not-found]
        from OCP.BRepMesh import (
            BRepMesh_IncrementalMesh,  # type: ignore[import-not-found]
        )
        from OCP.BRepPrimAPI import (  # type: ignore[import-not-found]
            BRepPrimAPI_MakeCylinder,
            BRepPrimAPI_MakeRevol,
        )
        from OCP.BRepTools import BRepTools  # type: ignore[import-not-found]
        from OCP.gp import (  # type: ignore[import-not-found]
            gp_Ax1,
            gp_Ax2,
            gp_Circ,
            gp_Dir,
            gp_Pnt,
            gp_Trsf,
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
        from OCP.TopAbs import (  # type: ignore[import-not-found]
            TopAbs_EDGE,
            TopAbs_FACE,
            TopAbs_SOLID,
        )
        from OCP.TopExp import TopExp, TopExp_Explorer  # type: ignore[import-not-found]
        from OCP.TopoDS import TopoDS, TopoDS_Compound  # type: ignore[import-not-found]
        from OCP.TopTools import (  # type: ignore[import-not-found]
            TopTools_IndexedMapOfShape,
            TopTools_ListOfShape,
        )

        from plugins.geometry.workers.stl_encoding import encode_si_stl
        require(OCP.__version__=="7.8.1.1","BACKEND_VERSION","Pinned OCP7.8.1.1 required")
        header={"protocol":PROTOCOL,"job_id":job,"correlation_id":correlation,"backend_version":VERSION}
        if action=="health":
            emit({**header,"event_type":"health","native_version":OCP.__version__}); return 0
        emit({**header,"event_type":"started"})
        def entities(shape,kind):
            explorer=TopExp_Explorer(shape,kind); result=[]
            while explorer.More(): result.append(explorer.Current()); explorer.Next()
            return result
        def transformed(shape,labels,rotation,translation):
            tr=gp_Trsf(); r=np.asarray(rotation).reshape(3,3); t=np.asarray(translation)*1000
            tr.SetValues(float(r[0,0]),float(r[0,1]),float(r[0,2]),float(t[0]),float(r[1,0]),float(r[1,1]),float(r[1,2]),float(t[1]),float(r[2,0]),float(r[2,1]),float(r[2,2]),float(t[2]))
            mover=BRepBuilderAPI_Transform(shape,tr,True)
            require(mover.IsDone(),"PLACEMENT_FAILED","Proper rigid component transform failed")
            return mover.Shape(),[(mover.ModifiedShape(face),name) for face,name in labels]
        def revolved(profile,sector=None,prefix=""):
            n=len(profile); points=[(x,ri) for x,ri,_ in profile]+[(x,ro) for x,_,ro in reversed(profile)]
            wire=BRepBuilderAPI_MakeWire(); labels=[]; edges=[]
            for i,(a,b) in enumerate(zip(points,points[1:]+points[:1],strict=True)):
                edge=BRepBuilderAPI_MakeEdge(gp_Pnt(a[0]*1000,a[1]*1000,0),gp_Pnt(b[0]*1000,b[1]*1000,0)).Edge(); wire.Add(edge)
                name="hot-wall" if i<n-1 else "axial-end" if i==n-1 else "outer-wall" if i<2*n-1 else "axial-start"
                edges.append((np.array([[a[0]*1000,a[1]*1000,0.],[b[0]*1000,b[1]*1000,0.]]),prefix+name))
            face=BRepBuilderAPI_MakeFace(wire.Wire(),True)
            require(face.IsDone(),"PROFILE_FAILED","Closed component profile face failed; no healing")
            revolver=BRepPrimAPI_MakeRevol(face.Face(),gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),sector[1],True) if sector else BRepPrimAPI_MakeRevol(face.Face(),gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),True)
            require(revolver.IsDone(),"REVOLVE_FAILED","Component profile revolution failed")
            # MakeWire can replace edges while sharing their endpoint vertices.
            # Bind labels to actual face edges by exact source endpoints within
            # floating-point roundoff, not to obsolete pre-wire object handles.
            for item in entities(face.Face(),TopAbs_EDGE):
                edge=TopoDS.Edge_s(item)
                endpoints=[]
                for vertex in (TopExp.FirstVertex_s(edge),TopExp.LastVertex_s(edge)):
                    point=BRep_Tool.Pnt_s(vertex); endpoints.append([point.X(),point.Y(),point.Z()])
                endpoints=np.array(endpoints)
                epsilon=64*np.finfo(float).eps*max(1.,float(np.abs(endpoints).max()))
                names={name for original,name in edges if np.allclose(endpoints,original,rtol=0,atol=epsilon) or np.allclose(endpoints,original[::-1],rtol=0,atol=epsilon)}
                require(len(names)==1,"SEMANTIC_EDGE_AMBIGUOUS","Actual profile edge must bind one exact source segment; no guessed face labels")
                name=next(iter(names))
                for generated in revolver.Generated(edge):
                    if generated.ShapeType()==TopAbs_FACE: labels.append((generated,name))
            if sector:
                labels.extend(((revolver.FirstShape(),prefix+"side-start"),(revolver.LastShape(),prefix+"side-end")))
                angle=sector[0]; r=np.array([[1.,0.,0.],[0.,math.cos(angle),-math.sin(angle)],[0.,math.sin(angle),math.cos(angle)]])
                return transformed(revolver.Shape(),labels,r,np.zeros(3))
            return revolver.Shape(),labels
        def indexed_labels(pairs):
            # OCCT's native IsSame shape-map semantics, never face-index guesses
            # or coordinate proximity. Cache each history traversal only once.
            index=TopTools_IndexedMapOfShape(); names={}
            for face,label in pairs:
                key=index.Add(face); names.setdefault(key,set()).add(label)
            return index,names
        def cut(shape,labels,tool,tool_labels):
            operation=BRepAlgoAPI_Cut(); arguments=TopTools_ListOfShape(); arguments.Append(shape); tools=TopTools_ListOfShape(); tools.Append(tool)
            operation.SetArguments(arguments); operation.SetTools(tools); operation.SetNonDestructive(True); operation.SetRunParallel(False); operation.Build()
            require(operation.IsDone(),"CUT_FAILED","Component Boolean subtraction failed; no repair")
            result=operation.Shape(); next_labels=[]; histories=[]
            for family in (labels,tool_labels):
                pairs=[]
                for original,name in family:
                    pairs.extend((face,name) for face in (original,*operation.Modified(original),*operation.Generated(original)))
                histories.append(indexed_labels(pairs))
            for face in entities(result,TopAbs_FACE):
                matches=set()
                for index,names in histories:
                    matches=names.get(index.FindIndex(face),set())
                    if matches:
                        break  # Surviving parent end faces keep their port semantics.
                next_labels.append((face,next(iter(matches)) if len(matches)==1 else "AMBIGUOUS" if matches else "UNRESOLVED"))
            return result,next_labels
        def properties(shape,surface=False):
            prop=GProp_GProps()
            (BRepGProp.SurfaceProperties_s if surface else BRepGProp.VolumeProperties_s)(shape,prop)
            p=prop.CentreOfMass()
            return prop.Mass()*(1e-6 if surface else 1e-9),[p.X()*.001,p.Y()*.001,p.Z()*.001]
        def pipe_elbow(pipe):
            axis = gp_Ax2(gp_Pnt(0,0,0),gp_Dir(1,0,0))
            outer = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(axis,pipe.outer_radius*1000)).Edge()).Wire()
            inner = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(axis,pipe.bore_radius*1000)).Edge()).Wire()
            maker = BRepBuilderAPI_MakeFace(outer,True)
            maker.Add(TopoDS.Wire_s(inner.Reversed()))
            require(maker.IsDone(),"PIPE_FACE_FAILED","Explicit annular elbow section failed; no healing")
            face = maker.Face()
            revolve = BRepPrimAPI_MakeRevol(face,gp_Ax1(gp_Pnt(0,pipe.bend_radius*1000,0),gp_Dir(0,0,1)),pipe.angle_rad,True)
            require(revolve.IsDone(),"PIPE_REVOLVE_FAILED","Circular annulus revolution failed")
            labels = [(revolve.FirstShape(),"pipe-end-a"),(revolve.LastShape(),"pipe-end-b")]
            for item in entities(face,TopAbs_EDGE):
                edge = TopoDS.Edge_s(item); radius = BRepAdaptor_Curve(edge).Circle().Radius()
                epsilon = 64*np.finfo(float).eps*max(1.,abs(radius))
                names = [name for original,name in ((pipe.bore_radius*1000,"pipe-inner-wall"),(pipe.outer_radius*1000,"pipe-outer-wall")) if abs(radius-original)<=epsilon]
                require(len(names)==1,"PIPE_SEMANTIC_EDGE","Actual section edge must bind exactly one source radius")
                labels.extend((generated,names[0]) for generated in revolve.Generated(edge) if generated.ShapeType()==TopAbs_FACE)
            return revolve.Shape(),labels
        compound=TopoDS_Compound(); builder=BRep_Builder(); builder.MakeCompound(compound)
        built=[]; manifest=[]; records=[]; total=0
        for i,part in enumerate(plan.parts):
            shape,labels=(pipe_elbow(part.pipe) if part.pipe and part.pipe.bend_radius is not None else
                          revolved(part.profile,part.sector,prefix="fluid." if part.role!="metal" else ""))
            for cavity in part.cavities:
                profile=cavity.profile
                if cavity.open_passage:
                    # Extend only into the already-empty plenum and exterior;
                    # no metal beyond the exact declared cap web is removed.
                    pad=10*request.source_tolerance_m+1e-8
                    profile=((profile[0][0]-pad,*profile[0][1:]),(profile[-1][0]+pad,*profile[-1][1:]))
                elif cavity.open_face:
                    pad=10*request.source_tolerance_m+1e-8
                    profile=((profile[0][0]-(pad if cavity.open_face=="start" else 0),*profile[0][1:]),
                             (profile[-1][0]+(pad if cavity.open_face=="end" else 0),*profile[-1][1:]))
                tool,tool_labels=revolved(profile,cavity.sector,prefix="manifold-"+cavity.role+"-plenum.")
                shape,labels=cut(shape,labels,tool,tool_labels)
            if part.cooling:
                c=part.cooling; rows=tuple((x,ri+c.hot_ligament,ri+c.hot_ligament+c.depth) for x,ri,_ in part.profile)
                for channel in range(c.count):
                    tool,tool_labels=revolved(rows,(c.phase_rad+2*math.pi*channel/c.count,c.width_rad),prefix="coolant-"+str(channel)+".")
                    shape,labels=cut(shape,labels,tool,tool_labels)
            for h,hole in enumerate(part.holes):
                axis=np.r_[1.,hole.slope_yz]; axis/=np.linalg.norm(axis)
                pad=10*request.source_tolerance_m+1e-8
                over=(pad+hole.radius*math.sqrt(max(0.,1-axis[0]**2)))/axis[0]
                begin,end=hole.axial_range or (part.profile[0][0],part.profile[-1][0])
                start=np.r_[begin,np.array(hole.center_yz)+begin*np.array(hole.slope_yz)]-axis*over
                tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*(start*1000)),gp_Dir(*axis)),hole.radius*1000,((end-begin)/axis[0]+2*over)*1000).Shape()
                label = ("manifold-"+hole.role+"-port-"+str(h) if hole.axial_range is not None else
                         "interface-fastener-clearance-"+str(h) if hole.role=="fastener-clearance" else
                         "injector-"+hole.role+"-port-"+str(h) if hole.role in {"fuel","oxidizer"} else "injector-port-"+str(h))
                shape,labels=cut(shape,labels,tool,[(face,label) for face in entities(tool,TopAbs_FACE)])
            rotation,translation=plan.placement(part.frame_id)
            shape,labels=transformed(shape,labels,rotation,translation)
            require(len(entities(shape,TopAbs_SOLID))==1 and BRepCheck_Analyzer(shape,True).IsValid(),"INVALID_COMPONENT_TOPOLOGY","Each declared part must be one valid solid; no sewing/healing/fusion")
            for other in built:
                common=BRepAlgoAPI_Common(shape,other)
                require(common.IsDone() and not entities(common.Shape(),TopAbs_SOLID),"COMPONENT_OVERLAP","Output part interiors overlap; choose only final operands or correct explicit placements")
            built.append(shape); builder.Add(compound,shape)
            faces=entities(shape,TopAbs_FACE); face_manifest=[]; face_index,face_names=indexed_labels(labels)
            for j,face in enumerate(faces):
                names=face_names.get(face_index.FindIndex(face),set())
                area,center=properties(face,True)
                face_manifest.append({"native_entity":"face-"+str(j),"semantic":next(iter(names)) if len(names)==1 else "UNRESOLVED","area_m2":area,"centroid_m":center})
            require(len(faces)<=5000,"COMPONENT_CAPACITY","Part exceeds the declared5000-face envelope")
            volume,center=properties(shape); box=Bnd_Box(); BRepBndLib.AddOptimal_s(shape,box,False,False)
            bounds=[v*.001 for v in box.Get()]
            require(volume>0,"INVALID_ORIENTATION","Positive signed component volume required")
            # Dense periodic fastener bores and toroidal elbows can be limited
            # by normal angle rather than the requested metric deflection.
            # Use0.1rad for these families, retaining the exact same linear
            # deflection and independent fidelity/topology/200k assembly limits.
            # This changes display/export tessellation, never analytic CAD.
            angular_dense = (part.pipe and part.pipe.bend_radius is not None) or any(h.role=="fastener-clearance" for h in part.holes)
            mesh_angle=.1 if angular_dense else .05
            mesher=BRepMesh_IncrementalMesh(shape,request.export_tolerance_m*1000*.6,False,mesh_angle,False)
            require(mesher.IsDone(),"EXPORT_FAILURE","Component tessellation failed")
            native=directory/("part-"+str(i)+"-mm.stl"); target=directory/("part-"+str(i)+".stl")
            writer=StlAPI_Writer(); writer.ASCIIMode=False
            require(not native.exists() and not target.exists() and writer.Write(shape,str(native)),"EXPORT_FAILURE","Refuse partial STL overwrite")
            try:
                encode_si_stl(native,target); raw=target.read_bytes(); count=int.from_bytes(raw[80:84],"little")
                records.append(raw[84:]); manifest.append({"part_id":part.part_id,"feature_id":part.feature_id,"frame_id":part.frame_id,"role":part.role,"triangle_start":total,"triangle_count":count,"volume_m3":volume,"centroid_m":center,"bounds_m":bounds,"faces":face_manifest}); total+=count
                require(total<=200000,"COMPONENT_CAPACITY","Combined STL exceeds200k-triangle qualified envelope; explicitly review a coarser export tolerance or split outputs")
            finally:
                native.unlink(missing_ok=True); target.unlink(missing_ok=True)
        source=directory/"source.brep"
        require(not source.exists() and BRepTools.Write_s(compound,str(source)),"EXPORT_FAILURE","Cannot create immutable component B-rep")
        stl=directory/"export.stl"
        with stl.open("xb") as stream: stream.write(b"COSMOS COMPONENT ASSEMBLY UNITS= m".ljust(80,b" ")+total.to_bytes(4,"little")+b"".join(records))
        STEPControl_Controller.Init_s(); require(Interface_Static.SetCVal_s("write.step.unit","M"),"EXPORT_FAILURE","Explicit metre STEP units required")
        writer=STEPControl_Writer(); writer.Model().SetLocalLengthUnit(1); writer.Model().SetWriteLengthUnit(1000)
        Interface_Static.SetIVal_s("write.precision.mode",1); Interface_Static.SetRVal_s("write.precision.val",request.export_tolerance_m*1000)
        step=directory/"export.step"
        require(not step.exists() and writer.Transfer(compound,STEPControl_AsIs)==IFSelect_RetDone and writer.Write(str(step))==IFSelect_RetDone,"EXPORT_FAILURE","Component STEP export failed")
        emit({**header,"event_type":"completed","source_name":"source.brep","source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
              "exports":[{"name":f.name,"format":f.suffix[1:],"file_unit":"m","sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in (step,stl)],
              "metrics":{"parts":manifest,"triangle_count":total,"kernel_unit":"mm","input_unit":"m","semantic_mapping":"construction-history-unresolved-blocks-handoff","assembly":"separate-declared-metal-and-fluid-bodies-not-automatic-fusion"}})
        return 0
    except Exception as error:  # noqa: BLE001 - typed isolated worker boundary
        emit({"protocol":PROTOCOL,"job_id":job,"correlation_id":correlation,"backend_version":VERSION,"event_type":"failed","code":error.code if isinstance(error,GeometryContractError) else "WORKER_FAILURE","message":str(error)[:1024]})
        return 2


if __name__=="__main__":
    raise SystemExit(main())
