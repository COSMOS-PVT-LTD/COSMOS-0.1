"""Retain fresh native fixtures in P12, never rewrite predecessor evidence."""
import json
from pathlib import Path

from api.ngg_workbench import runtime_config

HERE = Path(__file__).resolve().parent
source = HERE.parent / "P08_2026-10-09/local-runtime.json"
value = runtime_config(source.resolve())
value["evidence_directory"] = str(HERE / "native-regression")
out = HERE / "runtime-config.json"
with out.open("x") as handle:
    json.dump(value, handle, indent=2)
    handle.write("\n")
print(json.dumps({"runtime": "same hash-checked qualified native bytes", "retention": "P12/native-regression only"}))
