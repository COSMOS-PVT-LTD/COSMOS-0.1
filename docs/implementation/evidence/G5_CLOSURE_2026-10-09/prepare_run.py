"""New closure overlay. Never overwrite historical P07 evidence/configuration."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
config = json.loads(Path("/tmp/cosmos-p07.yVDtYl/native-config.json").read_text())
run = HERE / sys.argv[1]
run.mkdir(exist_ok=False)
config["evidence_directory"] = str(run)
for source in (ROOT / "plugins/geometry/workers/stl_encoding.py", ROOT / "plugins/geometry/protocol.py", ROOT / "systems/geometry/step_qa.py", ROOT / "systems/geometry/service.py"):
    config["sha256"][str(source)] = ""
config["sha256"] = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in config["sha256"]}
(HERE / "native-config.json").write_text(json.dumps(config, indent=2) + "\n")
(run / "native-config.json").write_text(json.dumps(config, indent=2) + "\n")
print(json.dumps({"closure_config": str(HERE / "native-config.json"), "runtime_hashes": len(config["sha256"])}))
