"""Engineering-review hardening tests for KG-BLOCK-005."""

from __future__ import annotations

import pytest

from knowledge.ingestion.exceptions import IngestionAdapterError
from knowledge.ingestion.models import IngestionArtifactRef, IngestionRequest, SourceFormat
from knowledge.ingestion_adapters import (
    AdapterExecutionError,
    DocxIngestionAdapter,
    IngestionOrchestrator,
    RepositoryBoundaryError,
    RepositoryIngestionAdapter,
    RepositoryIngestionConfig,
    build_default_registry,
)
from knowledge.source import (
    InMemorySourceVault,
    IntegrityService,
    VaultArtifact,
    VaultValidationError,
    sha256_bytes_digest,
    verify_digest,
)
from knowledge.source.vault import VaultArtifactMetadata


def _store_artifact(
    vault: InMemorySourceVault,
    *,
    source_id: str,
    artifact_id: str,
    content: bytes,
    source_format: SourceFormat,
) -> IngestionArtifactRef:
    digest = sha256_bytes_digest(content)
    vault.store(
        VaultArtifact(
            source_id=source_id,
            artifact_id=artifact_id,
            content=content,
            content_hash=digest,
            metadata=VaultArtifactMetadata(source_format=source_format.value),
        ),
    )

    return IngestionArtifactRef(
        source_id=source_id,
        artifact_id=artifact_id,
        source_format=source_format,
        content_hash=digest,
    )


def test_verify_digest_accepts_uppercase_hex() -> None:
    """Digest comparison must normalize uppercase hex deterministically."""

    content = b"case-check"
    digest = sha256_bytes_digest(content).upper()

    verify_digest(content, digest)


def test_sha256_empty_content_is_deterministic() -> None:
    """Empty artifacts must hash deterministically without rejection."""

    assert sha256_bytes_digest(b"") == sha256_bytes_digest(b"")
    assert len(sha256_bytes_digest(b"")) == 64


def test_vault_verify_integrity_returns_false_on_mismatch() -> None:
    """Integrity verification must return False without masking unrelated errors."""

    vault = InMemorySourceVault()
    content = b"vault-payload"
    digest = sha256_bytes_digest(content)

    vault.store(
        VaultArtifact(
            source_id="SRC-001",
            artifact_id="ART-001",
            content=content,
            content_hash=digest,
        ),
    )

    stored = vault.retrieve("SRC-001", "ART-001")
    corrupted = VaultArtifact(
        source_id=stored.source_id,
        artifact_id=stored.artifact_id,
        content=b"changed",
        content_hash=digest,
        metadata=stored.metadata,
    )
    vault._artifacts[stored.vault_key] = corrupted  # noqa: SLF001

    assert vault.verify_integrity("SRC-001", "ART-001") is False


def test_vault_rejects_duplicate_with_validation_error() -> None:
    """Duplicate vault keys must raise VaultValidationError."""

    vault = InMemorySourceVault()
    digest = sha256_bytes_digest(b"payload")
    artifact = VaultArtifact(
        source_id="SRC-001",
        artifact_id="ART-001",
        content=b"payload",
        content_hash=digest,
    )

    vault.store(artifact)

    with pytest.raises(VaultValidationError):
        vault.store(artifact)


def test_orchestrator_rejects_unsupported_format() -> None:
    """Auto dispatch must fail cleanly when no adapter supports the format."""

    from knowledge.ingestion_adapters.pdf import PdfIngestionAdapter
    from knowledge.ingestion_adapters.registry import IngestionAdapterRegistry

    vault = InMemorySourceVault()
    artifact = _store_artifact(
        vault,
        source_id="SRC-001",
        artifact_id="ART-MD",
        content=b"# markdown",
        source_format=SourceFormat.MARKDOWN,
    )
    partial_registry = IngestionAdapterRegistry((PdfIngestionAdapter(vault),))
    orchestrator = IngestionOrchestrator(partial_registry)

    with pytest.raises(IngestionAdapterError):
        orchestrator.ingest_auto(artifact)


def test_docx_adapter_rejects_malformed_zip() -> None:
    """Malformed DOCX input must raise a domain-specific adapter error."""

    vault = InMemorySourceVault()
    artifact = _store_artifact(
        vault,
        source_id="SRC-001",
        artifact_id="ART-DOCX",
        content=b"not-a-zip",
        source_format=SourceFormat.DOCX,
    )
    adapter = DocxIngestionAdapter(vault)
    request = IngestionRequest(
        artifact=artifact,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
    )

    with pytest.raises(AdapterExecutionError, match="DOCX"):
        adapter.ingest(request)


def test_ingestion_preserves_document_id_provenance() -> None:
    """Ingestion results must retain artifact identity for provenance tracing."""

    vault = InMemorySourceVault()
    artifact = _store_artifact(
        vault,
        source_id="SRC-PROV",
        artifact_id="ART-PROV-001",
        content=b"# Provenance\n",
        source_format=SourceFormat.MARKDOWN,
    )
    orchestrator = IngestionOrchestrator(build_default_registry(vault))

    result = orchestrator.ingest_auto(artifact)

    assert result.document_id == "ART-PROV-001"
    assert result.request.artifact.source_id == "SRC-PROV"
    assert result.request.artifact.content_hash == artifact.content_hash


def test_repository_rejects_symlink_escape(tmp_path) -> None:
    """Symlinks escaping the repository root must be rejected."""

    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.md"
    secret.write_text("# secret", encoding="utf-8")
    (root / "link.md").symlink_to(secret)

    vault = InMemorySourceVault()
    adapter = RepositoryIngestionAdapter(
        vault,
        RepositoryIngestionConfig(
            root_path=str(root),
            source_id="SRC-REPO",
            include_globs=("*.md",),
        ),
    )

    with pytest.raises(RepositoryBoundaryError):
        adapter.ingest_repository()


def test_repository_rejects_path_prefix_collision(tmp_path) -> None:
    """Path boundary checks must not use naive string prefix matching."""

    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo_ext"
    sibling.mkdir()
    leak = sibling / "leak.md"
    leak.write_text("# leak", encoding="utf-8")
    (root / "link.md").symlink_to(leak)

    vault = InMemorySourceVault()
    adapter = RepositoryIngestionAdapter(
        vault,
        RepositoryIngestionConfig(
            root_path=str(root),
            source_id="SRC-REPO",
            include_globs=("*.md",),
        ),
    )

    with pytest.raises(RepositoryBoundaryError):
        adapter.ingest_repository()


def test_frozen_ingestion_contract_import_smoke() -> None:
    """BLOCK-005 must remain compatible with frozen ingestion contracts."""

    from knowledge.ingestion import (  # noqa: PLC0415
        IngestionAdapter,
        IngestionRequest,
        IngestionResult,
        SourceFormat,
    )

    assert IngestionAdapter is not None
    assert SourceFormat.PDF.value == "PDF"
    assert IntegrityService is not None
    assert IngestionRequest is not None
    assert IngestionResult is not None
