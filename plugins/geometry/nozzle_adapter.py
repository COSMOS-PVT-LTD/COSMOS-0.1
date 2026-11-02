"""Separate explicitly enabled nozzle operation profile; reuse protocol decoding."""

from __future__ import annotations

from infrastructure.geometry import WorkerCommand
from plugins.geometry.adapters import Capabilities, GeometryBackend
from plugins.geometry.nozzle_protocol import VERSION, validate
from plugins.geometry.protocol import payload
from systems.contracts.geometry import Representation
from systems.contracts.geometry._wire import require


class NozzleAdapter(GeometryBackend):
    def capabilities(self) -> Capabilities:
        return Capabilities("occt", VERSION, Representation.ANALYTIC_BREP,
                            ("polyline_profile_intent", "radial_offset_closed_profile_intent", "revolve_x_intent"),
                            ("step", "stl"), ("throat-x",), 3, False)

    def build(self, job_id, request, snapshot, graph, directory, *, cancellation=None):
        require(self.enabled, "NGG_DISABLED", "Nozzle backend requires explicit qualified local runtime configuration")
        validate(request, snapshot, graph)
        command = WorkerCommand((*self.command.argv, str(directory)), self.command.environment)
        return self.supervisor.submit(job_id, command, payload(job_id, request, snapshot, graph), directory, cancellation=cancellation)

    def health(self, job_id, request, snapshot, graph, directory):
        require(self.enabled, "NGG_DISABLED", "Nozzle backend requires explicit qualified runtime configuration")
        validate(request, snapshot, graph)
        command = WorkerCommand((*self.command.argv, str(directory)), self.command.environment)
        return self.supervisor.submit(job_id, command, payload(job_id, request, snapshot, graph, action="health"), directory)
