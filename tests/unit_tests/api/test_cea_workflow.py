"""CEA mode, persistence and fail-closed coupling to real native execution."""

import pytest

from api.propulsion_workflow import (
    create_design,
    run_phase3,
    save_design,
    update_requirements,
)
from core.exceptions import InvalidInputError
from physics.exceptions import InsufficientDataError
from systems.configuration.thermochemistry import configure_thermochemistry
from systems.contracts.results import ResultStatus
from systems.persistence.design_store import DesignStore
from systems.projects.models import PropulsionDesign

CONFIG = {"mode": "nasa_cea", "fuel_temperature_k": 111.67, "oxidizer_temperature_k": 90.17}


def cea_design():
    design = create_design(name="CEA regression, not a validated engine")
    update_requirements(design, {"target_chamber_pressure": 5e5, "ambient_pressure": 0,
                              "mixture_ratio": 2.7239, "expansion_ratio": 10,
                              "propellant_selection": "LOX/LCH4"})
    return design


def test_real_cea_workflow_preserves_cstar_and_scales_thrust(tmp_path):
    pytest.importorskip("cea")
    design = cea_design()
    result = run_phase3(design, thermochemistry_configuration=CONFIG, throat_area_m2=.001)
    assert result["execution_ok"]
    assert not result["workflow_complete"]
    assert result["validation_level"] == "NOT_CLAIMED"
    thermo = result["stages"]["thermochemistry"]["outputs"]
    perf = result["stages"]["performance"]["outputs"]
    assert thermo["chamber_temperature"]["magnitude"] == pytest.approx(3093.338, abs=.02)
    assert perf["cstar"]["value"] == thermo["cstar"]["magnitude"]
    assert design.operating_point.characteristic_velocity.to_si() == perf["cstar"]["value"]
    assert perf["mass_flow"]["magnitude"] == pytest.approx(500 / perf["cstar"]["value"])
    assert perf["specific_impulse"]["value"] == pytest.approx(thermo["rocket_stations"]["exit"]["vacuum_isp_s"], rel=1e-5)
    assert not design.operating_point.gamma_is_assumption
    store = DesignStore(tmp_path)
    save_design(design, store)
    reloaded = store.load(design.design_id)
    assert reloaded.thermochemistry_configuration == CONFIG
    assert reloaded.workflow.current_result("thermochemistry").outputs["engine_provenance"] == thermo["engine_provenance"]
    configure_thermochemistry(reloaded, CONFIG | {"fuel_temperature_k": 112})
    assert reloaded.workflow.results["thermochemistry"].status is ResultStatus.STALE
    assert reloaded.workflow.results["performance"].status is ResultStatus.STALE
    assert reloaded.nozzle_design["geometry_status"] == "STALE"


def test_unavailable_cea_never_reuses_assumed_or_previous_cea_inputs(monkeypatch):
    design = cea_design()
    run_phase3(design, gamma=1.2, chamber_temperature_k=3000,
               molecular_weight_kg_per_mol=.022, throat_area_m2=.001)
    def unavailable(*args, **kwargs):
        raise InsufficientDataError("CEA unavailable regression")
    monkeypatch.setattr("plugins.nasa_cea.engine.NasaCeaEngine.evaluate", unavailable)
    result = run_phase3(design, thermochemistry_configuration=CONFIG, throat_area_m2=.001)
    assert not result["execution_ok"]
    assert result["stages"]["thermochemistry"]["status"] == "FAILED"
    assert result["stages"]["performance"]["status"] == "FAILED"
    assert design.operating_point.gamma is None
    assert design.operating_point.mass_flow is None
    assert not design.workflow.current_result("performance")
    assert design.nozzle_design["geometry_status"] == "STALE"


def test_cea_requires_temperatures_and_cannot_mix_manual_inputs():
    design = cea_design()
    result = run_phase3(design, thermochemistry_configuration={"mode": "nasa_cea"}, throat_area_m2=.001)
    assert not result["execution_ok"]
    assert "explicit" in result["stages"]["thermochemistry"]["errors"][0]["message"]
    with pytest.raises(InvalidInputError, match="does not accept assumed"):
        run_phase3(design, thermochemistry_configuration=CONFIG, gamma=1.2)


@pytest.mark.parametrize("bad", [{"mode": "auto"}, {"mode": "nasa_cea", "fuel_temperature_k": True},
                                 {"mode": "nasa_cea", "fuel_temperature_k": float("nan")},
                                 {"mode": "nasa_cea", "fuel_temperature_k": -1}, {"mode": "nasa_cea", "extra": 1}])
def test_configuration_validation_is_atomic(bad):
    design = cea_design()
    before = design.to_canonical_dict()
    with pytest.raises(InvalidInputError):
        configure_thermochemistry(design, bad)
    assert design.to_canonical_dict() == before


def test_legacy_design_does_not_implicitly_enable_cea():
    design = cea_design()
    payload = design.to_canonical_dict()
    payload.pop("thermochemistry_configuration")
    assert PropulsionDesign.from_canonical_dict(payload).thermochemistry_configuration == {}
