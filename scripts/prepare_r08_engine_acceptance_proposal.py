"""Offline DRAFT generator. No app-store, native-build, approval or export calls."""

import argparse
import json
import math
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from itertools import pairwise
from pathlib import Path

import numpy as np

from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_model import compile_model, from_contracts
from systems.geometry.component_reference import PartReference
from tests.fixtures.geometry_qualification_families import (
    area_reference,
    critical_witnesses,
)

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_SHA = "58761b31a87a729cd207d6cbda6a1bf110771e3b3835e6355788a8504e5fbb86"
SCHEMA = "cosmos.r08-engine-provisional-plan.v1"


def proposed_probe(
    plan, part, identifier, category, points_local, *, semantics="LOCAL_ENDPOINT_SPAN"
):
    rotation, translation = plan.placement(part.frame_id)
    points = np.asarray(points_local) @ rotation.T + translation
    ref = PartReference(plan, part)
    residual = float(np.abs(ref.sdf(points)).max())
    nominal = float(np.linalg.norm(points[1] - points[0]))
    if residual > 1e-6 or nominal <= 0:
        raise ValueError(
            "Unresolved nominal source witness: " + part.part_id + ":" + identifier
        )
    # Proposed numerical error allocation, NOT a sourced manufacturing allowable.
    span_error = min(0.0001, 0.05 * nominal)
    return {
        "id": identifier,
        "category": category,
        "points_m": points.tolist(),
        "nominal_span_m": nominal,
        "proposed_minimum_m": nominal - span_error,
        "proposed_maximum_m": nominal + span_error,
        "proposed_surface_tolerance_m": span_error / 2,
        "source_boundary_residual_m": residual,
        "semantics": semantics,
        "status": "DRAFT_NUMERICAL_BUDGET_NOT_APPROVED",
    }


def cooling_coverage(plan, part):
    rows = np.array(part.profile)
    throat = int(np.argmin(rows[:, 1]))
    minimum = rows[:, 1].min()
    minima = rows[np.abs(rows[:, 1] - minimum) < 1e-10, 0]
    tx = float((minima[0] + minima[-1]) / 2)
    plateau = 0
    while plateau + 1 < throat and abs(rows[plateau + 1, 1] - rows[0, 1]) < 1e-10:
        plateau += 1
    sites = {
        "chamber": float((rows[0, 0] + rows[max(1, plateau), 0]) / 2),
        "convergent": float((rows[plateau, 0] + rows[throat, 0]) / 2),
        "throat": tx,
        "divergent": float((tx + rows[-1, 0]) / 2),
        "exit": float((rows[-2, 0] + rows[-1, 0]) / 2),
    }
    c = part.cooling
    result = []
    for site, x in sites.items():
        ri, ro = (float(np.interp(x, rows[:, 0], rows[:, j])) for j in (1, 2))
        for channel in range(c.count):
            phase = c.phase_rad + 2 * math.pi * channel / c.count
            angle = phase + c.width_rad / 2
            point = lambda r, a, x=x: [x, r * math.cos(a), r * math.sin(a)]
            low, high = ri + c.hot_ligament, ri + c.hot_ligament + c.depth
            for label, r0, r1 in (
                ("hot-wall-radial", ri, low),
                ("roof-radial", high, ro),
                ("channel-depth-radial", low, high),
            ):
                result.append(
                    proposed_probe(
                        plan,
                        part,
                        f"{label}:{site}:{channel}",
                        label,
                        [point(r0, angle), point(r1, angle)],
                        semantics="RADIAL_SPAN_NOT_NORMAL_OR_GLOBAL_MINIMUM",
                    )
                )
            radius = (low + high) / 2
            result.append(
                proposed_probe(
                    plan,
                    part,
                    f"channel-width-chord:{site}:{channel}",
                    "channel-width-chord",
                    [point(radius, phase), point(radius, phase + c.width_rad)],
                    semantics="CHORD_NOT_ARC_WIDTH",
                )
            )
            next_phase = phase + 2 * math.pi / c.count
            probe = proposed_probe(
                plan,
                part,
                f"rib-endpoint-chord:{site}:{channel}",
                "rib-endpoint-chord",
                [point(radius, phase + c.width_rad), point(radius, next_phase)],
                semantics="CHORD_MAY_CROSS_GAS_BORE_NOT_MATERIAL_THICKNESS",
            )
            probe["nominal_arc_reference_m"] = radius * (
                2 * math.pi / c.count - c.width_rad
            )
            result.append(probe)
    return result, sites


