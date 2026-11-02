"""Execute prior actual HTTP cases without editing historical evidence."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
path = HERE.parent / "P05_2026-10-09/physics_parity.py"
spec = importlib.util.spec_from_file_location("p12_parity", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.run()
prior = json.loads((HERE.parent / "P11_2026-10-11/physics_after.json").read_text())
assert result == prior
for name, value in (("physics_after.json", result), ("physics-parity.json", {
    "pass": True, "cases": 5, "comparison": "exact", "numerical_tolerance": 0,
    "excluded_metadata_keys": sorted(module.VOLATILE), "baseline": "P11_2026-10-11/physics_after.json",
    "scope": "Assumed-state HTTP scientific responses, not equilibrium/native hardware evidence", "physical_validation": False,
})):
    with (HERE / name).open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")
print("Five actual scientific HTTP cases match P11 exactly")
