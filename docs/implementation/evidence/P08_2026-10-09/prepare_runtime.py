"""Explicit test-only runtime, reuse qualification pins; never enable production."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
config = json.loads((HERE.parent / "G5_CLOSURE_2026-10-09/native-config.json").read_text())
receipt = HERE.parent / "G5_CLOSURE_2026-10-09/decision.json"
config["g5_receipt"] = str(receipt)
config["g5_receipt_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
for name in ("plugins/geometry/workers/preview_reader.py", "systems/geometry/software_fixtures.py", "systems/geometry/workbench.py", "gui/ngg.py", "api/ngg_workbench.py"):
    config["sha256"][str(ROOT / name)] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
(HERE / "local-runtime.json").write_text(json.dumps(config, indent=2) + "\n")
print("Prepared explicit P08 local software-fixture runtime; production remains disabled")
