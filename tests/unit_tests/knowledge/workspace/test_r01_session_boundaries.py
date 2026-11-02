"""Principal isolation and durable session recovery; all roots are temporary."""
from __future__ import annotations

import hashlib
import json
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from knowledge.graph.concept_graph import ConceptEdge
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship
from knowledge.pdf.corpus import reynolds_pdf_bytes
from knowledge.workspace.access import KnowledgeGovernanceError, WorkspaceRole
from knowledge.workspace.backup import WorkspaceBackupError
from knowledge.workspace.corpus import chamber_csv_bytes
from knowledge.workspace.session import KnowledgeWorkspace

CONTENT = b"# Retained synthetic evidence\r\nregenerative cooling fixture\r\n--"


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def populated(root):
    workspace = KnowledgeWorkspace(root)
    source = workspace.ingest(CONTENT, filename="source.md").source
    assert source is not None
    workspace.conversations.create(user="retained-conversation")
    return workspace, source


def test_nested_principals_reset_exact_identity_after_exception():
    workspace = KnowledgeWorkspace(role=WorkspaceRole.VIEWER, actor_id="default-viewer")
    with workspace.as_principal(WorkspaceRole.ADMIN, "outer-admin"):
        assert (workspace.role, workspace.actor_id) == (WorkspaceRole.ADMIN, "outer-admin")
        with pytest.raises(RuntimeError, match="injected"), workspace.as_principal(WorkspaceRole.ENGINEER, "inner-engineer"):
            assert (workspace.role, workspace.actor_id) == (WorkspaceRole.ENGINEER, "inner-engineer")
            raise RuntimeError("injected")
        assert (workspace.role, workspace.actor_id) == (WorkspaceRole.ADMIN, "outer-admin")
    assert (workspace.role, workspace.actor_id) == (WorkspaceRole.VIEWER, "default-viewer")
    with pytest.raises(KnowledgeGovernanceError):
        workspace.backup()


def test_invalid_principal_never_changes_default_identity():
    workspace = KnowledgeWorkspace(role=WorkspaceRole.VIEWER, actor_id="default-viewer")
    with pytest.raises(ValueError), workspace.as_principal("NOT_A_ROLE", "spoofed"):
        pytest.fail("Invalid principal was entered")
    assert (workspace.role, workspace.actor_id) == (WorkspaceRole.VIEWER, "default-viewer")


def test_thread_context_does_not_inherit_other_request_and_serializes_entry():
    workspace = KnowledgeWorkspace(role=WorkspaceRole.VIEWER, actor_id="default-viewer")
    admin_entered = threading.Event()
    viewer_observed = threading.Event()
    viewer_entered = threading.Event()

    def administrator():
        with workspace.as_principal(WorkspaceRole.ADMIN, "thread-admin"):
            admin_entered.set()
            assert viewer_observed.wait(3)
            assert not viewer_entered.is_set()
            assert (workspace.role, workspace.actor_id) == (WorkspaceRole.ADMIN, "thread-admin")
        return workspace.role, workspace.actor_id

    def viewer():
        assert admin_entered.wait(3)
        assert (workspace.role, workspace.actor_id) == (WorkspaceRole.VIEWER, "default-viewer")
        viewer_observed.set()
        with workspace.as_principal(WorkspaceRole.VIEWER, "thread-viewer"):
            viewer_entered.set()
            with pytest.raises(KnowledgeGovernanceError):
                workspace.backup()
            return workspace.role, workspace.actor_id

    with ThreadPoolExecutor(2) as pool:
        first, second = pool.submit(administrator), pool.submit(viewer)
        assert first.result(timeout=5) == (WorkspaceRole.VIEWER, "default-viewer")
        assert second.result(timeout=5) == (WorkspaceRole.VIEWER, "thread-viewer")
    assert (workspace.role, workspace.actor_id) == (WorkspaceRole.VIEWER, "default-viewer")


