"""Prepare/seal a NEW local runtime campaign; never overwrite historical receipts."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from plugins.geometry.nozzle_protocol import POLICY, VERSION
from systems.geometry.engine_builds import methods

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/implementation/evidence/R07_NATIVE_INTEGRATION_2026-10-20"


def write_new(path, value):
    if path.exists():
        raise ValueError("Refuse to overwrite an existing qualification artifact: " + str(path))
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--campaign", default="")
    args = parser.parse_args()
    if args.campaign and not re.fullmatch(r"[a-z0-9-]{1,16}", args.campaign):
        raise ValueError("Bounded alphanumeric campaign suffix required")
    suffix = "-" + args.campaign if args.campaign else ""
    baseline = ROOT / "docs/implementation/evidence/R05_FINISH_2026-10-19/runtime-locked-config.json"
    prepared = EVIDENCE / ("runtime-prepared-config" + suffix + ".json")
    if not args.seal:
        config = json.loads(baseline.read_bytes())
        changed = []
        for name, digest in config["sha256"].items():
            path = Path(name)
            actual = sha256(path.read_bytes()).hexdigest()
            if actual != digest:
                if name not in {str(ROOT / "systems/geometry" / f) for f in ("authority.py", "qa.py", "service.py")}:
                    raise ValueError("Undeclared old native-runtime identity changed: " + name)
                changed.append({"path": name, "before": digest, "after": actual})
                config["sha256"][name] = actual
        config["sha256"].update({str(ROOT / name): digest for name, digest in methods().items()})
        config["evidence_directory"] = str(EVIDENCE / ("fixture-regression" + suffix))
        Path(config["evidence_directory"]).mkdir(mode=0o700)
        write_new(prepared, config)
        write_new(EVIDENCE / ("runtime-declared-changes" + suffix + ".json"), {"baseline_sha256": sha256(baseline.read_bytes()).hexdigest(), "changes": changed, "scope": "New software campaign, not a reseal of the historical receipt"})
        print("Prepared new hash-pinned campaign; no nozzle qualification or owner rollout yet.")
        return
    config = json.loads(prepared.read_bytes())
    for name, digest in config["sha256"].items():
        if sha256(Path(name).read_bytes()).hexdigest() != digest:
            raise ValueError("Prepared sources changed; preserve this campaign and prepare a separately named one: " + name)
    reports = {}
    for name in ("native-final" + suffix + ".xml", "fixture-regression" + suffix + ".xml"):
        path = EVIDENCE / name
        xml = ET.parse(path).getroot()
        suites = list(xml.iter("testsuite"))
        counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
        if counts["failures"] or counts["errors"] or counts["skipped"] or counts["tests"] < (7 if name.startswith("native-final") else 5):
            raise ValueError("Qualification requires executed, passing, unskipped native and fixture regression cases: " + name)
        reports[name] = {"sha256": sha256(path.read_bytes()).hexdigest(), **counts}
    receipt = EVIDENCE / ("nozzle-software-decision" + suffix + ".json")
    write_new(receipt, {"policy": POLICY, "version": VERSION, "software_qa_pass": True,
                       "method_sources": {str(ROOT / name): digest for name, digest in methods().items()}, "reports": reports,
                       "scope": "Bounded selected divergent radial-wall nozzle integration only; not all R07 requirements or independent human acceptance",
                       "physical_validation": "NOT_PERFORMED", "engineering_acceptance": "NOT_PERFORMED", "production_enabled": False})
    env = config["occt"]["environment"]
    command = lambda file: {"argv": [config["occt"]["argv"][0], str(ROOT / "plugins/geometry/workers" / file)], "environment": env}
    config["engine_nozzle"] = {"policy": POLICY, "version": VERSION, "worker": command("nozzle_worker.py"), "reader": command("nozzle_step_reader.py"), "receipt": str(receipt), "receipt_sha256": sha256(receipt.read_bytes()).hexdigest()}
    write_new(EVIDENCE / ("runtime-qualified-config" + suffix + ".json"), config)
    print("New selected-nozzle software receipt/config recorded. No live root migrated or enabled.")


if __name__ == "__main__":
    main()
