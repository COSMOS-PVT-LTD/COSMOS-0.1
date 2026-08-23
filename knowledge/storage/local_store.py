"""Local file-backed knowledge store for production RAG (Step 7)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from knowledge.graph.exceptions import GraphValidationError
from knowledge.graph.memory_store import InMemoryGraphStore
from knowledge.graph.serialization import (
    canonical_graph_record_digest,
    graph_record_from_mapping,
    graph_record_to_mapping,
)
from knowledge.source.integrity import sha256_text_digest
from knowledge.storage.exceptions import CorruptionError, SchemaMismatchError, _coerce_int
from knowledge.storage.schema import (
    DOCUMENT_REGISTRY_FILENAME,
    GRAPH_SNAPSHOT_FILENAME,
    INGESTION_STATE_FILENAME,
    PRODUCTION_SCHEMA_VERSION,
    STORE_MANIFEST_FILENAME,
)

__all__ = (
    "DocumentRecord",
    "IngestionState",
    "LocalKnowledgeStore",
    "StoreManifest",
)


def _sha256_file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class StoreManifest:
    """Top-level store manifest with schema and integrity metadata."""

    schema_version: str
    store_id: str
    graph_digest: str | None = None
    document_count: int = 0

    def to_mapping(self) -> dict[str, object]:
        return {
            "document_count": self.document_count,
            "graph_digest": self.graph_digest,
            "schema_version": self.schema_version,
            "store_id": self.store_id,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> StoreManifest:
        return cls(
            schema_version=str(data["schema_version"]),
            store_id=str(data["store_id"]),
            graph_digest=(
                str(data["graph_digest"])
                if data.get("graph_digest") is not None
                else None
            ),
            document_count=_coerce_int(data.get("document_count"), 0),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentRecord:
    """Persistent document metadata and integrity fingerprint."""

    document_id: str
    source_id: str
    artifact_id: str
    content_hash: str
    content_digest: str
    version: int = 1
    status: str = "ACTIVE"

    def to_mapping(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "content_digest": self.content_digest,
            "content_hash": self.content_hash,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "status": self.status,
            "version": self.version,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> DocumentRecord:
        return cls(
            document_id=str(data["document_id"]),
            source_id=str(data["source_id"]),
            artifact_id=str(data["artifact_id"]),
            content_hash=str(data["content_hash"]),
            content_digest=str(data["content_digest"]),
            version=_coerce_int(data.get("version"), 1),
            status=str(data.get("status", "ACTIVE")),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionState:
    """Incremental ingestion state for restart recovery."""

    last_processed_document_id: str | None = None
    processed_count: int = 0
    skipped_unchanged_count: int = 0
    failed_count: int = 0

    def to_mapping(self) -> dict[str, object]:
        return {
            "failed_count": self.failed_count,
            "last_processed_document_id": self.last_processed_document_id,
            "processed_count": self.processed_count,
            "skipped_unchanged_count": self.skipped_unchanged_count,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> IngestionState:
        last_id = data.get("last_processed_document_id")
        return cls(
            last_processed_document_id=str(last_id) if last_id else None,
            processed_count=_coerce_int(data.get("processed_count"), 0),
            skipped_unchanged_count=_coerce_int(data.get("skipped_unchanged_count"), 0),
            failed_count=_coerce_int(data.get("failed_count"), 0),
        )


class LocalKnowledgeStore:
    """File-backed local knowledge store with explicit schema/version control."""

    def __init__(self, root_dir: str | Path, *, store_id: str = "cosmos-local") -> None:
        self._root = Path(root_dir)
        self._store_id = store_id
        self._graph_store = InMemoryGraphStore()
        self._documents: dict[str, DocumentRecord] = {}
        self._ingestion_state = IngestionState()
        self._ensure_layout()

    @property
    def root_dir(self) -> Path:
        return self._root

    @property
    def graph_store(self) -> InMemoryGraphStore:
        return self._graph_store

    @property
    def documents(self) -> dict[str, DocumentRecord]:
        return dict(self._documents)

    @property
    def ingestion_state(self) -> IngestionState:
        return self._ingestion_state

    def _ensure_layout(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        (self._root / "documents").mkdir(exist_ok=True)
        (self._root / "indexes").mkdir(exist_ok=True)
        (self._root / "state").mkdir(exist_ok=True)

    def _manifest_path(self) -> Path:
        return self._root / STORE_MANIFEST_FILENAME

    def _graph_path(self) -> Path:
        return self._root / GRAPH_SNAPSHOT_FILENAME

    def _registry_path(self) -> Path:
        return self._root / DOCUMENT_REGISTRY_FILENAME

    def _ingestion_state_path(self) -> Path:
        return self._root / INGESTION_STATE_FILENAME

    def initialize(self) -> StoreManifest:
        """Initialize a fresh store manifest."""

        manifest = StoreManifest(
            schema_version=PRODUCTION_SCHEMA_VERSION,
            store_id=self._store_id,
            graph_digest=None,
            document_count=0,
        )
        self._write_json(self._manifest_path(), manifest.to_mapping())
        self._write_json(self._registry_path(), {"documents": []})
        self._write_json(self._ingestion_state_path(), self._ingestion_state.to_mapping())
        return manifest

    def load(self) -> StoreManifest:
        """Load store manifest and persisted artifacts."""

        if not self._manifest_path().is_file():
            return self.initialize()

        manifest = StoreManifest.from_mapping(
            self._read_json(self._manifest_path()),
        )

        if manifest.schema_version != PRODUCTION_SCHEMA_VERSION:
            raise SchemaMismatchError(
                f"Unsupported schema version '{manifest.schema_version}'.",
            )

        if manifest.store_id != self._store_id:
            raise SchemaMismatchError(
                f"Store id mismatch: expected '{self._store_id}', "
                f"found '{manifest.store_id}'.",
            )

        if self._graph_path().is_file():
            try:
                graph_mapping = self._read_json(self._graph_path())
                record = graph_record_from_mapping(graph_mapping)
            except GraphValidationError as exc:
                raise CorruptionError("Graph snapshot is malformed.") from exc

            self._graph_store.restore(record)
            digest = canonical_graph_record_digest(record)

            if manifest.graph_digest is not None and manifest.graph_digest != digest:
                raise CorruptionError("Graph snapshot digest mismatch.")

        if self._registry_path().is_file():
            registry = self._read_json(self._registry_path())
            documents = registry.get("documents", [])

            if isinstance(documents, list):
                self._documents = {
                    str(item["document_id"]): DocumentRecord.from_mapping(item)
                    for item in documents
                    if isinstance(item, dict)
                }

        if self._ingestion_state_path().is_file():
            self._ingestion_state = IngestionState.from_mapping(
                self._read_json(self._ingestion_state_path()),
            )

        return manifest

    def save_graph(self) -> str:
        """Persist the current graph snapshot and update manifest digest."""

        record = self._graph_store.snapshot()
        digest = canonical_graph_record_digest(record)
        self._write_json(self._graph_path(), graph_record_to_mapping(record))

        manifest = StoreManifest(
            schema_version=PRODUCTION_SCHEMA_VERSION,
            store_id=self._store_id,
            graph_digest=digest,
            document_count=len(self._documents),
        )
        self._write_json(self._manifest_path(), manifest.to_mapping())
        return digest

    def register_document(
        self,
        *,
        document_id: str,
        source_id: str,
        artifact_id: str,
        content: str,
    ) -> DocumentRecord:
        """Register or update a document record with integrity digests."""

        content_digest = sha256_text_digest(content)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        existing = self._documents.get(document_id)
        version = 1 if existing is None else existing.version + 1

        record = DocumentRecord(
            document_id=document_id,
            source_id=source_id,
            artifact_id=artifact_id,
            content_hash=content_hash,
            content_digest=content_digest,
            version=version,
        )
        self._documents[document_id] = record
        self._write_json(
            self._registry_path(),
            {"documents": [item.to_mapping() for item in self._documents.values()]},
        )
        return record

    def mark_document_removed(self, document_id: str) -> DocumentRecord | None:
        """Mark a document as removed while preserving registry provenance."""

        existing = self._documents.get(document_id)

        if existing is None:
            return None

        record = DocumentRecord(
            document_id=existing.document_id,
            source_id=existing.source_id,
            artifact_id=existing.artifact_id,
            content_hash=existing.content_hash,
            content_digest=existing.content_digest,
            version=existing.version,
            status="REMOVED",
        )
        self._documents[document_id] = record
        self._write_json(
            self._registry_path(),
            {"documents": [item.to_mapping() for item in self._documents.values()]},
        )
        return record

    def save_ingestion_state(self, state: IngestionState) -> None:
        """Persist incremental ingestion state."""

        self._ingestion_state = state
        self._write_json(self._ingestion_state_path(), state.to_mapping())

    def verify_integrity(self) -> bool:
        """Verify on-disk integrity for manifest and graph snapshot."""

        if not self._manifest_path().is_file():
            return True

        manifest = StoreManifest.from_mapping(
            self._read_json(self._manifest_path()),
        )

        if not self._graph_path().is_file():
            return manifest.graph_digest is None

        try:
            record = graph_record_from_mapping(self._read_json(self._graph_path()))
            canonical = canonical_graph_record_digest(record)
        except GraphValidationError:
            return False

        return manifest.graph_digest == canonical

    @staticmethod
    def _read_json(path: Path) -> dict[str, object]:
        payload = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(payload, dict):
            msg = f"Expected JSON object in '{path}'."
            raise CorruptionError(msg)

        return payload

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, indent=2, sort_keys=True)
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        temp_path.write_text(f"{encoded}\n", encoding="utf-8")
        temp_path.replace(path)
