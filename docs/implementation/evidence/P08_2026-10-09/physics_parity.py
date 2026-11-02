"""Re-use real predecessor HTTP cases, write a new P08 evidence overlay only."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("p05_parity", HERE.parent / "P05_2026-10-09/physics_parity.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
value = module.run()
baseline = HERE / "physics_before.json"
if sys.argv[1:] == ["capture"]:
    assert not baseline.exists()
    baseline.write_text(json.dumps(value, indent=2) + "\n")
    print("Captured 5 real HTTP scientific cases before P08 GUI changes")
else:
    (HERE / "physics_after.json").write_text(json.dumps(value, indent=2) + "\n")
    result = {"pass": value == json.loads(baseline.read_text()), "cases": 5, "comparison": "exact", "tolerance": 0,
              "physical_validation": False, "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest()}
    (HERE / "physics_parity.json").write_text(json.dumps(result, indent=2) + "\n")
    assert result["pass"]
    print("5 real HTTP scientific cases: exact parity PASS")
