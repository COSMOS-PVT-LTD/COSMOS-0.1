"""Small helper-boundary fixtures; no full-engine or scientific acceptance."""

import copy
import json
import sqlite3
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from core.serialization import canonical_json_dumps
from scripts import assess_compact_regeneration as analysis
from scripts import prepare_compact_display as display
from scripts import prepare_compact_regeneration as regeneration
from systems.geometry.qa import STL_RECORD


def write_json(path, value):
    path.write_text(json.dumps(value))


@pytest.fixture
def selection(tmp_path, monkeypatch):
    """Tiny authority records with fake construction; exercise IO identity only."""
    store = tmp_path / "store"
    (store / "blobs").mkdir(parents=True)
    database = store / "metadata.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE objects(project_id,domain,object_id,head_commit_id,version,content_hash)"
        )
        connection.execute("CREATE TABLE commits(commit_id PRIMARY KEY,byte_length)")

    def retain(domain, object_id, commit_id, record):
        raw = json.dumps(record).encode()
        digest = sha256(raw).hexdigest()
        (store / "blobs" / digest).write_bytes(raw)
        with sqlite3.connect(database) as connection:
            connection.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?,?)",
                ("test-project", domain, object_id, commit_id, 1, digest),
            )
            connection.execute("INSERT INTO commits VALUES(?,?)", (commit_id, len(raw)))
        return {
            "project_id": "test-project",
            "object_id": object_id,
            "commit_id": commit_id,
            "head": {"version": 1, "content_hash": digest},
        }

    source = {
        "snapshot_json": "synthetic-snapshot",
        "graph_json": "synthetic-graph",
        "baseline_commit_id": "synthetic-physics",
        "baseline_canonical_json": '{"test_only":true}',
    }
    source_ref = retain(
        "engine-component-model", "source-object", "source-commit", source
    )
    candidate_record = {
        "source_commit_id": "source-commit",
        "source_object_id": source_ref["object_id"],
        "source_sha256": source_ref["head"]["content_hash"],
        "specification": {"test_only": True},
        "recipe_sha256": "a" * 64,
    }
    candidate_ref = retain(
        "engine-redesign-candidate",
        "candidate-object",
        "candidate-commit",
        candidate_record,
    )
    source_selection = {
        **source_ref,
        "domain": "engine-component-model",
        "kind": "RETAINED_COMPONENT",
    }
    source_selection.pop("project_id")
    candidate_selection = {
        **candidate_ref,
        "domain": "engine-redesign-candidate",
        "kind": "COMPACT_CANDIDATE",
    }
    candidate_selection.pop("project_id")
    baseline_record = {
        "component_source": source_selection,
        "selection": candidate_selection,
        "propulsion_commit_id": source["baseline_commit_id"],
    }
    baseline_ref = retain(
        "engine-development-baseline",
        "selection-object",
        "selection-commit",
        baseline_record,
    )
    research = {
        "schema": "cosmos.compact-engine-input.v1",
        "source_commit_id": "source-commit",
        "source_model": {
            name: source[name] for name in ("snapshot_json", "graph_json")
        },
        "specification": candidate_record["specification"],
        "recipe_sha256": "a" * 64,
    }
    receipt = {
        "applied": True,
        "baseline": {"authority": baseline_ref, "record": baseline_record},
        "candidate": candidate_ref,
        "research_input": research,
    }
    path = tmp_path / "applied.json"
    write_json(path, receipt)
    wire = {
        "recipe_sha256": "a" * 64,
        "groups": [{"bounds_m": [0, 0, 0, 0.001, 0.001, 0.001]}],
    }

    class Candidate:
        def wire(self):
            return wire

        @staticmethod
        def report():
            return {"test_only": True}

    monkeypatch.setattr(
        regeneration, "DesignSnapshot", SimpleNamespace(from_json=lambda value: value)
    )
    monkeypatch.setattr(
        regeneration,
        "GeometryFeatureGraph",
        SimpleNamespace(from_json=lambda value: value),
    )
    monkeypatch.setattr(regeneration, "from_contracts", lambda *args: "synthetic-plan")
    monkeypatch.setattr(regeneration, "compile_candidate", lambda *args: Candidate())

    # Disk guard has its own native-feature test; do not depend on host free space.
    def preflight(output):
        if (
            not output.is_absolute()
            or output.exists()
            or output.is_symlink()
            or not output.parent.is_dir()
        ):
            raise ValueError("New output required")

    monkeypatch.setattr(regeneration, "preflight", preflight)
    return SimpleNamespace(
        store=store.resolve(),
        receipt=receipt,
        path=path,
        wire=wire,
        source=source,
        retain=retain,
        candidate_record=candidate_record,
        output=tmp_path / "new-campaign",
    )


