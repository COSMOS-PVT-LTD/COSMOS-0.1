import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
from hashlib import sha256
from pathlib import Path

import pytest

from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.materials.catalog import MATERIALS
from physics.si import UNIT_HTC
from systems.materials.research import (
    SCOPE,
    MaterialCondition,
    WallResearchInputs,
    research_wall,
    stage_conductivity,
)

RAW = b"Synthetic property reference ONLY; not alloy or hardware evidence"


def payload():
    return {"schema_version": 1, "scope": SCOPE, "evidence_id": "SYNTHETIC-K",
        "condition": {"alloy_id": "SYNTHETIC", "process": "manufactured analytic fixture",
            "machine": "fixture-machine", "powder": "fixture-feedstock", "heat_treatment": "fixture-condition",
            "orientation": "fixture-direction"},
        "source": {"url": "https://example.org/synthetic-reference", "sha256": sha256(RAW).hexdigest(), "locator": "synthetic table 1"},
        "temperature_unit": "degC", "temperatures": [0., 100., 500.], "conductivity_unit": "W/(m*K)",
        "conductivities": [100., 100., 100.], "statistic": "Synthetic constant-k fixture", "sample_count": None,
        "uncertainty_statement": "Analytic software test; no material uncertainty claim", "unresolved": []}


def wall(**updates):
    return replace(WallResearchInputs(Quantity(700., SI.get("K")), Quantity(300., SI.get("K")),
        Quantity(2000., UNIT_HTC), Quantity(10000., UNIT_HTC), Quantity(.01, SI.get("m2")),
        Quantity(.01, SI.get("m2")), Quantity(.01, SI.get("m2")), Quantity(.0015, SI.get("m")),
        Quantity(1e-6, SI.get("W")), 120), **updates)


def test_core_celsius_conversion_source_and_original_transcription_identity():
    record = stage_conductivity(payload(), RAW)
    assert record.curve.temperatures_k == (273.15, 373.15, 773.15)
    assert record.curve.source_sha256 == sha256(RAW).hexdigest()
    assert record.sample_count is None
    with pytest.raises(FrozenInstanceError):
        record.evidence_id = "changed"
    changed = payload(); changed["statistic"] = "A distinct reported statistic"
    assert stage_conductivity(changed, RAW).transcription_sha256 != record.transcription_sha256


def test_exact_identity_research_is_not_installation_or_allowable_and_catalog_unchanged():
    before = deepcopy(MATERIALS)
    record = stage_conductivity(payload(), RAW)
    result = research_wall(evidence=record, requested=record.condition, mode="EXACT_CONDITION_RESEARCH", inputs=wall())
    # Independent constant-k series resistance.
    expected = 400 / (1 / 20 + .0015 / (100 * .01) + 1 / 100)
    assert result.balance.heat_w == pytest.approx(expected, abs=1e-6)
    assert result.missing_or_mismatched_fields == ()
    assert not result.installed and not result.material_allowable_assessed
    assert not result.engine_operating_point_complete and result.physical_validation == "NOT_PERFORMED"
    assert MATERIALS == before


@pytest.mark.parametrize("field", ["process", "machine", "powder", "heat_treatment", "orientation"])
def test_unknown_is_not_a_wildcard_even_if_both_requested_and_source_unknown(field):
    data = payload(); data["condition"][field] = None
    record = stage_conductivity(data, RAW)
    assert field in record.condition.missing
    with pytest.raises(InvalidInputError, match="complete matching"):
        research_wall(evidence=record, requested=record.condition, mode="EXACT_CONDITION_RESEARCH", inputs=wall())
    result = research_wall(evidence=record, requested=record.condition,
        mode="UNMATCHED_SAME_ALLOY_COMPARISON", inputs=wall())
    assert field in result.missing_or_mismatched_fields
    assert not result.material_allowable_assessed