def other_coverage(plan, part):
    rotation, translation = plan.placement(part.frame_id)
    result = []
    # Existing independently checked nominal witnesses. Do not reuse their
    # manufactured-fixture error limits as engine acceptance requirements.
    for original in critical_witnesses(plan, part):
        if original["id"].startswith("port-"):
            continue  # Replaced by two cross-section directions at three sites.
        local = (np.array(original["points_m"]) - translation) @ rotation
        result.append(
            proposed_probe(
                plan, part, "source:" + original["id"], "nominal-source-span", local
            )
        )
    for i, hole in enumerate(part.holes):
        start, end = hole.axial_range or (part.profile[0][0], part.profile[-1][0])
        slope = np.array(hole.slope_yz)
        a = (
            np.array([-slope[1], slope[0]])
            if np.linalg.norm(slope)
            else np.array([1.0, 0.0])
        )
        a /= np.linalg.norm(a)
        b = np.array([-a[1], a[0]])
        for fraction in (0.1, 0.5, 0.9):
            x = start + (end - start) * fraction
            center = np.array(hole.center_yz) + x * slope
            for axis, direction in enumerate((a, b)):
                radius = hole.radius / math.sqrt(
                    1 - float(direction @ slope) ** 2 / (1 + float(slope @ slope))
                )
                points = [
                    np.r_[x, center + sign * radius * direction] for sign in (-1, 1)
                ]
                probe = proposed_probe(
                    plan,
                    part,
                    f"bore:{i}:{fraction}:{axis}",
                    "bore-cross-section",
                    points,
                    semantics="TRUE_DIAMETER"
                    if axis == 0
                    else "ELLIPTIC_SECTION_MAJOR_SPAN_NOT_TRUE_DIAMETER",
                )
                probe.update(
                    nominal_true_bore_diameter_m=2 * hole.radius,
                    nominal_axis_tilt_rad=math.atan(float(np.linalg.norm(slope))),
                    role=hole.role,
                )
                result.append(probe)
    if part.pipe:
        pipe = part.pipe
        for fraction in (0.1, 0.5, 0.9):
            if pipe.bend_radius is None:
                center = np.array(
                    [part.profile[0][0] + pipe.length * fraction, 0.0, 0.0]
                )
                u, v = np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])
            else:
                theta = pipe.angle_rad * fraction
                center = np.array(
                    [
                        pipe.bend_radius * math.sin(theta),
                        pipe.bend_radius * (1 - math.cos(theta)),
                        0.0,
                    ]
                )
                u, v = (
                    np.array([-math.sin(theta), math.cos(theta), 0.0]),
                    np.array([0.0, 0.0, 1.0]),
                )
            for j in range(4):
                direction = (
                    math.cos(j * math.pi / 2) * u + math.sin(j * math.pi / 2) * v
                )
                result.append(
                    proposed_probe(
                        plan,
                        part,
                        f"pipe-wall:{fraction}:{j}",
                        "pipe-wall",
                        [
                            center + pipe.bore_radius * direction,
                            center + pipe.outer_radius * direction,
                        ],
                    )
                )
            for j, direction in enumerate((u, v)):
                result.append(
                    proposed_probe(
                        plan,
                        part,
                        f"pipe-bore:{fraction}:{j}",
                        "pipe-bore",
                        [
                            center - pipe.bore_radius * direction,
                            center + pipe.bore_radius * direction,
                        ],
                    )
                )
    for i, cavity in enumerate(part.cavities):
        if cavity.sector:
            a, b = cavity.profile[0], cavity.profile[-1]
            phase, width = cavity.sector
            for fraction in (0.1, 0.5, 0.9):
                x = a[0] + fraction * (b[0] - a[0])
                point = lambda r, angle, x=x: [
                    x,
                    r * math.cos(angle),
                    r * math.sin(angle),
                ]
                result.append(
                    proposed_probe(
                        plan,
                        part,
                        f"sector-depth:{i}:{fraction}",
                        "header-sector-depth",
                        [
                            point(a[1], phase + width / 2),
                            point(a[2], phase + width / 2),
                        ],
                    )
                )
                radius = (a[1] + a[2]) / 2
                result.append(
                    proposed_probe(
                        plan,
                        part,
                        f"sector-width:{i}:{fraction}",
                        "header-sector-width-chord",
                        [point(radius, phase), point(radius, phase + width)],
                        semantics="CHORD_NOT_ARC_WIDTH",
                    )
                )
        if not cavity.open_face:
            continue
        a, b = cavity.profile[0], cavity.profile[-1]
        for j in range(4):
            angle = 0.37 + j * math.pi / 2
            radius = (a[1] + a[2]) / 2
            floor, opposite = (
                (b[0], part.profile[-1][0])
                if cavity.open_face == "start"
                else (a[0], part.profile[0][0])
            )
            polar = lambda x, r, angle=angle: [
                x,
                r * math.cos(angle),
                r * math.sin(angle),
            ]
            result.append(
                proposed_probe(
                    plan,
                    part,
                    f"groove-floor:{i}:{j}",
                    "groove-remaining-floor",
                    [polar(floor, radius), polar(opposite, radius)],
                )
            )
            result.append(
                proposed_probe(
                    plan,
                    part,
                    f"groove-depth:{i}:{j}",
                    "groove-depth-edge",
                    [polar(a[0], a[1]), polar(b[0], a[1])],
                    semantics="SHARP_RIM_TO_FLOOR_EDGE_DEPTH",
                )
            )
    plenums = [c for c in part.cavities if not c.open_face and not c.sector]
    ref = PartReference(plan, part)

    def land(label, category, x0, r0, x1, r1, quadrant):
        # Find a source-bound unperforated location within the requested quadrant.
        # This is source geometry selection, not fitting to generated mesh errors.
        for offset in range(32):
            angle = quadrant * math.pi / 2 + 0.37 + 0.02 * offset
            local = np.array(
                [
                    [x0, r0 * math.cos(angle), r0 * math.sin(angle)],
                    [x1, r1 * math.cos(angle), r1 * math.sin(angle)],
                ]
            )
            world = local @ rotation.T + translation
            segment = np.linspace(world[0], world[1], 33)
            if (np.abs(ref.sdf(world)) <= 1e-6).all() and (
                ref.sdf(segment) <= 1e-6
            ).all():
                probe = proposed_probe(plan, part, label, category, local)
                probe.update(
                    selected_local_azimuth_rad=angle, nominal_material_line_samples=33
                )
                result.append(probe)
                return
        raise ValueError(
            "No source-bound unperforated land: " + part.part_id + ":" + label
        )

    if plenums:
        for i, cavity in enumerate(plenums):
            a, b = cavity.profile[0], cavity.profile[-1]
            for j in range(4):
                radius = (a[1] + a[2]) / 2
                land(
                    f"back-web:{i}:{j}",
                    "header-back-web",
                    part.profile[0][0],
                    radius,
                    a[0],
                    radius,
                    j,
                )
                land(
                    f"front-web:{i}:{j}",
                    "header-front-web",
                    b[0],
                    radius,
                    part.profile[-1][0],
                    radius,
                    j,
                )
                for fraction in (0.1, 0.5, 0.9):
                    x = a[0] + fraction * (b[0] - a[0])
                    if i == 0 and part.profile[0][1] > 0:
                        land(
                            f"inner-land:{fraction}:{j}",
                            "header-inner-land",
                            x,
                            part.profile[0][1],
                            x,
                            a[1],
                            j,
                        )
                    if i == len(plenums) - 1:
                        land(
                            f"outer-land:{fraction}:{j}",
                            "header-outer-land",
                            x,
                            a[2],
                            x,
                            part.profile[0][2],
                            j,
                        )
        for i, (a, b) in enumerate(pairwise(plenums)):
            for fraction in (0.1, 0.5, 0.9):
                x = a.profile[0][0] + fraction * (a.profile[-1][0] - a.profile[0][0])
                for j in range(4):
                    land(
                        f"propellant-separating-web:{i}:{fraction}:{j}",
                        "fuel-lox-separating-web",
                        x,
                        a.profile[0][2],
                        x,
                        b.profile[0][1],
                        j,
                    )
    return result


