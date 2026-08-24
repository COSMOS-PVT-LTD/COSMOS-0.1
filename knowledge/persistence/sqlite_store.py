"""SQLite production persistence boundary. JSON snapshots remain compatible."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from typing import TYPE_CHECKING

from knowledge.persistence.migrations import MIGRATIONS, SCHEMA_VERSION

if TYPE_CHECKING:
    from knowledge.foundation.real_document_pipeline import RealDocumentPipelineResult

__all__ = (
    "DatabaseUnavailableError",
    "DuplicateSourceError",
    "KnowledgeDatabase",
    "MigrationError",
)


class DatabaseUnavailableError(RuntimeError):
    """SQLite database cannot be opened or is not writable."""


class DuplicateSourceError(ValueError):
    """A different source_id already owns this content hash."""


class MigrationError(RuntimeError):
    """Schema migration failed."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ProvenanceChain:
    source_id: str
    document_id: str
    page_number: int | None
    region_id: str | None
    image_hash: str | None
    content_hash: str
    candidate_id: str
    validation_state: str | None
    approval_decision: str | None


class KnowledgeDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(str(self.path))
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as exc:
            raise DatabaseUnavailableError(str(exc)) from exc
        self._connection = connection
        return connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def migrate(self) -> int:
        connection = self.connect()
        try:
            connection.executescript("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
            applied = {
                int(row[0])
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, script in MIGRATIONS:
                if version in applied:
                    continue
                connection.executescript(script)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (version, _now()),
                )
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise MigrationError(str(exc)) from exc
        return SCHEMA_VERSION

    def health(self) -> str:
        try:
            self.connect().execute("SELECT 1")
        except (sqlite3.Error, DatabaseUnavailableError):
            return "UNAVAILABLE"
        return "AVAILABLE"

    def persist_pipeline(self, result: RealDocumentPipelineResult) -> None:
        if result.registered is None:
            raise ValueError("Cannot persist a pipeline result without a registered source.")
        connection = self.connect()
        registered = result.registered
        try:
            with connection:
                self._upsert_source(connection, result)
                document_class = getattr(registered, "document_class", None)
                if document_class is not None and hasattr(document_class, "value"):
                    document_class = document_class.value
                connection.execute(
                    """
                    INSERT OR REPLACE INTO documents(
                        document_id, source_id, title, document_class, content_hash
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        registered.document_id,
                        registered.source_id,
                        registered.title,
                        document_class,
                        registered.content_hash,
                    ),
                )
                if result.extraction is not None:
                    for page in result.extraction.pages:
                        image_hash = next(
                            (item.image_hash for item in result.ocr_evidence if item.page_number == page.page_number),
                            "",
                        )
                        page_id = f"{registered.document_id}-p{page.page_number}"
                        connection.execute(
                            """
                            INSERT OR REPLACE INTO pages(
                                page_id, document_id, page_number, classification, char_count, image_hash
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                page_id,
                                registered.document_id,
                                page.page_number,
                                page.classification.value,
                                page.char_count,
                                image_hash,
                            ),
                        )
                for ocr in result.ocr_results:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO ocr_results(
                            ocr_id, source_id, document_id, page_number, image_hash,
                            backend, backend_version, text, confidence, failure
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"{ocr.source_id}-p{ocr.page_number}-{ocr.image_id}",
                            ocr.source_id,
                            ocr.document_id,
                            ocr.page_number,
                            ocr.image_hash,
                            ocr.adapter_name,
                            ocr.engine_version,
                            ocr.text,
                            ocr.confidence,
                            ocr.failure.value if ocr.failure else None,
                        ),
                    )
                for math in result.math_ocr_results:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO math_ocr_results(
                            math_ocr_id, source_id, document_id, page_number, region_id,
                            image_hash, source_representation, latex, backend, failure
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"{math.source_id}-{math.region_id}",
                            math.source_id,
                            math.document_id,
                            math.page_number,
                            math.region_id,
                            math.image_hash,
                            math.source_representation,
                            math.latex,
                            math.backend,
                            math.failure.value if math.failure else None,
                        ),
                    )
                reconstructions = {
                    item.source_equation_id: item for item in result.reconstructions
                }
                for candidate in result.equation_candidates:
                    reconstructed = reconstructions.get(candidate.candidate_id)
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO equation_candidates(
                            candidate_id, source_id, document_id, page_number, region_id,
                            raw_text, normalized_text, latex, image_hash, extraction_method,
                            backend, backend_version, version
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            candidate.candidate_id,
                            candidate.source_id,
                            candidate.document_id,
                            candidate.page_number,
                            candidate.region_id,
                            candidate.raw_text,
                            reconstructed.normalized_representation if reconstructed else None,
                            reconstructed.latex if reconstructed else candidate.latex,
                            next(
                                (item.image_hash for item in result.ocr_evidence if item.page_number == candidate.page_number),
                                None,
                            ),
                            candidate.provenance.extraction_method,
                            next((item.backend for item in result.math_ocr_results), None),
                            next((item.backend_version for item in result.math_ocr_results), None),
                            candidate.version,
                        ),
                    )
                    for binding in candidate.variables:
                        connection.execute(
                            """
                            INSERT OR REPLACE INTO variable_candidates(variable_id, candidate_id, symbol)
                            VALUES (?, ?, ?)
                            """,
                            (f"{candidate.candidate_id}-{binding.symbol}", candidate.candidate_id, binding.symbol),
                        )
                for entity in result.entity_candidates:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO entity_candidates(entity_id, document_id, kind, text)
                        VALUES (?, ?, ?, ?)
                        """,
                        (entity.candidate_id, entity.document_id, entity.kind, entity.statement),
                    )
                for validated in result.validated_equations:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO validation_results(
                            validation_id, candidate_id, state, dimension_state, semantic_state, unit_state, reasons
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"val-{validated.candidate.candidate_id}",
                            validated.candidate.candidate_id,
                            validated.state.value,
                            validated.dimension_state.value,
                            validated.semantic_state.value,
                            validated.unit_state.value,
                            json.dumps(list(validated.reasons)),
                        ),
                    )
                for package in result.review_packages:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO reviews(
                            review_id, candidate_id, validation_state, page_image_hash, ocr_text, warnings
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"rev-{package.candidate_id}",
                            package.candidate_id,
                            package.validation_state,
                            package.page_image_hash,
                            package.ocr_text,
                            json.dumps(list(package.warnings)),
                        ),
                    )
                for conflict in result.conflicts:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO contradictions(
                            contradiction_id, left_entity_id, right_entity_id, reason, relation
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            f"{conflict.left_entity_id}-{conflict.right_entity_id}",
                            conflict.left_entity_id,
                            conflict.right_entity_id,
                            conflict.reason,
                            getattr(conflict, "relation", None),
                        ),
                    )
                connection.execute(
                    "INSERT INTO audit_events(action, entity_id, timestamp, payload_json) VALUES (?, ?, ?, ?)",
                    (
                        "PERSIST_PIPELINE",
                        registered.source_id,
                        _now(),
                        json.dumps({"status": result.status.value}),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            message = str(exc)
            if "content_hash" in message:
                raise DuplicateSourceError(message) from exc
            raise
        except sqlite3.Error as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def persist_approval(
        self,
        *,
        candidate_id: str,
        decision: str,
        reviewer: str,
        payload: dict[str, object],
        supersedes_id: str | None = None,
    ) -> None:
        connection = self.connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO approvals(approval_id, candidate_id, decision, reviewer, approved_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (f"appr-{candidate_id}-{_now()}", candidate_id, decision, reviewer, _now()),
                )
                connection.execute(
                    """
                    INSERT INTO knowledge_versions(
                        version_id, entity_id, entity_type, payload_json, supersedes_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"ver-{candidate_id}-{_now()}",
                        candidate_id,
                        "Equation",
                        json.dumps(payload, sort_keys=True),
                        supersedes_id,
                        _now(),
                    ),
                )
        except sqlite3.Error as exc:
            raise DatabaseUnavailableError(str(exc)) from exc

    def source_hash(self, source_id: str) -> str:
        row = self.connect().execute(
            "SELECT content_hash FROM sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        if row is None:
            raise KeyError(source_id)
        return str(row["content_hash"])

    def equation_versions(self, entity_id: str) -> tuple[str, ...]:
        rows = self.connect().execute(
            "SELECT version_id FROM knowledge_versions WHERE entity_id = ? ORDER BY created_at",
            (entity_id,),
        ).fetchall()
        return tuple(str(row["version_id"]) for row in rows)

    def trace_equation(self, candidate_id: str) -> ProvenanceChain:
        connection = self.connect()
        row = connection.execute(
            """
            SELECT e.candidate_id, e.source_id, e.document_id, e.page_number, e.region_id,
                   e.image_hash, s.content_hash, v.state AS validation_state, a.decision
            FROM equation_candidates e
            JOIN sources s ON s.source_id = e.source_id
            LEFT JOIN validation_results v ON v.candidate_id = e.candidate_id
            LEFT JOIN approvals a ON a.candidate_id = e.candidate_id
            WHERE e.candidate_id = ?
            ORDER BY a.approved_at DESC
            LIMIT 1
            """,
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise KeyError(candidate_id)
        return ProvenanceChain(
            source_id=str(row["source_id"]),
            document_id=str(row["document_id"]),
            page_number=row["page_number"],
            region_id=row["region_id"],
            image_hash=row["image_hash"],
            content_hash=str(row["content_hash"]),
            candidate_id=str(row["candidate_id"]),
            validation_state=row["validation_state"],
            approval_decision=row["decision"],
        )

    def _upsert_source(self, connection: sqlite3.Connection, result: RealDocumentPipelineResult) -> None:
        registered = result.registered
        assert registered is not None
        existing = connection.execute(
            "SELECT source_id FROM sources WHERE content_hash = ?",
            (registered.content_hash,),
        ).fetchone()
        if existing is not None and str(existing["source_id"]) != registered.source_id:
            raise DuplicateSourceError(
                f"content hash already registered as {existing['source_id']}",
            )
        rights_status = getattr(registered, "rights_status", None)
        if rights_status is None:
            rights_status = "INTERNAL"
        elif hasattr(rights_status, "value"):
            rights_status = rights_status.value
        document_class = getattr(registered, "document_class", None)
        if document_class is not None and hasattr(document_class, "value"):
            document_class = document_class.value
        connection.execute(
            """
            INSERT OR REPLACE INTO sources(
                source_id, document_id, title, filename, content_hash, file_hash,
                rights_status, license, document_class, edition, revision, publisher,
                author, organization, publication_year, usage_constraints, ingested_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registered.source_id,
                registered.document_id,
                registered.title,
                registered.filename,
                registered.content_hash,
                registered.file_hash,
                rights_status,
                getattr(registered, "license", None),
                document_class,
                registered.edition,
                registered.revision,
                registered.publisher,
                registered.author,
                getattr(registered, "organization", None),
                getattr(registered, "publication_year", None),
                getattr(registered, "usage_constraints", None),
                registered.ingested_at,
                registered.created_at,
            ),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
