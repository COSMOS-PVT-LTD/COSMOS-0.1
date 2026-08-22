"""
COSMOS Knowledge Foundation

Module:
    knowledge.repository.repository

Purpose:
    Defines the in-memory document repository used by the
    COSMOS Knowledge Foundation.

Description:
    The repository provides the authoritative storage layer
    for validated Document objects.

    It exposes a stable API independent of the underlying
    storage backend so that future implementations may use
    SQLite, PostgreSQL, DuckDB, Redis, vector databases, or
    remote knowledge servers without requiring changes to
    calling code.

Responsibilities:
    - Store validated Document objects
    - Provide O(1) document lookup
    - Prevent duplicate document identifiers
    - Maintain repository integrity
    - Provide immutable access to repository contents

Author:
    COSMOS Development Team

Version:
    0.1.0
"""
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Final

from knowledge.models.document import Document

class RepositoryError(Exception):
    """
    Base exception for repository-related errors.

    Notes
    -----
    Future versions should inherit from
    CosmosError once the global exception
    hierarchy is finalized.
    """


class RepositoryValidationError(RepositoryError):
    """
    Raised when repository validation fails.
    """


class DuplicateDocumentError(RepositoryError):
    """
    Raised when attempting to insert a
    duplicate document identifier.
    """

class DocumentNotFoundError(RepositoryError):
    """
    Raised when a requested document
    cannot be found.
    """

class DocumentRepository:
    """
    In-memory repository for Document objects.

    The repository owns validated Document
    instances and provides a stable storage API.

    Notes
    -----
    Internal storage is intentionally abstracted
    behind the public API so that future storage
    backends can replace the in-memory mapping
    without breaking callers.
    """

    def __init__(
        self,
    ) -> None:
        """
        Initialize an empty document repository.

        The repository stores validated Document
        instances using document_id as the unique key.

        Notes
        -----
        The internal storage is intentionally hidden
        behind the public API to allow future storage
        backends to replace the in-memory mapping
        without breaking client code.
        """

        self._documents: MutableMapping[
            str,
            Document,
        ] = {}

    def add_document(
        self,
        document: Document,
    ) -> None:
        """
        Store a validated document.

        Args:
            document:
                The Document instance to store.

        Raises:
            RepositoryValidationError:
                If the document is invalid.

            DuplicateDocumentError:
                If the document identifier already exists.
        """

        self._validate_document(
            document,
        )

        self._check_duplicate(
            document.document_id,
        )

        self._documents[
            document.document_id
        ] = document

    def get_document(
        self,
        document_id: str,
    ) -> Document:
        """
        Retrieve a document.

        Args:
            document_id:
                Repository identifier.

        Returns:
            Document

        Raises:
            DocumentNotFoundError
        """

        self._validate_document_id(
            document_id,
        )

        try:
            return self._documents[
                document_id
            ]

        except KeyError as exc:
            raise DocumentNotFoundError(
                (
                    "Unknown document "
                    f"'{document_id}'."
                )
            ) from exc

    def remove_document(
        self,
        document_id: str,
    ) -> None:
        """
        Remove a document.

        Raises:
            DocumentNotFoundError
        """

        self._validate_document_id(
            document_id,
        )

        if (
            document_id
            not in self._documents
        ):
            raise DocumentNotFoundError(
                (
                    "Unknown document "
                    f"'{document_id}'."
                )
            )

        del self._documents[
            document_id
        ]

    def has_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Determine whether a document exists.
        """

        self._validate_document_id(
            document_id,
        )

        return (
            document_id
            in self._documents
        )

    def document_count(
        self,
    ) -> int:
        """
        Return repository size.
        """

        return len(
            self._documents
        )

    def document_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return immutable tuple of
        repository identifiers.
        """

        return tuple(
            self._documents.keys()
        )

    def all_documents(
        self,
    ) -> tuple[Document, ...]:
        """
        Return immutable snapshot of
        all documents.
        """

        return tuple(
            self._documents.values()
        )


    def is_empty(
        self,
    ) -> bool:
        """
        Return True if repository
        contains no documents.
        """

        return (
            not self._documents
        )

    def clear(
        self,
    ) -> None:
        """
        Remove all stored documents.
        """

        self._documents.clear()

    def _validate_document(
        self,
        document: Document,
    ) -> None:
        """
        Validate a document object.

        Parameters
        ----------
        document : Document

        Raises
        ------
        RepositoryValidationError
            If the document is invalid.
        """

        if document is None:
            raise RepositoryValidationError(
                "Document must not be None."
            )

        if not isinstance(
            document,
            Document,
        ):
            raise RepositoryValidationError(
                "Object must be a Document instance."
            )

        self._validate_document_id(
            document.document_id,
        )


    def _validate_document_id(
        self,
        document_id: str,
    ) -> None:
        """
        Validate a document identifier.

        Parameters
        ----------
        document_id : str

        Raises
        ------
        RepositoryValidationError
            If the identifier is invalid.
        """

        if not isinstance(
            document_id,
            str,
        ):
            raise RepositoryValidationError(
                "document_id must be a string."
            )

        if not document_id.strip():
            raise RepositoryValidationError(
                "document_id must not be blank."
            )

    def _check_duplicate(
        self,
        document_id: str,
    ) -> None:
        """
        Check whether a document identifier
        already exists.

        Parameters
        ----------
        document_id : str

        Raises
        ------
        DuplicateDocumentError
            If the identifier already exists.
        """

        if document_id in self._documents:
            raise DuplicateDocumentError(
                (
                    "Duplicate document "
                    f"identifier: "
                    f"'{document_id}'."
                )
            )
    