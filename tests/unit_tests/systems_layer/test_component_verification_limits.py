from systems.geometry.component_workspace import ComponentWorkspace


def test_component_evidence_capacity_is_bounded_and_general_supervisor_is_unchanged(tmp_path):
    from infrastructure.geometry import WorkerSupervisor
    from infrastructure.geometry.supervisor import MAX_WIRE_BYTES
    workspace=ComponentWorkspace(tmp_path,dict)
    try:
        assert workspace.supervisor.stdout_limit==16*1024**2
        assert workspace.supervisor.timeout_s==120
        with WorkerSupervisor() as ordinary:
            assert ordinary.stdout_limit==MAX_WIRE_BYTES==2*1024**2
    finally:workspace.close()