def test_selected_input_export_preserves_small_authority_records(selection):
    before = {p.name: p.read_bytes() for p in (selection.store / "blobs").iterdir()}
    result = regeneration.prepare(
        selection.path, selection.store, selection.output, 0.0005
    )
    assert result["authority_heads_matched"] and not result["app_data_modified"]
    assert result["engineering_acceptance"] == "NOT_PERFORMED"
    assert (
        json.loads((selection.output / "research-input.json").read_text())
        == selection.receipt["research_input"]
    )
    assert before == {
        p.name: p.read_bytes() for p in (selection.store / "blobs").iterdir()
    }


def test_preparation_refuses_stale_candidate_head_before_output_creation(selection):
    with sqlite3.connect(selection.store / "metadata.sqlite3") as connection:
        connection.execute(
            "UPDATE objects SET version=2 WHERE domain='engine-redesign-candidate'"
        )
    with pytest.raises(ValueError, match="head changed"):
        regeneration.prepare(selection.path, selection.store, selection.output, 0.0005)
    assert not selection.output.exists()


def test_preparation_refuses_changed_retained_blob(selection):
    digest = selection.receipt["candidate"]["head"]["content_hash"]
    (selection.store / "blobs" / digest).write_text("changed")
    with pytest.raises(ValueError, match="hash/length"):
        regeneration.prepare(selection.path, selection.store, selection.output, 0.0005)
    assert not selection.output.exists()


def test_preparation_cannot_relabel_an_unselected_same_recipe_candidate(selection):
    other = selection.retain(
        "engine-redesign-candidate",
        "other-object",
        "other-commit",
        selection.candidate_record,
    )
    selection.receipt["candidate"] = other
    write_json(selection.path, selection.receipt)
    with pytest.raises(ValueError, match="[Ss]election|[Ss]elected|candidate"):
        regeneration.prepare(selection.path, selection.store, selection.output, 0.0005)
    assert not selection.output.exists()


@pytest.mark.parametrize("voxel", [float("nan"), float("inf"), 0.000001, 0.1])
def test_preparation_refuses_unbounded_voxel_without_store_initialization(
    tmp_path, voxel
):
    with pytest.raises(ValueError, match="bounded research voxel"):
        regeneration.prepare(
            tmp_path / "missing.json",
            tmp_path / "missing-store",
            tmp_path / "output",
            voxel,
        )
    assert (
        not (tmp_path / "missing-store").exists() and not (tmp_path / "output").exists()
    )


def test_preparation_refuses_existing_output_and_overlarge_field(selection):
    selection.output.mkdir()
    marker = selection.output / "keep"
    marker.write_text("unchanged")
    with pytest.raises(ValueError, match="New output"):
        regeneration.prepare(selection.path, selection.store, selection.output, 0.0005)
    assert marker.read_text() == "unchanged"
    other = selection.output.parent / "overlarge"
    selection.wire["groups"][0]["bounds_m"] = [0, 0, 0, 1, 1, 1]
    with pytest.raises(ValueError, match="120M"):
        regeneration.prepare(selection.path, selection.store, other, 0.0005)
    assert not other.exists()


def test_preparation_requires_existing_database_and_unique_json(tmp_path):
    with pytest.raises(ValueError, match="Existing authority database"):
        regeneration.prepare(
            tmp_path / "receipt", tmp_path / "store", tmp_path / "output", 0.0005
        )
    malformed = tmp_path / "duplicate.json"
    malformed.write_text('{"key":1,"key":2}')
    with pytest.raises(ValueError, match="Duplicate"):
        regeneration.read_json(malformed)


