"""Strict read-only source-bound fluid/mechanical interface inspection."""
import json
from dataclasses import asdict

from systems.geometry.component_authority import DOMAIN, from_source
from systems.geometry.component_circuits import assess_circuits
from systems.geometry.component_interfaces import inspect_interfaces
from systems.projects.authority import InvalidRecord, RecordNotFound


def handle(components,actor,method,project,parts,query,body):
    if method!="GET" or len(parts)!=1:raise RecordNotFound("Interface inspection is read-only for an exact saved component model")
    if (body or set(query) not in ({"commit","tolerance_m"},{"commit","tolerance_m","fuel_boundary","oxidizer_boundary"})
        or any(len(v)!=1 for v in query.values()) or not query["commit"][0]):
        raise InvalidRecord("Exact component commit and explicit numerical tolerance_m required; no posted/query overrides")
    source=components.repository.get_snapshot(actor,project,domain=DOMAIN,object_id=parts[0],commit_id=query["commit"][0])
    plan=from_source(source); report=inspect_interfaces(plan,float(query["tolerance_m"][0]))
    if "fuel_boundary" in query:
        report["circuits"]=assess_circuits(plan,report,query["fuel_boundary"][0],query["oxidizer_boundary"][0])
        report["geometry_route_complete"]=report["circuits"]["topology_complete"]
    return {"ok":True,"persisted":False,"authority":{"project_id":project,"object_id":source.object_id,"commit_id":source.commit_id,"head":asdict(source.head)},
            "baseline_commit_id":json.loads(source.payload)["baseline_commit_id"],"upstream_current":components.models.current(actor,source),**report}
