"""Explicitly enabled process boundary; no native CAD imports in application host."""

from infrastructure.geometry import WorkerCommand
from plugins.geometry.adapters import Capabilities, GeometryBackend
from plugins.geometry.component_protocol import validate
from plugins.geometry.protocol import payload
from systems.contracts.geometry import Representation
from systems.contracts.geometry._wire import require
from systems.geometry.component_model import OPERATIONS, VERSION


class ComponentAdapter(GeometryBackend):
    def capabilities(self):
        return Capabilities("occt",VERSION,Representation.ANALYTIC_BREP,OPERATIONS,("step","stl"),("proper-rigid-frame-tree",),24,False)

    def build(self,job_id,request,snapshot,graph,directory,*,cancellation=None):
        require(self.enabled,"NGG_DISABLED","Qualified component runtime must be explicitly enabled")
        validate(request,snapshot,graph)
        command = WorkerCommand((*self.command.argv,str(directory)),self.command.environment)
        return self.supervisor.submit(job_id,command,payload(job_id,request,snapshot,graph),directory,cancellation=cancellation)

    def health(self,job_id,request,snapshot,graph,directory):
        require(self.enabled,"NGG_DISABLED","Qualified component runtime must be explicitly enabled")
        validate(request,snapshot,graph)
        command = WorkerCommand((*self.command.argv,str(directory)),self.command.environment)
        return self.supervisor.submit(job_id,command,payload(job_id,request,snapshot,graph,action="health"),directory)
