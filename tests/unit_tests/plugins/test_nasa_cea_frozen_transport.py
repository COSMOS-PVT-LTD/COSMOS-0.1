"""Frozen transport uses native results only, bounded by a full-product reference."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from physics.exceptions import ThermochemistryError
from physics.quantities import pascal
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from plugins.nasa_cea import bind_nasa_cea_engine
from plugins.nasa_cea.engine import _check_frozen_reference


@pytest.mark.parametrize("fuel,temp,ratio,pc,eps", [
    ("LCH4",111.15,2.,5e5,1.1), ("LCH4",111.15,2.633,5e5,1.507333415512496),
    ("LCH4",111.15,3.5,5e5,8.), ("LCH4",111.15,3.,5e6,8.),
    ("LH2",20.27,5.55157,53.3172e5,25.), ("RP1",298.15,2.3,5e6,8.),
])
def test_real_native_frozen_full_reference_and_transport(fuel,temp,ratio,pc,eps):
    pytest.importorskip("cea")
    req = CeaRequest(fuel,"LOX",ratio,pascal(pc),equilibrium=False,expansion_ratio=eps)
    engine = bind_nasa_cea_engine(fuel_temperature_k=temp,oxidizer_temperature_k=90.15)
    result = run_thermochemistry(req,engine)
    proof = result.provenance["frozen_transport_qualification"]
    assert proof["strategy"] == "EXACT_ZERO_SPECIES_EXCLUDED_WITH_FULL_PRODUCT_REFERENCE"
    assert proof["maximum_relative_station_discrepancy"] < 1e-5
    assert proof["maximum_absolute_mole_fraction_discrepancy"] < 1e-10
    assert result.provenance["chemistry_mode"] == "frozen_chamber"
    for station in result.rocket_stations.values():
        assert station["cp_frozen_j_kg_k"]*station["viscosity_pa_s"]/station["conductivity_frozen_w_m_k"] == pytest.approx(station["prandtl_frozen"],rel=1e-6)
    assert result.rocket_stations["exit"]["area_ratio"] == pytest.approx(eps,rel=5e-4)
    assert run_thermochemistry(req,engine).rocket_stations == result.rocket_stations


def pair():
    fields = {key:[1.,2.,3.] for key in ("T","P","MW","gamma_s","Mach","Isp","ae_at","c_star","Isp_vacuum")}
    reference = SimpleNamespace(converged=True,num_pts=3,**fields,
        mole_fractions={"major":[1.-1e-15]*3,"trace":[1e-15]*3,"zero":[0.]*3})
    actual = deepcopy(reference)
    del actual.mole_fractions["zero"]
    return reference,actual


def test_exact_zero_only_removal_keeps_positive_trace():
    reference,actual = pair()
    assert _check_frozen_reference(reference,actual)["excluded_exact_zero_species_count"] == 1
    del actual.mole_fractions["trace"]
    with pytest.raises(ThermochemistryError,match="positive trace"):
        _check_frozen_reference(reference,actual)


@pytest.mark.parametrize("change", ["partial_reference","partial_transport","state","composition","nonfinite","new_species","normalization"])
def test_reference_mismatch_rejected_without_fabricated_result(change):
    reference,actual = pair()
    if change == "partial_reference": reference.converged=False
    if change == "partial_transport": actual.num_pts=2
    if change == "state": actual.T[2]=4
    if change == "composition": actual.mole_fractions["major"][2]=.9
    if change == "nonfinite": actual.P[1]=float("nan")
    if change == "new_species": actual.mole_fractions["extra"]=[0.]*3
    if change == "normalization":
        reference.mole_fractions["major"]=[.5]*3
        actual.mole_fractions["major"]=[.5]*3
    with pytest.raises(ThermochemistryError):
        _check_frozen_reference(reference,actual)
