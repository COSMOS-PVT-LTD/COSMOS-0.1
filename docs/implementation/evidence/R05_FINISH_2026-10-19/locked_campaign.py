"""New final campaign destination; preserve native identities and old receipts."""
import json
from pathlib import Path

base = Path(__file__).resolve().parent
config = json.loads((base / "runtime-config.json").read_text())
destination = base / "native-locked-regression"
destination.mkdir(exist_ok=False)
config["evidence_directory"] = str(destination)
with (base / "runtime-locked-config.json").open("x") as stream:
    stream.write(json.dumps(config, indent=2) + "\n")
print("Fresh output campaign; all pinned native identities/qualification unchanged.")
