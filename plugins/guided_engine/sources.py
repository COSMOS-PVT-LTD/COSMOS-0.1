"""Offline, original-byte NIST reference states. Not hot-fluid property coverage."""

from __future__ import annotations

import csv
import io
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from core.exceptions import InvalidInputError

ROOT = Path(__file__).resolve().parent / "data"
STATES = {
    "fuel": (
        "LCH4",
        "C74828",
        111.15,
        "e6e585088034a0cbad3d541ddff36a74fbc7dad3ceb446452afacc11d5470214",
    ),
    "oxidizer": (
        "LOX",
        "C7782447",
        90.15,
        "679267127dbae87aed6d2ac2547f06fa8df10663f6c3d7748a18204add918425",
    ),
}


def package():
    result = {
        "id": "nist-methalox-cold-6bar-v1",
        "version": 1,
        "scope": "EXACT_COLD_REFERENCE_STATES_ONLY",
        "states": {},
    }
    for name, (species, cas, temperature, checksum) in STATES.items():
        path = ROOT / (name + "-nist-6bar.tsv")
        if not path.is_file() or path.is_symlink():
            raise InvalidInputError(
                "Reviewed guided property package is missing; no replacement source was selected."
            )
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != checksum:
            raise InvalidInputError(
                "Reviewed NIST package checksum mismatch; keep originals and reconcile a new package version."
            )
        rows = list(csv.DictReader(io.StringIO(raw.decode()), delimiter="\t"))
        selected = [
            r
            for r in rows
            if float(r["Temperature (K)"]) == temperature
            and float(r["Pressure (bar)"]) == 6
        ]
        if len(selected) != 1 or selected[0]["Phase"] != "liquid":
            raise InvalidInputError(
                "NIST package does not contain the exact declared liquid state."
            )
        r = selected[0]
        url = (
            "https://webbook.nist.gov/cgi/fluid.cgi?Action=Data&Wide=on&ID="
            + cas
            + "&Type=IsoTherm&Digits=6&PLow=6&PHigh=6.1&PInc=0.1&T="
            + str(temperature)
            + "&RefState=DEF&TUnit=K&PUnit=bar&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=Pa%2As&STUnit=N%2Fm"
        )
        if urlsplit(url).hostname != "webbook.nist.gov" or parse_qs(
            urlsplit(url).query
        )["ID"] != [cas]:
            raise InvalidInputError("Source identity mismatch.")
        result["states"][name] = {
            "species": species,
            "temperature_k": temperature,
            "pressure_pa": 600000.0,
            "phase": "liquid",
            "sha256": checksum,
            "url": url,
            "reference_state": "NIST DEF",
            "properties": {
                "density_kg_m3": float(r["Density (kg/m3)"]),
                "viscosity_pa_s": float(r["Viscosity (Pa*s)"]),
                "cp_j_kg_k": 1000 * float(r["Cp (J/g*K)"]),
                "conductivity_w_m_k": float(r["Therm. Cond. (W/m*K)"]),
            },
            "uncertainty": None,
            "category": "SOURCE_PROPERTY",
            "authority": "NIST calculated reference fluid, not engine measurements",
        }
    return result
