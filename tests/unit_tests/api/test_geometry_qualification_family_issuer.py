"""Admission parser fixtures; none of these XML files are executed evidence."""

import json
import xml.etree.ElementTree as ET
from hashlib import sha256

import pytest

from scripts.qualify_geometry_qa import FAMILIES, family_campaigns
from tests.fixtures.geometry_qualification_families import FAMILIES as FIXTURES


def proof(kind):
    policy = {"refinement_resolutions_m": [0.0003125, 0.00025, 0.0002]}
    return {
        "kind": kind,
        "policy": policy,
        "policy_sha256": sha256(
            json.dumps(policy, sort_keys=True, allow_nan=False).encode()
        ).hexdigest(),
        "physical_validation": "NOT_PERFORMED",
        "campaign": [
            {"voxel_resolution_m": h, "pass": True, "parts": [{"pass": True}]}
            for h in (None, *policy["refinement_resolutions_m"])
        ],
    }


def report(tmp_path, rows):
    root = ET.Element("testsuite")
    for value in rows:
        props = ET.SubElement(ET.SubElement(root, "testcase"), "properties")
        ET.SubElement(
            props, "property", name="r08_family_campaign", value=json.dumps(value)
        )
    path = tmp_path / "NOT_EXECUTED_parser_fixture.xml"
    ET.ElementTree(root).write(path)
    return path


def test_required_scope_inventory_cannot_drift_from_executed_fixture_inventory():
    assert len(FAMILIES) == 22 and set(FIXTURES) == FAMILIES


def test_family_parser_requires_one_complete_campaign_per_declared_case(tmp_path):
    assert family_campaigns(report(tmp_path, [proof(k) for k in FAMILIES])) == sorted(
        FAMILIES
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "fail",
        "part-fail",
        "hash",
        "resolution",
        "physical",
        "unknown",
    ],
)
def test_unqualified_family_evidence_cannot_issue_runtime(tmp_path, change):
    rows = [proof(k) for k in FAMILIES]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[-1] = rows[0]
    elif change == "fail":
        rows[0]["campaign"][1]["pass"] = False
    elif change == "part-fail":
        rows[0]["campaign"][1]["parts"][0]["pass"] = False
    elif change == "hash":
        rows[0]["policy_sha256"] = "0" * 64
    elif change == "resolution":
        rows[0]["campaign"][1]["voxel_resolution_m"] = 0.0005
    elif change == "physical":
        rows[0]["physical_validation"] = "VALIDATED"
    else:
        rows[0]["kind"] = "unsupported-profile"
    with pytest.raises(ValueError):
        family_campaigns(report(tmp_path, rows))
