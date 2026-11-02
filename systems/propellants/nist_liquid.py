"""Strict retained NIST isobar adapter; no network, storage or live-state edits."""
from __future__ import annotations

import csv
import io
import math
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit

from core.exceptions import InvalidInputError
from physics.fluids.liquid_table import LiquidState, LiquidTable

IDS = {"LCH4": "C74828", "LOX": "C7782447"}
FIELDS = ("Temperature (K)", "Pressure (bar)", "Density (kg/m3)",
          "Enthalpy (kJ/kg)", "Cp (J/g*K)", "Viscosity (Pa*s)",
          "Therm. Cond. (W/m*K)", "Phase")


def isobar(raw: bytes, url: str, *, fluid_id: str, temperatures_k: tuple[float,...], pressure_pa: float) -> tuple[LiquidState,...]:
    """Reject wrong requests, units, phases, missing/duplicate nodes and bad data.

    Raw TSV does not identify its species. The retained HTTPS request URL is
    mandatory provenance, rather than claiming the response is self-identifying.
    """
    if type(raw) is not bytes or not 0<len(raw)<=1024**2 or type(url) is not str:
        raise InvalidInputError("Bounded original NIST response bytes and request URL required")
    uri=urlsplit(url);query=parse_qs(uri.query,keep_blank_values=True)
    units={"ID":IDS.get(fluid_id),"Type":"IsoBar","RefState":"DEF","TUnit":"K",
           "PUnit":"bar","DUnit":"kg/m3","HUnit":"kJ/kg","VisUnit":"Pa*s"}
    if (fluid_id not in IDS or uri.scheme!="https" or uri.netloc!="webbook.nist.gov"
        or uri.path!="/cgi/fluid.cgi" or uri.fragment or any(len(v)!=1 for v in query.values())
        or any(query.get(k)!=[v] for k,v in units.items())):
        raise InvalidInputError("Exact same-fluid NIST DEF isobar URL and declared SI conversion units required")
    try:
        if float(query["P"][0])*1e5!=pressure_pa:raise ValueError("wrong pressure")
        reader=csv.DictReader(io.StringIO(raw.decode("utf-8")),delimiter="\t");rows=list(reader)
        if (not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames)
            or not set(FIELDS)<=set(reader.fieldnames) or len(rows)!=len(temperatures_k)):
            raise ValueError("missing/duplicate columns or rows")
        states=[]
        for row,t in zip(rows,temperatures_k,strict=True):
            if (None in row or None in row.values() or row["Phase"]!="liquid"
                or not math.isclose(float(row["Temperature (K)"]),t,rel_tol=0,abs_tol=1e-7)
                or not math.isclose(float(row["Pressure (bar)"])*1e5,pressure_pa,rel_tol=0,abs_tol=1e-3)):
                raise ValueError("not the exact requested wholly liquid grid")
            state=LiquidState(float(row["Density (kg/m3)"]),1000*float(row["Enthalpy (kJ/kg)"]),
                              1000*float(row["Cp (J/g*K)"]),float(row["Viscosity (Pa*s)"]),float(row["Therm. Cond. (W/m*K)"]))
            values=(state.density_kg_m3,state.enthalpy_j_kg,state.cp_j_kg_k,state.viscosity_pa_s,state.conductivity_w_m_k)
            if not all(math.isfinite(v) for v in values) or any(v<=0 for i,v in enumerate(values) if i!=1):
                raise ValueError("nonphysical/nonfinite property")
            states.append(state)
        return tuple(states)
    except (ValueError,KeyError,TypeError,UnicodeError,csv.Error) as error:
        raise InvalidInputError("NIST response does not match exact request/units/liquid grid") from error


def liquid_table(*, fluid_id: str, temperatures_k: tuple[float,...], pressures_pa: tuple[float,...],
                 responses: tuple[tuple[str,bytes],...], lowest_saturation_temperature_k: float,
                 saturation_sha256: str) -> LiquidTable:
    if type(responses) is not tuple or len(responses)!=len(pressures_pa):
        raise InvalidInputError("Exactly one retained isobar URL/response per pressure required")
    columns=[isobar(raw,url,fluid_id=fluid_id,temperatures_k=temperatures_k,pressure_pa=p)
             for (url,raw),p in zip(responses,pressures_pa,strict=True)]
    return LiquidTable(fluid_id,temperatures_k,pressures_pa,
                       tuple(tuple(column[i] for column in columns) for i in range(len(temperatures_k))),
                       lowest_saturation_temperature_k,
                       "NIST SRD69 fluid system, retained HTTPS isobars: "+" ; ".join(url for url,_ in responses),
                       "NIST DEF, same species across all isobars; h kJ/kg -> J/kg, Cp J/g/K -> J/kg/K",
                       tuple(sha256(raw).hexdigest() for _,raw in responses)+(saturation_sha256,))