@pytest.mark.parametrize("field", ["process", "machine", "powder", "heat_treatment", "orientation"])
def test_named_conditions_do_not_match_different_processing_or_powder(field):
    record = stage_conductivity(payload(), RAW)
    target = replace(record.condition, **{field: "a different condition"})
    with pytest.raises(InvalidInputError):
        research_wall(evidence=record, requested=target, mode="EXACT_CONDITION_RESEARCH", inputs=wall())
    result = research_wall(evidence=record, requested=target, mode="UNMATCHED_SAME_ALLOY_COMPARISON", inputs=wall())
    assert result.missing_or_mismatched_fields == (field,)


def test_unresolved_evidence_cannot_become_exact_condition_by_matching_labels():
    data = payload(); data["unresolved"] = ["Unresolved specimen condition"]
    record = stage_conductivity(data, RAW)
    with pytest.raises(InvalidInputError):
        research_wall(evidence=record, requested=record.condition, mode="EXACT_CONDITION_RESEARCH", inputs=wall())


@pytest.mark.parametrize("mode", ["EXACT_CONDITION_RESEARCH", "UNMATCHED_SAME_ALLOY_COMPARISON"])
def test_in939_or_generic_different_alloy_cannot_substitute(mode):
    record = stage_conductivity(payload(), RAW)
    with pytest.raises(InvalidInputError, match="Different alloy"):
        research_wall(evidence=record, requested=replace(record.condition, alloy_id="IN939"), mode=mode, inputs=wall())


def test_comparison_does_not_allow_cryogenic_or_hot_extrapolation_or_wrong_dimensions():
    record = stage_conductivity(payload(), RAW)
    for inputs in (wall(coolant_temperature=Quantity(111.15, SI.get("K")), coolant_coefficient=Quantity(20000., UNIT_HTC)),
            wall(gas_temperature=Quantity(3000., SI.get("K")), gas_coefficient=Quantity(20000., UNIT_HTC))):
        with pytest.raises(OutOfRangeError):
            research_wall(evidence=record, requested=record.condition, mode="UNMATCHED_SAME_ALLOY_COMPARISON", inputs=inputs)
    with pytest.raises(DimensionError):
        research_wall(evidence=record, requested=record.condition, mode="EXACT_CONDITION_RESEARCH", inputs=wall(thickness=Quantity(1, SI.get("Pa"))))


@pytest.mark.parametrize("update", [
    {"schema_version": True}, {"schema_version": 2}, {"scope": "INSTALLED"}, {"allowable": True},
    {"temperature_unit": "F"}, {"conductivity_unit": "kW/(m*K)"}, {"temperatures": [0.]},
    {"temperatures": [100., 0., 500.]}, {"temperatures": [0., float("nan"), 500.]},
    {"conductivities": [100., 0., 100.]}, {"conductivities": [100., float("inf"), 100.]},
    {"conductivities": [True, 100., 100.]}, {"conductivities": ["100", 100., 100.]},
    {"sample_count": True}, {"sample_count": 0}, {"statistic": ""},
    {"uncertainty_statement": ""}, {"unresolved": ["gap", "gap"]},
])
def test_strict_schema_units_original_nodes_and_unknowns(update):
    with pytest.raises((InvalidInputError, ValueError)):
        stage_conductivity(payload() | update, RAW)


@pytest.mark.parametrize("url", ["http://example.org/data", "https://user:secret@example.org/data",
    "https://example.org:invalid/data", "https://example.org:444/data", "https://example.org/data#table"])
def test_source_url_and_document_bytes_are_not_optional(url):
    data = payload(); data["source"]["url"] = url
    with pytest.raises(InvalidInputError):
        stage_conductivity(data, RAW)


def test_source_tamper_and_implicit_install_mode_fail():
    with pytest.raises(InvalidInputError, match="source SHA256"):
        stage_conductivity(payload(), RAW + b"altered")
    record = stage_conductivity(payload(), RAW)
    with pytest.raises(InvalidInputError, match="no engine installation"):
        research_wall(evidence=record, requested=record.condition, mode="ENGINE_INSTALL", inputs=wall())
    with pytest.raises(InvalidInputError):
        MaterialCondition(**(asdict(record.condition) | {"heat_treatment": ""}))


