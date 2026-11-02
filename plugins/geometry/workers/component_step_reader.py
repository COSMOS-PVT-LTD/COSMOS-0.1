"""Pinned separate Gmsh reimport; no CAD-construction imports or acceptance authority."""

import json
import math
import os
import sys
from pathlib import Path


def main():
    output=os.fdopen(os.dup(1),"w",buffering=1); os.dup2(2,1)
    if len(sys.argv)!=2: raise ValueError("Exactly one retained STEP candidate required")
    path=Path(sys.argv[1])
    if not path.is_absolute() or path.is_symlink() or not 0<path.stat().st_size<=64*1024**2: raise ValueError("Bounded immutable STEP required")
    raw=sys.stdin.buffer.read(16*1024**2+1)
    if len(raw)>16*1024**2: raise ValueError("Component reimport sample payload exceeds bound")
    request=json.loads(raw)
    if set(request)!={"parts","body_relative_volume","body_centroid_m","reverse_distance_m"} or not 1<=len(request["parts"])<=24: raise ValueError("Exact bounded component reimport request required")
    for key in ("body_relative_volume","body_centroid_m","reverse_distance_m"):
        if type(request[key]) not in (int,float) or not math.isfinite(request[key]) or not 0<request[key]<.1: raise ValueError("Explicit finite reimport limits required")
    import gmsh  # type: ignore[import-not-found]
    import numpy as np
    expected=[]
    for part in request["parts"]:
        if set(part)!={"id","volume_m3","centroid_m","bounds_m","samples_m"}: raise ValueError("Exact part-matching/sample fields required")
        samples=np.array(part["samples_m"],dtype=float)
        if samples.ndim!=2 or samples.shape[1]!=3 or not 1<=len(samples)<=30000 or not np.isfinite(samples).all() or np.abs(samples).max()>10: raise ValueError("Bounded finite actual reference samples required")
        expected.append((part,samples))
    gmsh.initialize([],readConfigFiles=False)
    try:
        if gmsh.__version__!="4.15.0": raise ValueError("Pinned Gmsh4.15.0 required")
        gmsh.option.setNumber("General.Terminal",0); gmsh.option.setNumber("General.NumThreads",1)
        gmsh.option.setString("Geometry.OCCTargetUnit","MM"); gmsh.option.setNumber("Geometry.OCCAutoFix",0)
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl",1); gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative",0)
        deflection=request["reverse_distance_m"]/10
        gmsh.option.setNumber("Mesh.StlLinearDeflection",deflection*1000)
        gmsh.model.add("independent-component-reimport"); gmsh.model.occ.importShapes(str(path)); gmsh.model.occ.synchronize()
        bodies=gmsh.model.getEntities(3)
        if len(bodies)!=len(expected) or len(gmsh.model.getEntities(2))>12000: raise ValueError("STEP hierarchy/body count/face envelope differs from exact admitted components")
        descriptors=[]
        for _,tag in bodies:
            descriptors.append({"tag":tag,"volume_m3":gmsh.model.occ.getMass(3,tag)*1e-9,"centroid_m":np.array(gmsh.model.occ.getCenterOfMass(3,tag))*.001,"bounds_m":np.array(gmsh.model.getBoundingBox(3,tag))*.001})
        assignments=[]; used=set()
        for part,samples in expected:
            matches=[d for d in descriptors if abs(d["volume_m3"]-part["volume_m3"])/part["volume_m3"]<=request["body_relative_volume"]
                     and np.linalg.norm(d["centroid_m"]-part["centroid_m"])<=request["body_centroid_m"]
                     and np.max(np.abs(d["bounds_m"]-part["bounds_m"]))<=request["reverse_distance_m"]]
            if len(matches)!=1 or matches[0]["tag"] in used: raise ValueError("Ambiguous/missing actual imported body; no automatic remap or latest-body substitution")
            used.add(matches[0]["tag"]); assignments.append((part,samples,matches[0]))
        bounds=gmsh.model.getBoundingBox(-1,-1); size=max(bounds[i+3]-bounds[i] for i in range(3))/32
        gmsh.option.setNumber("Mesh.MeshSizeMin",size/2); gmsh.option.setNumber("Mesh.MeshSizeMax",size)
        local_sizes={}
        for _,tag in bodies:
            faces=gmsh.model.getBoundary([(3,tag)],combined=False,oriented=False,recursive=False)
            cylinders=[abs(face) for _,face in faces if gmsh.model.getType(2,abs(face))=="Cylinder"]
            planes=[face for _,face in faces if gmsh.model.getType(2,abs(face))=="Plane"]
            # Independently imported annular tubes can be far smaller than the
            # assembly bounding box. Its old global minimum produced periodic
            # cylinder meshes with four incident triangles on one linear edge.
            # Resolve actual CAD curvature, without healing, welding, deleting
            # elements, changing expected Euler values or widening QA limits.
            tube=len(faces)==4 and len(cylinders)==2 and len(planes)==2
            radii=[];long_cylinders=[]
            for face in cylinders:
                low,high=gmsh.model.getParametrizationBounds(2,face)
                curvature=float(np.max(np.abs(gmsh.model.getCurvature(2,face,((np.array(low)+np.array(high))/2).tolist()))))
                if not math.isfinite(curvature) or curvature<=0:raise ValueError("Imported cylinder curvature unavailable for bounded tube meshing")
                radii.append(1/curvature)
                derivative=gmsh.model.getDerivative(2,face,((np.array(low)+np.array(high))/2).tolist())
                length=(high[1]-low[1])*float(np.linalg.norm(derivative[3:]))
                if not math.isfinite(length) or length<0:raise ValueError("Imported cylinder axial extent unavailable")
                if length*curvature/2>4:long_cylinders.append((face,1/curvature))
            if tube:
                local_size=min(size,min(radii)/4)
                points=gmsh.model.getBoundary([(3,tag)],combined=False,oriented=False,recursive=True)
                for point in points:local_sizes[point]=min(local_sizes.get(point,size),local_size)
            else:
                # Slender imported bores in large annular headers have the
                # same coarse periodic-seam pathology. Refine their own CAD
                # boundary vertices, not every face of the assembly. The4:1
                # aspect is a meshing trigger, NOT a fluid-flow correlation.
                for face,radius in long_cylinders:
                    points=gmsh.model.getBoundary([(2,face)],combined=False,oriented=False,recursive=True)
                    for point in points:local_sizes[point]=min(local_sizes.get(point,size),radius/4)
        for point,local_size in local_sizes.items():gmsh.model.mesh.setSize([point],local_size)
        if local_sizes:gmsh.option.setNumber("Mesh.MeshSizeMin",min(size/2,min(local_sizes.values())/2))
        gmsh.model.mesh.generate(2)
        tags,coordinates,_=gmsh.model.mesh.getNodes()
        if len(tags)>100000: raise ValueError("Independent component reimport exceeds100k total-node sampling budget")
        node_map={int(tag):i for i,tag in enumerate(tags)}; positions=np.array(coordinates).reshape(-1,3)*.001
        result=[]
        for part,samples,body in assignments:
            faces=gmsh.model.getBoundary([(3,body["tag"])],combined=False,oriented=False,recursive=False)
            if len(faces)>5000: raise ValueError("Body face count exceeds qualified envelope")
            best=np.full(len(samples),np.inf); descriptors=[]; triangles=[]
            for _,face in faces:
                face=abs(face); area=gmsh.model.occ.getMass(2,face)*1e-6; center=np.array(gmsh.model.occ.getCenterOfMass(2,face))*.001
                descriptors.append({"entity_ref":"step-body-"+str(body["tag"])+".face-"+str(face),"area_m2":area,"centroid_m":center.tolist(),"carrier":gmsh.model.getType(2,face)})
                box=np.array(gmsh.model.getBoundingBox(2,face))*.001
                indices=np.flatnonzero(((samples>=box[:3]-request["reverse_distance_m"]) & (samples<=box[3:]+request["reverse_distance_m"])).all(axis=1))
                if len(indices):
                    closest,uv=gmsh.model.getClosestPoint(2,face,(samples[indices]*1000).reshape(-1).tolist())
                    inside=np.array([gmsh.model.isInside(2,face,uv[i:i+2],parametric=True)==1 for i in range(0,len(uv),2)])
                    distances=np.linalg.norm(np.array(closest).reshape(-1,3)*.001-samples[indices],axis=1)
                    best[indices]=np.minimum(best[indices],np.where(inside,distances,np.inf))
                kinds,_,nodes=gmsh.model.mesh.getElements(2,face)
                if list(kinds)!=[2]: raise ValueError("Linear imported surface triangles required")
                triangles.extend(np.array(nodes[0]).reshape(-1,3).tolist())
            tris=np.array(triangles,dtype=np.int64)
            directed=np.vstack((tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]))
            edges,inverse,counts=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
            orientation=np.bincount(inverse,weights=np.where(directed[:,0]<directed[:,1],1,-1))
            used_nodes=np.unique(tris); actual=positions[[node_map[int(tag)] for tag in used_nodes]]
            if len(actual)>30000: raise ValueError("Body exceeds30k actual surface-node bound")
            result.append({"part_id":part["id"],"volume_m3":body["volume_m3"],"centroid_m":body["centroid_m"].tolist(),"bounds_m":body["bounds_m"].tolist(),"faces":descriptors,
                           "surface_samples_m":actual.tolist(),"reverse_distances_m":[float(v) if np.isfinite(v) else None for v in best],"unmatched_reverse_samples":int((~np.isfinite(best)).sum()),
                           "nonmanifold_edges":int((counts!=2).sum()),"orientation_errors":int((orientation!=0).sum()),"euler_characteristic":len(used_nodes)-len(edges)+len(tris),"triangle_count":len(tris)})
        print(json.dumps({"reader":"gmsh","version":gmsh.__version__,"units":"m","import_unit":"mm","bbox_deflection_m":deflection,"parts":result},allow_nan=False),file=output,flush=True)
    finally:
        gmsh.finalize()


if __name__=="__main__":
    main()
