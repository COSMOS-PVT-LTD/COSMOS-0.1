"""Register real PDF sources with hash identity and duplicate detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from knowledge.source.integrity import sha256_bytes_digest
from knowledge.source.vault import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.references.document_class import DocumentClass
from knowledge.references.rights import RightsStatus

__all__ = ("DuplicateKind", "RegisteredSource", "SourceModifiedError", "SourceRegistry")


class DuplicateKind(Enum):
    NONE = "NONE"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    SAME_CONTENT_DIFFERENT_FILENAME = "SAME_CONTENT_DIFFERENT_FILENAME"
    DIFFERENT_REVISION = "DIFFERENT_REVISION"
    DIFFERENT_EDITION = "DIFFERENT_EDITION"
    MODIFIED_SOURCE = "MODIFIED_SOURCE"


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisteredSource:
    source_id: str
    document_id: str
    title: str
    filename: str
    file_hash: str
    content_hash: str
    media_type: str
    file_size: int
    created_at: str
    ingested_at: str
    source_type: str
    publisher: str | None = None
    author: str | None = None
    edition: str | None = None
    revision: str | None = None
    publication_date: str | None = None
    duplicate_kind: DuplicateKind = DuplicateKind.NONE
    rights_status: RightsStatus = RightsStatus.INTERNAL
    document_class: DocumentClass = DocumentClass.COSMOS_INTERNAL
    license: str | None = None
    organization: str | None = None
    publication_year: int | None = None
    usage_constraints: str | None = None


class SourceRegistry:
    """In-memory source identity index over the existing vault."""

    def __init__(self, vault: InMemorySourceVault | None = None) -> None:
        self.vault = vault or InMemorySourceVault()
        self._by_id: dict[str, RegisteredSource] = {}
        self._by_hash: dict[str, str] = {}

    def register(
        self,
        content: bytes,
        *,
        source_id: str,
        document_id: str,
        title: str,
        filename: str,
        source_type: str = "ENGINEERING_PDF",
        publisher: str | None = None,
        author: str | None = None,
        edition: str | None = None,
        revision: str | None = None,
        publication_date: str | None = None,
        rights_status: RightsStatus | None = None,
        document_class: DocumentClass | None = None,
        license: str | None = None,
        organization: str | None = None,
        publication_year: int | None = None,
        usage_constraints: str | None = None,
    ) -> RegisteredSource:
        digest = sha256_bytes_digest(content)
        now = datetime.now(timezone.utc).isoformat()
        duplicate = DuplicateKind.NONE
        if digest in self._by_hash:
            existing = self._by_id[self._by_hash[digest]]
            if existing.filename == filename:
                duplicate = DuplicateKind.EXACT_DUPLICATE
            else:
                duplicate = DuplicateKind.SAME_CONTENT_DIFFERENT_FILENAME
        elif source_id in self._by_id and self._by_id[source_id].content_hash != digest:
            raise SourceModifiedError(
                f"Source '{source_id}' hash changed; refusing silent replacement.",
            )
        else:
            for existing in self._by_id.values():
                if existing.title != title:
                    continue
                if edition and existing.edition and existing.edition != edition:
                    duplicate = DuplicateKind.DIFFERENT_EDITION
                    break
                if revision and existing.revision and existing.revision != revision:
                    duplicate = DuplicateKind.DIFFERENT_REVISION
                    break

        record = RegisteredSource(
            source_id=source_id,
            document_id=document_id,
            title=title,
            filename=filename,
            file_hash=digest,
            content_hash=digest,
            media_type="application/pdf",
            file_size=len(content),
            created_at=now,
            ingested_at=now,
            source_type=source_type,
            publisher=publisher,
            author=author,
            edition=edition,
            revision=revision,
            publication_date=publication_date,
            duplicate_kind=duplicate,
            rights_status=rights_status or RightsStatus.INTERNAL,
            document_class=document_class or DocumentClass.COSMOS_INTERNAL,
            license=license,
            organization=organization,
            publication_year=publication_year,
            usage_constraints=usage_constraints,
        )
        if duplicate not in {
            DuplicateKind.EXACT_DUPLICATE,
            DuplicateKind.SAME_CONTENT_DIFFERENT_FILENAME,
        }:
            self.vault.store(
                VaultArtifact(
                    source_id=source_id,
                    artifact_id=document_id,
                    content=content,
                    content_hash=digest,
                    metadata=VaultArtifactMetadata(
                        source_format="PDF",
                        media_type="application/pdf",
                    ),
                ),
            )
            self._by_id[source_id] = record
            self._by_hash[digest] = source_id
        return record

    def get(self, source_id: str) -> RegisteredSource:
        return self._by_id[source_id]


class SourceModifiedError(ValueError):
    """Source identity exists with a different hash."""
