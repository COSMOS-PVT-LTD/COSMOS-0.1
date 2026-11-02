"""Unit tests for the nasa/cea thermochemistry adapter."""

from __future__ import annotations

import pytest

from physics.exceptions import ThermochemistryError
from physics.quantities import pascal
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from plugins.nasa_cea.species_map import to_cea_species


def test_species_aliases_methalox() -> None:
    assert to_cea_species("LCH4") == "CH4(L)"
    assert to_cea_species("LOX") == "O2(L)"
    assert to_cea_species("CH4(L)") == "CH4(L)"


def test_import_or_skip_engine() -> None:
    cea = pytest.importorskip("cea")
    assert cea is not None
    from plugins.nasa_cea import bind_nasa_cea_engine

    engine = bind_nasa_cea_engine()
    result = run_thermochemistry(
        CeaRequest("LCH4", "LOX", 2.7239, pascal(0.5e6)),
        engine=engine,
    )
    assert result.chamber_temperature.to_si() == pytest.approx(3093.3, abs=15.0)
    assert 1.05 < result.gamma < 1.4
    assert 0.015 < result.molar_mass.to_si() < 0.025


def test_nasa_rp1311_example8_hydrolox_reference():
    pytest.importorskip("cea")
    from plugins.nasa_cea import bind_nasa_cea_engine
    result = run_thermochemistry(CeaRequest("LH2", "LOX", 5.55157, pascal(53.3172e5), expansion_ratio=25),
                                bind_nasa_cea_engine(fuel_temperature_k=20.27, oxidizer_temperature_k=90.17))
    # NASA's distributed RP-1311 example 8 (legacy CEA2 output, September 2004 data).
    # Tolerances cover printed precision and modern database differences.
    assert result.chamber_temperature.to_si() == pytest.approx(3383.8446, rel=1e-3)
    assert result.characteristic_velocity.to_si() == pytest.approx(2332.3356, rel=1e-3)
    assert result.molar_mass.to_si() == pytest.approx(.01271565, rel=1e-3)
    assert result.rocket_stations["exit"]["temperature_k"] == pytest.approx(1468.156, rel=2e-3)


@pytest.mark.parametrize("fuel,temperature,ratio", [("LCH4", 111.67, 2.7239), ("RP1", 298.15, 2.3)])
def test_real_species_transport_and_provenance(fuel, temperature, ratio):
    pytest.importorskip("cea")
    from plugins.nasa_cea import bind_nasa_cea_engine
    result = run_thermochemistry(CeaRequest(fuel, "LOX", ratio, pascal(5e6), expansion_ratio=8),
                                bind_nasa_cea_engine(fuel_temperature_k=temperature, oxidizer_temperature_k=90.17))
    assert result.engine_version == "3.3.4"
    assert sum(result.mole_fractions.values()) == pytest.approx(1)
    assert result.rocket_stations["throat"]["mach"] == pytest.approx(1, abs=1e-4)
    assert result.rocket_stations["exit"]["area_ratio"] == pytest.approx(8, rel=5e-4)
    assert result.provenance["reactant_temperature_defaults_used"] is False
    assert all(len(value) == 64 for value in result.provenance["database_sha256"].values())
    for row in result.rocket_stations.values():
        assert row["cp_frozen_j_kg_k"] * row["viscosity_pa_s"] / row["conductivity_frozen_w_m_k"] == pytest.approx(row["prandtl_frozen"])


def test_nonconvergence_cannot_return_partial_native_solution(monkeypatch):
    from types import SimpleNamespace

    import numpy as np

    from plugins.nasa_cea import bind_nasa_cea_engine
    from plugins.nasa_cea import engine as adapter
    class Mixture:
        def __init__(self, *args, **kwargs): pass
        def of_ratio_to_weights(self, *args): return np.array([.25, .75])
        def calc_property(self, *args): return 1.
    class Solver:
        def __init__(self, *args, **kwargs): pass
        def solve(self, *args, **kwargs): pass
    fake = SimpleNamespace(__version__="3.3.4", __file__=__file__, Mixture=Mixture, RocketSolver=Solver, R=1., ENTHALPY=1,
                           Reactant=lambda name: SimpleNamespace(get_valid_temperature_range=lambda: (10., 1000.)),
                           RocketSolution=lambda solver: SimpleNamespace(converged=False, num_pts=2))
    monkeypatch.setattr(adapter, "import_module", lambda name: fake)
    with pytest.raises(ThermochemistryError, match="did not converge"):
        run_thermochemistry(CeaRequest("LCH4", "LOX", 3, pascal(5e6), expansion_ratio=8), bind_nasa_cea_engine())


def test_reactant_temperature_outside_nasa_database_is_rejected():
    pytest.importorskip("cea")
    from plugins.nasa_cea import bind_nasa_cea_engine
    from plugins.nasa_cea.engine import OutOfRangeError
    with pytest.raises(OutOfRangeError, match="outside NASA database range"):
        run_thermochemistry(CeaRequest("LCH4", "LOX", 3, pascal(5e6), expansion_ratio=8),
                            bind_nasa_cea_engine(fuel_temperature_k=300, oxidizer_temperature_k=90.17))
