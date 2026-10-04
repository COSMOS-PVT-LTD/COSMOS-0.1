import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_volume import convection, diffusion, interpolation
from numerics.finite_volume.control_volume import ControlVolumes
from numerics.finite_volume.fluxes import cell_outward_fluxes
from numerics.finite_volume.fv_solver import solve
from numerics.utilities.convergence import observed_order


@pytest.mark.parametrize("v",[-2.,0.,2.])
def test_constant_conservation(v):
    edges=np.linspace(0,1,11)
    result=solve(edges,np.zeros(10),DirichletBoundary(3,3),velocity=v)
    np.testing.assert_allclose(result.solution.value,3,atol=3e-14)
    np.testing.assert_allclose(result.face_fluxes,3*v,atol=5e-14)
    assert abs(result.global_balance)<1e-12

def test_linear_diffusion_and_internal_cancellation():
    edges=np.array([0.,.1,.3,.6,1.])
    cells=ControlVolumes.build(edges)
    result=solve(edges,np.zeros(4),DirichletBoundary(1,3))
    np.testing.assert_allclose(result.solution.value,1+2*cells.centers,atol=1e-13)
    np.testing.assert_allclose(result.face_fluxes,-2,atol=1e-13)
    outward=cell_outward_fluxes(result.face_fluxes)
    np.testing.assert_array_equal(outward[:-1,1]+outward[1:,0],0)
    assert abs(outward.sum())<1e-13

def test_manufactured_refinement():
    errors=[]
    for n in (10,20,40):
        edges=np.linspace(0,1,n+1)
        cells=ControlVolumes.build(edges)
        result=solve(edges,np.pi**2*np.sin(np.pi*cells.centers),DirichletBoundary(0,0))
        errors.append(np.max(np.abs(result.solution.value-np.sin(np.pi*cells.centers))))
        assert result.cell_balance_norm<1e-11
        assert abs(result.global_balance)<1e-11
    assert observed_order(errors[0],errors[1])==pytest.approx(2,abs=.02)
    assert observed_order(errors[1],errors[2])==pytest.approx(2,abs=.02)

def test_fluxes_and_bad_input():
    assert convection.flux(2,3,4)==8
    assert convection.flux(2,3,-4)==-12
    assert diffusion.flux(2,3,.5,2)==-4
    assert interpolation.linear(2,4,.25)==2.5
    with pytest.raises(InvalidInputError):
        interpolation.linear(1,2,2)
    with pytest.raises(InvalidInputError):
        solve([0,1],[0],DirichletBoundary(0,1),diffusivity=0)
    with pytest.raises(InvalidInputError):
        ControlVolumes.build([0,0,1])
