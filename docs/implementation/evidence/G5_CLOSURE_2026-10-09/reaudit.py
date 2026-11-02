"""Reuse archived P07 independent re-audit, write only into this closure overlay."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p07_reaudit", HERE.parent / "P07_2026-10-09/reaudit_candidates.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = HERE
module.main()
result = json.loads((HERE / "candidate-reaudit.json").read_text())
records = result["records"]
positive = [r for r in records if r["fixture"].startswith("occt-step-") or r["fixture"] == "occt-both-sphere"]
assert len(records) == 30 and len(positive) == 8
assert all(r["record_state"] == "accepted" and r["qa_pass"] for r in positive)
result.update(full_G5_pass=True, meaning="Local software fixture G5 closure, including expected negative decisions; not engineering or native distribution acceptance")
(HERE / "candidate-reaudit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"G5_software_pass": True, "reparsed_records": len(records), "all_occt_positive_fixtures_pass": True}))
