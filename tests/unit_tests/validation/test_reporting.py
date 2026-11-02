"""Immutable report/package contracts; real native proof is in browser evidence."""
import hashlib
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from knowledge.workspace.evidence_navigation import EvidenceNavigation
from knowledge.workspace.session import KnowledgeWorkspace
from systems.contracts.geometry._wire import GeometryContractError
from tests.fixtures.knowledge_reports import (
    CLAIM_ID,
    SOURCE_ID,
    add_knowledge,
    report_services,
)
from validation.reporting import EngineeringReports


@pytest.fixture
def setup():
    workspace = KnowledgeWorkspace(seed_corpus=False)
    add_knowledge(workspace)
    return EngineeringReports(), EvidenceNavigation(workspace), report_services()


def make(setup, title="Synthetic report <script>alert(1)</script>", claims=None):
    r, nav, (c, s, g, key) = setup
    return r.create("actor", title, key, [CLAIM_ID] if claims is None else claims, c, s, g, nav)


def test_exact_report_lineage_and_deterministic_package(setup):
    first, second = make(setup), make(setup); r, _, _ = setup
    assert first == second and len(r.context("actor")["report_ids"]) == 1
    assert hashlib.sha256(first["canonical_json"].encode()).hexdigest() == first["report_id"]
    report = first["report"]; dataset = json.loads(report["dataset_canonical_json"])
    assert report["input_revision"] == dataset["study_id"] and report["run_id"] == dataset["run_id"]
    assert report["status"]["independent_acceptance"] is False and report["status"]["production_handoff"] is False
    raw = r.package("actor", first["report_id"])
    assert raw == r.package("actor", second["report_id"])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert set(archive.namelist()) == {"report.json", "report.md", "report.html", "manifest.json"}
        manifest = json.loads(archive.read("manifest.json"))
        for name, expected in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
        assert archive.read("report.json") == first["canonical_json"].encode()
        assert b"<script>alert" not in archive.read("report.html") and b"&lt;script&gt;" in archive.read("report.html")


def test_defensive_copy_ownership_and_review_never_grants_acceptance(setup):
    result = make(setup); r, _, _ = setup; key = result["report_id"]
    result["report"]["status"]["production_handoff"] = True
    assert r.get("actor", key)["report"]["status"]["production_handoff"] is False
    with pytest.raises(GeometryContractError): r.get("other", key)
    before = r.package("actor", key); intent = r.review("actor", key, "Synthetic inspection only")
    assert not intent["independent_acceptance"] and r.package("actor", key) == before


def test_stale_sources_preserve_original_report_and_refuse_new_generation(setup):
    original = make(setup); r, nav, (c, s, g, _) = setup; c.freshness = "stale"
    value = r.get("actor", original["report_id"], c, s, g, nav)
    assert value["freshness"] == "stale" and value["canonical_json"] == original["canonical_json"]
    with pytest.raises(GeometryContractError, match="current actual"): make(setup)


def test_changed_knowledge_review_marks_original_stale(setup):
    original = make(setup); r, nav, (c, s, g, _) = setup; source = nav.workspace.vault.get(SOURCE_ID)
    nav.workspace.vault.update_record(replace(source, version=2))
    assert r.get("actor", original["report_id"], c, s, g, nav)["freshness"] == "stale"


def test_tampered_source_unavailable_and_not_attachable(setup):
    _, nav, _ = setup; nav.workspace.vault._memory_originals[SOURCE_ID] = b"tampered synthetic source"
    assert nav.claim(CLAIM_ID)["claim"]["source_navigation_status"] == "evidence-unavailable-or-review-pending"
    with pytest.raises(GeometryContractError, match="hash-checked originals"): make(setup)


@pytest.mark.parametrize("claims", [["missing"], [CLAIM_ID, CLAIM_ID], ["../outside"], [True], ["a"]*9])
def test_invalid_claim_selection(setup, claims):
    with pytest.raises(GeometryContractError): make(setup, claims=claims)


@pytest.mark.parametrize("title", ["", " ", "x"*129, True, "a\0b"])
def test_invalid_title(setup, title):
    with pytest.raises(GeometryContractError): make(setup, title)


def test_dataset_mismatch_refused(setup):
    _, _, (_, s, _, _) = setup; original = s.dataset
    def changed(*args):
        value = original(*args); value["temperature_k"][0] += 1; return value
    s.dataset = changed
    with pytest.raises(GeometryContractError, match="exact P09 dataset"): make(setup)


def test_corrupt_stored_report_refuses_export(setup):
    value = make(setup); r, _, _ = setup; key = value["report_id"]; r.session("actor").reports[key] += b" "
    with pytest.raises(GeometryContractError, match="checksum mismatch"): r.package("actor", key)


def test_report_includes_renderer_identity_and_readable_scientific_sections(setup):
    value = make(setup); r, _, _ = setup; files = r.files("actor", value["report_id"])
    assert value["report"]["reproducibility"]["renderer_source"]["sha256"] == hashlib.sha256((Path(__file__).resolve().parents[3]/'validation/reporting.py').read_bytes()).hexdigest()
    assert b"Method and SI operating conditions" in files["report.md"]
    assert b"Discrepancy and predeclared criteria" in files["report.html"]
