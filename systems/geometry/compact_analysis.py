"""Pure, source-bound compact-engine thermal/feed applicability assessment.

This is NOT a thermal/feed solver or a release gate. It cannot turn axial CAD
sections into flow-normal passages, qualify a correlation, extrapolate a source
curve, or infer fluid/material approval. The caller verifies retained raw bytes
at its IO boundary; this module retains the supplied record and source identities.
"""

from __future__ import annotations

import math
from hashlib import sha256

from core.exceptions import CosmosError
from core.serialization import canonical_json_dumps
from physics.fluids.liquid_table import LiquidState, LiquidTable
from physics.heat_transfer.temperature_wall import ConductivityCurve
from systems.geometry.component_model import from_contracts
from systems.geometry.engine_redesign import Candidate, compile_candidate


def record_sha256(value):
    """Canonical identity of an injected JSON record, not proof of raw bytes."""
    return sha256(canonical_json_dumps({"record": value}).encode()).hexdigest()


def _liquid(record):
    names = set(LiquidTable.__dataclass_fields__)
    if type(record) is not dict or set(record) != names:
        raise ValueError(
            "An explicit complete retained liquid-table record is required"
        )
    return LiquidTable(
        **{
            **record,
            "temperatures_k": tuple(record["temperatures_k"]),
            "pressures_pa": tuple(record["pressures_pa"]),
            "raw_sha256": tuple(record["raw_sha256"]),
            "states": tuple(
                tuple(LiquidState(**state) for state in row) for row in record["states"]
            ),
        }
    )


def _curve(record):
    if type(record) is not dict or type(record.get("curve")) is not dict:
        raise ValueError("Each explicit material record must contain its curve")
    values = record["curve"]
    if set(values) != set(ConductivityCurve.__dataclass_fields__):
        raise ValueError(
            "A complete condition/source-bound conductivity curve is required"
        )
    return ConductivityCurve(
        **{
            **values,
            "temperatures_k": tuple(values["temperatures_k"]),
            "conductivities_w_m_k": tuple(values["conductivities_w_m_k"]),
        }
    )


