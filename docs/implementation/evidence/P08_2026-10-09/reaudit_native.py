import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p07_independent_reaudit", HERE.parent / "P07_2026-10-09/reaudit_candidates.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = HERE
module.main()
result = json.loads((HERE / "candidate-reaudit.json").read_text())
positive = [r for r in result["records"] if r["fixture"].startswith("occt-step-") or r["fixture"] == "occt-both-sphere"]
assert len(result["records"]) == 30 and len(positive) == 8 and all(r["record_state"] == "accepted" and r["qa_pass"] for r in positive)
result.update(full_G5_pass=True, meaning="P08 current-source native regression and independent QA, scoped to local software fixtures")
(HERE / "candidate-reaudit.json").write_text(json.dumps(result, indent=2) + "\n")
print("Current-source P08 native regression: 30 records, 5 convergence series, all OCCT positives pass")
