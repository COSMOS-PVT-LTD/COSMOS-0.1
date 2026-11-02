"""PicoGK field derivation from immutable component intent; no BREP/mesh conversion."""
from dataclasses import asdict, replace
from hashlib import sha256
import json

import numpy as np

from infrastructure.geometry import WorkerCommand
from plugins.geometry.adapters import Capabilities, GeometryBackend
from plugins.geometry.protocol import payload,checked_file
from systems.contracts.geometry import Representation, GeometryFeatureGraph, OutputFormat
from systems.contracts.geometry._wire import require, MAX_WIRE_BYTES
from systems.geometry.component_model import from_contracts, OPERATIONS
from systems.geometry.component_reference import PartReference

VERSION="picogk-2.2.0.components.v1"
POLICY="picogk.components-mesh-software-qa.v1"
SCHEMA="cosmos.picogk-components-field.v1"


def field_graph(plan):
    """Distinct typed representation/hash, preserving source features and parameters."""
    return GeometryFeatureGraph(plan.graph.graph_id,plan.snapshot.snapshot_id,
        tuple(replace(f,representation=Representation.IMPLICIT_FIELD) for f in plan.graph.features),plan.graph.output_feature_ids)


def plan_for(snapshot,graph):
    require(all(f.representation is Representation.IMPLICIT_FIELD for f in graph.features),"PICO_REPRESENTATION","Explicit implicit component graph required")
    analytic=GeometryFeatureGraph(graph.graph_id,snapshot.snapshot_id,
        tuple(replace(f,representation=Representation.ANALYTIC_BREP) for f in graph.features),graph.output_feature_ids)
    return from_contracts(snapshot,analytic)


def validate(request,snapshot,graph):
    graph.validate_snapshot(snapshot)
    require(request.backend_id=="picogk" and request.backend_version==VERSION and request.representation is Representation.IMPLICIT_FIELD
        and request.approximation_profile=="sparse_volume" and request.output_formats==(OutputFormat.STL,),"PICO_POLICY","PicoGK component fields support explicit voxel/STL output only; no analytic STEP substitution")
    require(request.snapshot_id==snapshot.snapshot_id and request.feature_graph_sha256==graph.content_sha256 and request.feature_graph_id==graph.graph_id
        and request.frame_id==snapshot.frame_id=="world","PICO_LINEAGE","Exact component snapshot/graph/world frame required")
    h=request.voxel_resolution_m
    require(h is not None and 2.5e-5<=h<=.002,"PICO_RESOLUTION","Explicit voxel resolution must be25 micrometres–2 millimetres within the local software envelope")
    plan=plan_for(snapshot,graph)
    require(0<len(plan.parts)<=64,"PICO_CAPACITY","1–64 explicit component output parts required")
    # Callback rendering visits the bounding cells, not just the thin solid.
    cells=sum(float(np.prod((PartReference(plan,p).bounds_m[3:]-PartReference(plan,p).bounds_m[:3])/h+5)) for p in plan.parts)
    require(cells<=120_000_000,"PICO_CAPACITY","Explicit field sampling exceeds120M bounding cells; split source outputs or select a separately studied resolution")
    return plan


def fields(plan):
    result=[]
    for p in plan.parts:
        rotation,translation=plan.placement(p.frame_id)
        result.append({**asdict(p),"rotation":rotation.ravel().tolist(),"translation_m":translation.tolist(),"bounds_m":PartReference(plan,p).bounds_m.tolist()})
    return result


class PicoComponentAdapter(GeometryBackend):
    artifact_limit_bytes=256*1024**2
    def inspect(self,directory,file):
        return checked_file(directory,file.name,file.sha256,max_bytes=self.artifact_limit_bytes)

    def capabilities(self):
        return Capabilities("picogk",VERSION,Representation.IMPLICIT_FIELD,OPERATIONS,("stl",),("proper-rigid-frame-tree",),24,False)

    def build(self,job_id,request,snapshot,graph,directory,*,cancellation=None):
        require(self.enabled,"NGG_DISABLED","Separately qualified PicoGK component runtime required")
        plan=validate(request,snapshot,graph)
        envelope=json.loads(payload(job_id,request,snapshot,graph))
        wire=json.dumps(fields(plan),allow_nan=False,separators=(",",":"))
        envelope.update(component_schema=SCHEMA,fields_wire=wire,fields_sha256=sha256(wire.encode()).hexdigest())
        raw=json.dumps(envelope,allow_nan=False,separators=(",",":")).encode()
        require(len(raw)<=MAX_WIRE_BYTES,"CONTRACT_LIMIT","Bounded PicoGK component envelope exceeded")
        command=WorkerCommand((*self.command.argv,str(directory)),self.command.environment)
        return self.supervisor.submit(job_id,command,raw,directory,cancellation=cancellation)
