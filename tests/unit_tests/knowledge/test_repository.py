"""
Unit tests for knowledge.repository.repository.
"""

from __future__ import annotations

try:
    import pytest.integration  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback for environments without pytest
    from contextlib import contextmanager
    class _PyTestShim:
        @contextmanager
        def raises(self, exc):
            try:
                yield
            except Exception as e:
                if not isinstance(e, exc):
                    raise
            else:
                raise AssertionError(f"Did not raise {exc}")

    pytest = _PyTestShim()

from knowledge.models.document import (
    Document,
    DocumentApprovalStatus,
    DocumentType,
    SecurityLevel,
)
from knowledge.models.reference import (
    Reference,
    ReferenceStatus,
    ReferenceType,
)
from knowledge.repository.repository import (
    DocumentNotFoundError,
    DocumentRepository,
    DuplicateDocumentError,
    RepositoryValidationError,
)
def create_reference() -> Reference:
    """
    Create a valid Reference object for testing.
    """

    return Reference(
        reference_id="ref-001",
        title="Rocket Propulsion Elements",
        authors=(
            "George P. Sutton",
        ),
        reference_type=ReferenceType.BOOK,
        status=ReferenceStatus.APPROVED,
    )
def create_document(
    document_id: str = "doc-001",
) -> Document:
    """
    Create a valid Document object.
    """

    return Document(
        document_id=document_id,
        document_version_id="v1",
        title="Rocket Engine Fundamentals",
        content="Rocket propulsion engineering.",
        document_type=DocumentType.MANUAL,
        reference=create_reference(),
        approval_status=DocumentApprovalStatus.DRAFT,
        security_level=SecurityLevel.INTERNAL,
    )

def test_repository_creation() -> None:
    """
    Verify repository initializes empty.
    """

    repository = DocumentRepository()

    assert repository.is_empty()
    assert repository.document_count() == 0

def test_add_document() -> None:
    """
    Verify document insertion.
    """

    repository = DocumentRepository()

    document = create_document()

    repository.add_document(document)

    assert repository.document_count() == 1 

def test_get_document() -> None:
    """
    Verify retrieval by ID.
    """

    repository = DocumentRepository()

    document = create_document()

    repository.add_document(document)

    retrieved = repository.get_document(
        "doc-001"
    )

    assert retrieved == document

def test_duplicate_document() -> None:
    """
    Duplicate IDs shall fail.
    """

    repository = DocumentRepository()

    document = create_document()

    repository.add_document(document)

    with pytest.raises(
        DuplicateDocumentError,
    ):
        repository.add_document(document)

def test_remove_document() -> None:
    """
    Verify removal.
    """

    repository = DocumentRepository()

    document = create_document()

    repository.add_document(document)

    repository.remove_document(
        document.document_id
    )

    assert repository.is_empty()

def test_missing_document() -> None:
    """
    Missing IDs raise.
    """

    repository = DocumentRepository()

    with pytest.raises(
        DocumentNotFoundError,
    ):
        repository.get_document(
            "missing"
        ) 

def test_invalid_document() -> None:
    """
    None shall be rejected.
    """

    repository = DocumentRepository()

    with pytest.raises(
        RepositoryValidationError,
    ):
        repository.add_document(None)  # type: ignore[arg-type]

def test_has_document() -> None:
    """
    Verify lookup.
    """

    repository = DocumentRepository()

    document = create_document()

    repository.add_document(document)

    assert repository.has_document(
        document.document_id
    )

def test_document_ids() -> None:
    """
    Verify immutable ID tuple.
    """

    repository = DocumentRepository()

    repository.add_document(
        create_document()
    )

    ids = repository.document_ids()

    assert ids == (
        "doc-001",
    )

def test_all_documents() -> None:
    """
    Verify immutable snapshot.
    """

    repository = DocumentRepository()

    document = create_document()

    repository.add_document(document)

    documents = repository.all_documents()

    assert documents == (
        document,
    )

def test_clear() -> None:
    """
    Verify repository reset.
    """

    repository = DocumentRepository()

    repository.add_document(
        create_document()
    )

    repository.clear()

    assert repository.is_empty()
    
        