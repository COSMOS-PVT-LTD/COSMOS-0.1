import json

import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.mesh.connectivity import build
from numerics.mesh.grid_generation import uniform_1d, uniform_2d
from numerics.mesh.quality import polygon_quality, structured_quality
from numerics.mesh.refinement import refine
from numerics.mesh.unstructured_mesh import UnstructuredMesh


def test_structured_1d_refinement_serialization():
    mesh=uniform_1d(0,1,4)
    np.testing.assert_array_equal(mesh.cells,[[0,1],[1,2],[2,3],[3,4]])
    assert mesh.node_index(3)==3
    fine=refine(mesh)
    np.testing.assert_array_equal(fine.x[::2],mesh.x)
    assert len(fine.cells)==8
    assert json.loads(mesh.to_json())["kind"]=="structured"
    assert mesh.to_json()==uniform_1d(0,1,4).to_json()
    connectivity=build(mesh.cells,len(mesh.nodes))
    assert sum(len(c)==2 for c in connectivity.face_cells)==3
    assert structured_quality(mesh).minimum_measure==.25

def test_structured_2d_shared_faces_and_quality():
    mesh=uniform_2d((0,2),(0,1),2,2)
    assert mesh.node_index(2,1)==5
    np.testing.assert_array_equal(mesh.cells[0],[0,1,4,3])
    connectivity=build(mesh.cells,len(mesh.nodes))
    assert len(connectivity.faces)==12
    assert sum(len(c)==2 for c in connectivity.face_cells)==4
    assert len(refine(mesh).cells)==16
    assert structured_quality(mesh).maximum_edge_ratio==2
    assert polygon_quality(mesh.nodes,mesh.cells).minimum_measure==.5
    with pytest.raises(InvalidInputError):
        mesh.node_index(3,0)

def test_unstructured_real_data_and_bad_cells():
    nodes=[[0,0],[1,0],[1,1],[0,1]]
    mesh=UnstructuredMesh.build(nodes,[[0,1,2],[0,2,3]])
    assert len(build(mesh.cells,4).faces)==5
    assert mesh.to_json()==UnstructuredMesh.build(nodes,[[0,1,2],[0,2,3]]).to_json()
    for cells in ([[0,2,1]],[[0,1,9]],[[0,1,1]],[[0,1,2.5]]):
        with pytest.raises(InvalidInputError):
            UnstructuredMesh.build(nodes,cells)
    with pytest.raises(InvalidInputError):
        build([[0,1,2],[0,1,3],[0,1,4]],5)
