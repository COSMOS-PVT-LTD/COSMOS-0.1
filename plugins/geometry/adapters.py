"""Default-disabled process adapters. No native library is imported in the host."""
from __future__ import annotations

import json
import math
import threading
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path

from infrastructure.geometry import ProcessResult, WorkerCommand, WorkerSupervisor
from systems.contracts.geometry import (
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryContractError,
    GeometryFeatureGraph,
    Representation,
)
from systems.contracts.geometry._wire import require

from .protocol import (
    CAD_VERSION,
    PICO_VERSION,
    PROTOCOL,
    BackendResult,
    ExportFile,
    checked_file,
    payload,
    validate_slice,
)


@dataclass(frozen=True, slots=True)
class Capabilities:
    backend_id: str
    version: str
    source_representation: Representation
    operations: tuple[str, ...]
    formats: tuple[str, ...]
    frames: tuple[str, ...] = ("identity_root",)
    maximum_features: int = 64
    production_enabled: bool = False


class GeometryBackend:
    """Explicit trusted configuration; instances have no store or GUI ownership."""

    artifact_limit_bytes = 64 * 1024**2

    def __init__(self, backend_id: str, command: WorkerCommand, supervisor: WorkerSupervisor, *, enabled: bool = False) -> None:
        require(backend_id in {"picogk", "occt"}, "UNKNOWN_BACKEND", "Unknown geometry backend")
        self.backend_id, self.command, self.supervisor, self.enabled = backend_id, command, supervisor, enabled

    def capabilities(self) -> Capabilities:
        implicit = self.backend_id == "picogk"
        return Capabilities(self.backend_id, PICO_VERSION if implicit else CAD_VERSION,
                            Representation.IMPLICIT_FIELD if implicit else Representation.ANALYTIC_BREP,
                            ("primitive.sphere", "boolean.union", "boolean.difference", "boolean.intersection")
                            + (() if implicit else ("primitive.box", "primitive.cylinder")),
                            ("stl",) if implicit else ("step", "stl"))

    def build(self, job_id: str, request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph,
              directory: Path, *, cancellation: threading.Event | None = None) -> Future[ProcessResult]:
        require(self.enabled, "NGG_DISABLED", "Geometry adapters are disabled; enable explicitly in trusted local configuration")
        validate_slice(request, snapshot, graph, self.backend_id)
        caps = self.capabilities()
        require(request.representation is caps.source_representation and all(f.representation is caps.source_representation for f in graph.features), "REPRESENTATION_MISMATCH", "Backend representation mismatch")
        require({f.value for f in request.output_formats} <= set(caps.formats), "UNSUPPORTED_FORMAT", "Backend cannot export a requested format")
        command = WorkerCommand((*self.command.argv, str(directory)), self.command.environment)
        return self.supervisor.submit(job_id, command, payload(job_id, request, snapshot, graph), directory, cancellation=cancellation)

    def cancel(self, job_id: str) -> bool:
        return self.supervisor.cancel(job_id)

    def health(self, job_id: str, request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph,
               directory: Path) -> Future[ProcessResult]:
        require(self.enabled, "NGG_DISABLED", "Geometry adapter is disabled")
        validate_slice(request, snapshot, graph, self.backend_id)
        command = WorkerCommand((*self.command.argv, str(directory)), self.command.environment)
        return self.supervisor.submit(job_id, command, payload(job_id, request, snapshot, graph, action="health"), directory)

    def decode(self, result: ProcessResult, request: GeometryBuildRequest, directory: Path) -> BackendResult:
        def pairs(items):
            require(len({k for k, _ in items}) == len(items), "DUPLICATE_KEY", "Duplicate response key")
            return dict(items)
        def finite(number: str) -> float:
            value = float(number)
            require(math.isfinite(value), "NONFINITE", "Nonfinite worker response number")
            return value
        def constant(_: str):
            raise GeometryContractError("NONFINITE", "Nonfinite worker JSON constant")
        try:
            events = [json.loads(line, object_pairs_hook=pairs, parse_float=finite, parse_constant=constant) for line in result.stdout.splitlines() if line.strip()]
        except GeometryContractError:
            raise
        except (ValueError, UnicodeError) as error:
            raise GeometryContractError("INVALID_RESPONSE", "Worker emitted malformed JSON") from error
        if result.code != "OK":
            failed = events[-1] if events and type(events[-1]) is dict and events[-1].get("event_type") == "failed" else {}
            if failed:
                require(failed.get("protocol") == PROTOCOL and failed.get("job_id") == result.job_id
                        and failed.get("correlation_id") == request.correlation_id and failed.get("backend_version") == request.backend_version,
                        "INVALID_RESPONSE", "Worker failure identity mismatch")
                from systems.contracts.geometry._wire import identifier
                require("code" in failed, "INVALID_RESPONSE", "Worker failure requires a code")
                identifier(failed["code"], "code")
            code = failed.get("code", result.code) if result.code == "WORKER_CRASH" else result.code
            raise GeometryContractError(code, failed.get("message", "Worker failed; no artifact is accepted"))
        require(len(events) == 2 and all(type(e) is dict for e in events), "INVALID_RESPONSE", "Expected one started and one completed event")
        for event in events:
            require(event.get("protocol") == PROTOCOL and event.get("job_id") == result.job_id
                    and event.get("correlation_id") == request.correlation_id and event.get("backend_version") == request.backend_version,
                    "INVALID_RESPONSE", "Worker protocol/version/correlation mismatch")
        require(events[0].get("event_type") == "started" and events[1].get("event_type") == "completed", "INVALID_RESPONSE", "Worker did not finish a normal build")
        require(set(events[0]) == {"protocol", "job_id", "correlation_id", "event_type", "backend_version"}
                and set(events[1]) == {"protocol", "job_id", "correlation_id", "event_type", "backend_version", "source_name", "source_sha256", "exports", "metrics"}, "INVALID_RESPONSE", "Unknown/missing response fields")
        final = events[1]
        source_name = "source.vdb" if self.backend_id == "picogk" else "source.brep"
        require(final["source_name"] == source_name, "INVALID_RESPONSE", "Incorrect source representation file")
        checked_file(directory, source_name, final["source_sha256"],max_bytes=self.artifact_limit_bytes)
        require(type(final["exports"]) is list and len(final["exports"]) == len(request.output_formats), "INVALID_RESPONSE", "Incomplete export set")
        exports = []
        for item in final["exports"]:
            require(type(item) is dict and set(item) == {"name", "sha256", "format", "file_unit"}, "INVALID_RESPONSE", "Malformed export descriptor")
            require(item["format"] in {f.value for f in request.output_formats} and item["name"] == "export." + item["format"]
                    and item["file_unit"] == "m", "INVALID_RESPONSE", "Unrequested format or non-SI export")
            checked_file(directory, item["name"], item["sha256"],max_bytes=self.artifact_limit_bytes)
            exports.append(ExportFile(**item))
        require(len({e.format for e in exports}) == len(exports), "INVALID_RESPONSE", "Duplicate export formats")
        require(type(final["metrics"]) is dict, "INVALID_RESPONSE", "Malformed worker observations")
        return BackendResult(source_name, final["source_sha256"], tuple(exports), final["metrics"])

    def inspect(self, directory: Path, file: ExportFile) -> Path:
        """Byte integrity only; independent geometry QA belongs to Systems."""
        return checked_file(directory, file.name, file.sha256)

    def export(self, *_: object) -> None:
        raise GeometryContractError("REBUILD_REQUIRED", "Export format/tolerance is immutable per build; submit a new explicit request")


class PicoGKAdapter(GeometryBackend):
    def __init__(self, command: WorkerCommand, supervisor: WorkerSupervisor, *, enabled: bool = False) -> None:
        super().__init__("picogk", command, supervisor, enabled=enabled)


class OCCTAdapter(GeometryBackend):
    def __init__(self, command: WorkerCommand, supervisor: WorkerSupervisor, *, enabled: bool = False) -> None:
        super().__init__("occt", command, supervisor, enabled=enabled)