def test_two_workspaces_have_independent_principal_contexts():
    first = KnowledgeWorkspace(role=WorkspaceRole.VIEWER, actor_id="first-default")
    second = KnowledgeWorkspace(role=WorkspaceRole.REVIEWER, actor_id="second-default")
    with first.as_principal(WorkspaceRole.ADMIN, "first-admin"):
        assert (second.role, second.actor_id) == (WorkspaceRole.REVIEWER, "second-default")
        with second.as_principal(WorkspaceRole.APPROVER, "second-approver"):
            assert (first.role, first.actor_id) == (WorkspaceRole.ADMIN, "first-admin")
        assert (second.role, second.actor_id) == (WorkspaceRole.REVIEWER, "second-default")
    assert (first.role, first.actor_id) == (WorkspaceRole.VIEWER, "first-default")


@pytest.mark.parametrize("role", [WorkspaceRole.VIEWER, WorkspaceRole.ENGINEER, WorkspaceRole.REVIEWER, WorkspaceRole.APPROVER])
def test_nonadmin_principal_cannot_close_sqlite_or_create_backup(tmp_path, role):
    workspace, source = populated(tmp_path / "workspace")
    before = hashes(workspace.root)
    backend = workspace.persistence
    with workspace.as_principal(role, role.value):
        with pytest.raises(KnowledgeGovernanceError):
            workspace.restore(tmp_path / "missing.zip")
        with pytest.raises(KnowledgeGovernanceError):
            workspace.backup(tmp_path / "unauthorized.zip")
    assert workspace.persistence is backend
    assert backend.get("sources", source.source_id)["sha256"] == source.sha256
    assert hashes(workspace.root) == before
    assert not (tmp_path / "unauthorized.zip").exists()
    backend.close()


@pytest.mark.parametrize("kind", ["missing", "not-zip", "truncated", "checksum", "bad-manifest"])
def test_rejected_restore_session_reopens_original_sqlite_and_preserves_caches(tmp_path, kind):
    workspace, source = populated(tmp_path / "workspace")
    valid = workspace.backup(tmp_path / "valid.zip")
    invalid = tmp_path / "invalid.zip"
    if kind == "not-zip":
        invalid.write_bytes(b"not a ZIP")
    elif kind == "truncated":
        invalid.write_bytes(valid.read_bytes()[:-20])
    elif kind in {"checksum", "bad-manifest"}:
        with zipfile.ZipFile(valid) as original, zipfile.ZipFile(invalid, "x") as altered:
            for name in original.namelist():
                data = original.read(name)
                if kind == "bad-manifest" and name == "backup_manifest.json":
                    data = b'{"format":"unsupported"}'
                if kind == "checksum" and name.startswith("jobs/"):
                    data += b" "
                altered.writestr(name, data)
    before = hashes(workspace.root)
    old_backend = workspace.persistence
    old_vault, old_jobs, old_conversations = workspace.vault, workspace.jobs, workspace.conversations
    old_datasets, old_pipeline, old_drafts, old_service = workspace.datasets, workspace._pipeline_results, workspace._drafts, workspace._service
    with pytest.raises(WorkspaceBackupError):
        workspace.restore(invalid)
    assert hashes(workspace.root) == before
    assert workspace.persistence is not old_backend
    assert workspace.vault is old_vault and workspace.jobs is old_jobs and workspace.conversations is old_conversations
    assert workspace.datasets is old_datasets and workspace._pipeline_results is old_pipeline
    assert workspace._drafts is old_drafts and workspace._service is old_service
    assert workspace.persistence.get("sources", source.source_id)["sha256"] == source.sha256
    workspace.persistence.put("acceptance", "after-refusal", {"usable": True})
    assert workspace.persistence.get("acceptance", "after-refusal") == {"usable": True}
    assert workspace.vault.retrieve_original(source.source_id) == CONTENT
    assert workspace.search_documents("regenerative cooling")
    assert workspace.metrics.restores == 0
    assert not list(tmp_path.glob(".cosmos-restore-recovery-*"))
    workspace.persistence.close()


