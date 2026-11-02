"""Read-only runtime identities; mutate only generated task-owned manifest copies."""

from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path

from api.nozzle_geometry import runtime_configuration


def main():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "docs/implementation/evidence/R07_NATIVE_INTEGRATION_2026-10-20"
    path = evidence / "runtime-qualified-config-v4.json"
    baseline = json.loads(path.read_bytes())
    assert runtime_configuration(path)["engine_nozzle"]["policy"] == "r07.engine-nozzle-software-qa.v1"
    cases = []
    tests = {
        "wrong-policy": lambda c: c["engine_nozzle"].update(policy="p07.software-fixtures.v1"),
        "missing-receipt": lambda c: c["engine_nozzle"].update(receipt="/private/tmp/nonexistent-r07-receipt.json"),
        "receipt-digest": lambda c: c["engine_nozzle"].update(receipt_sha256="0" * 64),
        "worker-path": lambda c: c["engine_nozzle"]["worker"].update(argv=[c["occt"]["argv"][0], "/private/tmp/not-a-nozzle-worker.py"]),
        "replacement-interpreter": lambda c: c["engine_nozzle"]["worker"].update(argv=["/usr/bin/python3", c["engine_nozzle"]["worker"]["argv"][1]]),
        "changed-source-hash": lambda c: c["sha256"].update({str(root / "api/nozzle_geometry.py"): "0" * 64}),
        "missing-worker-hash": lambda c: c["sha256"].pop(str(root / "plugins/geometry/workers/nozzle_worker.py")),
        "fixture-only-config": lambda c: c.pop("engine_nozzle"),
    }
    with tempfile.TemporaryDirectory(prefix="cosmos-r07-manifest-") as temporary:
        for name, change in tests.items():
            config = deepcopy(baseline)
            change(config)
            candidate = Path(temporary) / (name + ".json")
            candidate.write_text(json.dumps(config))
            try:
                runtime_configuration(candidate)
            except ValueError as error:
                cases.append({"case": name, "rejected": True, "code": getattr(error, "code", type(error).__name__)})
            else:
                raise AssertionError("Unqualified native runtime accepted: " + name)
    (evidence / "runtime-negative-proof.json").write_text(json.dumps({"valid_profile_accepted": True, "negative_cases": cases, "native_execution_performed": False, "live_data_untouched": True}, indent=2) + "\n")
    print("Valid separate profile accepted;", len(cases), "unsafe/mismatched manifest copies refused without native execution.")


if __name__ == "__main__":
    main()
