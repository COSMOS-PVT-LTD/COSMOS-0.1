import pytest

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from systems.propellants.nist_liquid import isobar, liquid_table

URL="https://webbook.nist.gov/cgi/fluid.cgi?ID=C74828&Type=IsoBar&RefState=DEF&TUnit=K&PUnit=bar&DUnit=kg/m3&HUnit=kJ/kg&VisUnit=Pa*s&P=5"
RAW=(b"Temperature (K)\tPressure (bar)\tDensity (kg/m3)\tEnthalpy (kJ/kg)\tCp (J/g*K)\tViscosity (Pa*s)\tTherm. Cond. (W/m*K)\tPhase\n"
     b"110\t5\t420\t-1\t3.4\t.00012\t.18\tliquid\n120\t5\t400\t34\t3.6\t.0001\t.17\tliquid\n")


def test_explicit_unit_conversion_and_two_pressure_surface():
    states=isobar(RAW,URL,fluid_id="LCH4",temperatures_k=(110.,120.),pressure_pa=5e5)
    assert states[0].enthalpy_j_kg==-1000 and states[1].cp_j_kg_k==3600
    table=liquid_table(fluid_id="LCH4",temperatures_k=(110.,120.),pressures_pa=(5e5,6e5),
        responses=((URL,RAW),(URL.replace("P=5","P=6"),RAW.replace(b"\t5\t",b"\t6\t"))),
        lowest_saturation_temperature_k=135.,saturation_sha256="a"*64)
    state=table.evaluate(Quantity(115,SI.get("K")),Quantity(5.5e5,SI.get("Pa")))
    assert state.density_kg_m3==410 and state.enthalpy_j_kg==16500
    assert len(table.raw_sha256)==3


@pytest.mark.parametrize("raw",[RAW.replace(b"liquid",b"vapor"),RAW.replace(b"120\t5",b"110\t5"),
    RAW.replace(b".00012",b"nan"),RAW.replace(b"Cp (J/g*K)",b"Cp (J/kg*K)"),
    RAW.replace(b"110\t5",b"110\t8"),RAW+b"120\t5\t400\t34\t3.6\t.0001\t.17\tliquid\n"])
def test_wrong_phase_units_grid_nonfinite_missing_or_duplicate_nodes(raw):
    with pytest.raises(InvalidInputError):isobar(raw,URL,fluid_id="LCH4",temperatures_k=(110.,120.),pressure_pa=5e5)


@pytest.mark.parametrize("url",[URL.replace("C74828","C7782447"),URL.replace("https:","http:"),
    URL.replace("webbook.nist.gov","untrusted.example"),URL+"&P=5",URL.replace("DEF","IIR"),URL.replace("P=5","P=6")])
def test_url_provenance_cannot_be_silently_substituted(url):
    with pytest.raises(InvalidInputError):isobar(RAW,url,fluid_id="LCH4",temperatures_k=(110.,120.),pressure_pa=5e5)
