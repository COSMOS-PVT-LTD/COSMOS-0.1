import math
from dataclasses import replace

import pytest

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.feed.matched_liquid_cell import (
    PassageGeometry,
    PassageTransfer,
    matched_liquid_cell,
)
from physics.heat_transfer.temperature_wall import ConductivityCurve
from physics.si import UNIT_HTC
from tests.unit_tests.physics.test_heated_liquid_segment import table


def q(v,u):return Quantity(v,UNIT_HTC if u=="W/m2/K" else SI.get(u))


def response(geometry,state,re,pr,t,p):
    if re>2300:raise OutOfRangeError("Synthetic circular Poiseuille fixture only, not a native sector model")
    return PassageTransfer(64/re,q(5000,"W/m2/K"),"Analytic manufactured circular response; NOT engine/hardware evidence","1"*64,geometry.source_graph_id)


def arguments():
    area=math.pi*.01**2/4;surface=math.pi*.01
    geometry=PassageGeometry(q(area,"m2"),q(.01,"m"),q(1,"m"),q(surface,"m2"),q(surface,"m2"),
        q(surface,"m2"),q(.001,"m"),1,"synthetic-circular-graph","CONSTANT_AREA_FLOW_NORMAL")
    return {"table": table(),"geometry": geometry,"transfer": response,
        "conductivity": ConductivityCurve("SYNTHETIC","analytic fixture only",(100.,1000.),(200.,200.),"Manufactured constant k", "2"*64),
        "mass_flow": q(.0014,"kg/s"),"inlet_temperature": q(115,"K"),"inlet_pressure": q(7e5,"Pa"),"outlet_pressure_min": q(5e5,"Pa"),
        "outlet_temperature_lower": q(115,"K"),"outlet_temperature_upper": q(130,"K"),"gas_temperature": q(600,"K"),"gas_coefficient": q(1,"W/m2/K"),
        "power_tolerance": q(1e-7,"W"),"pressure_tolerance": q(1e-5,"Pa"),"max_iterations": 100}


def test_independent_coupled_convection_wall_enthalpy_and_poiseuille_solution():
    result=matched_liquid_cell(**arguments());mass=.0014;surface=math.pi*.01
    resistance=(1+1/5000+.001/200)/surface
    pressure_drop=128*.001*mass/(math.pi*1000*.01**4)
    # h=Cp(T-100)+P/rho; pressure work retained in the independent balance.
    heat=(600-115-pressure_drop/(2*1000*2000))/(resistance+1/(2*mass*2000))
    assert result.heat_w==pytest.approx(heat,abs=2e-7)
    assert result.outlet_temperature_k==pytest.approx(115+(heat/mass+pressure_drop/1000)/2000,abs=2e-9)
    assert 7e5-result.outlet_pressure_pa==pytest.approx(pressure_drop,abs=1e-5)
    assert abs(result.energy_residual_w)<1e-7 and abs(result.momentum_residual_pa)<1e-5
    assert result.wall.hot_wall_temperature_k>result.wall.cold_wall_temperature_k>115
    assert result.physical_validation=="NOT_PERFORMED"


def test_heat_is_recomputed_when_flow_gas_and_wall_change():
    args=arguments();a=matched_liquid_cell(**args)
    b=matched_liquid_cell(**(args|{"mass_flow": q(.001,"kg/s")}))
    c=matched_liquid_cell(**(args|{"gas_temperature": q(500,"K")}))
    assert b.heat_w<a.heat_w and b.outlet_temperature_k>a.outlet_temperature_k
    assert c.heat_w<a.heat_w


def test_identical_parallel_passages_preserve_per_passage_solution():
    args=arguments();one=matched_liquid_cell(**args)
    many=matched_liquid_cell(**(args|{"geometry": replace(args["geometry"],parallel_count=6),"mass_flow": q(.0084,"kg/s")}))
    assert many.heat_w==pytest.approx(6*one.heat_w,abs=1e-6)
    assert many.outlet_temperature_k==pytest.approx(one.outlet_temperature_k,abs=1e-8)


def test_axial_geometry_missing_response_stale_graph_and_phase_exit_fail_closed():
    args=arguments()
    with pytest.raises(InvalidInputError,match="flow-normal"):
        matched_liquid_cell(**(args|{"geometry": replace(args["geometry"],section_basis="LOCAL_AXIAL_NOT_FLOW_NORMAL")}))
    with pytest.raises(InvalidInputError):matched_liquid_cell(**(args|{"transfer": None}))
    def stale(*values):return replace(response(*values),geometry_graph_id="different")
    with pytest.raises(InvalidInputError,match="Source-bound"):matched_liquid_cell(**(args|{"transfer": stale}))
    with pytest.raises(OutOfRangeError):matched_liquid_cell(**(args|{"gas_coefficient": q(1000,"W/m2/K")}))


@pytest.mark.parametrize("field",["mass_flow","inlet_temperature","gas_coefficient","power_tolerance"])
def test_non_boolean_dimensioned_inputs_required(field):
    args=arguments();args[field]=True
    with pytest.raises(InvalidInputError):matched_liquid_cell(**args)
