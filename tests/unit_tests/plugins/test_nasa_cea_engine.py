"""Unit tests for the nasa/cea thermochemistry adapter."""

from __future__ import annotations

import pytest

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
