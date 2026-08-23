"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.exceptions

Purpose:
    Graph-layer exceptions for the COSMOS Knowledge Graph contracts.

Description:
    Extends the shared COSMOS exception hierarchy defined in core.exceptions.
    Graph-specific failures are grouped here so downstream KG batches can
    catch graph contract, validation, or storage errors without coupling to
  unrelated domains.
"""

from __future__ import annotations

from core.exceptions import CosmosError, ValidationError

__all__ = (
    "GraphContractError",
    "GraphConstructionError",
    "GraphError",
    "GraphQueryError",
    "GraphStorageError",
    "GraphValidationError",
)


class GraphError(CosmosError):
    """Base class for Knowledge Graph layer failures."""


class GraphValidationError(ValidationError, GraphError):
    """Indicate that a graph contract failed structural validation."""


class GraphContractError(GraphError):
    """Indicate misuse of a graph contract or invariant violation.

    Used by graph integration layers (for example KG-003 entity/relationship
    adapters) for invariant violations that are distinct from structural
    validation failures covered by ``GraphValidationError``.
    """


class GraphStorageError(GraphError):
    """Indicate that a graph storage operation failed."""


class GraphConstructionError(GraphError):
    """Indicate that graph construction failed."""


class GraphQueryError(GraphError):
    """Indicate that a graph query operation failed."""