@pytest.fixture
def native(tmp_path):
    directory = tmp_path / "native"
    directory.mkdir()
    records = np.zeros(1, dtype=STL_RECORD)
    records["vertices"] = [[[0, 0, 0], [0.001, 0, 0], [0, 0.001, 0]]]
    records["normal"] = [0, 0, 1]
    path = directory / "UNQUALIFIED-export.stl"
    path.write_bytes(
        b"SYNTHETIC DISPLAY FIXTURE; UNITS= m".ljust(80, b" ")
        + (1).to_bytes(4, "little")
        + records.tobytes()
    )
    parts = [
        {
            "part_id": "test-triangle",
            "role": "metal",
            "triangle_start": 0,
            "triangle_count": 1,
        }
    ]
    manifest = {
        "schema": "cosmos.compact-engine-build-evidence.v1",
        "complete": True,
        "qualification": "NOT_PERFORMED",
        "recipe_sha256": "a" * 64,
        "source_commit_id": "test-source",
        "result": {
            "ok": True,
            "backend": "picogk",
            "voxel_m": 0.0008,
            "triangle_count": 1,
            "parts": parts,
        },
        "artifacts": {path.name: sha256(path.read_bytes()).hexdigest()},
    }
    write_json(directory / "manifest.json", manifest)
    python = tmp_path / "explicit-python"
    python.touch()
    return SimpleNamespace(
        directory=directory,
        path=path,
        records=records,
        parts=parts,
        manifest=manifest,
        python=python,
        output=tmp_path / "display",
    )


def test_display_derivative_is_labelled_and_never_changes_native_bytes(
    native, monkeypatch
):
    before = native.path.read_bytes()

    def worker(*args, **kwargs):
        data = native.records["vertices"].astype("<f4").tobytes()
        (kwargs["cwd"] / "positions.f32").write_bytes(data)
        return SimpleNamespace(
            returncode=0,
            stderr="test-only worker",
            stdout=json.dumps(
                {
                    "parts": native.parts,
                    "sha256": sha256(data).hexdigest(),
                    "method": "Synthetic display test; no real reduction",
                }
            ),
        )

    monkeypatch.setattr(display.subprocess, "run", worker)
    result = display.prepare(native.directory, native.output, native.python)
    assert result["scope"] == "DISPLAY_DERIVATIVE_NOT_NATIVE_ENGINEERING_MESH"
    assert result["result"]["backend"] == "picogk-display"
    assert result["native_mesh_sha256"] == sha256(before).hexdigest()
    assert result["engineering_acceptance"] == "NOT_PERFORMED"
    assert native.path.read_bytes() == before


def test_display_refuses_bad_source_hash_and_existing_output(native):
    changed = copy.deepcopy(native.manifest)
    changed["artifacts"][native.path.name] = "b" * 64
    write_json(native.directory / "manifest.json", changed)
    with pytest.raises(ValueError, match="hash mismatch"):
        display.prepare(native.directory, native.output, native.python)
    assert not native.output.exists()
    write_json(native.directory / "manifest.json", native.manifest)
    native.output.mkdir()
    marker = native.output / "preserve"
    marker.write_text("keep")
    with pytest.raises(ValueError, match="no overwrite"):
        display.prepare(native.directory, native.output, native.python)
    assert marker.read_text() == "keep"


def test_display_worker_failure_keeps_diagnostic_without_completed_manifest(
    native, monkeypatch
):
    monkeypatch.setattr(
        display.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stderr="manufactured failure", stdout=""
        ),
    )
    before = native.path.read_bytes()
    with pytest.raises(ValueError, match="reduction failed"):
        display.prepare(native.directory, native.output, native.python)
    assert (native.output / "display-worker.log").read_text() == "manufactured failure"
    assert not (native.output / "manifest.json").exists()
    assert native.path.read_bytes() == before


def test_assessment_cannot_overwrite_or_accept_changed_raw_source(tmp_path):
    output = tmp_path / "existing.json"
    output.write_text("preserve")
    with pytest.raises(ValueError, match="no overwrite"):
        analysis.assess(tmp_path, tmp_path, tmp_path / "sat.tsv", tmp_path, output)
    assert output.read_text() == "preserve"
    raw = tmp_path / "source.tsv"
    raw.write_text("data")
    assert analysis.verified(raw, sha256(b"data").hexdigest())["verified"]
    with pytest.raises(ValueError, match="missing/changed"):
        analysis.verified(raw, "a" * 64)


def test_assessment_rejects_different_bound_baseline_before_reading_properties(
    tmp_path, monkeypatch
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    write_json(
        campaign / "preflight.json",
        {
            "baseline_sha256": sha256(
                canonical_json_dumps({"wrong": True}).encode()
            ).hexdigest()
        },
    )
    write_json(campaign / "bound-propulsion-baseline.json", {"test_only": True})
    monkeypatch.setattr(
        analysis, "load_candidate", lambda _: ("synthetic-candidate", {}, "a" * 64)
    )
    output = tmp_path / "assessment.json"
    with pytest.raises(ValueError, match="baseline identity changed"):
        analysis.assess(
            campaign,
            tmp_path / "no-liquid",
            tmp_path / "no-saturation",
            tmp_path / "no-material",
            output,
        )
    assert not output.exists()
