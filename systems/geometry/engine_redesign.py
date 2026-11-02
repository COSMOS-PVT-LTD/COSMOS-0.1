"""Isolated compact-engine CSG recipes; no baseline mutation or physics sizing.

This extension deliberately does not change the qualified R07 component language.
Its positive operands, cuts and reference integrals are consumed identically by
the new native generators. Radial station depths are not rectangular channels,
normal-section dimensions, material allowables or a cooling solution.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from hashlib import sha256

import numpy as np

from core.serialization import canonical_json_dumps
from systems.contracts.geometry._wire import require
from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import Part, keys, scalar
from systems.geometry.component_reference import PartReference

SCHEMA = "cosmos.compact-engine-candidate.v1"
RECIPE_SCHEMA = "cosmos.compact-engine-csg.v1"
LIMITS = (
    "PRELIMINARY_GEOMETRY_ONLY; R08 qualification remains on hold",
    "No manufacturing, sealing, material-bond, pressure or hot-fire acceptance",
    "Piecewise-linear source gas path retained; no efficiency improvement claimed",
    "Axial-sector radial dimensions, not normal-flow sections or rectangular surrogates",
    "Helical channels, automated thermal sizing and automatic baseline replacement unsupported",
)


def quantity(value, unit="m"):
    return {"value": value, "unit": unit}


def _tolerance(plan):
    return next(
        p.value_si for p in plan.snapshot.parameters_si if p.name == "source_tolerance"
    )


def suggest(plan):
    """Seed only unambiguous source roles, without inventing engineering sizes."""
    cooled = [p for p in plan.parts if p.role == "metal" and p.cooling]
    require(
        len(cooled) == 1,
        "REDESIGN_SOURCE",
        "Exactly one saved cooled metal body required",
    )
    body = cooled[0]
    headers = [
        p
        for p in plan.parts
        if p.role == "metal" and any(c.open_passage and c.sector for c in p.cavities)
    ]
    require(
        len(headers) == 2,
        "REDESIGN_SOURCE",
        "Exactly two source cooling headers required; select another source if ambiguous",
    )
    report = inspect_interfaces(plan, _tolerance(plan))
    ports = {p["id"]: p for p in report["ports"]}
    edges = set()
    # Starting at the upper header supply opening, stop at the injector head.
    # This is geometry/adjacency only; fluid identity is not inferred by proximity.
    upper = next(
        (
            h
            for h in headers
            if any(
                {ports[m["from"]]["part_id"], ports[m["to"]]["part_id"]}
                == {h.part_id, body.part_id}
                and "UPPER_COLLECTOR_CONNECTION"
                in {ports[m["from"]]["kind"], ports[m["to"]]["kind"]}
                for m in report["matches"]
            )
        ),
        None,
    )
    require(
        upper is not None,
        "REDESIGN_SOURCE",
        "Upper collector must mate the saved channel start",
    )
    pipes = {p.part_id for p in plan.parts if p.role == "metal" and p.pipe}
    for match in report["matches"]:
        a, b = ports[match["from"]]["part_id"], ports[match["to"]]["part_id"]
        if a in pipes or b in pipes:
            edges.add(tuple(sorted((a, b))))
    neighbors = lambda name: {b if a == name else a for a, b in edges if name in (a, b)}
    route = set()
    pending = list(neighbors(upper.part_id) & pipes)
    while pending:
        part = pending.pop()
        if part in route:
            continue
        route.add(part)
        pending.extend((neighbors(part) & pipes) - route)
    require(
        2 <= len(route) <= 16,
        "REDESIGN_SOURCE",
        "A multi-piece return route connected to the upper collector is required",
    )
    c = body.cooling
    return {
        "schema": SCHEMA,
        "body_part_id": body.part_id,
        "header_part_ids": sorted(p.part_id for p in headers),
        "return_part_ids": sorted(route),
        "channel_family": "variable_radial_axial_sector",
        "stations": [
            {
                "x": quantity(x),
                "hot_ligament": quantity(c.hot_ligament),
                "depth": quantity(c.depth),
            }
            for x, _, _ in body.profile
        ],
    }


@dataclass(frozen=True)
class Group:
    part_id: str
    add: tuple[Part, ...]
    subtract: tuple[Part, ...] = ()


@dataclass(frozen=True)
class Candidate:
    plan: object
    specification: dict
    groups: tuple[Group, ...]
    channels: tuple[Part, ...]

    def wire(self):
        def operand(part):
            r, t = self.plan.placement(part.frame_id)
            return {
                **asdict(part),
                "rotation": r.reshape(-1).tolist(),
                "translation_m": t.tolist(),
                "bounds_m": PartReference(self.plan, part).bounds_m.tolist(),
            }

        groups = []
        for group in self.groups:
            refs = [PartReference(self.plan, p) for p in group.add]
            bounds = np.array([r.bounds_m for r in refs])
            volume = sum(r.volume_m3 for r in refs) - sum(
                PartReference(self.plan, p).volume_m3 for p in group.subtract
            )
            require(
                volume > 0,
                "REDESIGN_VOLUME",
                "Positive additive-minus-cut reference volume required",
            )
            groups.append(
                {
                    "part_id": group.part_id,
                    "add": [operand(p) for p in group.add],
                    "subtract": [operand(p) for p in group.subtract],
                    "reference_volume_m3": volume,
                    "bounds_m": [
                        *bounds[:, :3].min(axis=0).tolist(),
                        *bounds[:, 3:].max(axis=0).tolist(),
                    ],
                }
            )
        value = {
            "schema": RECIPE_SCHEMA,
            "source_snapshot_sha256": sha256(
                self.plan.snapshot.to_json().encode()
            ).hexdigest(),
            "source_graph_sha256": sha256(
                self.plan.graph.to_json().encode()
            ).hexdigest(),
            "source_tolerance_m": _tolerance(self.plan),
            "groups": groups,
            "qualification": "NOT_PERFORMED",
            "limits": list(LIMITS),
        }
        return {
            **value,
            "recipe_sha256": sha256(canonical_json_dumps(value).encode()).hexdigest(),
        }

    def report(self):
        body = next(
            p
            for p in self.plan.parts
            if p.part_id == self.specification["body_part_id"]
        )
        c = body.cooling
        rows = self.channels[0].profile
        stations = []
        for (x, ri, ro), (_, hot, outer) in zip(body.profile, rows, strict=True):
            area = 0.5 * c.width_rad * (outer**2 - hot**2)
            perimeter = c.width_rad * (hot + outer) + 2 * (outer - hot)
            stations.append(
                {
                    "x_m": x,
                    "inner_radius_m": hot,
                    "outer_radius_m": outer,
                    "radial_hot_ligament_m": hot - ri,
                    "radial_outer_ligament_m": ro - outer,
                    "axial_aperture_area_m2": area,
                    "axial_aperture_perimeter_m": perimeter,
                    "axial_aperture_4A_over_P_m": 4 * area / perimeter,
                }
            )
        wire = self.wire()
        return {
            "schema": "cosmos.compact-engine-inspection.v1",
            "source_metal_parts": sum(p.role == "metal" for p in self.plan.parts),
            "candidate_metal_groups": len(self.groups),
            "groups": [
                {
                    "part_id": g["part_id"],
                    "source_part_ids": [p["part_id"] for p in g["add"]],
                    "reference_volume_m3": g["reference_volume_m3"],
                }
                for g in wire["groups"]
            ],
            "channel_count": c.count,
            "width_rad": c.width_rad,
            "stations": stations,
            "total_channel_volume_m3": sum(
                PartReference(self.plan, p).volume_m3 for p in self.channels
            ),
            "preserved": [
                "source gas path",
                "head and plate bores",
                "external supply ports",
                "source return centerline",
                "blind seal-groove envelopes",
            ],
            "thermal_mapping": "REQUIRES_MATCHED_VARIABLE_SECTOR_MODEL",
            "feed_closure": "REQUIRES_CANDIDATE_MATCHED_RECOMPUTATION",
            "native_topology": "NOT_BUILT",
            "material_joining": "NOT_ASSESSED",
            "limits": list(LIMITS),
            "recipe_sha256": wire["recipe_sha256"],
        }


def compile_candidate(plan, specification):
    keys(
        specification,
        (
            "schema",
            "body_part_id",
            "header_part_ids",
            "return_part_ids",
            "channel_family",
            "stations",
        ),
        "compact candidate",
    )
    require(
        specification["schema"] == SCHEMA
        and specification["channel_family"] == "variable_radial_axial_sector",
        "REDESIGN_FAMILY",
        "Only variable radial-depth axial sectors are supported; no helical/rectangular substitution",
    )
    metal = {p.part_id: p for p in plan.parts if p.role == "metal"}
    body_id = specification["body_part_id"]
    require(
        type(body_id) is str
        and body_id in metal
        and metal[body_id].cooling is not None,
        "REDESIGN_SOURCE",
        "Exact cooled metal body ID required",
    )
    body = metal[body_id]
    require(
        sum(p.cooling is not None for p in metal.values()) == 1,
        "REDESIGN_SOURCE",
        "Exactly one cooled metal body is supported per compact candidate",
    )
    require(
        not body.holes and not body.cavities and not body.sector,
        "REDESIGN_SOURCE",
        "Body with intersecting auxiliary cuts is outside this bounded family",
    )

    def selection(key, low, high):
        ids = specification[key]
        require(
            type(ids) is list
            and low <= len(ids) <= high
            and all(type(v) is str for v in ids)
            and len(ids) == len(set(ids))
            and set(ids) <= set(metal),
            "REDESIGN_SELECTION",
            "Unique bounded exact source metal IDs required",
        )
        return tuple(metal[i] for i in ids)

    headers = selection("header_part_ids", 2, 2)
    route = selection("return_part_ids", 2, 16)
    require(
        len({body_id, *(p.part_id for p in headers), *(p.part_id for p in route)})
        == 3 + len(route),
        "REDESIGN_SELECTION",
        "Source operands cannot be consumed twice",
    )
    require(
        all(p.pipe for p in route),
        "REDESIGN_ROUTE",
        "Return union accepts only explicit source pipe primitives",
    )
    require(
        len({(p.pipe.bore_radius, p.pipe.outer_radius) for p in route}) == 1,
        "REDESIGN_ROUTE",
        "Return route must retain one source bore and outer radius",
    )
    tolerance = _tolerance(plan)
    inspection = inspect_interfaces(plan, tolerance)
    ports = {p["id"]: p for p in inspection["ports"]}
    header_ends = {}
    for header in headers:
        matches = [
            m
            for m in inspection["matches"]
            if {ports[m["from"]]["part_id"], ports[m["to"]]["part_id"]}
            == {body_id, header.part_id}
            and ports[m["from"]]["aperture"]["kind"]
            == ports[m["to"]]["aperture"]["kind"]
            == "ANNULAR_SECTOR"
        ]
        require(
            len(matches) == body.cooling.count,
            "REDESIGN_HEADER",
            "Both source headers must mate every exact channel aperture",
        )
        ends = {
            ports[m["from"]]["kind"]
            if ports[m["from"]]["part_id"] == body_id
            else ports[m["to"]]["kind"]
            for m in matches
        }
        require(
            len(ends) == 1,
            "REDESIGN_HEADER",
            "Each collector must mate exactly one channel end",
        )
        header_ends[header.part_id] = next(iter(ends))
    require(
        set(header_ends.values())
        == {"UPPER_COLLECTOR_CONNECTION", "NOZZLE_INLET_CONNECTION"},
        "REDESIGN_HEADER",
        "Distinct upper and nozzle-end collectors required",
    )
    route_ids = {p.part_id for p in route}
    route_ports = [p for p in ports.values() if p["part_id"] in route_ids]
    used = set()
    edges = []
    for i, a in enumerate(route_ports):
        for b in route_ports[i + 1 :]:
            if a["part_id"] == b["part_id"]:
                continue
            if (
                np.linalg.norm(np.array(a["position_m"]) - b["position_m"]) <= tolerance
                and np.dot(a["normal"], b["normal"]) < -1 + 1e-10
            ):
                require(
                    a["id"] not in used and b["id"] not in used,
                    "REDESIGN_ROUTE",
                    "Branching/coincident return endpoints are forbidden",
                )
                used.update((a["id"], b["id"]))
                edges.append((a["part_id"], b["part_id"]))
    seen = {route[0].part_id}
    for _ in route:
        seen.update(b for a, b in edges if a in seen)
        seen.update(a for a, b in edges if b in seen)
    require(
        len(edges) == len(route) - 1
        and seen == route_ids
        and len(route_ports) - len(used) == 2,
        "REDESIGN_ROUTE",
        "One connected, unbranched open return chain required",
    )
    # Bind both free endpoints to saved non-route ports, including the upper collector.
    endpoints = [p for p in route_ports if p["id"] not in used]
    destinations = []
    for endpoint in endpoints:
        peers = [
            ports[m["to"]] if m["from"] == endpoint["id"] else ports[m["from"]]
            for m in inspection["matches"]
            if endpoint["id"] in (m["from"], m["to"])
        ]
        peers = [p for p in peers if p["part_id"] not in route_ids]
        require(
            len(peers) == 1,
            "REDESIGN_ROUTE",
            "Each return endpoint must bind one exact external source port",
        )
        destinations.append(peers[0])
    require(
        any(
            header_ends.get(p["part_id"]) == "UPPER_COLLECTOR_CONNECTION"
            for p in destinations
        )
        and any(
            p["fluid"] == "fuel" and p["kind"] == "MANIFOLD_INLET" for p in destinations
        ),
        "REDESIGN_ROUTE",
        "Return must connect a cooling collector to the separate fuel head inlet",
    )
    raw = specification["stations"]
    require(
        type(raw) is list and len(raw) == len(body.profile),
        "REDESIGN_STATIONS",
        "Exactly one SI station at every saved gas-path vertex required",
    )
    rows = []
    for index, (station, (x, ri, ro)) in enumerate(zip(raw, body.profile, strict=True)):
        keys(station, ("x", "hot_ligament", "depth"), "channel station")
        sx, ligament, depth = (
            scalar(station[k], "m") for k in ("x", "hot_ligament", "depth")
        )
        require(
            sx == x,
            "REDESIGN_STATIONS",
            "Gas-path station locations are immutable in this candidate family",
        )
        require(
            min(ligament, depth, ro - ri - ligament - depth) > 10 * tolerance,
            "REDESIGN_LIGAMENT",
            "Radial ligaments and passage depth must exceed ten source tolerances (numerical floor, not strength acceptance)",
        )
        if index in (0, len(raw) - 1):
            require(
                ligament == body.cooling.hot_ligament and depth == body.cooling.depth,
                "REDESIGN_HEADER",
                "End stations must preserve the saved header apertures exactly",
            )
        rows.append((x, ri + ligament, ri + ligament + depth))
    c = body.cooling
    channels = tuple(
        Part(
            "candidate-channel-" + str(i),
            body.feature_id,
            body.frame_id,
            tuple(rows),
            role="coolant",
            sector=(c.phase_rad + 2 * math.pi * i / c.count, c.width_rad),
        )
        for i in range(c.count)
    )
    consumed = {body_id, *(p.part_id for p in headers), *route_ids}
    groups = (
        Group(
            "integrated-cooling-body", (replace(body, cooling=None), *headers), channels
        ),
        Group("continuous-fuel-return", route),
        *(
            Group(p.part_id, (p,))
            for p in plan.parts
            if p.role == "metal" and p.part_id not in consumed
        ),
    )
    require(
        len({g.part_id for g in groups}) == len(groups),
        "REDESIGN_SELECTION",
        "Derived group IDs collide with retained source parts",
    )
    # Canonical copy prevents a caller's subsequent draft edits changing the recipe.
    import json

    return Candidate(
        plan, json.loads(canonical_json_dumps(specification)), tuple(groups), channels
    )
