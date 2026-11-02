"""Explicit actual-engine workload, with the same supervised process limits."""
import json
import os
from hashlib import sha256
from pathlib import Path

import pytest

from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_model import from_contracts
from systems.geometry.pico_component_builds import PicoLimits
from systems.geometry.pico_preview import reduce_preview
from tests.integration_tests.geometry.test_pico_preview_native import workspace


def test_actual_16_part_engine_display_under_process_budget(tmp_path,record_property):
    names=("PICO_LARGE_INPUTS","PICO_LARGE_RECORD","PICO_LARGE_STL")
    if not all(os.environ.get(n) for n in names):pytest.skip("Explicit isolated actual-engine evidence campaign required")
    inputs=json.loads(Path(os.environ[names[0]]).read_bytes());record=json.loads(Path(os.environ[names[1]]).read_bytes())
    native=json.loads(record["record_json"]);proof=json.loads(record["evidence_json"]);raw=Path(os.environ[names[2]]).read_bytes()
    assert sha256(raw).hexdigest()==native["artifacts"][0]["sha256"] and proof["qa-stl"]["pass"]
    m=json.loads(inputs["model_canonical_json"]);p=from_contracts(DesignSnapshot.from_json(m["snapshot_json"]),GeometryFeatureGraph.from_json(m["graph_json"]))
    w=workspace(tmp_path);before=sha256(raw).hexdigest()
    try:
        data,parts,_,display=reduce_preview(w,raw,proof["worker_observations"]["parts"],p,PicoLimits.from_spec(inputs["qa_specification"]))
        assert len(parts)==16 and all(r["pass"] for r in display["parts"])
        assert len(data)<=7200000 and sha256(raw).hexdigest()==before
        assert display["process"]["observed_rss_bytes"]<=1024**3 and display["process"]["elapsed_s"]<=300
        record_property("actual_engine_display",json.dumps({"source_sha256":before,"display_sha256":display["preview_sha256"],"source_triangles":proof["worker_observations"]["triangle_count"],"preview_triangles":len(data)//36,"parts":len(parts),"process":display["process"]}))
    finally:w.close()
