"""Sourcing/approval helper regressions; synthetic TSV data, never engine evidence."""
from copy import deepcopy
from hashlib import sha256

import pytest


@pytest.fixture
def helpers(monkeypatch):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / "scripts"))
    from apply_approved_methalox_study import validate_approved
    from prepare_approved_methalox_study import read_state
    return read_state, validate_approved


def tsv(temperature, phase="liquid", pressure=6, viscosity=.001):
    return ("Temperature (K)\tPressure (bar)\tDensity (kg/m3)\tCp (J/g*K)\tViscosity (Pa*s)\tTherm. Cond. (W/m*K)\tPhase\n"
            f"{temperature}\t{pressure}\t1000\t2\t{viscosity}\t.1\t{phase}\n").encode()


def test_single_liquid_state_units_and_no_inferred_property_window(helpers):
    read, _ = helpers
    result = read(tsv(111.15), pressure_bar=6, temperature_k=111.15)
    assert result["properties_si"]["cp_j_kg_k"] == 2000
    assert result["state"] == {"temperature_k": 111.15, "pressure_pa": 600000}
    assert set(result) == {"properties_si", "raw_row", "state"}


@pytest.mark.parametrize("raw", [tsv(111.15, phase="gas"), tsv(90.15), tsv(111.15, pressure=8),
                                     tsv(111.15, viscosity=float("nan"))])
def test_wrong_state_phase_and_nonfinite_are_rejected(helpers, raw):
    with pytest.raises(ValueError):
        helpers[0](raw, pressure_bar=6, temperature_k=111.15)


def test_approval_config_is_exact_and_raw_state_bound(tmp_path, helpers):
    _, validate = helpers
    spec = {"schema": "cosmos.approved-preliminary-methalox-study.v1",
            "requirements": {"burn_duration": {"magnitude": 5, "unit_symbol": "s"}},
            "regulated_source_pressure_absolute_pa_each": 800000,
            "material_candidates_only": {"liner": "GRCop-42", "jacket": "INCONEL 718"},
            "subsystem_inputs": {"injector": {"property_source": "Synthetic helper test only"}}, "nist_states": {}}
    for name, temp in (("fuel", 111.15), ("oxidizer", 90.15)):
        raw = tsv(temp)
        (tmp_path / f"{name}-nist-6bar.tsv").write_bytes(raw)
        spec["nist_states"][name] = {"6": {"sha256": sha256(raw).hexdigest()}}
        spec["subsystem_inputs"]["injector"].update({f"{name}_{key}": value for key, value in
            {"pressure_drop_pa": 100000, "cd": .7, "hole_count": 8, "density_kg_m3": 1000, "viscosity_pa_s": .001}.items()})
    validate(spec, tmp_path)
    changed = deepcopy(spec)
    changed["subsystem_inputs"]["injector"]["fuel_cd"] = .8
    with pytest.raises(ValueError, match="differs"):
        validate(changed, tmp_path)
    changed = deepcopy(spec)
    changed["subsystem_inputs"]["materials"] = {"material_id": "stainless_304"}
    with pytest.raises(ValueError, match="scope"):
        validate(changed, tmp_path)
    (tmp_path / "fuel-nist-6bar.tsv").write_bytes(tsv(111.15, pressure=8))
    with pytest.raises(ValueError, match="hash mismatch"):
        validate(spec, tmp_path)
