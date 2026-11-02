"""P00 diagnostic probes. Only temporary stores and evidence files are written."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def main() -> None:
    from api.catalogs import list_workflow_catalog
    from api.propulsion_workflow import save_design
    from gui.workbenches.registry import WORKBENCH_PAGES
    from systems.contracts.results import CalculationResult, ResultStatus
    from systems.persistence.design_store import DesignStore
    from systems.projects.models import PropulsionDesign

    hashes = json.loads((OUT / "source_hashes.json").read_text())
    changed = [p for p, sha in hashes.items()
               if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != sha]
    xml = ET.parse(OUT / "pytest.xml").getroot()
    cases = xml.findall(".//testcase")
    groups = Counter(c.get("classname", "").split(".")[1] for c in cases)
    skips = [{"class": c.get("classname"), "name": c.get("name"),
              "reason": c.find("skipped").get("message")} for c in cases
             if c.find("skipped") is not None]
    scientific = Counter()
    for c in cases:
        for area in ("core", "physics", "numerics", "systems_layer", "knowledge", "gui", "api", "plugins"):
            if f".{area}." in c.get("classname", ""):
                scientific[area] += 1
    with tempfile.TemporaryDirectory(prefix="cosmos-p00-store-probe-") as tmp:
        store = DesignStore(tmp)
        design = PropulsionDesign(design_id="p00-diagnostic-only", name="initial")
        store.save(design)
        first, second = store.load(design.design_id), store.load(design.design_id)
        save_design(first, store, edits={"base_revision": 0, "name": "first writer change",
                                         "editor_drafts": {"p00-proof": "first writer draft"}})
        save_design(second, store, edits={"base_revision": 0, "name": "second writer change"})
        final = store.load(design.design_id)
        persistence = {"first_writer_drafts": first.editor_drafts,
                       "saved_drafts": final.editor_drafts, "saved_name": final.name,
                       "lost_first_writer_change": final.editor_drafts != first.editor_drafts,
                       "scope": "Two aggregates loaded before the first save; API base_revision checks compare with each loaded object. HTTP race exposure is inferred, not stress-tested.",
                       "revision_files": sorted(p.name for p in Path(tmp).glob("*.json")),
                       "saved_revision": final.revision}
    result = CalculationResult(calculation_type="p00.probe", status=ResultStatus.CURRENT,
                               inputs={"x": 1}, outputs={"y": 2})
    result.inputs["x"] = 3
    mutability = {"current_result_input_mutation_allowed": result.inputs["x"] == 3,
                  "interpretation": "Current envelopes are mutable; published immutable snapshots need a separate boundary."}
    edges = json.loads((OUT / "import_edges.json").read_text())
    forbidden = {"core": {"physics", "numerics", "systems", "gui", "api", "knowledge"},
                 "numerics": {"physics", "systems", "gui", "api", "engineering", "simulation", "knowledge"},
                 "physics": {"systems", "gui", "api", "engineering", "simulation"}}
    violations = [e for e in edges if e["target"].split(".")[0] in
                  forbidden.get(e["source"].split("/")[0], set())]
    latency = []
    for _ in range(7):
        start = time.perf_counter()
        with urllib.request.urlopen("http://127.0.0.1:8790/login", timeout=3) as response:
            response.read()
        latency.append(time.perf_counter() - start)
    probes = {"original_snapshot_files_changed": changed,
              "test_categories_collected": dict(groups), "domain_test_case_counts": dict(scientific),
              "skipped_tests": skips, "persistence_probe": persistence,
              "result_mutability_probe": mutability, "static_direct_import_violations": violations,
              "loopback_login_http_seconds": {"samples": latency, "median": statistics.median(latency),
                                                "scope": "warm loopback HTTP transfer only, not browser startup or interaction latency"}}
    (OUT / "diagnostic_probes.json").write_text(json.dumps(probes, indent=2, sort_keys=True) + "\n")
    (OUT / "workbench_inventory.json").write_text(json.dumps(
        [asdict(item) for page in WORKBENCH_PAGES for item in page], indent=2) + "\n")
    (OUT / "workflow_inventory.json").write_text(json.dumps(list_workflow_catalog(), indent=2) + "\n")
    print(json.dumps({"original_files_changed": changed, "cases": len(cases), "skipped": len(skips),
                      "lost_update_observed": persistence["lost_first_writer_change"],
                      "direct_import_violations": len(violations), "registered_workbenches": 12}))


if __name__ == "__main__":
    main()
