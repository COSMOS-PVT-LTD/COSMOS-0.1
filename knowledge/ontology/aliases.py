"""Controlled alias operations for KG-025."""

from __future__ import annotations

from knowledge.ontology.exceptions import AliasConflictError, OntologyValidationError
from knowledge.ontology.models import OntologyAlias
from knowledge.ontology.registry import OntologyRegistry, OntologyTermNotFoundError

__all__ = (
    "list_aliases",
    "register_alias",
)


def register_alias(
    registry: OntologyRegistry,
    *,
    alias: str,
    canonical_term_id: str,
) -> OntologyAlias:
    """Register a controlled alias for an existing canonical ontology term."""

    if not isinstance(registry, OntologyRegistry):
        raise OntologyValidationError(
            "registry must be an OntologyRegistry instance."
        )

    cleaned = alias.strip()

    if not cleaned:
        raise OntologyValidationError("alias must not be blank.")

    registry.get_term(canonical_term_id)

    alias_record = OntologyAlias(
        alias=cleaned,
        canonical_term_id=canonical_term_id,
    )

    try:
        registry.register_alias(alias_record)
    except OntologyTermNotFoundError:
        raise
    except AliasConflictError:
        raise

    return alias_record


def list_aliases(registry: OntologyRegistry) -> tuple[OntologyAlias, ...]:
    """Return registered aliases in deterministic order."""

    return registry.list_aliases()
