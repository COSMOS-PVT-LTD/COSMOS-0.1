"""Exact bytes may be restored; history may not be rewritten to hide damage."""

import sqlite3
from hashlib import sha256

import pytest

from scripts.restore_exact_blob import command
from tests.unit_tests.infrastructure import test_durable_jobs as durable_job_fixtures
from tests.unit_tests.infrastructure.test_durable_jobs import (
    OWNER,
    admit,
    complete,
)

setup = durable_job_fixtures.setup


@pytest.fixture
def missing(setup, tmp_path):
    repository, jobs, project, source = setup
    job = complete(jobs, admit(jobs, source))
    blob = job.blobs[0]
    target = repository.files.blobs / blob.content_hash
    source_file = (tmp_path / "retained-copy.bin").resolve()
    source_file.write_bytes(target.read_bytes())
    target.unlink()  # Only this manufactured temporary test-store artifact.
    return repository, project, source_file, target, blob.content_hash


def test_preview_has_no_authority_writes_and_apply_restores_exact_bytes(missing):
    repository, _project, source, target, digest = missing
    root = repository.files.root.resolve()
    before = sha256(repository.path.read_bytes()).hexdigest()
    preview = command(root, source, digest)
    assert not preview["applied"] and not target.exists()
    assert sha256(repository.path.read_bytes()).hexdigest() == before
    result = command(
        root, source, digest, apply_preview_sha256=preview["preview_sha256"]
    )
    assert result["applied"] and result["metadata_unchanged"]
    assert result["durable_job_integrity"] == "PASS"
    assert target.read_bytes() == source.read_bytes()
    assert sha256(repository.path.read_bytes()).hexdigest() == before
    with pytest.raises(ValueError, match="never overwrites"):
        command(root, source, digest)


def test_wrong_bytes_never_publish_even_with_expected_length(missing):
    repository, _project, source, target, digest = missing
    source.write_bytes(b"x" * source.stat().st_size)
    with pytest.raises(ValueError, match="differs from original"):
        command(repository.files.root.resolve(), source, digest)
    assert not target.exists()


def test_unknown_digest_and_missing_store_never_initialize(missing, tmp_path):
    repository, _project, source, target, _digest = missing
    with pytest.raises(ValueError, match="existing referenced"):
        command(repository.files.root.resolve(), source, "f" * 64)
    new_root = (tmp_path / "never-initialized").resolve()
    with pytest.raises(ValueError, match="no initialization"):
        command(new_root, source, "f" * 64)
    assert not new_root.exists() and not target.exists()


def test_changed_metadata_preview_rejected_without_restore(missing):
    repository, _project, source, target, digest = missing
    root = repository.files.root.resolve()
    preview = command(root, source, digest)
    repository.create_project(
        OWNER,
        title="Unrelated manufactured project",
        mission="Test",
        operation_id="second-project",
    )
    with pytest.raises(ValueError, match="preview changed"):
        command(root, source, digest, apply_preview_sha256=preview["preview_sha256"])
    assert not target.exists()


def test_source_alias_and_existing_receipt_are_refused(missing, tmp_path):
    repository, _project, source, target, digest = missing
    alias = tmp_path / "alias.bin"
    alias.symlink_to(source)
    with pytest.raises(ValueError, match="regular source"):
        command(repository.files.root.resolve(), alias, digest)
    receipt = (tmp_path / "receipt.json").resolve()
    receipt.write_text("retained test receipt")
    with pytest.raises(ValueError, match="new absolute"):
        command(repository.files.root.resolve(), source, digest, output=receipt)
    assert receipt.read_text() == "retained test receipt" and not target.exists()


def test_commit_byte_recovery_is_explicitly_unsupported(setup, tmp_path):
    repository, _jobs, _project, _source = setup
    with sqlite3.connect(repository.path) as connection:
        digest = connection.execute(
            "SELECT content_hash FROM commits LIMIT 1"
        ).fetchone()[0]
    target = repository.files.blobs / digest
    copy = (tmp_path / "commit-copy.bin").resolve()
    copy.write_bytes(target.read_bytes())
    target.unlink()  # Only this manufactured temporary test-store commit.
    before = sha256(repository.path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Commit-byte recovery is unsupported"):
        command(repository.files.root.resolve(), copy, digest)
    assert not target.exists()
    assert sha256(repository.path.read_bytes()).hexdigest() == before
