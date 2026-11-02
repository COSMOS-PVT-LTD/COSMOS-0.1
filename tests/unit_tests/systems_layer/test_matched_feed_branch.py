from dataclasses import replace

import pytest

from core.exceptions import InvalidInputError
from physics.exceptions import OutOfRangeError
from systems.cycle.matched_feed_branch import MatchedFeedCell, solve_matched_feed_branch
from tests.unit_tests.physics.test_matched_liquid_cell import arguments, q


def run(**updates):
    a=arguments();cell=MatchedFeedCell("heated","tank","injector",a["geometry"],a["transfer"],a["conductivity"],
        a["gas_temperature"],a["gas_coefficient"],a["outlet_temperature_lower"],a["outlet_temperature_upper"])
    values={"table": a["table"],"cells": (cell,),"source_interface": "tank","injector_interface": "injector",
        "source_temperature": a["inlet_temperature"],"source_pressure": a["inlet_pressure"],
        "chamber_pressure": q(5e5,"Pa"),"minimum_manifold_pressure": q(5.1e5,"Pa"),"injector_total_area": q(1e-7,"m2"),
        "discharge_coefficient": q(.7,"1"),"flow_lower": q(.001,"kg/s"),"flow_upper": q(.002,"kg/s"),"mass_tolerance": q(1e-8,"kg/s"),
        "power_tolerance": a["power_tolerance"],"pressure_tolerance": a["pressure_tolerance"],"max_iterations": 100}
    return solve_matched_feed_branch(**(values|updates))


def test_wall_heat_heated_liquid_pressure_and_injector_close_together():
    result=run()
    assert abs(result.injector_residual_kg_s)<=1e-8
    assert result.total_heat_w>0 and result.manifold_temperature_k>115
    assert result.manifold_pressure_pa<7e5 and abs(result.energy_residual_w)<1e-7
    assert result.cells[0].mass_flow_kg_s==result.mass_flow_kg_s
    assert not result.engine_operating_point_complete and result.physical_validation=="NOT_PERFORMED"


def test_unconnected_or_unbracketed_route_cannot_be_solved_by_invented_loss():
    with pytest.raises(InvalidInputError):run(source_interface="other")
    with pytest.raises(InvalidInputError):run(injector_interface="other")
    with pytest.raises(OutOfRangeError):run(flow_lower=q(.0018,"kg/s"))


def test_supplied_transfer_domain_error_propagates_without_cold_fallback():
    a=arguments()
    def unsupported(*args):raise OutOfRangeError("Actual sector correlation not supplied")
    cell=MatchedFeedCell("sector","tank","injector",a["geometry"],unsupported,a["conductivity"],
        a["gas_temperature"],a["gas_coefficient"],a["outlet_temperature_lower"],a["outlet_temperature_upper"])
    with pytest.raises(OutOfRangeError,match="Actual sector"):run(cells=(replace(cell,cell_id="no-guess"),))


def test_injector_uses_recomputed_heated_density_not_cold_input_density():
    a=arguments();constant=run()
    # Manufactured variable-density field for algebraic coupling verification,
    # NOT a thermodynamic EOS or a methane/LOX validation reference.
    surface=replace(a["table"],states=tuple(tuple(replace(s,density_kg_m3=1000/(1+.002*(t-115)))
        for s in row) for t,row in zip(a["table"].temperatures_k,a["table"].states,strict=True)))
    heated=run(table=surface)
    last=heated.cells[-1]
    expected=.7*1e-7*(2*last.outlet_state.density_kg_m3*(heated.manifold_pressure_pa-5e5))**.5
    cold_guess=.7*1e-7*(2*1000*(heated.manifold_pressure_pa-5e5))**.5
    assert heated.injector_capacity_kg_s==pytest.approx(expected,rel=1e-14)
    assert abs(heated.mass_flow_kg_s-cold_guess)>100*1e-8
    assert heated.mass_flow_kg_s<constant.mass_flow_kg_s
