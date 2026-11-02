"""Typed bounded component feature language; no native imports or physics sizing."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from itertools import pairwise
from typing import Any

import numpy as np

from core.quantity import Quantity
from core.serialization import canonical_json_dumps
from core.unit import SI
from systems.contracts.geometry import (
    CoordinateFrame,
    DesignSnapshot,
    GeometryFeature,
    GeometryFeatureGraph,
    Representation,
    SIParameter,
    SourceReference,
)
from systems.contracts.geometry._wire import digest, identifier, require

SCHEMA = "cosmos.engine-component-model.v1"
VERSION = "occt-7.8.1.ocp-7.8.1.1.r07components.v1"
POLICY = "r07.components-software-qa.v1"
IDENTITY = (1., 0., 0., 0., 1., 0., 0., 0., 1.)
OPERATIONS = ("profile.wall", "profile.solid", "pipe.circular", "pipe.elbow", "cooling.axial_sector", "injector.showerhead", "injector.doublet", "injector.biprop_doublet", "injector.biprop_radial_doublet", "manifold.dual_annular", "manifold.cooling_annular", "manifold.cooling_front_supply", "interface.bolted_flange", "interface.bolt_pattern", "interface.face_groove", "interface.face_grooves", "injector.triplet", "injector.coaxial", "injector.pintle", "placement.rigid")


def keys(value, expected, label):
    require(type(value) is dict and set(value) == set(expected), "COMPONENT_FIELDS", "Exact supported fields required for " + label)


def scalar(value, unit):
    keys(value, ("value", "unit"), "explicit quantity")
    require(value["unit"] == unit and type(value["value"]) in (int, float) and math.isfinite(value["value"]), "COMPONENT_UNIT", "Explicit finite canonical SI quantity [" + unit + "] required; no guessed conversion")
    return float(value["value"])


@dataclass(frozen=True)
class Hole:
    radius: float
    center_yz: tuple[float, float]  # At plate x=0.
    slope_yz: tuple[float, float]  # dy/dx,dz/dx; finite straight bore.
    role: str
    axial_range: tuple[float, float] | None = None


@dataclass(frozen=True)
class Cavity:
    profile: tuple[tuple[float, float, float], ...]
    role: str
    sector: tuple[float, float] | None = None
    open_passage: bool = False
    open_face: str | None = None


def hole_radial_bounds(hole,begin,end):
    """Conservative ellipse envelope throughout an overlapping axial interval."""
    if hole.axial_range:
        begin,end=max(begin,hole.axial_range[0]),min(end,hole.axial_range[1])
    if begin>end:return None
    c=np.array(hole.center_yz);s=np.array(hole.slope_yz);ss=float(s@s)
    nearest=min(max(-float(c@s)/ss,begin),end) if ss else begin
    minor=float(np.linalg.norm(c+nearest*s));major=max(float(np.linalg.norm(c+x*s)) for x in (begin,end))
    projected=hole.radius*math.sqrt(1+ss)
    return minor-projected,major+projected


@dataclass(frozen=True)
class Cooling:
    count: int
    width_rad: float
    hot_ligament: float
    depth: float
    phase_rad: float
    fluid_domains: bool


@dataclass(frozen=True)
class CircularPipe:
    bore_radius: float
    outer_radius: float
    length: float | None = None
    bend_radius: float | None = None
    angle_rad: float | None = None


@dataclass(frozen=True)
class Part:
    part_id: str
    feature_id: str
    frame_id: str
    profile: tuple[tuple[float, float, float], ...]
    holes: tuple[Hole, ...] = ()
    cooling: Cooling | None = None
    role: str = "metal"
    sector: tuple[float, float] | None = None
    cavities: tuple[Cavity, ...] = ()
    pipe: CircularPipe | None = None

    @property
    def euler(self) -> int:
        if self.pipe:
            return 0  # One continuous through bore; no closed-off pipe caps.
        if self.sector:
            return 2
        return (2 if all(row[1] == 0 for row in self.profile) else 0) - 2 * (len(self.holes) + sum(c.sector is not None for c in self.cavities) + (self.cooling.count if self.cooling else 0))


@dataclass(frozen=True)
class ComponentPlan:
    snapshot: DesignSnapshot
    graph: GeometryFeatureGraph
    parts: tuple[Part, ...]

    def placement(self, frame_id):
        frames = {f.frame_id: f for f in self.snapshot.frames}
        rotation, translation = np.eye(3), np.zeros(3)
        current = frame_id
        while current is not None:
            frame = frames[current]
            r = np.array(frame.rotation).reshape(3, 3)
            rotation, translation = r @ rotation, r @ translation + frame.origin_m
            current = frame.parent_frame_id
        return rotation, translation


def compile_model(spec: dict[str, Any], namespace: str, revision: str, created_at: str, *, sources: tuple[SourceReference, ...] = ()) -> ComponentPlan:
    keys(spec, ("schema", "source", "source_tolerance", "export_tolerance", "frames", "features", "outputs", *(["constraints"] if "constraints" in spec else [])), "component model")
    if "constraints" in spec:
        from systems.geometry.driving_constraints import resolve
        spec = resolve(spec)["specification"]
    require(spec["schema"] == SCHEMA and type(spec["source"]) is str and 0 < len(spec["source"].strip()) <= 2048, "COMPONENT_SOURCE", "Versioned component specification and explicit applicability source required")
    require(type(spec["features"]) is list and 1 <= len(spec["features"]) <= 24 and type(spec["frames"]) is list and 1 <= len(spec["frames"]) <= 24, "COMPONENT_CAPACITY", "1–24 features and frames required")
    source_hash = digest(spec)
    globals_hash = digest({k:spec[k] for k in ("schema","source","source_tolerance","export_tolerance", *(["constraints"] if "constraints" in spec else []))})
    refs = [*sources, SourceReference("component-spec", "component-spec/" + globals_hash + ".json", globals_hash)]
    frames, parameters, features = [], [], []
    for raw in spec["frames"]:
        keys(raw, ("id", "parent", "origin", "rotation"), "coordinate frame")
        require(type(raw["origin"]) is list and len(raw["origin"]) == 3 and type(raw["rotation"]) is list and len(raw["rotation"]) == 9, "COMPONENT_FRAME", "Explicit 3D SI origin and proper row-major rotation required")
        require(all(type(v) in (int, float) and math.isfinite(v) for v in raw["rotation"]), "COMPONENT_FRAME", "Finite proper rotation required")
        origin = tuple(scalar(v, "m") for v in raw["origin"])
        require(max(abs(v) for v in origin) <= 5, "COMPONENT_ENVELOPE", "Frame origin outside the declared five-metre local envelope")
        frames.append(CoordinateFrame(raw["id"], raw["parent"], origin, tuple(raw["rotation"])))
    require(any(f.frame_id == "world" and f.parent_frame_id is None and f.origin_m == (0., 0., 0.) and f.rotation == IDENTITY for f in frames), "COMPONENT_FRAME", "Explicit identity world root required; placements use child frames")
    for name in ("source_tolerance", "export_tolerance"):
        value = scalar(spec[name], "m")
        require((1e-10 if name == "source_tolerance" else 1e-7) <= value < .001, "COMPONENT_TOLERANCE", "Explicit source/export tolerances must meet declared kernel/float32 floors and bounded envelope")
        parameters.append(SIParameter.from_quantity(name, Quantity(value, SI.get("m")), si_unit="m", source_ref_id="component-spec"))
    for raw in spec["features"]:
        keys(raw, ("id", "operation", "frame", "depends_on", "parameters"), "feature")
        identifier(raw["id"], "feature id")
        require(len(raw["id"]) <= 48 and raw["operation"] in OPERATIONS and type(raw["depends_on"]) is list and type(raw["parameters"]) is dict and len(raw["parameters"]) <= 400, "UNSUPPORTED_COMPONENT", "Bounded supported typed feature operation required; no arbitrary code/formula evaluation")
        names = []
        feature_source = "feature-" + raw["id"]
        feature_hash = digest(raw)
        refs.append(SourceReference(feature_source,"component-feature/"+feature_hash+".json",feature_hash))
        for key, quantity in raw["parameters"].items():
            identifier(key, "parameter")
            require(type(quantity) is dict and quantity.get("unit") in {"m", "rad", "1"}, "COMPONENT_UNIT", "Supported feature parameters use canonical m/rad/1")
            value = scalar(quantity, quantity["unit"])
            name = raw["id"] + "." + key
            parameters.append(SIParameter.from_quantity(name, Quantity(value, SI.get(quantity["unit"])), si_unit=quantity["unit"], source_ref_id=feature_source))
            names.append(name)
        features.append(GeometryFeature(raw["id"], raw["operation"], ("source_tolerance","export_tolerance",*names), tuple(raw["depends_on"]), raw["frame"], Representation.ANALYTIC_BREP))
    require(type(spec["outputs"]) is list, "COMPONENT_OUTPUTS", "Explicit output-feature selection required")
    snapshot = DesignSnapshot(namespace, revision, tuple(parameters), tuple(frames), "world", tuple(refs), created_at)
    graph = GeometryFeatureGraph("components-" + source_hash, snapshot.snapshot_id, tuple(features), tuple(spec["outputs"]))
    return from_contracts(snapshot, graph)


def from_contracts(snapshot: DesignSnapshot, graph: GeometryFeatureGraph) -> ComponentPlan:
    graph.validate_snapshot(snapshot)
    require(snapshot.project_id.startswith("engine-component-") and snapshot.frame_id == "world", "COMPONENT_NAMESPACE", "Exact separately admitted component namespace/world frame required")
    params = {p.name: p for p in snapshot.parameters_si}
    require({"source_tolerance", "export_tolerance"} <= set(params), "COMPONENT_TOLERANCE", "Retained tolerances required")
    source_tol, export_tol = params["source_tolerance"].value_si, params["export_tolerance"].value_si
    require(params["source_tolerance"].unit_symbol == params["export_tolerance"].unit_symbol == "m" and 1e-10 <= source_tol < .001 and 1e-7 <= export_tol < .001, "COMPONENT_TOLERANCE", "Retained finite SI tolerances outside supported floors/envelope")
    values: dict[str, tuple[Part, ...]] = {}
    parts: tuple[Part, ...]
    for feature_id in graph.topological_order():
        feature = next(f for f in graph.features if f.feature_id == feature_id)
        require(feature.operation in OPERATIONS and feature.representation is Representation.ANALYTIC_BREP, "UNSUPPORTED_COMPONENT", "No implicit/faceted conversion or undeclared feature operation")
        require(all(key.startswith(feature_id + ".") or key in {"source_tolerance","export_tolerance"} for key in feature.parameter_refs)
                and {"source_tolerance","export_tolerance"} <= set(feature.parameter_refs), "COMPONENT_BINDING", "Feature parameters must bind their own exact names and explicit common tolerances")
        p = {key[len(feature_id) + 1:]: params[key] for key in feature.parameter_refs if key.startswith(feature_id + ".")}
        def q(key, unit="m", *, positive=True, p=p, feature_id=feature_id):
            require(key in p and p[key].unit_symbol == unit, "COMPONENT_PARAMETER", "Missing/mismatched explicit parameter " + feature_id + "." + key)
            value = p[key].value_si
            require(math.isfinite(value) and (not positive or value > 0), "COMPONENT_PARAMETER", "Invalid finite component parameter " + key)
            return value
        def count(key, low, high, q=q):
            value = q(key, "1")
            require(value == int(value) and low <= value <= high, "COMPONENT_CAPACITY", "Integer " + key + " outside the declared operation envelope")
            return int(value)
        def exact(names, p=p, feature_id=feature_id):
            require(set(p) == set(names), "COMPONENT_PARAMETER", "Unknown/missing parameters for " + feature_id)
        if feature.operation in {"profile.wall", "profile.solid"}:
            n = count("point_count", 2, 129)
            names = {"point_count"} | {f"{key}{i}" for i in range(n) for key in ("x", "inner", "outer")}
            exact(names)
            rows = tuple((q(f"x{i}", positive=False), q(f"inner{i}", positive=False), q(f"outer{i}")) for i in range(n))
            require(all(0 <= r < outer <= 1 and outer-r > 4 * max(source_tol, export_tol) for _, r, outer in rows)
                    and max(abs(x) for x, _, _ in rows) <= 3 and all(b[0]-a[0] > 1e-8 for a,b in pairwise(rows)), "COMPONENT_ENVELOPE", "Monotone axial profile and resolved positive wall required; no smoothing or healing")
            require(all(r > 0 for _,r,_ in rows) if feature.operation == "profile.wall" else all(r == 0 for _,r,_ in rows), "COMPONENT_PROFILE", "Wall needs a through bore; solid profile needs explicit zero inner radii")
            parts = (Part(feature_id, feature_id, feature.frame_id, rows),)
        elif feature.operation in {"pipe.circular", "pipe.elbow"}:
            elbow = feature.operation == "pipe.elbow"
            exact(("bore_radius", "wall_thickness", "bend_radius", "angle") if elbow else ("bore_radius", "wall_thickness", "length"))
            bore, wall = q("bore_radius"), q("wall_thickness")
            outer = bore + wall; margin = 4 * max(source_tol, export_tol)
            require(min(bore, wall) > margin and outer <= .1, "PIPE_ENVELOPE", "Resolved positive bore/wall and outer radius <=100mm required")
            if elbow:
                radius, angle = q("bend_radius"), q("angle", "rad")
                # Frozen Core canonical storage rounds SI values. Compare the
                # closed angular limits in that same representation, so exact
                # 15/90-degree inputs survive save/reload. No CAD tolerance or
                # geometry is healed/snap-rounded here.
                angles=json.loads(canonical_json_dumps({"minimum":math.pi/12,"maximum":math.pi/2,"value":angle}))
                require(2*outer + margin < radius <= 1 and angles["minimum"] <= angles["value"] <= angles["maximum"],
                    "PIPE_BEND_ENVELOPE", "Explicit centerline bend radius >2 outer radii, <=1m, and angle15..90deg required; no miter/balancing-loss inference")
                pipe = CircularPipe(bore, outer, bend_radius=radius, angle_rad=angle)
                rows = ()  # A toroidal elbow is not an axial radius profile.
            else:
                length = q("length")
                require(margin < length <= 3, "PIPE_ENVELOPE", "Resolved straight pipe length <=3m required")
                pipe = CircularPipe(bore, outer, length=length)
                rows = ((0., bore, outer), (length, bore, outer))
            require(not feature.dependency_ids, "COMPONENT_OPERAND", "Pipe geometry requires explicit dimensions/frame, not an inferred cut operand")
            parts = (Part(feature_id, feature_id, feature.frame_id, rows, pipe=pipe),)
        elif feature.operation == "cooling.axial_sector":
            exact(("count", "width", "hot_ligament", "depth", "phase", "fluid_domains"))
            require(len(feature.dependency_ids) == 1 and len(values[feature.dependency_ids[0]]) == 1, "COMPONENT_OPERAND", "Cooling pattern requires one exact wall operand")
            parent = values[feature.dependency_ids[0]][0]
            require(parent.frame_id == feature.frame_id and not parent.holes and parent.cooling is None and parent.pipe is None and all(r > 0 for _,r,_ in parent.profile), "COMPONENT_OPERAND", "Cooling needs one uncut positive-bore wall in the same frame")
            fluid = q("fluid_domains", "1", positive=False)
            require(fluid in {0., 1.}, "COMPONENT_FLUID", "Explicit0/1 coolant fluid-domain output selection required")
            cooling = Cooling(count("count", 3, 16), q("width", "rad"), q("hot_ligament"), q("depth"), q("phase", "rad", positive=False), bool(fluid))
            require(0 < cooling.width_rad < 2*math.pi/cooling.count and abs(cooling.phase_rad) <= 2*math.pi
                    and min(cooling.hot_ligament, cooling.depth, min(ro-ri-cooling.hot_ligament-cooling.depth for _,ri,ro in parent.profile)) > 4 * max(source_tol, export_tol)
                    and min(r for _,r,_ in parent.profile) * (2*math.pi/cooling.count-cooling.width_rad) > 4 * max(source_tol, export_tol), "COMPONENT_LIGAMENT", "Internal passages need positive resolved hot wall, roof, channel and rib; no overlap/open hot-wall cuts")
            parts = (replace(parent, part_id=feature_id, feature_id=feature_id, cooling=cooling),)
            if cooling.fluid_domains:
                rows = tuple((x,ri+cooling.hot_ligament,ri+cooling.hot_ligament+cooling.depth) for x,ri,_ in parent.profile)
                parts += tuple(Part(feature_id+".fluid-"+str(i), feature_id, feature.frame_id, rows, role="coolant-fluid-domain", sector=(cooling.phase_rad+2*math.pi*i/cooling.count,cooling.width_rad)) for i in range(cooling.count))
        elif feature.operation == "manifold.dual_annular":
            exact(("radius", "back_web", "plenum_length", "front_web", "fuel_inner", "fuel_outer", "oxidizer_inner", "oxidizer_outer",
                   "fuel_inlet_radius", "oxidizer_inlet_radius", "fuel_inlet_phase", "oxidizer_inlet_phase",
                   "ring_radius", "separation", "count", "fuel_hole_radius", "oxidizer_hole_radius", "phase"))
            radius, back, length, front = (q(k) for k in ("radius", "back_web", "plenum_length", "front_web"))
            rings = [q(k) for k in ("fuel_inner", "fuel_outer", "oxidizer_inner", "oxidizer_outer")]
            ring, separation, n, phase = q("ring_radius"), q("separation"), count("count", 3, 24), q("phase", "rad", positive=False)
            margin = 4 * max(source_tol, export_tol)
            require(radius <= 1 and back + length + front <= .5 and min(back, length, front) > margin
                    and rings[0] > margin and rings[-1] + margin < radius and all(b-a > margin for a,b in pairwise(rings))
                    and separation > margin and abs(phase) <= 2*math.pi, "MANIFOLD_WALL", "Two disjoint resolved annular plenums and positive end webs required")
            holes, cavities = [], []
            for index, name in enumerate(("fuel", "oxidizer")):
                low, high = rings[2*index:2*index+2]
                outlet_radius, inlet_radius = q(name+"_hole_radius"), q(name+"_inlet_radius")
                inlet_phase = q(name+"_inlet_phase", "rad", positive=False)
                center_radius = ring + (-1 if index == 0 else 1)*separation/2
                require(min(outlet_radius, inlet_radius) > margin and abs(inlet_phase) <= 2*math.pi
                        and low + outlet_radius + margin < center_radius < high - outlet_radius - margin
                        and 2*center_radius*math.sin(math.pi/n) > 2*outlet_radius + margin
                        and 2*inlet_radius + 2*margin < high-low,
                        "MANIFOLD_PORT", "Every separate inlet/outlet must open wholly inside its own plenum, with resolved walls and port ligaments")
                cavities.append(Cavity(((back,low,high),(back+length,low,high)), name))
                inlet_ring = (low+high)/2
                holes.append(Hole(inlet_radius,(inlet_ring*math.cos(inlet_phase),inlet_ring*math.sin(inlet_phase)),(0.,0.),name+"-inlet",(0.,back)))
                for i in range(n):
                    angle = phase + 2*math.pi*i/n
                    holes.append(Hole(outlet_radius,(center_radius*math.cos(angle),center_radius*math.sin(angle)),(0.,0.),name+"-outlet",(back+length,back+length+front)))
            parts = (Part(feature_id,feature_id,feature.frame_id,((0.,0.,radius),(back+length+front,0.,radius)),tuple(holes),cavities=tuple(cavities)),)
        elif feature.operation in {"manifold.cooling_annular","manifold.cooling_front_supply"}:
            exact(("bore_radius","outer_radius","back_web","plenum_length","front_web","plenum_inner","plenum_outer",
                   "port_inner","port_outer","supply_hole_radius","supply_phase","count","width","phase"))
            bore,outer,back,length,front,low,high,port_low,port_high,supply=(q(k) for k in
                ("bore_radius","outer_radius","back_web","plenum_length","front_web","plenum_inner","plenum_outer","port_inner","port_outer","supply_hole_radius"))
            n=count("count",3,16);width=q("width","rad");phase=q("phase","rad",positive=False)
            supply_phase=q("supply_phase","rad",positive=False);margin=4*max(source_tol,export_tol)
            require(outer<=1 and back+length+front<=.5
                    and min(bore,back,length,front,low-bore,port_low-low,port_high-port_low,high-port_high,outer-high,supply)>margin
                    and 2*supply+2*margin<high-low and abs(phase)<=2*math.pi and abs(supply_phase)<=2*math.pi
                    and 0<width<2*math.pi/n and port_low*min(width,2*math.pi/n-width)>margin,
                    "COOLING_HEADER_LIGAMENT","Resolved central gas bore, annular plenum, separate sector ports and supply/edge/web/rib ligaments required")
            total=back+length+front;ring=(low+high)/2
            cooling_cavities=(Cavity(((back,low,high),(back+length,low,high)),"coolant"),)+tuple(
                Cavity(((back+length,port_low,port_high),(total,port_low,port_high)),"coolant-outlet-"+str(i),(phase+2*math.pi*i/n,width),True)
                for i in range(n))
            front_supply=feature.operation=="manifold.cooling_front_supply"
            if front_supply:
                require(ring-supply-port_high>margin,"COOLING_HEADER_SUPPLY_INTERSECTION",
                    "Front supply bore must be wholly outside every channel-sector radial envelope")
            supply_hole=Hole(supply,(ring*math.cos(supply_phase),ring*math.sin(supply_phase)),(0.,0.),
                "coolant-outlet" if front_supply else "coolant-inlet",(back+length,total) if front_supply else (0.,back))
            parts=(Part(feature_id,feature_id,feature.frame_id,((0.,bore,outer),(total,bore,outer)),(supply_hole,),cavities=cooling_cavities),)
        elif feature.operation == "interface.bolt_pattern":
            exact(("bolt_circle_radius", "bolt_hole_radius", "count", "phase"))
            require(len(feature.dependency_ids)==1 and len(values[feature.dependency_ids[0]])==1,
                    "COMPONENT_OPERAND", "Bolt cuts need one exact annular operand")
            parent=values[feature.dependency_ids[0]][0]
            require(parent.frame_id==feature.frame_id and parent.pipe is None and parent.cooling is None
                    and parent.sector is None and parent.role=="metal" and len(parent.profile)==2
                    and parent.profile[0][1:]==parent.profile[1][1:]
                    and not any(h.role=="fastener-clearance" for h in parent.holes),
                    "BOLT_PATTERN_OPERAND", "Uniform solid/annular metal in the same frame and no existing fastener pattern required")
            ring,hole=q("bolt_circle_radius"),q("bolt_hole_radius")
            n,phase=count("count",3,32),q("phase","rad",positive=False)
            margin=4*max(source_tol,export_tol);bore,outer=parent.profile[0][1:]
            require(hole>margin and abs(phase)<=2*math.pi and bore+hole+margin<ring<outer-hole-margin
                    and 2*ring*math.sin(math.pi/n)>2*hole+margin,
                    "FLANGE_LIGAMENT", "Resolved annular edge and bolt-to-bolt ligaments required")
            # Conservative radial exclusion protects every plenum/sector, not
            # just a sampled angle or an invented nominal wall thickness.
            require(all(ring+hole+margin<min(row[1] for row in c.profile)
                        or ring-hole-margin>max(row[2] for row in c.profile) for c in parent.cavities),
                    "BOLT_CAVITY_INTERSECTION", "Bolt bores must leave a resolved ligament to every cavity radial envelope")
            cuts=tuple(Hole(hole,(ring*math.cos(phase+2*math.pi*i/n),ring*math.sin(phase+2*math.pi*i/n)),(0.,0.),"fastener-clearance") for i in range(n))
            def separated(c,h,parent=parent,margin=margin):
                begin,end=h.axial_range or (parent.profile[0][0],parent.profile[-1][0])
                center=np.array(c.center_yz)-h.center_yz;slope=np.array(h.slope_yz);ss=float(slope@slope)
                x=min(max(float(center@slope)/ss,begin),end) if ss else begin
                return float(np.linalg.norm(center-x*slope))>c.radius+h.radius*math.sqrt(1+ss)+margin
            require(all(separated(c,h) for c in cuts for h in parent.holes),
                    "BOLT_PORT_INTERSECTION", "Fastener cuts must not intersect existing fluid ports")
            parts=(replace(parent,part_id=feature_id,feature_id=feature_id,holes=parent.holes+cuts),)
        elif feature.operation in {"interface.face_groove","interface.face_grooves"}:
            multiple=feature.operation=="interface.face_grooves"
            n=count("count",1,5) if multiple else 1
            dimensions=("inner_radius","outer_radius","depth","face")
            exact({"count",*[name+str(i) for i in range(n) for name in dimensions]} if multiple else dimensions)
            require(len(feature.dependency_ids)==1 and len(values[feature.dependency_ids[0]])==1,
                    "COMPONENT_OPERAND","Face groove needs one exact metal operand")
            parent=values[feature.dependency_ids[0]][0]
            require(parent.frame_id==feature.frame_id and parent.pipe is None and parent.cooling is None
                    and parent.sector is None and parent.role=="metal" and len(parent.profile)==2
                    and parent.profile[0][1:]==parent.profile[-1][1:],"GROOVE_OPERAND","Uniform solid/annular metal in the same frame required")
            start,end=parent.profile[0][0],parent.profile[-1][0];bore,outer=parent.profile[0][1:]
            margin=4*max(source_tol,export_tol)
            for index in range(n):
                suffix=str(index) if multiple else ""
                low,high,depth=(q(name+suffix) for name in dimensions[:3]);face=q("face"+suffix,"1",positive=False)
                require(face in {-1.,1.},"GROOVE_FACE","Explicit -1 start or +1 end face required")
                require(min(low-bore,high-low,outer-high,depth,end-start-depth)>margin,
                        "GROOVE_LIGAMENT","Resolved radial lands, groove width/depth and retained blind floor required")
                a,b=(start,start+depth) if face<0 else (end-depth,end)
                require(all(b+margin<c.profile[0][0] or a-margin>c.profile[-1][0]
                        or high+margin<min(r[1] for r in c.profile) or low-margin>max(r[2] for r in c.profile)
                        for c in parent.cavities),"GROOVE_CAVITY_INTERSECTION","Groove must retain resolved floor/land to every cavity")
                bounds=[hole_radial_bounds(h,a,b) for h in parent.holes]
                require(all(v is None or v[1]+margin<low or v[0]-margin>high for v in bounds),
                        "GROOVE_PORT_INTERSECTION","Full annular groove must not breach any fluid/fastener bore")
                role="face-groove-"+feature_id+("-"+suffix if multiple else "")
                cavity=Cavity(((a,low,high),(b,low,high)),role,open_face="start" if face<0 else "end")
                parent=replace(parent,part_id=feature_id,feature_id=feature_id,cavities=parent.cavities+(cavity,))
            parts=(parent,)
        elif feature.operation == "interface.bolted_flange":
            exact(("bore_radius", "outer_radius", "thickness", "bolt_circle_radius", "bolt_hole_radius", "count", "phase"))
            bore, outer, thickness, ring, hole = (q(k) for k in ("bore_radius", "outer_radius", "thickness", "bolt_circle_radius", "bolt_hole_radius"))
            n, phase = count("count", 3, 32), q("phase", "rad", positive=False)
            margin = 4*max(source_tol,export_tol)
            require(outer <= 1 and thickness <= .5 and min(bore,thickness,hole) > margin and abs(phase) <= 2*math.pi
                    and bore + hole + margin < ring < outer - hole - margin
                    and 2*ring*math.sin(math.pi/n) > 2*hole + margin,
                    "FLANGE_LIGAMENT", "Resolved central bore, bolt/edge ligaments and explicit finite flange dimensions required")
            flange_holes = tuple(Hole(hole,(ring*math.cos(phase+2*math.pi*i/n),ring*math.sin(phase+2*math.pi*i/n)),(0.,0.),"fastener-clearance") for i in range(n))
            parts = (Part(feature_id,feature_id,feature.frame_id,((0.,bore,outer),(thickness,bore,outer)),flange_holes),)
        elif feature.operation in {"injector.showerhead", "injector.doublet", "injector.biprop_doublet", "injector.biprop_radial_doublet", "injector.triplet"}:
            inclined = feature.operation != "injector.showerhead"
            biprop = feature.operation in {"injector.biprop_doublet", "injector.biprop_radial_doublet"}
            bore_keys = ("fuel_hole_radius", "oxidizer_hole_radius") if biprop else ("hole_radius",)
            exact(("radius", "thickness", "ring_radius", "count", *bore_keys, "phase", *(("separation", "angle") if inclined else ())))
            radius, thickness, ring, n, phase = q("radius"), q("thickness"), q("ring_radius"), count("count", 3, 24), q("phase", "rad", positive=False)
            bores = [q(key) for key in bore_keys]
            require(radius <= 1 and thickness <= .5 and min(bores) > 4 * max(source_tol, export_tol) and abs(phase) <= 2*math.pi, "COMPONENT_ENVELOPE", "Plate/bore dimensions outside resolved local envelope")
            separation, angle = (q("separation"), q("angle", "rad")) if inclined else (0., 0.)
            require(angle < .7, "COMPONENT_ANGLE", "Bore inclination outside the declared below0.7rad envelope")
            holes = []
            for i in range(n):
                a = phase + 2*math.pi*i/n
                radial, tangent = np.array([math.cos(a), math.sin(a)]), np.array([-math.sin(a), math.cos(a)])
                pair_axis = radial if feature.operation == "injector.biprop_radial_doublet" else tangent
                for side in ((-1, 1) if inclined else (0,)):
                    center = ring * radial + side * separation / 2 * pair_axis
                    slope = -side * math.tan(angle) * pair_axis
                    role = ("fuel" if side < 0 else "oxidizer") if biprop else "paired-port" if inclined else "axial-port"
                    bore = bores[0 if side < 0 else 1] if biprop else bores[0]
                    holes.append(Hole(bore, tuple(center), tuple(slope), role))
                if feature.operation == "injector.triplet":
                    holes.append(Hole(bores[0], tuple(ring*radial), (0., 0.), "central-port"))
            margin = 4 * max(source_tol, export_tol)
            for h in holes:
                u = math.sqrt(1+sum(v*v for v in h.slope_yz))
                require(max(np.linalg.norm(np.array(h.center_yz) + x*np.array(h.slope_yz)) for x in (0., thickness)) + h.radius*u + margin < radius, "COMPONENT_BORE_EDGE", "Bore intersects the plate outer edge; enlarge plate or change explicit layout")
            for a,b in ((a,b) for i,a in enumerate(holes) for b in holes[i+1:]):
                delta, velocity = np.array(a.center_yz)-b.center_yz, np.array(a.slope_yz)-b.slope_yz
                v2 = float(velocity @ velocity)
                x = float(np.clip(-float(delta @ velocity)/v2,0,thickness)) if v2 else 0.
                clearance = float(np.linalg.norm(delta+x*velocity)) - a.radius*math.sqrt(1+sum(v*v for v in a.slope_yz)) - b.radius*math.sqrt(1+sum(v*v for v in b.slope_yz))
                require(clearance > margin, "COMPONENT_BORE_COLLISION", "Inclined/central bores intersect or have unresolved ligament inside the plate; impingement must occur outside metal")
            rows = ((0., 0., radius), (thickness, 0., radius))
            parts = (Part(feature_id, feature_id, feature.frame_id, rows, tuple(holes)),)
        elif feature.operation == "injector.coaxial":
            exact(("length", "inner_bore", "inner_outer", "outer_inner", "outer_radius"))
            length = q("length")
            radii = [q(k) for k in ("inner_bore", "inner_outer", "outer_inner", "outer_radius")]
            require(length <= 1 and radii[-1] <= 1 and all(b-a > 4*max(source_tol,export_tol) for a,b in pairwise(radii)), "COMPONENT_GAP", "Coaxial tubes need distinct resolved metal walls and fluid annulus")
            parts = tuple(Part(feature_id+suffix, feature_id, feature.frame_id, ((0.,ri,ro),(length,ri,ro))) for suffix,ri,ro in ((".inner-tube",radii[0],radii[1]),(".outer-sleeve",radii[2],radii[3])))
        elif feature.operation == "injector.pintle":
            exact(("length", "rod_radius", "stem_inner", "stem_outer", "sleeve_inner", "sleeve_outer", "radial_gap", "tip_length", "tip_radius"))
            length, gap, tip = q("length"), q("radial_gap"), q("tip_length")
            rod, si, so, oi, oo, rt = [q(k) for k in ("rod_radius","stem_inner","stem_outer","sleeve_inner","sleeve_outer","tip_radius")]
            require(length <= 1 and 0 < gap < length and tip <= length and oo <= 1 and all(b-a > 4*max(source_tol,export_tol) for a,b in pairwise((rod,si,so,oi,oo)))
                    and so < rt < oo and min(gap,tip,rod) > 4*max(source_tol,export_tol), "COMPONENT_GAP", "Resolved coaxial feed walls, rod, radial discharge gap and explicit deflector needed")
            parts = (Part(feature_id+".stem",feature_id,feature.frame_id,((-length,si,so),(-gap,si,so))),
                     Part(feature_id+".sleeve",feature_id,feature.frame_id,((-length,oi,oo),(0.,oi,oo))),
                     Part(feature_id+".rod-deflector",feature_id,feature.frame_id,((-length,0.,rod),(0.,0.,rod),(tip,0.,rt))))
        else:
            exact(())
            require(len(feature.dependency_ids) == 1, "COMPONENT_OPERAND", "Rigid placement requires exactly one predecessor")
            parts = tuple(replace(part, part_id=feature_id+"."+str(i), feature_id=feature_id, frame_id=feature.frame_id) for i,part in enumerate(values[feature.dependency_ids[0]]))
        values[feature_id] = parts
    output = tuple(part for name in graph.output_feature_ids for part in values[name])
    require(0 < len(output) <= 24 and len({p.part_id for p in output}) == len(output), "COMPONENT_CAPACITY", "Select1–24 uniquely named output parts; suppress consumed parent operands explicitly")
    require(set(params) == {"source_tolerance", "export_tolerance"} | {key for f in graph.features for key in f.parameter_refs}, "COMPONENT_BINDING", "No unbound hidden parameters allowed")
    return ComponentPlan(snapshot, graph, output)


def profile_parameters(points, *, solid=False):
    """Explicit source mapper; no resampling, inferred wall sizing or defaults."""
    q = lambda v: {"value": v, "unit": "m"}
    result = {"point_count": {"value": len(points), "unit": "1"}}
    for i,(x,inner,outer) in enumerate(points):
        result.update({"x"+str(i):q(x), "inner"+str(i):q(0. if solid else inner), "outer"+str(i):q(outer)})
    return result
