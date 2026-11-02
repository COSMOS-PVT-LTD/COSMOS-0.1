"""Negative copies of the final manifest; no native execution or live changes."""
import json
import tempfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from api.component_geometry import runtime_configuration


def main():
    root=Path(__file__).resolve().parents[1];directory=root/"docs/implementation/evidence/R07_COMPONENTS_2026-10-20"
    profile=directory/"runtime-qualified-v3.json";original=profile.read_bytes();baseline=json.loads(original)
    assert runtime_configuration(profile)["engine_components"]["policy"]=="r07.components-software-qa.v1"
    tests={
        "no-component-profile":lambda c:c.pop("engine_components"),
        "wrong-component-policy":lambda c:c["engine_components"].update(policy="p07.software-fixtures.v1"),
        "wrong-version":lambda c:c["engine_components"].update(version="unqualified"),
        "missing-separate-receipt":lambda c:c["engine_components"].update(receipt="/private/tmp/nonexistent-component-receipt.json"),
        "receipt-digest":lambda c:c["engine_components"].update(receipt_sha256="0"*64),
        "nozzle-receipt-is-not-component-qualification":lambda c:c["engine_components"].update(receipt=c["engine_nozzle"]["receipt"],receipt_sha256=c["engine_nozzle"]["receipt_sha256"]),
        "untrusted-worker-path":lambda c:c["engine_components"]["worker"].update(argv=[c["occt"]["argv"][0],"/private/tmp/not-a-component-worker.py"]),
        "replacement-interpreter":lambda c:c["engine_components"]["worker"].update(argv=["/usr/bin/python3",c["engine_components"]["worker"]["argv"][1]]),
        "missing-pinned-reader":lambda c:c["sha256"].pop(str(root/"plugins/geometry/workers/component_step_reader.py")),
        "changed-component-method":lambda c:c["sha256"].update({str(root/"systems/geometry/component_reference.py"):"0"*64}),
    }
    results=[]
    with tempfile.TemporaryDirectory(prefix="cosmos-component-negative-") as temporary:
        for name,mutate in tests.items():
            value=deepcopy(baseline);mutate(value);path=Path(temporary)/(name+".json");path.write_text(json.dumps(value))
            try: runtime_configuration(path)
            except ValueError as error: results.append({"case":name,"rejected":True,"code":getattr(error,"code",type(error).__name__)})
            else: raise AssertionError("Unsafe component runtime was accepted: "+name)
    assert profile.read_bytes()==original
    (directory/"runtime-negative-proof.json").write_text(json.dumps({"valid_profile_accepted":True,"manifest_sha256":sha256(original).hexdigest(),"negative_cases":results,"native_execution_performed":False,"owner_data_untouched":True},indent=2)+"\n")
    print("Final component profile accepted;",len(results),"unsafe copies rejected without native execution.")


if __name__=="__main__": main()
