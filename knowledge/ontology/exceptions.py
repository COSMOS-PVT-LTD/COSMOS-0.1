"""
COSMOS Knowledge Foundation

Module:
    knowledge.ontology.exceptions

Purpose:
    Ontology-layer exceptions.
"""

from __future__ import annotations

from knowledge.extraction.exceptions import ExtractionError, ExtractionValidationError

__all__ = (
    "AliasConflictError",
    "CanonicalizationError",
    "DuplicateOntologyTermError",
    "OntologyError",
    "OntologyIdentityError",
    "OntologyRegistryError",
    "OntologyRelationshipError",
    "OntologyTermNotFoundError",
    "OntologyValidationError",
    "TaxonomyCycleError",
)


class OntologyError(ExtractionError):
    """Base class for ontology-layer failures."""


class OntologyValidationError(ExtractionValidationError):
    """Indicate that an ontology contract failed validation."""


class OntologyRegistryError(OntologyError):
    """Indicate an ontology registry operation failure."""


class DuplicateOntologyTermError(OntologyRegistryError):
    """Indicate that a term identifier is already registered."""


class OntologyTermNotFoundError(OntologyRegistryError):
    """Indicate that an ontology term was not found."""


class OntologyIdentityError(OntologyValidationError):
    """Indicate invalid or unstable ontology identity input."""


class CanonicalizationError(OntologyError):
    """Indicate canonicalization processing failure."""


class AliasConflictError(OntologyRegistryError):
    """Indicate alias registration or resolution conflict."""


class TaxonomyCycleError(OntologyRegistryError):
    """Indicate a taxonomy cycle or invalid hierarchy edge."""


class OntologyRelationshipError(OntologyRegistryError):
    """Indicate ontology relationship rule validation failure."""
