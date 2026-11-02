"""Rerun actual P05 baseline cases without rewriting any predecessor evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P05 = HERE.parent / "P05_2026-10-09"
spec = importlib.util.spec_from_file_location("p06_physics_baseline", P05 / "physics_parity.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.run()
baseline = json.loads((P05 / "physics_before.json").read_text())
equal = baseline == result
(HERE / "physics_after.json").write_text(json.dumps(result, indent=2) + "\n")
(HERE / "physics_parity.json").write_text(json.dumps({"pass": equal, "actualHTTPcases": 5, "numericalTolerance": 0,
    "comparison": "exact", "baseline": "P05_2026-10-09/physics_before.json",
    "baselineSHA256": hashlib.sha256((P05 / "physics_before.json").read_bytes()).hexdigest(),
    "physicalValidationClaimed": False}, indent=2) + "\n")
assert equal, "Scientific regression relative to the P05 captured baseline"
print("PASS: five actual scientific HTTP cases exactly match P05; no geometry kernel invoked")
