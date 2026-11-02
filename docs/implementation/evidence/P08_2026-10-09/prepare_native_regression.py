import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
config = json.loads((HERE / "local-runtime.json").read_text())
directory = HERE / (sys.argv[1] if sys.argv[1:] else "native-regression")
directory.mkdir(exist_ok=False)
config["evidence_directory"] = str(directory)
(HERE / "native-regression-config.json").write_text(json.dumps(config, indent=2) + "\n")
(directory / "runtime-config.json").write_text(json.dumps(config, indent=2) + "\n")
print("Prepared fresh P08 native regression; prior G5/P07 evidence remains unchanged")