def test_reviewed_supplier_statistics_remain_separate_and_unmatched():
    from scripts.prepare_material_research import SOURCE_SHA, TRANSCRIPTION_SHA

    path = Path(__file__).resolve().parents[3] / "docs/implementation/evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/GRCOP42_RESEARCH_TRANSCRIPTIONS.json"
    raw = path.read_bytes()
    assert sha256(raw).hexdigest() == TRANSCRIPTION_SHA
    mean, reported_statistic = json.loads(raw)
    assert mean["temperatures"] == reported_statistic["temperatures"] == [25., 260., 537.8]
    assert mean["conductivities"] == [323., 317., 303.]
    assert reported_statistic["conductivities"] == [303., 309., 299.]
    for record in (mean, reported_statistic):
        assert record["source"]["sha256"] == SOURCE_SHA
        assert record["sample_count"] is None and record["unresolved"]
        assert record["condition"]["process"] is None and record["condition"]["heat_treatment"] is None


def test_cli_staging_physics_checks_and_new_folder_preservation(tmp_path, monkeypatch, capsys):
    from scripts import prepare_material_research as cli

    a = payload(); a["evidence_id"] = "SYNTHETIC-A"; a["condition"]["alloy_id"] = "GRCop-42"
    b = deepcopy(a); b["evidence_id"] = "SYNTHETIC-B"; b["conductivities"] = [200., 200., 200.]
    original = json.dumps([a, b]).encode()
    source = tmp_path / "source.pdf"; source.write_bytes(RAW)
    tables = tmp_path / "tables.json"; tables.write_bytes(original)
    output = tmp_path / "isolated-study"
    monkeypatch.setattr(cli, "SOURCE_SHA", sha256(RAW).hexdigest())
    monkeypatch.setattr(cli, "TRANSCRIPTION_SHA", sha256(original).hexdigest())
    monkeypatch.setattr(cli, "EVIDENCE_IDS", {"SYNTHETIC-A", "SYNTHETIC-B"})
    monkeypatch.setattr("sys.argv", ["study", "--source-pdf", str(source), "--transcriptions", str(tables), "--output", str(output)])
    cli.main()
    report = json.loads((output / "research-checks.json").read_bytes())
    assert report["software_checks_pass"] and len(report["checks"]) == 8
    implementation = json.loads((output / "implementation-manifest.json").read_bytes())
    assert set(implementation["sha256"]) == set(cli.IMPLEMENTATION_FILES)
    assert sum(row["status"] == "OUT_OF_DOMAIN" for row in report["checks"]) == 4
    assert all(row["exact_condition_rejected"] for row in report["checks"])
    assert not report["installed"] and not report["engine_complete"] and report["r08"] == "HOLD"
    assert (output / "source.pdf").read_bytes() == source.read_bytes() == RAW
    assert (output / "original-transcriptions.json").read_bytes() == original == tables.read_bytes()
    before = (output / "research-checks.json").read_bytes()
    with pytest.raises(FileExistsError):
        cli.main()
    assert (output / "research-checks.json").read_bytes() == before
    assert json.loads(capsys.readouterr().out)["software_checks_pass"]


def test_cli_rejects_unreviewed_transcription_before_creating_output(tmp_path, monkeypatch):
    from scripts import prepare_material_research as cli

    source = tmp_path / "source.pdf"; source.write_bytes(RAW)
    tables = tmp_path / "tables.json"; tables.write_text("[]")
    output = tmp_path / "must-not-be-created"
    monkeypatch.setattr(cli, "SOURCE_SHA", sha256(RAW).hexdigest())
    monkeypatch.setattr("sys.argv", ["study", "--source-pdf", str(source), "--transcriptions", str(tables), "--output", str(output)])
    with pytest.raises(ValueError, match="transcription"):
        cli.main()
    assert not output.exists()
