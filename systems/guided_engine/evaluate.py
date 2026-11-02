"""Bounded target sizing over existing Physics/Systems models, not a second CEA."""

from __future__ import annotations

import math

from core.exceptions import InvalidInputError
from core.unit import SI
from physics.compressible_flow.external_nozzle import scale_external_nozzle
from physics.quantities import pascal, quantity, square_metre
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from systems.configuration.subsystems import configure_subsystems
from systems.contracts.results import ResultStatus
from systems.cycle.models import CycleConfiguration, CycleType
from systems.guided_engine.resolution import digest
from systems.projects.models import PropulsionDesign
from systems.propellants.models import PropellantConfiguration
from systems.requirements.models import DesignRequirements
from systems.stages.chamber import run_chamber_stage
from systems.stages.nozzle import run_nozzle_stage
from systems.stages.subsystems import run_injector_stage
from systems.workflow.orchestrator import run_phase3_chain, update_phase4_graph_status


def evaluate(plan, engine):
    """Pure orchestration: provider is injected; no storage/network/process access."""
    expected = dict(plan)
    if expected.pop("review_hash", None) != digest(expected):
        raise InvalidInputError(
            "Guided resolution hash changed; review the exact basis again."
        )
    b, e, policy = plan["brief"], plan["effective"], plan["selection"]
    pc, pa, target = (
        b["chamber_pressure"]["value"],
        plan["ambient_pressure_pa"],
        b["thrust"]["value"],
    )
    eps_lock = e.get("expansion_ratio", {}).get("value")
    eps = (
        eps_lock
        if eps_lock is not None
        else policy["vacuum_expansion_ratio"]
        if pa == 0
        else None
    )
    rows = []

    def point(of):
        thermo = run_thermochemistry(
            CeaRequest("LCH4", "LOX", of, pascal(pc), expansion_ratio=eps),
            engine=engine,
        )
        station = thermo.rocket_stations["exit"]
        performance = scale_external_nozzle(
            pascal(pc),
            pascal(pa),
            square_metre(1),
            station["area_ratio"],
            thermo.characteristic_velocity,
            quantity(station["velocity_m_s"], SI.get("m/s")),
            pascal(station["pressure_pa"]),
        )
        row = {
            "mixture_ratio": of,
            "specific_impulse_s": performance.specific_impulse_s,
            "expansion_ratio": station["area_ratio"],
            "force_per_throat_area_n_m2": performance.force.to_si(),
        }
        if not all(math.isfinite(v) and v > 0 for v in row.values()):
            raise InvalidInputError(
                "CEA search point has invalid performance; no assumed fallback."
            )
        rows.append(row)
        return row

    if "mixture_ratio" in e:
        selected = point(e["mixture_ratio"]["value"])
    else:
        # Finite policy-pinned search; do not imply a global hardware optimum.
        coarse = [point(round(1.5 + i * 0.1, 8)) for i in range(31)]
        best = max(coarse, key=lambda r: r["specific_impulse_s"])
        if best is coarse[0] or best is coarse[-1]:
            raise InvalidInputError(
                "Mixture-ratio search reaches the profile boundary. No optimum selected; use reviewed wider bounds in a new profile."
            )
        fine = [
            point(round(best["mixture_ratio"] - 0.1 + i * 0.01, 8)) for i in range(21)
        ]
        selected = max(fine, key=lambda r: r["specific_impulse_s"])
        if selected is fine[0] or selected is fine[-1]:
            raise InvalidInputError(
                "Refined mixture-ratio optimum is boundary-limited; no automatic optimum claim."
            )
    at = target / selected["force_per_throat_area_n_m2"]
    if "throat_area" in e:
        at = e["throat_area"]["value"]
        if not math.isclose(
            at * selected["force_per_throat_area_n_m2"],
            target,
            rel_tol=policy["thrust_relative_tolerance"],
        ):
            raise InvalidInputError(
                "Target thrust and locked throat area conflict. Unlock area or use existing-hardware evaluation; feed conditions were not tuned."
            )
    of, eps = selected["mixture_ratio"], selected["expansion_ratio"]
    design = PropulsionDesign(
        name=f"Guided methalox · {target:g} N · {pc / 1e5:g} bar abs",
        description="Source-bound preliminary guided sizing. Not manufacturing, hot-fire or physical acceptance.",
    )
    design.requirements = DesignRequirements(
        target_thrust=quantity(target, SI.get("N")),
        target_chamber_pressure=pascal(pc),
        ambient_pressure=pascal(pa),
        mixture_ratio=of,
        expansion_ratio=eps,
        burn_duration=None
        if b["burn_duration"] is None
        else quantity(b["burn_duration"]["value"], SI.get("s")),
        propellant_selection="LOX/LCH4",
        cycle_type="PRESSURE_FED",
        notes="Guided review " + plan["review_hash"],
    )
    design.propellant_configuration = PropellantConfiguration(
        fuel_id="LCH4", oxidizer_id="LOX", mixture_ratio=of
    )
    design.cycle_configuration = CycleConfiguration.for_type(CycleType.PRESSURE_FED)
    design.thermochemistry_configuration = {
        "mode": "nasa_cea",
        "fuel_temperature_k": e["fuel_temperature"]["value"],
        "oxidizer_temperature_k": e["oxidizer_temperature"]["value"],
    }
    configure_subsystems(
        design,
        {
            "chamber": {
                "characteristic_length_m": e["characteristic_length"]["value"],
                "contraction_ratio": e["contraction_ratio"]["value"],
            },
            "nozzle": {
                "length_fraction": e["nozzle_length_fraction"]["value"],
                "start_angle_deg": e["nozzle_start_angle"]["value"],
                "exit_angle_deg": e["nozzle_exit_angle"]["value"],
                "blend_radius_ratio": e["nozzle_blend_radius_ratio"]["value"],
                "point_count": e["nozzle_point_count"]["value"],
            },
        },
    )
    result = run_phase3_chain(
        design, throat_area_m2=at, expansion_ratio=eps, thermochemistry_engine=engine
    )
    if not result.ok:
        raise InvalidInputError(
            "Guided CEA/performance chain did not produce current results; no success fallback."
        )
    update_phase4_graph_status(design)
    stages = [
        {
            "name": "Thermochemistry and performance",
            "state": "SUCCEEDED",
            "basis": "Ideal CEA equilibrium, not delivered hardware performance",
        }
    ]
    for name, stage in (
        ("Chamber sizing", run_chamber_stage(design)),
        ("Nozzle contour", run_nozzle_stage(design, require_contour=True)),
    ):
        if stage.status is not ResultStatus.CURRENT:
            raise InvalidInputError(name + " failed: " + str(stage.errors))
        stages.append(
            {"name": name, "state": "SUCCEEDED", "basis": "Preliminary geometry model"}
        )
    properties = plan["property_package"]["states"]
    manifold = pc + e["injector_pressure_drop"]["value"]
    cold_supported = all(
        manifold == properties[name]["pressure_pa"]
        and e[name + "_temperature"]["value"] == properties[name]["temperature_k"]
        for name in ("fuel", "oxidizer")
    )
    if cold_supported:
        config = {
            "property_source": "Exact retained NIST cold liquid states; source SHA256 "
            + ", ".join(properties[n]["sha256"] for n in ("fuel", "oxidizer"))
            + "; provisional Cd/count/drop accepted through guided review "
            + plan["review_hash"]
        }
        for name in ("fuel", "oxidizer"):
            for key in ("density_kg_m3", "viscosity_pa_s"):
                config[name + "_" + key] = properties[name]["properties"][key]
            config[name + "_cd"] = e["injector_cd"]["value"]
            config[name + "_hole_count"] = e["injector_holes"]["value"]
            config[name + "_pressure_drop_pa"] = e["injector_pressure_drop"]["value"]
        configure_subsystems(design, {"injector": config})
        # Configuring an input invalidates downstream stages; rerun from the
        # exact same admitted geometry/state rather than relabelling old results.
        result = run_phase3_chain(
            design,
            throat_area_m2=at,
            expansion_ratio=eps,
            thermochemistry_engine=engine,
        )
        run_chamber_stage(design)
        nozzle = run_nozzle_stage(design, require_contour=True)
        injector = run_injector_stage(design)
        if (
            not result.ok
            or injector.status is not ResultStatus.CURRENT
            or nozzle.status is not ResultStatus.CURRENT
        ):
            raise InvalidInputError(
                "Configured cold hydraulic chain failed; inspect explicit source applicability."
            )
    stages.append(
        {
            "name": "Cold injector hydraulics",
            "state": "SUCCEEDED" if cold_supported else "BLOCKED",
            "basis": "Cold reference only; no heated regenerative-outlet claim"
            if cold_supported
            else "No property package for this exact injector pressure/temperature; ideal performance is retained",
        }
    )
    remaining = e["regulated_feed_pressure"]["value"] - manifold
    stages.append(
        {
            "name": "Feed pressure screening",
            "state": "SCREENED" if remaining > 0 else "INFEASIBLE",
            "basis": "Available minus Pc and injector drop; remaining pressure must cover all actual upstream line/valve/cooling losses, not a solved closure",
        }
    )
    for name, reason in (
        (
            "Matched cooling and heated feed",
            "Requires matched passage geometry, hot-fluid/phase coverage and thermal boundary data",
        ),
        (
            "Cooled wall / pressure joints",
            "Requires temperature/process-specific properties, qualified joint and selected seal basis",
        ),
        (
            "Physical validation",
            "Requires real measurements, uncertainty and qualified review",
        ),
    ):
        stages.append({"name": name, "state": "BLOCKED", "basis": reason})
    perf = design.workflow.current_result("performance")
    if perf is None:
        raise InvalidInputError(
            "Performance became stale while assembling the guided result."
        )
    force = perf.outputs["thrust"]["magnitude"]
    if not math.isclose(force, target, rel_tol=policy["thrust_relative_tolerance"]):
        raise InvalidInputError(
            "Final performance does not meet the predeclared target tolerance."
        )
    mdot = design.operating_point.mass_flow.to_si()
    report = {
        "schema": "cosmos.guided-result.v1",
        "target_thrust_n": target,
        "calculated_thrust_n": force,
        "thrust_relative_error": (force - target) / target,
        "mixture_ratio": of,
        "expansion_ratio": eps,
        "specific_impulse_s": selected["specific_impulse_s"],
        "throat_area_m2": at,
        "throat_diameter_m": 2 * math.sqrt(at / math.pi),
        "exit_diameter_m": 2 * math.sqrt(at * eps / math.pi),
        "mass_flow_kg_s": mdot,
        "fuel_flow_kg_s": mdot / (1 + of),
        "oxidizer_flow_kg_s": mdot * of / (1 + of),
        "propellant_mass_kg": None
        if b["burn_duration"] is None
        else mdot * b["burn_duration"]["value"],
        "remaining_feed_pressure_pa": remaining,
        "injector_manifold_pressure_pa": manifold,
        "chamber": design.chamber_design,
        "nozzle": design.nozzle_design,
        "injector": design.injector_design,
        "search_points": rows,
        "stages": stages,
        "review_hash": plan["review_hash"],
        "physical_validation": "NOT_PERFORMED",
        "engineering_acceptance": "NOT_PERFORMED",
        "engine_complete": False,
        "model_scope": "IDEAL_PERFORMANCE_PRELIMINARY_GEOMETRY_AND_COLD_HYDRAULICS",
    }
    return design, report
