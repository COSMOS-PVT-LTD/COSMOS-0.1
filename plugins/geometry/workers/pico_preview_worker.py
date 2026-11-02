"""Display-only mesh reduction in a pinned process; never geometry generation."""
import json
from pathlib import Path
import sys

import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints,vtkVersion
from vtkmodules.vtkCommonDataModel import vtkCellArray,vtkPolyData
from vtkmodules.vtkFiltersCore import vtkDecimatePro,vtkQuadricDecimation
from vtkmodules.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy

from systems.geometry.qa import STL_RECORD
from plugins.geometry.display_encoding import remove_dangling_display_flaps


def reduced(path,part,target):
    """One part's VTK lifetime; never retain its large input into the next part."""
    count=part["triangle_count"]
    with path.open("rb") as f:
        f.seek(84+50*part["triangle_start"]);source=np.fromfile(f,dtype=STL_RECORD,count=count)
    tri=source["vertices"];assert len(source)==count and np.isfinite(tri).all()
    if target>=count:return tri.astype("<f4",copy=True)
    vertices,ids=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True)
    del tri,source
    points=vtkPoints();points.SetData(numpy_to_vtk(vertices.astype(np.float64),deep=True))
    cells=vtkCellArray();cells.SetData(numpy_to_vtkIdTypeArray(np.arange(count+1,dtype=np.int64)*3,deep=True),numpy_to_vtkIdTypeArray(ids.astype(np.int64),deep=True))
    assert cells.ConvertTo32BitStorage()  # Bounded <4M vertices/cells; exact integer IDs.
    del vertices,ids
    mesh=vtkPolyData();mesh.SetPoints(points);mesh.SetPolys(cells)
    del points,cells
    if count>800000:
        # A tight display-only prepass bounds the more memory-heavy quadric
        # input. Independent encoded QA remains the acceptance authority.
        coarse=vtkDecimatePro();coarse.SetInputData(mesh);coarse.SetTargetReduction(1-600000/count)
        coarse.PreserveTopologyOn();coarse.SplittingOff();coarse.BoundaryVertexDeletionOff()
        coarse.SetErrorIsAbsolute(1);coarse.SetAbsoluteError(1e-7);coarse.SetOutputPointsPrecision(1)
        coarse.Update();compact=vtkPolyData();compact.DeepCopy(coarse.GetOutput())
        del coarse,mesh
        mesh=compact;count=mesh.GetNumberOfPolys()
        print(part["part_id"],"1e-7 m absolute-error prepass ->",count,file=sys.stderr)
    reducer=vtkQuadricDecimation();reducer.SetInputData(mesh);reducer.SetTargetReduction(1-target/count)
    reducer.VolumePreservationOn();reducer.AttributeErrorMetricOff();reducer.Update()
    result=reducer.GetOutput();positions=vtk_to_numpy(result.GetPoints().GetData())
    offsets=vtk_to_numpy(result.GetPolys().GetOffsetsArray());indices=vtk_to_numpy(result.GetPolys().GetConnectivityArray())
    assert np.all(np.diff(offsets)==3)
    return positions[indices.reshape(-1,3)].astype("<f4",copy=True)


def main():
    value=json.loads(sys.stdin.buffer.read(65537))
    assert set(value)=={"parts","sha256"} and vtkVersion.GetVTKVersion()=="9.3.1"
    from hashlib import sha256
    path=Path.cwd()/"input.stl";assert path.is_file() and not path.is_symlink() and 84<path.stat().st_size<=256*1024**2
    digest=sha256()
    with path.open("rb") as f:
        header=f.read(84);digest.update(header);count=int.from_bytes(header[80:84],"little")
        for block in iter(lambda:f.read(1024**2),b""):digest.update(block)
    assert b"UNITS= m" in header[:80] and 0<count<=4000000 and path.stat().st_size==84+50*count and digest.hexdigest()==value["sha256"]
    arrays=[];parts=[];start=0;n=count;weight=sum(np.sqrt(p["triangle_count"]) for p in value["parts"])
    for p in value["parts"]:
        count=p["triangle_count"];target=min(count,4+int(np.sqrt(count)*(199800-4*len(value["parts"]))/weight))
        tri=reduced(path,p,target)
        tri=np.asarray(tri,dtype="<f4");assert np.isfinite(tri).all()
        tri,removed_flaps=remove_dangling_display_flaps(tri)
        print(p["part_id"],count,"->",len(tri),"target",target,file=sys.stderr)
        arrays.append(tri);parts.append({**p,"source_triangle_start":p["triangle_start"],"source_triangle_count":count,"triangle_start":start,"triangle_count":len(tri),"removed_display_flap_faces":removed_flaps});start+=len(tri)
    assert 0<start<=199900,"Topology-preserving reduction cannot meet viewport budget; no triangle-discard fallback"
    data=np.concatenate(arrays).tobytes()
    with Path("positions.f32").open("xb") as f:f.write(data)
    print(json.dumps({"parts":parts,"sha256":sha256(data).hexdigest(),"method":"VTK 9.3.1 vtkDecimatePro prepass for parts over 800k faces (absolute-error option 1e-7 m, topology preservation on, splitting/boundary deletion off), then vtkQuadricDecimation; volume preservation on; double-coordinate input; square-root per-part budget; exact dangling single-face flap cleanup; independent encoded topology and source-dimension checks required"}))


if __name__=="__main__":main()