def draft_component(plan, part, spec, count, baseline_h):
    probes, sites = (
        cooling_coverage(plan, part)
        if part.cooling
        else (other_coverage(plan, part), {})
    )
    grouped = {}
    for probe in probes:
        grouped.setdefault(probe["category"], []).append(probe)
    batches = []
    for category, items in grouped.items():
        for index in range(0, len(items), 32):
            batches.append(
                {
                    "id": f"{category}:{index // 32}",
                    "witnesses": items[index : index + 32],
                }
            )
    candidate = deepcopy(spec)
    candidate["outputs"] = [part.feature_id]
    endpoint = min(p["proposed_surface_tolerance_m"] for p in probes)
    candidate["export_tolerance"]["value"] = min(
        candidate["export_tolerance"]["value"], endpoint / 2
    )
    compiled = compile_model(
        candidate,
        "engine-component-r08-provisional-" + part.part_id,
        "DRAFT-NOT-SAVED",
        "2026-10-28T00:00:00Z",
    )
    if len(compiled.parts) != 1 or asdict(compiled.parts[0]) != asdict(part):
        raise ValueError("Derived output changed nominal component geometry")
    if part.cooling:
        spacings = [0.00075, 0.0006, 0.00048]
    elif part.part_id == "collector-mount-bolts":
        spacings = [0.0005, 0.0004, 0.00032]
    elif part.part_id == "head-mount-bolts":
        spacings = [0.00045, 0.00036, 0.000288]
    elif part.part_id == "gas-joint-groove":
        spacings = [0.0004, 0.00032, 0.000256]
    elif part.part_id == "lower-coolant-header":
        spacings = [0.0003, 0.00024, 0.000192]
    else:
        spacings = [0.000125, 0.0001, 0.00008]
    estimates = [math.ceil(1.25 * count * (baseline_h / h) ** 2) for h in spacings]
    if max(estimates) > 4_000_000:
        raise ValueError("Proposed part study exceeds screening cap estimate")
    return {
        "part_id": part.part_id,
        "feature_id": part.feature_id,
        "frame_id": part.frame_id,
        "role": part.role,
        "nominal_area_m2": area_reference(part),
        "nominal_source_geometry_preserved": True,
        "proposed_specification": candidate,
        "proposed_specification_sha256": sha256(
            json.dumps(candidate, sort_keys=True, allow_nan=False).encode()
        ).hexdigest(),
        "proposed_analytic_limits": {
            "relative_volume": 0.002 if part.pipe else 0.005,
            "relative_area": 0.005 if part.pipe else 0.01,
            "centroid_m": 0.00005,
            "bounds_m": 0.00005,
            "surface_distance_m": 0.00005,
            "export_deflection_m": candidate["export_tolerance"]["value"],
        },
        "material_assignment": None,
        "mesh_intent_approval": None,
        "reviewer": None,
        "coverage_sites_local_x_m": sites,
        "witness_count": len(probes),
        "policy_batches": batches,
        "three_grid_screen": {
            "spacing_m": spacings,
            "baseline_triangles": count,
            "projected_triangles_with_25_percent_margin": estimates,
            "projection_status": "UNVERIFIED_H_INVERSE_SQUARED_ESTIMATE_NOT_A_BOUND",
            "finest_h_over_strictest_endpoint_budget": spacings[-1] / endpoint,
            "accuracy_feasibility": "NOT_ESTABLISHED_DO_NOT_RELAX_LIMITS",
        },
    }


