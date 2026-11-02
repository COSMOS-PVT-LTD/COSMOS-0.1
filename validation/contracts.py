"""Immutable, bounded comparison contracts. Values stay explicit until conversion."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from systems.contracts.geometry._wire import digest, dumps, require, sha, source_uri

MODEL = "steady-spherical-conduction-v1"
CONDITIONS = {"radius_m", "conductivity_w_m_k", "generation_w_m3", "surface_k"}
PROVENANCE = {"source", "author", "version", "source_sha256", "license", "method", "calibration_usage", "uncertainty_basis", "instrumentation"}


def text(value: Any, name: str) -> str:
    require(type(value) is str and 0 < len(value.strip()) <= 1024 and "\0" not in value,
            "INVALID_METADATA", f"Bounded nonempty {name} required")
    return value


def number(value: Any, name: str, *, minimum: float = 0) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum and abs(value) <= 1e12,
            "INVALID_NUMBER", f"Finite bounded {name} required; booleans are not numbers")
    return float(value)


def fields(value: Any, expected: set[str]) -> None:
    require(type(value) is dict and set(value) == expected, "INVALID_FIELDS", "Exact versioned fields required; no client approval/success flags")


@dataclass(frozen=True, slots=True)
class ThermalDataset:
    canonical: bytes

    @classmethod
    def parse(cls, value: dict[str, Any]) -> ThermalDataset:
        fields(value, {"schema_version", "kind", "quantity", "coordinate_unit", "value_unit", "frame_id", "model_id", "conditions", "coordinates", "values", "standard_uncertainty_k", "provenance"})
        require(value["schema_version"] == "p10-thermal-v1" and value["kind"] in {"simulation", "analytic-reference", "external-solver", "experimental"},
                "INVALID_DATASET", "Unsupported dataset schema/kind")
        require(value["quantity"] == "Temperature" and value["coordinate_unit"] in {"m", "mm"} and value["value_unit"] in {"K", "degC"},
                "INVALID_UNIT", "Only Temperature K/degC versus Radius m/mm is supported")
        text(value["frame_id"], "frame_id")
        require(value["model_id"] == MODEL, "MODEL_MISMATCH", "Only steady isotropic spherical conduction with uniform generation and fixed outer temperature is supported")
        fields(value["conditions"], CONDITIONS)
        for key in CONDITIONS:
            number(value["conditions"][key], key, minimum=1e-12)
        x, y, u = value["coordinates"], value["values"], value["standard_uncertainty_k"]
        require(type(x) is list and type(y) is list and 2 <= len(x) <= 1024 and len(y) == len(x), "DATASET_LIMIT", "2–1024 paired observations required")
        converted = [number(v, "radius") * (0.001 if value["coordinate_unit"] == "mm" else 1) for v in x]
        require(all(a < b for a, b in pairwise(converted)) and converted[-1] <= value["conditions"]["radius_m"],
                "INVALID_COORDINATES", "Strictly increasing radii inside declared geometry required")
        for v in y:
            number(v, "temperature", minimum=-273.15 if value["value_unit"] == "degC" else 0)
            require(v + (273.15 if value["value_unit"] == "degC" else 0) > 0, "INVALID_TEMPERATURE", "Positive absolute temperature required")
        require(u is None or type(u) is list and len(u) == len(x), "INVALID_UNCERTAINTY", "Standard output uncertainties must match observations or be explicitly unknown")
        if u is not None:
            for v in u:
                number(v, "standard_uncertainty_k")
        p = value["provenance"]
        fields(p, PROVENANCE)
        for key in PROVENANCE:
            text(p[key], key)
        sha(p["source_sha256"], "source_sha256")
        source_uri(p["source"])
        require(p["calibration_usage"] in {"held-out", "calibration", "not-applicable"}, "INVALID_PROVENANCE", "Declare calibration versus held-out data")
        if value["kind"] == "experimental":
            require(u is not None and all(v > 0 for v in u) and p["instrumentation"] != "not-applicable" and p["uncertainty_basis"] != "unknown",
                    "EXPERIMENTAL_EVIDENCE_INCOMPLETE", "Measured data needs positive standard uncertainty, instrumentation and uncertainty basis")
        raw = dumps(value).encode()
        require(len(raw) <= 256 * 1024, "DATASET_LIMIT", "Canonical dataset limit is 256KiB")
        return cls(raw)

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical)

    @property
    def content_sha256(self) -> str:
        return digest(self.data)


@dataclass(frozen=True, slots=True)
class Criteria:
    canonical: bytes

    @classmethod
    def parse(cls, value: dict[str, Any]) -> Criteria:
        fields(value, {"intended_use", "rationale", "max_abs_error_k", "max_combined_standard_uncertainty_k", "coverage_factor", "correlation", "allow_unit_conversion"})
        text(value["intended_use"], "intended_use"); text(value["rationale"], "acceptance rationale")
        number(value["max_abs_error_k"], "max_abs_error_k", minimum=1e-12)
        number(value["max_combined_standard_uncertainty_k"], "uncertainty limit", minimum=1e-12)
        require(1 <= number(value["coverage_factor"], "coverage factor") <= 10, "INVALID_UNCERTAINTY", "Explicit coverage factor in [1,10] required; no automatic confidence interpretation")
        number(value["correlation"], "correlation", minimum=-1)
        require(value["correlation"] <= 1 and type(value["allow_unit_conversion"]) is bool, "INVALID_CRITERIA", "Explicit correlation [-1,1] and conversion choice required")
        return cls(dumps(value).encode())

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical)

    @property
    def content_sha256(self) -> str:
        return digest(self.data)
