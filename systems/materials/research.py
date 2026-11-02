"""Source-bound conductivity research, separate from live material selection.

This is a staging boundary, not an allowables database. Retaining document
bytes proves their identity, not the correctness of a manual transcription.
Exact-condition studies require a fully specified, equal material identity.
Incomplete records can only be used as explicitly unmatched comparisons of the
same alloy. Neither mode grants installation or manufacturing authority.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from hashlib import sha256
from typing import Any, Literal
from urllib.parse import urlsplit

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.heat_transfer.temperature_wall import (
    ConductivityCurve,
    WallBalance,
    temperature_dependent_wall,
)

ResearchMode = Literal["EXACT_CONDITION_RESEARCH", "UNMATCHED_SAME_ALLOY_COMPARISON"]
SCOPE = "ISOLATED_MATERIAL_RESEARCH_NOT_ENGINE_INPUTS_OR_ALLOWABLES"


def _label(value: object) -> bool:
    return type(value) is str and 0 < len(value) <= 4000 and value.strip() == value


def _keys(value: object, expected: set[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != expected:
        raise InvalidInputError(f"Exact {name} schema required; missing/unknown fields rejected")
    return value


@dataclass(frozen=True, slots=True)
class MaterialCondition:
    alloy_id: str
    process: str | None
    machine: str | None
    powder: str | None
    heat_treatment: str | None
    orientation: str | None

    def __post_init__(self) -> None:
        if not _label(self.alloy_id) or any(
            value is not None and not _label(value)
            for key, value in asdict(self).items() if key != "alloy_id"
        ):
            raise InvalidInputError("Explicit alloy and nonempty condition labels, or null for unknown, required")

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(key for key, value in asdict(self).items() if value is None)


@dataclass(frozen=True, slots=True)
class ConductivityEvidence:
    evidence_id: str
    condition: MaterialCondition
    curve: ConductivityCurve
    source_locator: str
    statistic: str
    uncertainty_statement: str
    sample_count: int | None
    unresolved: tuple[str, ...]
    transcription_sha256: str


def stage_conductivity(payload: dict[str, Any], raw_source: bytes) -> ConductivityEvidence:
    """Validate a manually inspected table against retained source identity.

    No networking, filesystem reads, live design writes or catalog mutation.
    Celsius conversion belongs to Core; interpolation/heat balance to Physics.
    Unknown sample size/condition/uncertainty is retained, never inferred.
    """
    data = _keys(payload, {
        "schema_version", "scope", "evidence_id", "condition", "source",
        "temperature_unit", "temperatures", "conductivity_unit", "conductivities",
        "statistic", "uncertainty_statement", "sample_count", "unresolved",
    }, "conductivity research")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["scope"] != SCOPE:
        raise InvalidInputError("Only version 1 isolated research evidence can be staged")
    source = _keys(data["source"], {"url", "sha256", "locator"}, "source")
    if not all(_label(source[key]) for key in source):
        raise InvalidInputError("Nonempty source URL, document hash and table locator required")
    try:
        uri = urlsplit(source["url"])
        if (uri.scheme != "https" or not uri.hostname or uri.username or uri.password
                or uri.fragment or uri.port not in {None, 443}):
            raise ValueError("not public HTTPS")
    except ValueError as error:
        raise InvalidInputError("Original public HTTPS source URL required") from error
    if (type(raw_source) is not bytes or not 0 < len(raw_source) <= 32 * 1024**2
            or sha256(raw_source).hexdigest() != source["sha256"]):
        raise InvalidInputError("Retained original document bytes do not match source SHA256")
    identity = _keys(data["condition"], {f.name for f in fields(MaterialCondition)}, "material condition")
    condition = MaterialCondition(**identity)
    if (type(data["temperature_unit"]) is not str or data["temperature_unit"] not in {"K", "degC"}
            or data["conductivity_unit"] != "W/(m*K)"):
        raise InvalidInputError("Explicit supported absolute temperature and conductivity units required")
    ts, ks = data["temperatures"], data["conductivities"]
    if (type(ts) is not list or type(ks) is not list
            or any(type(value) not in {int, float} for value in ts + ks)):
        raise InvalidInputError("Original finite numeric table columns required; no Boolean/string coercion")
    temperatures = tuple(Quantity(t, SI.get(data["temperature_unit"])).to_si() for t in ts)
    unresolved = data["unresolved"]
    if (type(unresolved) is not list or len(unresolved) > 64
            or any(not _label(value) for value in unresolved)
            or len(set(unresolved)) != len(unresolved)):
        raise InvalidInputError("Explicit distinct unresolved evidence statements required")
    if any(not _label(data[key]) for key in ("evidence_id", "statistic", "uncertainty_statement")):
        raise InvalidInputError("Explicit identity, reported statistic and uncertainty statement required")
    count = data["sample_count"]
    if count is not None and (type(count) is not int or not 1 <= count <= 1000000):
        raise InvalidInputError("Positive known sample count or null for unreported required")
    curve = ConductivityCurve(condition.alloy_id,
        json.dumps(identity, sort_keys=True, separators=(",", ":")), temperatures, tuple(ks),
        source["url"] + " | " + source["locator"] + " | " + data["statistic"], source["sha256"])
    # Hash the original-unit transcription, not merely the converted curve.
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return ConductivityEvidence(data["evidence_id"], condition, curve, source["locator"],
        data["statistic"], data["uncertainty_statement"], count, tuple(unresolved), digest)


@dataclass(frozen=True, slots=True)
class WallResearchInputs:
    gas_temperature: Quantity
    coolant_temperature: Quantity
    gas_coefficient: Quantity
    coolant_coefficient: Quantity
    gas_area: Quantity
    coolant_area: Quantity
    conduction_area: Quantity
    thickness: Quantity
    heat_tolerance: Quantity
    max_iterations: int


@dataclass(frozen=True, slots=True)
class MaterialWallResearch:
    evidence_id: str
    mode: ResearchMode
    source_condition: MaterialCondition
    requested_condition: MaterialCondition
    missing_or_mismatched_fields: tuple[str, ...]
    balance: WallBalance
    source_sha256: str
    transcription_sha256: str
    reported_statistic: str
    uncertainty_statement: str
    unresolved: tuple[str, ...]
    scope: str = SCOPE
    installed: bool = False
    material_allowable_assessed: bool = False
    physical_validation: str = "NOT_PERFORMED"
    engine_operating_point_complete: bool = False


def research_wall(*, evidence: ConductivityEvidence, requested: MaterialCondition,
                  mode: ResearchMode, inputs: WallResearchInputs) -> MaterialWallResearch:
    """Bounded planar comparison only; never a rib/bimetal/engine calculation."""
    if (type(evidence) is not ConductivityEvidence or type(requested) is not MaterialCondition
            or type(inputs) is not WallResearchInputs):
        raise InvalidInputError("Staged evidence, explicit requested condition and wall research inputs required")
    if requested.alloy_id != evidence.condition.alloy_id:
        raise InvalidInputError("Different alloy cannot be substituted, even in this same-alloy research workflow")
    gaps = tuple(key for key, value in asdict(requested).items()
        if value is None or getattr(evidence.condition, key) is None or getattr(evidence.condition, key) != value)
    if mode == "EXACT_CONDITION_RESEARCH":
        if gaps or evidence.unresolved:
            raise InvalidInputError("Exact-condition research requires complete matching identity and resolved evidence; use an explicitly unmatched comparison or obtain data")
    elif mode != "UNMATCHED_SAME_ALLOY_COMPARISON":
        raise InvalidInputError("Explicit supported research mode required; no engine installation/allowable mode")
    result = temperature_dependent_wall(conductivity=evidence.curve,
        **{f.name: getattr(inputs, f.name) for f in fields(inputs)})
    return MaterialWallResearch(evidence.evidence_id, mode, evidence.condition, requested, gaps, result,
        evidence.curve.source_sha256, evidence.transcription_sha256, evidence.statistic,
        evidence.uncertainty_statement, evidence.unresolved)