def assess_readiness(
    candidate,
    *,
    liquid_record=None,
    material_records=(),
    physics_identity=None,
):
    """Report exact geometry and blockers; never return solved heat/pressure.

    ``physics_identity`` has baseline_sha256, baseline_commit_id,
    component_source_commit_id and recipe_sha256. Hashes bind to the candidate's
    own engine-baseline reference and recipe; commit labels are retained caller
    authority, not independently resolved by this IO-free module. Optional
    liquid_table_sha256/material_records_sha256 pin the supplied canonical records.
    Material records use the retained staged-record format: ``curve`` plus an
    explicit ``condition`` mapping. Unresolved process fields remain unresolved.
    """
    report = {
        "schema": "cosmos.compact-matched-analysis-readiness.v1",
        "status": "BLOCKED",
        "research_only": True,
        "matched_thermal_feed_solved": False,
        "engineering_acceptance": "NOT_PERFORMED",
        "physical_validation": "NOT_PERFORMED",
        "geometry": None,
        "liquid_domain": None,
        "material_domains": [],
        "provenance": {"raw_source_verification": "REQUIRED_AT_CALLER_IO_BOUNDARY"},
        "blockers": [],
        "solution": {
            "heat_w": None,
            "coolant_outlet_temperature_k": None,
            "coolant_outlet_pressure_pa": None,
            "hot_wall_temperature_k": None,
            "engine_operating_point": None,
        },
    }

    def blocked(code, detail):
        report["blockers"].append({"code": code, "detail": detail})

    if type(candidate) is not Candidate:
        blocked(
            "CANDIDATE_SOURCE_MISSING",
            "An exact compiled compact candidate is required",
        )
        return report
    try:
        replayed = from_contracts(candidate.plan.snapshot, candidate.plan.graph)
        rebuilt = compile_candidate(replayed, candidate.specification)
        wire = candidate.wire()
        if (
            wire != rebuilt.wire()
            or candidate.channels != rebuilt.channels
            or candidate.groups != rebuilt.groups
        ):
            raise ValueError(
                "Candidate operands differ from their exact source specification"
            )
        geometry = candidate.report()
    except (CosmosError, ValueError, TypeError, KeyError, AttributeError) as error:
        blocked("CANDIDATE_SOURCE_CHANGED", str(error))
        return report
    routes = [
        part
        for part in candidate.plan.parts
        if part.part_id in candidate.specification["return_part_ids"]
    ]
    geometry["return_route"] = {
        "part_ids": [part.part_id for part in routes],
        "source_primitive_count": len(routes),
        "physical_fitting_count": "NOT_INFERRED_FROM_CAD_SEGMENTS",
        "centerline_length_m": math.fsum(
            part.pipe.length
            if part.pipe.length is not None
            else part.pipe.bend_radius * abs(part.pipe.angle_rad)
            for part in routes
        ),
        "bore_diameter_m": 2 * routes[0].pipe.bore_radius,
        "flow_characteristics": "NOT_SUPPLIED",
    }
    geometry["section_basis"] = "AXIAL_APERTURES_NOT_FLOW_NORMAL"
    geometry["native_topology"] = "NOT_INSPECTED_BY_THIS_ANALYSIS"
    report["geometry"] = geometry
    report["provenance"].update(
        {
            key: wire[key]
            for key in (
                "recipe_sha256",
                "source_snapshot_sha256",
                "source_graph_sha256",
            )
        }
    )
    refs = [
        ref
        for ref in candidate.plan.snapshot.source_refs
        if ref.ref_id == "engine-baseline"
    ]
    required = {
        "baseline_sha256",
        "baseline_commit_id",
        "component_source_commit_id",
        "recipe_sha256",
    }
    optional = {"liquid_table_sha256", "material_records_sha256"}
    if (
        type(physics_identity) is not dict
        or not required <= set(physics_identity)
        or set(physics_identity) - required - optional
        or any(
            type(v) is not str or not 0 < len(v) <= 240
            for v in physics_identity.values()
        )
    ):
        blocked(
            "PHYSICS_IDENTITY_MISSING",
            "Explicit bounded baseline/component commits and source/recipe hashes required",
        )
    elif (
        len(refs) != 1
        or physics_identity["baseline_sha256"] != refs[0].source_sha256
        or physics_identity["recipe_sha256"] != wire["recipe_sha256"]
    ):
        blocked(
            "PHYSICS_SOURCE_MISMATCH",
            "Physics identity must match the exact candidate baseline reference and recipe",
        )
    else:
        report["provenance"]["physics_identity"] = dict(physics_identity)
    table = None
    try:
        table = _liquid(liquid_record)
        identity = record_sha256(liquid_record)
        report["provenance"].update(
            liquid_table_sha256=identity, liquid_raw_sha256=list(table.raw_sha256)
        )
        if (
            type(physics_identity) is dict
            and physics_identity.get("liquid_table_sha256", identity) != identity
        ):
            blocked(
                "LIQUID_SOURCE_CHANGED",
                "Retained liquid record differs from its explicit expected identity",
            )
        report["liquid_domain"] = {
            "fluid_id": table.fluid_id,
            "temperature_min_k": table.temperatures_k[0],
            "temperature_max_k": table.temperatures_k[-1],
            "pressure_min_pa": table.pressures_pa[0],
            "pressure_max_pa": table.pressures_pa[-1],
            "conservative_saturation_temperature_k": table.lowest_saturation_temperature_k,
            "enthalpy_reference": table.enthalpy_reference,
            "source": table.source,
        }
    except (CosmosError, ValueError, TypeError, KeyError, AttributeError) as error:
        blocked("LIQUID_DATA_MISSING_OR_INVALID", str(error))
    if (
        type(material_records) not in (list, tuple)
        or not 1 <= len(material_records) <= 16
    ):
        blocked(
            "MATERIAL_DATA_MISSING",
            "One to sixteen explicit conductivity research records required",
        )
        material_records = ()
    try:
        identity = record_sha256(list(material_records))
        report["provenance"]["material_records_sha256"] = identity
        if (
            type(physics_identity) is dict
            and physics_identity.get("material_records_sha256", identity) != identity
        ):
            blocked(
                "MATERIAL_SOURCE_CHANGED",
                "Material records differ from their explicit expected identity",
            )
    except (CosmosError, ValueError, TypeError):
        blocked(
            "MATERIAL_DATA_INVALID", "Material records must be finite canonical JSON"
        )
    for index, record in enumerate(material_records):
        try:
            curve = _curve(record)
            domain = {
                "record_index": index,
                "material_id": curve.material_id,
                "condition": curve.condition,
                "temperature_min_k": curve.temperatures_k[0],
                "temperature_max_k": curve.temperatures_k[-1],
                "source_sha256": curve.source_sha256,
                "source": curve.source,
            }
            condition = record.get("condition")
            if type(condition) is not dict or any(
                not condition.get(key)
                for key in (
                    "alloy_id",
                    "process",
                    "machine",
                    "heat_treatment",
                    "orientation",
                )
            ):
                blocked(
                    "MATERIAL_CONDITION_UNRESOLVED",
                    f"Material record {index} lacks complete manufacturing/heat-treatment condition",
                )
            if table is not None:
                low = max(curve.temperatures_k[0], table.temperatures_k[0])
                high = min(
                    curve.temperatures_k[-1], table.lowest_saturation_temperature_k
                )
                domain["subcooled_contact_domain_overlap"] = low < high
                if low >= high:
                    blocked(
                        "NO_WALL_LIQUID_DOMAIN_OVERLAP",
                        f"Material record {index} cannot contain a coolant-contact wall below the conservative liquid saturation bound; no extrapolation",
                    )
            report["material_domains"].append(domain)
        except (CosmosError, ValueError, TypeError, KeyError, AttributeError) as error:
            blocked("MATERIAL_DATA_INVALID", f"Material record {index}: {error}")
    for code, detail in (
        (
            "VARIABLE_SECTOR_TRANSFER_UNSUPPORTED",
            "Axial station area/perimeter are not flow-normal sections or applicable friction/convection correlations",
        ),
        (
            "FULL_HOT_GAS_COVERAGE_REQUIRED",
            "Matched chamber/convergent/throat/nozzle and collector gas boundaries are not supplied",
        ),
        (
            "FEED_CHARACTERISTICS_REQUIRED",
            "Actual collector/entry/bend/split/valve/control characteristics are not supplied; no fitted balancing resistance",
        ),
        (
            "RIB_ROOF_BIMETAL_MODEL_REQUIRED",
            "Planar ligament response is not rib/roof/bimetal conduction or cooled-wall strength",
        ),
        (
            "HEATED_OPERATING_CLOSURE_REQUIRED",
            "Heated injection, CEA enthalpy, gas heat withdrawal and engine mass/pressure closure are not solved",
        ),
    ):
        blocked(code, detail)
    return report
