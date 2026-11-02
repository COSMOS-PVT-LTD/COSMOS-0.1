import math

import pytest

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.si import UNIT_SPECIFIC_ENERGY
from systems.cycle.heated_feed_branch import CircularFeedCell, solve_heated_feed_branch
from tests.unit_tests.physics.test_heated_liquid_segment import table


def run(**updates):
    q=lambda v,u:Quantity(v,SI.get(u))
    cell=CircularFeedCell("straight-test-pipe","tank","injector",q(1,"m"),q(.01,"m"),q(0,"m"),q(0,"1"),q(.1,"W"),
        "Manufactured analytic circular-pipe fixture, NOT native sector cooling or hardware")
    args={"table":table(),"cells":(cell,),"source_interface":"tank","injector_interface":"injector",
        "source_temperature":q(115,"K"),"source_pressure":q(7e5,"Pa"),"chamber_pressure":q(5e5,"Pa"),
        "minimum_manifold_pressure":q(5.1e5,"Pa"),"injector_total_area":q(1e-7,"m2"),"discharge_coefficient":q(.7,"1"),
        "flow_lower":q(.001,"kg/s"),"flow_upper":q(.002,"kg/s"),"mass_tolerance":q(1e-8,"kg/s"),
        "pressure_tolerance":q(1e-4,"Pa"),"specific_energy_tolerance":Quantity(1e-7,UNIT_SPECIFIC_ENERGY),"max_iterations":100}
    return solve_heated_feed_branch(**(args|updates))


def test_branch_closes_geometry_derived_loss_and_actual_heated_injector_state():
    result=run()
    # Independent closed-form Poiseuille + orifice quadratic, not the
    # zero-pipe-loss capacity (.0014 kg/s) used as an approximate target.
    a=128*.001/(math.pi*1000*.01**4)
    b=(.7*1e-7)**2*2*1000
    expected=2*b*2e5/(math.sqrt((b*a)**2+4*b*2e5)+b*a)
    assert result.mass_flow_kg_s==pytest.approx(expected,abs=1e-10)
    assert abs(result.injector_residual_kg_s)<=1e-8
    assert result.manifold_temperature_k>115 and result.manifold_pressure_pa<7e5
    assert result.prescribed_heat_w==.1 and not result.engine_operating_point_complete
    assert result.physical_validation=="NOT_PERFORMED"


def test_route_order_and_input_bracket_are_not_invented():
    with pytest.raises(InvalidInputError):run(source_interface="unconnected-tank")
    with pytest.raises(InvalidInputError):run(injector_interface="other-manifold")
    with pytest.raises(OutOfRangeError):run(flow_lower=Quantity(.0018,SI.get("kg/s")))


def test_no_circular_pipe_substitution_for_a_sector_passage():
    with pytest.raises(InvalidInputError):run(cells=({"native_sector":"channels","hydraulic_diameter":"guess"},))
