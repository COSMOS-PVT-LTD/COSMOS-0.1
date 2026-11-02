import pytest

from scripts.prepare_methalox_thermal_envelope import inlet_enthalpy, saturation_states


def saturation():
    return ("Temperature (K)\tPressure (bar)\tDensity (l, kg/m3)\tEnthalpy (l, kJ/kg)\tEnthalpy (v, kJ/kg)\n"
            + "\n".join(f"{130+p}\t{p}\t380\t{p*20}\t550" for p in (5,6,7,8))).encode()


def test_saturation_parser_retains_common_units_and_both_branches():
    values = saturation_states(saturation())
    assert len(values) == 4 and values[0]["pressure_pa"] == 500000.
    assert values[-1]["saturated_liquid_enthalpy_j_kg"] == 160000.
    assert values[-1]["saturated_vapour_enthalpy_j_kg"] == 550000.


@pytest.mark.parametrize("edit", [lambda s:s.replace(b"\t5\t",b"\t4\t"), lambda s:s+s.splitlines()[-1],
    lambda s:s.replace(b"550",b"0"), lambda s:s.replace(b"380",b"nan"),
    lambda s:s.replace(b"kJ/kg",b"kJ/mol")])
def test_wrong_grid_duplicates_phase_branch_or_units_reject(edit):
    with pytest.raises((ValueError,KeyError)):
        saturation_states(edit(saturation()))


def test_exact_inlet_phase_state_and_explicit_energy_conversion():
    raw=b"Temperature (K)\tPressure (bar)\tPhase\tEnthalpy (kJ/kg)\n111.15\t8\tliquid\t-1.2\n"
    assert inlet_enthalpy(raw) == -1200.
    for changed in (raw.replace(b"liquid",b"vapor"),raw.replace(b"111.15",b"112"),raw.replace(b"\t8\t",b"\t9\t"),raw+raw.splitlines()[-1]):
        with pytest.raises(ValueError):
            inlet_enthalpy(changed)
