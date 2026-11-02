"""Real topology-preserving display reduction, separate from PicoGK generation."""
import json
import os
from pathlib import Path

import numpy as np
import pytest

from plugins.geometry.pico_components import field_graph
from systems.contracts.geometry import BuildState
from systems.geometry.pico_component_builds import (
    PicoLimits,
    PicoReference,
    PicoWorkspace,
)
from systems.geometry.pico_mesh_qa import read_mesh
from systems.geometry.pico_preview import reduce_preview
from tests.fixtures.component_geometry import plan
from tests.integration_tests.geometry.test_pico_components_native import command
from tests.unit_tests.systems_layer.test_pico_components import qa, request_for


def workspace(tmp_path):
    value=os.environ.get("PICO_PREVIEW_PYTHON")
    if not value:pytest.skip("Explicit separately pinned VTK display campaign required")
    repo=Path(__file__).resolve().parents[3];python=Path(value).absolute();c=command()
    cfg={"worker":{"argv":list(c.argv),"environment":dict(c.environment)},"preview_worker":{"argv":[str(python),str(repo/"plugins/geometry/workers/pico_preview_worker.py")],"environment":{"PYTHONPATH":str(repo),"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}},"sha256":{},"manifest_sha256":"1"*64}
    return PicoWorkspace(tmp_path.resolve(),lambda:cfg)


@pytest.mark.parametrize("kind,h",[("injector.pintle",.000125),("injector.coaxial",.0001),("injector.doublet",.0002)])
def test_real_reduction_remains_closed_and_source_bound(tmp_path,kind,h):
    w=workspace(tmp_path);p=plan(kind);limits=PicoLimits.from_spec(qa(h))
    try:
        s=w.service_for(limits);_,f=s.submit(request_for(p,h),p.snapshot,field_graph(p),PicoReference(p));candidate=f.result(timeout=300)
        assert candidate.record.state is BuildState.ACCEPTED,candidate.evidence_json
        proof=json.loads(candidate.evidence_json);raw,_=read_mesh(candidate.directory/"export.stl")
        positions,parts,_,display=reduce_preview(w,raw,proof["worker_observations"]["parts"],p,limits)
        assert len(positions)<=7_200_000 and all(p["pass"] and p["components"]==1 and p["nonmanifold_edges"]==0 for p in display["parts"])
        assert sum(p["triangle_count"] for p in parts)==len(positions)//36
        assert np.isfinite(np.frombuffer(positions,dtype="<f4")).all()
        assert reduce_preview(w,raw,proof["worker_observations"]["parts"],p,limits)[0]==positions
    finally:w.close()


def test_cancelled_display_process_cannot_publish_preview(tmp_path):
    import threading
    w=workspace(tmp_path);p=plan("pipe.circular");limits=PicoLimits.from_spec(qa())
    try:
        s=w.service_for(limits);_,f=s.submit(request_for(p),p.snapshot,field_graph(p),PicoReference(p));candidate=f.result(timeout=160)
        assert candidate.record.state is BuildState.ACCEPTED
        proof=json.loads(candidate.evidence_json);raw,_=read_mesh(candidate.directory/"export.stl");token=threading.Event();token.set()
        with pytest.raises(ValueError,match="reduction failed"):
            reduce_preview(w,raw,proof["worker_observations"]["parts"],p,limits,cancellation=token)
        assert not w.previews
    finally:w.close()
