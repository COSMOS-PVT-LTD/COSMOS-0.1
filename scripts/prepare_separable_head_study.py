"""Retain NEW isolated mechanical-layout calculations; no CAD or owner writes."""
import argparse
import json
from hashlib import sha256
from pathlib import Path

from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import compile_model
from systems.geometry.separable_head_layout import prepare_layout


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("assembly","proposal","output"):parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args();raw=(args.assembly/"model-envelope.json").read_bytes();source=json.loads(raw)
    proposal_raw=args.proposal.read_bytes();proposal=json.loads(proposal_raw);spec=source["model"]["specification"]
    plan=compile_model(spec,"engine-component-separable-head-preparation","retained-study","2026-10-21T00:00:00Z")
    result=prepare_layout(spec,inspect_interfaces(plan,1e-6),proposal)
    root=Path(__file__).resolve().parents[1]
    native=json.loads((args.assembly/"native-job.json").read_bytes())
    evidence={"source_authority":source["authority"],"source_envelope_sha256":sha256(raw).hexdigest(),
        "source_native_job_state":native["state"],"proposal_sha256":sha256(proposal_raw).hexdigest(),
        "methods":{name:sha256((root/name).read_bytes()).hexdigest() for name in
            ("scripts/prepare_separable_head_study.py","systems/geometry/separable_head_layout.py","systems/geometry/component_model.py","systems/geometry/component_reference.py","systems/geometry/component_interfaces.py","systems/geometry/component_joints.py")}}
    args.output.mkdir(parents=True,mode=0o700,exist_ok=False)
    for name,value in (("proposal.json",proposal),("layout.json",result),("source-identities.json",evidence)):
        with (args.output/name).open("x") as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({"native_geometry":result["native_geometry"],"installed":False,
        "face_land_width_m":result["conservative_head_face_land_width_m"],"gas_volume_difference_m3":result["gas_volume_difference_m3"],
        "return_port_clearance_m":result["front_supply_to_chamber_outer_clearance_m"],"remaining_native_requirements":len(result["native_requirements"])}))


if __name__=="__main__":main()
