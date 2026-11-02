"""Thin facade for bounded source-bound CAD inspection and drawings."""
from hashlib import sha256
import json

from api.geometry_projects import BinarySource
from systems.contracts.geometry._wire import require
from systems.geometry.driving_constraints import resolve


class UnreleasedDrawingSource(BinarySource):
    """Unreleased engineering drawing, never manufacturing acceptance."""


def handle(api,actor,method,project,parts,query,body):
    api.repository.get_project(actor,project)
    service=api.cad_tools
    if parts==["capabilities"] and method=="GET":
        require(not query,"CAD_FIELDS","No capability overrides")
        return service.capabilities()
    if parts==["constraints"] and method=="POST":
        require(set(body)=={"specification"} and not query,"CAD_FIELDS","Explicit source specification required")
        resolved=resolve(body["specification"])
        from systems.geometry.component_model import compile_model
        plan=compile_model(resolved["specification"],"engine-component-constraint-preview","constraint-preview","2000-01-01T00:00:00Z")
        return {"ok":True,"persisted":False,"resolved_specification":resolved["specification"],"constraint_report":resolved["report"],"body_count":len(plan.parts),"physical_validation":"NOT_PERFORMED"}
    require(len(parts)==3 and parts[0]=="jobs" and method=="GET","CAD_ROUTE","Exact retained job and supported read-only CAD operation required")
    require(all(len(v)==1 for v in query.values()),"CAD_FIELDS","Duplicate CAD query fields forbidden")
    values={k:v[0] for k,v in query.items()}
    if parts[2]=="clearance":return service.clearance(actor,project,parts[1],values)
    require(parts[2] in {"drawing.pdf","drawing.svg","drawing.json"},"CAD_ROUTE","Supported unreleased drawing format required")
    format=parts[2].split(".")[1];result,output=service.drawing(actor,project,parts[1],values,format)
    if format=="json":output=json.dumps(result,allow_nan=False,indent=2).encode()
    return UnreleasedDrawingSource("UNRELEASED-component-drawing."+format,output,sha256(output).hexdigest())
