"""Explicit hash-qualified local runtime, shared bounded supervisor; no auto-install."""

from __future__ import annotations

import threading
from pathlib import Path

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.nozzle_adapter import NozzleAdapter
from systems.contracts.geometry._wire import require
from systems.geometry.nozzle_qa import NozzleBuildService, NozzleQALimits


class NozzleWorkspace:
    def __init__(self, root: Path, configuration):
        require(root.is_absolute() and not root.is_symlink(), "UNSAFE_PATH", "Trusted private absolute candidate root required")
        self.root, self.configuration = root, configuration
        self.root.mkdir(mode=0o700, exist_ok=True)
        self.supervisor = WorkerSupervisor(timeout_s=60)
        self.services: dict[NozzleQALimits, NozzleBuildService] = {}
        self.lock = threading.Lock()
        self.closed = False

    @property
    def runtime_hashes(self):
        config = self.configuration()
        return {**config["sha256"], "runtime-manifest": config["manifest_sha256"]}

    def service_for(self, limits: NozzleQALimits):
        config = self.configuration()
        with self.lock:
            require(not self.closed, "SERVICE_CLOSED", "Nozzle workspace is closed")
            if limits not in self.services:
                require(len(self.services) < 16, "QA_PROFILE_LIMIT", "Local runtime admits at most 16 distinct explicit QA policies per application lifetime")
                item = config["engine_nozzle"]
                worker = WorkerCommand(tuple(item["worker"]["argv"]), tuple(item["worker"]["environment"].items()))
                reader = WorkerCommand(tuple(item["reader"]["argv"]), tuple(item["reader"]["environment"].items()))
                self.services[limits] = NozzleBuildService(NozzleAdapter("occt", worker, self.supervisor, enabled=True), self.root, step_reader=reader, limits=limits)
            return self.services[limits]

    def close(self):
        with self.lock:
            self.closed = True
            services = tuple(self.services.values())
        for service in services:
            service.close()
        self.supervisor.close()
