"""Component-policy composition over the existing bounded native supervisor."""

import threading
from pathlib import Path

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.component_adapter import ComponentAdapter
from systems.contracts.geometry._wire import require
from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits

# Imported assemblies retain actual surface-node and face witnesses. The
# reader independently bounds 100k total nodes / 12k faces; the generic 2MiB
# process response cap cannot carry that evidence for a real engine assembly.
# Keep the generic input cap, timeout, RSS and all geometric QA unchanged.
COMPONENT_VERIFICATION_OUTPUT_BYTES = 16 * 1024 * 1024


class ComponentWorkspace:
    def __init__(self,root:Path,configuration):
        require(root.is_absolute() and not root.is_symlink(),"UNSAFE_PATH","Private absolute component candidate root required")
        root.mkdir(mode=0o700,exist_ok=True)
        self.root,self.configuration=root,configuration
        self.supervisor=WorkerSupervisor(timeout_s=120,stdout_limit=COMPONENT_VERIFICATION_OUTPUT_BYTES)
        self.services:dict[ComponentQALimits,ComponentBuildService]={}
        self.lock=threading.Lock(); self.closed=False

    @property
    def runtime_hashes(self):
        config=self.configuration()
        return {**config["sha256"],"runtime-manifest":config["manifest_sha256"]}

    def service_for(self,limits):
        config=self.configuration()
        with self.lock:
            require(not self.closed,"SERVICE_CLOSED","Component runtime is closed")
            if limits not in self.services:
                require(len(self.services)<16,"QA_PROFILE_LIMIT","At most16 distinct explicit component QA profiles per application lifetime")
                item=config["engine_components"]
                worker=WorkerCommand(tuple(item["worker"]["argv"]),tuple(item["worker"]["environment"].items()))
                reader=WorkerCommand(tuple(item["reader"]["argv"]),tuple(item["reader"]["environment"].items()))
                self.services[limits]=ComponentBuildService(ComponentAdapter("occt",worker,self.supervisor,enabled=True),self.root,step_reader=reader,limits=limits)
            return self.services[limits]

    def close(self):
        with self.lock:
            self.closed=True; services=tuple(self.services.values())
        for service in services: service.close()
        self.supervisor.close()
