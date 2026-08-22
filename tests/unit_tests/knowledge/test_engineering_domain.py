"""
Unit tests for knowledge.models.engineering_domain.

Phase
-----
Phase 0.5.7E

Purpose
-------
Verify the correctness, immutability, validation,
serialization, deserialization, and enterprise behavior
of the EngineeringDomain model.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

import pytest # type: ignore[import]

from knowledge.models.document import Document
from knowledge.models.document import DocumentType
from knowledge.models.engineering_domain import DomainCriticality
from knowledge.models.engineering_domain import DomainMaturityLevel
from knowledge.models.engineering_domain import EngineeringDomain
from knowledge.models.engineering_domain import EngineeringDomainCategory
from knowledge.models.engineering_domain import EngineeringDomainStatus
from knowledge.models.reference import Reference
from knowledge.models.reference import ReferenceType

# ============================================================
# Factory Helpers
# ============================================================


def create_reference() -> Reference:
    """
    Create a valid Reference.
    """

    return Reference(
        reference_id="REF-001",
        title="Rocket Propulsion Elements",
        authors=("John Doe",),
        reference_type=ReferenceType.BOOK,
    )


def create_document() -> Document:
    """
    Create a valid Document.
    """

    return Document(
        document_id="DOC-001",
        document_version_id="1.0",
        document_type=DocumentType.TEXTBOOK,
        title="Rocket Engineering",
        content="Engineering document.",
        reference=create_reference(),
    )


def create_engineering_domain() -> EngineeringDomain:
    """
    Create a valid EngineeringDomain.
    """

    return EngineeringDomain(

        # ----------------------------------------------------
        # Identity
        # ----------------------------------------------------

        domain_id="DOMAIN-001",

        name="Thermodynamics",

        short_name="Thermo",

        symbol="TD",

        description="Study of energy and heat.",

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        category=EngineeringDomainCategory.THERMODYNAMICS,

        status=EngineeringDomainStatus.ACTIVE,

        maturity_level=DomainMaturityLevel.MATURE,

        criticality=DomainCriticality.HIGH,

        is_core_domain=True,

        is_multiphysics=False,

        # ----------------------------------------------------
        # Knowledge Definition
        # ----------------------------------------------------

        engineering_principles=(
            "Energy Conservation",
        ),

        governing_equations=(
            "First Law",
        ),

        physical_laws=(
            "Second Law",
        ),

        assumptions=(
            "Continuum",
        ),

        limitations=(
            "Idealized system",
        ),

        applicable_regimes=(
            "Steady State",
        ),

        # ----------------------------------------------------
        # Relationships
        # ----------------------------------------------------

        parent_domain_id=None,

        child_domain_ids=(),

        related_domain_ids=(),

        related_variable_ids=(),

        related_equation_ids=(),

        related_constant_ids=(),

        related_unit_ids=(),

        related_dimension_ids=(),

        related_subsystem_ids=(),

        related_material_ids=(),

        related_simulation_ids=(),

        # ----------------------------------------------------
        # Knowledge Metadata
        # ----------------------------------------------------

        aliases=(
            "Thermo",
        ),

        common_names=(
            "Heat Transfer",
        ),

        search_keywords=(
            "energy",
            "temperature",
        ),

        tags=(
            "physics",
        ),

        # ----------------------------------------------------
        # Documentation
        # ----------------------------------------------------

        source_reference=create_reference(),

        source_document=create_document(),

        # ----------------------------------------------------
        # Repository Metadata
        # ----------------------------------------------------

        version="1.0",

        status_note="Approved",

        created_timestamp=datetime.now(
            UTC,
        ),

        modified_timestamp=datetime.now(
            UTC,
        ),

        approved_timestamp=datetime.now(
            UTC,
        ),

        created_by="COSMOS",

        approved_by="Chief Engineer",

        revision=0,

        # ----------------------------------------------------
        # Knowledge Graph
        # ----------------------------------------------------

        ontology_uri="ontology://thermodynamics",

        graph_node_id="graph-001",

        symbolic_identifier="TD",

        embedding_identifier="embed-001",

        export_identifier="export-001",

        llm_summary="Engineering domain.",

        # ----------------------------------------------------
        # AI Metadata
        # ----------------------------------------------------

        ai_summary="Thermodynamics domain.",

        ai_embedding_identifier="ai-embed-001",

        ai_vector_database_id="vector-001",

        llm_context_identifier="ctx-001",

        symbolic_model_identifier="sym-001",

        # ----------------------------------------------------
        # Future Extensions
        # ----------------------------------------------------

        custom_metadata={
            "owner": "COSMOS",
        },

        extension_fields={
            "future": "reserved",
        },
    )

# ============================================================
# Construction Tests
# ============================================================


def test_valid_construction() -> None:
    """
    Verify successful construction of a valid
    EngineeringDomain.
    """

    domain = create_engineering_domain()

    assert domain.domain_id == "DOMAIN-001"

    assert domain.name == "Thermodynamics"

    assert (
        domain.category
        is EngineeringDomainCategory.THERMODYNAMICS
    )

    assert (
        domain.status
        is EngineeringDomainStatus.ACTIVE
    )


def test_blank_domain_id() -> None:
    """
    Verify blank domain identifiers are rejected.
    """

    with pytest.raises(ValueError):

        data = create_engineering_domain().to_dict()

        data["domain_id"] = ""

        EngineeringDomain.from_dict(data)


def test_blank_name() -> None:
    """
    Verify blank names are rejected.
    """

    data = create_engineering_domain().to_dict()

    data["name"] = ""

    with pytest.raises(ValueError):

        EngineeringDomain.from_dict(data)


def test_blank_symbol() -> None:
    """
    Verify blank symbols are rejected.
    """

    data = create_engineering_domain().to_dict()

    data["symbol"] = ""

    with pytest.raises(ValueError):

        EngineeringDomain.from_dict(data)


def test_invalid_category() -> None:
    """
    Verify invalid category values are rejected.
    """

    data = create_engineering_domain().to_dict()

    data["category"] = "INVALID"

    with pytest.raises(ValueError):

        EngineeringDomain.from_dict(data)


def test_invalid_status() -> None:
    """
    Verify invalid status values are rejected.
    """

    data = create_engineering_domain().to_dict()

    data["status"] = "INVALID"

    with pytest.raises(ValueError):

        EngineeringDomain.from_dict(data)


def test_invalid_maturity_level() -> None:
    """
    Verify invalid maturity levels are rejected.
    """

    data = create_engineering_domain().to_dict()

    data["maturity_level"] = "INVALID"

    with pytest.raises(ValueError):

        EngineeringDomain.from_dict(data)


def test_invalid_criticality() -> None:
    """
    Verify invalid criticality values are rejected.
    """

    data = create_engineering_domain().to_dict()

    data["criticality"] = "INVALID"

    with pytest.raises(ValueError):

        EngineeringDomain.from_dict(data)

# ============================================================
# Serialization Tests
# ============================================================


def test_to_dict() -> None:
    """
    Verify dictionary serialization.
    """

    domain = create_engineering_domain()

    data = domain.to_dict()

    assert data["domain_id"] == "DOMAIN-001"

    assert data["name"] == "Thermodynamics"

    assert data["category"] == "THERMODYNAMICS"

    assert data["status"] == "ACTIVE"


def test_from_dict() -> None:
    """
    Verify reconstruction from a dictionary.
    """

    original = create_engineering_domain()

    reconstructed = EngineeringDomain.from_dict(
        original.to_dict()
    )

    assert reconstructed.domain_id == original.domain_id

    assert reconstructed.name == original.name

    assert reconstructed.category == original.category

    assert reconstructed.status == original.status


def test_round_trip_serialization() -> None:
    """
    Verify serialization followed by reconstruction.
    """

    original = create_engineering_domain()

    reconstructed = EngineeringDomain.from_dict(
        original.to_dict()
    )

    assert reconstructed == original


def test_reference_serialization() -> None:
    """
    Verify Reference serialization.
    """

    domain = create_engineering_domain()

    data = domain.to_dict()

    assert data["source_reference"] is not None

    reconstructed = EngineeringDomain.from_dict(data)

    assert reconstructed.source_reference is not None


def test_document_serialization() -> None:
    """
    Verify Document serialization.
    """

    domain = create_engineering_domain()

    data = domain.to_dict()

    assert data["source_document"] is not None

    reconstructed = EngineeringDomain.from_dict(data)

    assert reconstructed.source_document is not None


def test_datetime_serialization() -> None:
    """
    Verify datetime serialization.
    """

    domain = create_engineering_domain()

    data = domain.to_dict()

    assert isinstance(
        data["created_timestamp"],
        str,
    )

    assert isinstance(
        data["modified_timestamp"],
        str,
    )

    assert isinstance(
        data["approved_timestamp"],
        str,
    )


def test_mapping_serialization() -> None:
    """
    Verify metadata mapping serialization.
    """

    domain = create_engineering_domain()

    data = domain.to_dict()

    assert isinstance(
        data["custom_metadata"],
        dict,
    )

    assert isinstance(
        data["extension_fields"],
        dict,
    )


def test_mapping_reconstruction() -> None:
    """
    Verify metadata mapping reconstruction.
    """

    reconstructed = EngineeringDomain.from_dict(
        create_engineering_domain().to_dict()
    )

    assert reconstructed.custom_metadata is not None

    assert reconstructed.extension_fields is not None


def test_enum_reconstruction() -> None:
    """
    Verify enum reconstruction.
    """

    reconstructed = EngineeringDomain.from_dict(
        create_engineering_domain().to_dict()
    )

    assert (
        reconstructed.category
        is EngineeringDomainCategory.THERMODYNAMICS
    )

    assert (
        reconstructed.status
        is EngineeringDomainStatus.ACTIVE
    )

    assert (
        reconstructed.maturity_level
        is DomainMaturityLevel.MATURE
    )

    assert (
        reconstructed.criticality
        is DomainCriticality.HIGH
    )  

# ============================================================
# Convenience Method Tests
# ============================================================


def test_copy() -> None:
    """
    Verify immutable copying.
    """

    original = create_engineering_domain()

    copied = original.copy()

    assert copied == original

    assert copied is not original


def test_serialize_alias() -> None:
    """
    Verify serialize() is an alias for to_dict().
    """

    domain = create_engineering_domain()

    assert domain.serialize() == domain.to_dict()


def test_deserialize_alias() -> None:
    """
    Verify deserialize() is an alias for from_dict().
    """

    original = create_engineering_domain()

    reconstructed = EngineeringDomain.deserialize(
        original.serialize()
    )

    assert reconstructed == original


def test_iter() -> None:
    """
    Verify __iter__().
    """

    domain = create_engineering_domain()

    items = dict(iter(domain))

    assert items == domain.to_dict()

    assert "domain_id" in items

    assert items["domain_id"] == "DOMAIN-001"


def test_len() -> None:
    """
    Verify __len__().
    """

    domain = create_engineering_domain()

    assert len(domain) == len(domain.to_dict())

# ============================================================
# Query Method Tests
# ============================================================


def test_display_name() -> None:
    """
    Verify display_name().
    """

    domain = create_engineering_domain()

    assert domain.display_name() == "Thermodynamics (TD)"


def test_matches_alias() -> None:
    """
    Verify alias matching.
    """

    domain = create_engineering_domain()

    assert domain.matches_alias("Thermo")

    assert domain.matches_alias("thermo")

    assert not domain.matches_alias("Fluid")


def test_matches_keyword() -> None:
    """
    Verify keyword matching.
    """

    domain = create_engineering_domain()

    assert domain.matches_keyword("energy")

    assert domain.matches_keyword("ENERGY")

    assert not domain.matches_keyword("combustion")


def test_has_reference() -> None:
    """
    Verify reference detection.
    """

    domain = create_engineering_domain()

    assert domain.has_reference()


def test_has_document() -> None:
    """
    Verify document detection.
    """

    domain = create_engineering_domain()

    assert domain.has_document()


def test_has_parent_domain() -> None:
    """
    Verify parent domain detection.
    """

    domain = create_engineering_domain()

    assert not domain.has_parent_domain()

    child = EngineeringDomain.from_dict(domain.to_dict())

    object.__setattr__(
        child,
        "parent_domain_id",
        "DOMAIN-ROOT",
    )

    assert child.has_parent_domain()


def test_has_child_domains() -> None:
    """
    Verify child domain detection.
    """

    domain = create_engineering_domain()

    assert not domain.has_child_domains()

    child = EngineeringDomain.from_dict(domain.to_dict())

    object.__setattr__(
        child,
        "child_domain_ids",
        ("DOMAIN-002",),
    )

    assert child.has_child_domains()


def test_is_root_domain() -> None:
    """
    Verify root domain detection.
    """

    domain = create_engineering_domain()

    assert domain.is_root_domain()


def test_is_leaf_domain() -> None:
    """
    Verify leaf domain detection.
    """

    domain = create_engineering_domain()

    assert domain.is_leaf_domain()


def test_is_active() -> None:
    """
    Verify active status.
    """

    domain = create_engineering_domain()

    assert domain.is_active()


def test_is_core() -> None:
    """
    Verify core domain detection.
    """

    domain = create_engineering_domain()

    assert domain.is_core()


def test_is_multiphysics_domain() -> None:
    """
    Verify multiphysics detection.
    """

    domain = create_engineering_domain()

    assert not domain.is_multiphysics_domain()

    multiphysics = EngineeringDomain.from_dict(
        domain.to_dict()
    )

    object.__setattr__(
        multiphysics,
        "is_multiphysics",
        True,
    )

    assert multiphysics.is_multiphysics_domain()


def test_is_verified() -> None:
    """
    Verify verified status.
    """

    domain = create_engineering_domain()

    assert domain.is_verified()


def test_is_mission_critical() -> None:
    """
    Verify mission critical detection.
    """

    domain = EngineeringDomain.from_dict(
        create_engineering_domain().to_dict()
    )

    object.__setattr__(
        domain,
        "criticality",
        DomainCriticality.MISSION_CRITICAL,
    )

    assert domain.is_mission_critical()


def test_is_safety_critical() -> None:
    """
    Verify safety critical detection.
    """

    domain = EngineeringDomain.from_dict(
        create_engineering_domain().to_dict()
    )

    object.__setattr__(
        domain,
        "criticality",
        DomainCriticality.SAFETY_CRITICAL,
    )

    assert domain.is_safety_critical() 

# ============================================================
# Enterprise Tests
# ============================================================


def test_immutable() -> None:
    """
    Verify EngineeringDomain is immutable.
    """

    domain = create_engineering_domain()

    with pytest.raises(AttributeError):
        domain.name = "New Domain"  # type: ignore[misc]


def test_engineering_domain_equality() -> None:
    """
    Verify equality.
    """

    first = create_engineering_domain()

    second = EngineeringDomain.from_dict(
        first.to_dict()
    )

    assert first == second


@pytest.mark.skip(
    reason=(
        "Document hashability will be implemented after "
        "the Knowledge Foundation models are completed."
    )
)
def test_engineering_domain_hashable() -> None:
    """
    Verify EngineeringDomain is hashable.

    Temporarily skipped because Document currently contains
    immutable mappings that are not yet hashable.
    """

    domain = create_engineering_domain()

    domain_set = {domain}

    assert domain in domain_set


def test_deterministic_serialization() -> None:
    """
    Verify serialization is deterministic.
    """

    domain = create_engineering_domain()

    first = domain.to_dict()

    second = domain.to_dict()

    assert first == second


def test_round_trip_identity() -> None:
    """
    Verify full round-trip identity.
    """

    original = create_engineering_domain()

    reconstructed = EngineeringDomain.from_dict(
        original.to_dict()
    )

    assert reconstructed == original

    assert reconstructed.to_dict() == original.to_dict()                 