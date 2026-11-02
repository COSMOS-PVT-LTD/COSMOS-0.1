"""Separate bounded implicit-component mesh QA; existing analytic QA stays unchanged."""
from pathlib import Path
import numpy as np

from systems.contracts.geometry._wire import require
from systems.geometry.qa import STL_RECORD, distances_to_triangles

MAX_TRIANGLES=4_000_000


def read_mesh(path:Path):
    require(path.is_file() and not path.is_symlink() and 84<path.stat().st_size<=256*1024**2,"PICO_STL","Bounded owned STL required")
    raw=path.read_bytes();count=int.from_bytes(raw[80:84],"little")
    require(b"UNITS= m" in raw[:80] and 0<count<=MAX_TRIANGLES and len(raw)==84+50*count,"PICO_STL","Explicit SI and complete bounded binary triangles required")
    records=np.frombuffer(raw,STL_RECORD,count=count,offset=84)
    require(bool(np.isfinite(records["vertices"]).all()) and bool(np.isfinite(records["normal"]).all()),"PICO_STL","Nonfinite encoded mesh")
    return raw,records


def audit_part(records,reference,limits,check_budget):
    """Independent encoded triangles/formulas; no native-kernel measurements trusted."""
    check_budget();tri=records["vertices"].astype(float);normals=records["normal"].astype(float)
    cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);lengths=np.linalg.norm(cross,axis=1)
    vertices,ids=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True);faces=ids.reshape(-1,3)
    directed=np.vstack((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]))
    edges,inverse,counts=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
    orientation=np.bincount(inverse,weights=np.where(directed[:,0]<directed[:,1],1,-1))
    parents=np.arange(len(vertices))
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for i,(a,b) in enumerate(edges):
        if i%65536==0:check_budget()
        parents[find(a)]=find(b)
    components=len({find(i) for i in range(len(vertices))})
    six=np.einsum("ij,ij->i",tri[:,0],np.cross(tri[:,1],tri[:,2]));volume=float(six.sum()/6)
    require(np.isfinite(volume) and volume>0,"PICO_VOLUME","Encoded mesh has no positive finite volume")
    centroid=(six[:,None]*tri.sum(axis=1)).sum(axis=0)/(24*volume)
    euler=len(vertices)-len(edges)+len(faces)
    topology=bool((lengths>0).all() and (counts==2).all() and (orientation==0).all() and components==1 and euler==reference.part.euler
        and len(np.unique(np.sort(faces,axis=1),axis=0))==len(faces))
    if topology:topology=bool((np.einsum("ij,ij->i",normals,cross/lengths[:,None])>.999).all())
    forward=[]
    for points in (vertices,tri.mean(axis=1)):
        for i in range(0,len(points),16384):check_budget();forward.extend(np.abs(reference.sdf(points[i:i+16384])).tolist())
    forward=np.asarray(forward)
    # Near-collinear positive-area triangles can lose the barycentric denominator
    # to roundoff. The shared routine still tests all edge distances; any absent
    # finite witness fails below rather than fabricating a successful distance.
    with np.errstate(invalid="ignore",divide="ignore"):
        reverse=distances_to_triangles(reference.surface_samples(),tri,ceiling_m=limits.reverse_m,check_budget=check_budget) if topology else np.array([])
    reverse_finite=bool(len(reverse) and np.isfinite(reverse).all())
    volume_error=abs(volume-reference.volume_m3)/reference.volume_m3;centroid_error=float(np.linalg.norm(centroid-reference.centroid_m))
    bounds=np.r_[vertices.min(axis=0),vertices.max(axis=0)];bound_error=float(np.max(np.abs(bounds-reference.bounds_m)))
    dimensions=bool(topology and reverse_finite and volume_error<=limits.relative_volume and centroid_error<=limits.centroid_m
        and forward.max()<=limits.forward_m and reverse.max()<=limits.reverse_m and bound_error<=limits.reverse_m)
    return {"part_id":reference.part.part_id,"role":reference.part.role,"pass":dimensions,"topology_pass":topology,"dimensions_pass":dimensions,
        "triangle_count":len(tri),"euler_characteristic":euler,"expected_euler_characteristic":reference.part.euler,"components":components,
        "nonmanifold_edges":int((counts!=2).sum()),"orientation_errors":int((orientation!=0).sum()),"degenerate_faces":int((lengths==0).sum()),
        "volume_m3":volume,"relative_volume_error":volume_error,"centroid_m":centroid.tolist(),"centroid_error_m":centroid_error,
        "bounds_m":bounds.tolist(),"bounds_error_m":bound_error,"surface_area_m2":float(lengths.sum()/2),
        "forward_max_m":float(forward.max()),"forward_p95_m":float(np.percentile(forward,95)),"forward_sample_count":len(forward),
        "reverse_max_m":float(reverse.max()) if reverse_finite else None,"reverse_p95_m":float(np.percentile(reverse,95)) if reverse_finite else None,
        "reverse_samples":len(reverse),"unmatched_reverse_samples":int((~np.isfinite(reverse)).sum()),"limits":{"relative_volume":limits.relative_volume,"centroid_m":limits.centroid_m,"forward_m":limits.forward_m,"reverse_m":limits.reverse_m},
        "units":"m","physical_validation":"NOT_PERFORMED","scope":"Independent STL topology/integrals and sampled signed-CSG residual/point-to-triangle comparisons; not certified Hausdorff, self-intersection or manufacturing acceptance"}
