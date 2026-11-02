"""Exact combinatorial cleanup for reduced DISPLAY meshes, never original CAD/STL."""
import numpy as np


def remove_dangling_display_flaps(triangles):
    """Remove a dangling single-face flap joined to one otherwise closed edge.

    Require two boundary edges, one three-face edge and one vertex referenced
    by this triangle alone. No coordinate welding, area epsilon, smoothing,
    hole filling or original-artifact mutation. Independent QA must still pass.
    """
    _,ids=np.unique(triangles.reshape(-1,3),axis=0,return_inverse=True)
    faces=ids.reshape(-1,3);n=len(faces)
    edges=np.vstack((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]))
    _,inverse,counts=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True)
    incidence=np.sort(counts[inverse].reshape(3,n).T,axis=1)
    vertex_count=np.bincount(ids)
    remove=np.all(incidence==[1,1,3],axis=1)&np.any(vertex_count[faces]==1,axis=1)
    return triangles[~remove],int(remove.sum())