def test_successful_restore_relocates_originals_reopens_and_retains_previous_root(tmp_path):
    original, source = populated(tmp_path / "donor")
    original.persistence.put("acceptance", "snapshot", {"retained": True})
    archive = original.backup(tmp_path / "snapshot.zip")
    expected_jobs = [item.to_mapping() for item in original.list_jobs()]
    expected_conversations = [item.to_mapping() for item in original.conversations.store.list()]
    original.persistence.close()
    original.root.rename(tmp_path / "offline-donor")
    restored = KnowledgeWorkspace(tmp_path / "restored")
    restored.persistence.put("acceptance", "previous", {"recoverable": True})
    before = hashes(restored.root)
    old_vault, old_jobs, old_conversations = restored.vault, restored.jobs, restored.conversations
    restored.restore(archive)
    record = restored.vault.get(source.source_id)
    assert restored.vault.retrieve_original(source.source_id) == CONTENT
    assert record.sha256 == hashlib.sha256(CONTENT).hexdigest() == source.sha256
    assert Path(record.storage_uri).is_relative_to(restored.root)
    assert Path(record.storage_uri).is_file()
    assert restored.persistence.get("sources", source.source_id)["storage_uri"] == record.storage_uri
    assert restored.persistence.get("acceptance", "snapshot") == {"retained": True}
    assert restored.persistence.get("acceptance", "previous") is None
    restored.persistence.put("acceptance", "reopened", {"usable": True})
    assert restored.persistence.get("acceptance", "reopened") == {"usable": True}
    assert restored.vault is not old_vault and restored.jobs is not old_jobs and restored.conversations is not old_conversations
    assert [item.to_mapping() for item in restored.list_jobs()] == expected_jobs
    assert [item.to_mapping() for item in restored.conversations.store.list()] == expected_conversations
    assert restored.search_documents("regenerative cooling")
    assert restored.metrics.restores == 1
    recovery = next(tmp_path.glob(".cosmos-restore-recovery-*/previous"))
    assert hashes(recovery) == before
    receipt = json.loads((recovery.parent / "restore_receipt.json").read_text())
    assert receipt["destination"] == str(restored.root)
    restored.persistence.close()


@pytest.mark.parametrize("seed_corpus", [False, True])
def test_successful_restore_invalidates_post_snapshot_models_but_rehydrates_snapshot_datasets(tmp_path, seed_corpus):
    workspace = KnowledgeWorkspace(tmp_path / "workspace", seed_corpus=seed_corpus)
    original = workspace.ingest(chamber_csv_bytes(), filename="snapshot.csv")
    assert original.source is not None
    dataset_id = f"DS-{original.source.source_id}"
    expected = workspace.persistence.get("datasets", dataset_id)
    assert expected is not None and workspace.datasets[dataset_id] == expected
    archive = workspace.backup(tmp_path / "snapshot.zip")

    later_csv = workspace.ingest(b"label,value (m)\npost-snapshot,12.5\n", filename="later.csv")
    later_text = workspace.ingest(b"# Post-snapshot candidate\n$$ F = m a $$\n", filename="later.md")
    later_pdf = workspace.ingest(reynolds_pdf_bytes(), filename="later.pdf")
    assert later_csv.source is not None and later_text.source is not None and later_pdf.source is not None
    assert f"DS-{later_csv.source.source_id}" in workspace.datasets
    assert later_text.source.source_id in workspace._drafts
    assert later_pdf.source.source_id in workspace._pipeline_results
    old_service = workspace.service
    old_service.graph.add(ConceptEdge(source_id="EQ-POST-SNAPSHOT", target_id=later_text.source.source_id,
                                     relationship=EngineeringRelationship.DERIVED_FROM))
    assert "EQ-POST-SNAPSHOT" in {node["id"] for node in workspace.knowledge_graph()["nodes"]}
    if seed_corpus:
        assert workspace._seed_corpus_loaded is True

    workspace.restore(archive)
    assert workspace._service is None
    assert workspace._seed_corpus_loaded is False
    assert workspace._pipeline_results == {} and workspace._drafts == {}
    assert workspace.datasets == {dataset_id: expected}
    assert workspace.persistence.get("datasets", dataset_id) == expected
    assert workspace.persistence.get("datasets", f"DS-{later_csv.source.source_id}") is None
    assert {source.source_id for source in workspace.list_sources()} == {original.source.source_id}
    assert workspace.service is not old_service
    graph = workspace.knowledge_graph()
    assert not {"EQ-POST-SNAPSHOT", later_csv.source.source_id, later_text.source.source_id, later_pdf.source.source_id} & {node["id"] for node in graph["nodes"]}
    assert workspace.vault.verify(original.source.source_id)
    workspace.persistence.close()