def prepare(capture, baseline, expected_sha):
    raw = capture.read_bytes()
    if (
        expected_sha != CAPTURE_SHA
        or len(raw) > 2 * 1024**2
        or sha256(raw).hexdigest() != expected_sha
    ):
        raise ValueError("Exact bounded immutable engine capture required")
    captured = json.loads(raw)
    if (
        sha256(captured["model_canonical_json"].encode()).hexdigest()
        != captured["model_sha256"]
    ):
        raise ValueError("Saved model identity mismatch")
    evidence = json.loads(baseline.read_bytes())
    if evidence["inputs_sha256"] != expected_sha or not evidence["software_qa_pass"]:
        raise ValueError("Native count baseline must bind exact capture")
    model = json.loads(captured["model_canonical_json"])
    plan = from_contracts(
        DesignSnapshot.from_json(model["snapshot_json"]),
        GeometryFeatureGraph.from_json(model["graph_json"]),
    )
    counts = {
        p["part_id"]: p["triangle_count"]
        for p in evidence["worker_observations"]["parts"]
    }
    if set(counts) != {p.part_id for p in plan.parts}:
        raise ValueError("No omitted or extra source parts allowed")
    parts = [
        draft_component(
            plan,
            p,
            model["specification"],
            counts[p.part_id],
            evidence["worker_observations"]["actual_voxel_m"],
        )
        for p in plan.parts
    ]
    return {
        "schema": SCHEMA,
        "proposal_revision": "DRAFT-2",
        "status": "DRAFT_NOT_APPROVED_NOT_EXECUTABLE",
        "preparation_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "approval_recorded": False,
        "app_data_written": False,
        "native_campaign_executed": False,
        "model_commit_id": captured["model_commit_id"],
        "model_sha256": captured["model_sha256"],
        "capture_sha256": expected_sha,
        "baseline_sha256": sha256(baseline.read_bytes()).hexdigest(),
        "scope": "Geometry-only analytic baseline and bounded implicit screening; not manufacturing/pressure/thermal/CFD acceptance",
        "assembly_checks_not_covered_by_endpoint_witnesses": [
            {"check": "declared mating-port centers", "proposed_max_offset_m": 0.00005},
            {
                "check": "declared mating-port axes and injector bore angles",
                "proposed_max_angle_error_rad": math.radians(0.1),
            },
            {
                "check": "bolt/gland interface mapping and geometric interference",
                "status": "REAL_CAD_INSPECTION_REQUIRED",
            },
            {
                "check": "fluid continuity and volume mesh",
                "status": "NOT_ESTABLISHED_METAL_ONLY_SOURCE",
            },
            {
                "check": "global minimum normal wall/rib thickness",
                "status": "NOT_CERTIFIED_BY_LOCAL_RADIAL_OR_CHORD_CHECKS",
            },
        ],
        "parts": parts,
        "total_witnesses": sum(p["witness_count"] for p in parts),
        "total_policy_batches": sum(len(p["policy_batches"]) for p in parts),
        "approval_blockers": [
            "intended use and proposed numerical budgets",
            "material/region and mesh-intent assignments",
            "independent real engineer and coverage review",
            "assembly interface and angle checks",
            "actual campaign results; estimates are not feasibility proof",
        ],
        "execution_minimum_free_disk_gib_proposed": 10,
        "sources": [
            "https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html",
            "https://occt3d.com/dev/doc/overview/html/occt_user_guides__mesh.html",
        ],
        "source_scope": "References support methodology only; no reference prescribes these proposed engine tolerances",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--capture-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    output = a.output.resolve()
    if output.exists() or ROOT / "docs/implementation/evidence" not in output.parents:
        raise ValueError(
            "New repository evidence output required; preserve historical artifacts"
        )
    draft = prepare(a.capture, a.baseline, a.capture_sha256)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as f:
        json.dump(draft, f, indent=2, allow_nan=False)
    print(
        "DRAFT only:",
        len(draft["parts"]),
        "parts;",
        draft["total_witnesses"],
        "nominal witnesses;",
        draft["total_policy_batches"],
        "proposed batches",
    )


if __name__ == "__main__":
    main()
