"""
Unit tests for knowledge.models.subsystem.



Construction and validation tests.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime
from datetime import timezone

import pytest # type: ignore

from knowledge.models.document import Document
from knowledge.models.document import DocumentType
from knowledge.models.reference import Reference
from knowledge.models.reference import ReferenceType
from knowledge.models.subsystem import CriticalityLevel
from knowledge.models.subsystem import Subsystem
from knowledge.models.subsystem import SubsystemCategory
from knowledge.models.subsystem import SubsystemStatus
from knowledge.models.subsystem import SystemLevel
from knowledge.models.subsystem import TechnologyReadinessLevel
from knowledge.models.variable import EngineeringDomain
from datetime import timezone


def create_reference() -> Reference:
    """Create a valid Reference for tests."""

    return Reference(
        reference_id="REF-001",
        reference_type=ReferenceType.NASA_REPORT,
        authors=("NASA",),
        title="Rocket Propulsion",
        publication_year=1971,
    )


def create_document() -> Document:
    """Create a valid Document for tests."""

    return Document(
        document_id="DOC-001",
        document_version_id="1.0",
        document_type=DocumentType.TECHNICAL_NOTE,
        title="Rocket Engineering",
        content="Engineering document.",
        reference=create_reference(),
    )


def create_subsystem() -> Subsystem:
    """Construct a minimal but valid Subsystem for tests."""

    now = datetime.now(timezone.utc)

    return Subsystem(
        subsystem_id="SUBSYS-001",
        name="Propulsion",
        short_name="PROP",
        symbol="PROP",
        description="Propulsion subsystem.",

        category=SubsystemCategory.PROPULSION,
        status=SubsystemStatus.ACTIVE,
        engineering_domain=EngineeringDomain.GENERAL,
        system_level=SystemLevel.SUBSYSTEM,
        criticality=CriticalityLevel.HIGH,
        technology_readiness_level=TechnologyReadinessLevel.TRL9,

        parent_subsystem_id=None,
        child_subsystem_ids=(),
        hierarchy_path=(),
        hierarchy_depth=0,

        engineering_disciplines=(),
        supported_physics=(),
        applicable_regimes=(),
        interfaces=(),
        design_constraints=(),
        requirements=(),

        aliases=("propulsion",),
        common_names=("propulsion subsystem",),
        search_keywords=("propulsion", "rocket"),
        tags=(),

        related_variable_ids=(),
        related_equation_ids=(),
        related_constant_ids=(),
        related_unit_ids=(),
        related_dimension_ids=(),
        related_material_ids=(),
        related_component_ids=(),
        related_simulation_ids=(),

        source_reference=create_reference(),
        source_document=create_document(),

        version="1.0",
        status_note="Approved",

        created_timestamp=now,
        modified_timestamp=now,
        approved_timestamp=now,

        created_by="COSMOS",
        approved_by="Chief Engineer",
        revision=1,

        ontology_uri=None,
        graph_node_id=None,
        symbolic_identifier=None,
        embedding_identifier=None,
        export_identifier=None,
        llm_summary=None,

        responsible_team=None,
        responsible_engineer=None,
        owning_organization=None,
        project_name=None,
        program_name=None,

        verification_status=None,
        validation_status=None,
        verification_method=None,
        verification_document_ids=(),
        test_case_ids=(),

        safety_classification=None,
        reliability_target=None,
        failure_mode_ids=(),
        hazard_ids=(),
        risk_ids=(),

        cad_model_ids=(),
        cfd_model_ids=(),
        fem_model_ids=(),
        optimization_case_ids=(),
        simulation_case_ids=(),
        digital_twin_identifier=None,

        manufacturing_processes=(),
        manufacturing_constraints=(),
        inspection_requirements=(),
        supplier_ids=(),

        repository_path=None,
        repository_identifier=None,
        knowledge_tags=(),
        ontology_terms=(),
        semantic_keywords=(),

        ai_summary=None,
        ai_embedding_identifier=None,
        ai_vector_database_id=None,
        llm_context_identifier=None,
        symbolic_model_identifier=None,

        custom_metadata=None,
        extension_fields=None,
    )

# ============================================================
# Serialization & Deserialization
# ============================================================


def test_to_dict() -> None:
    """
    Verify serialization to dictionary.
    """

    subsystem = create_subsystem()

    data = subsystem.to_dict()

    assert isinstance(data, dict)

    assert data["subsystem_id"] == "SUBSYS-001"

    assert data["name"] == "Propulsion"

    assert data["symbol"] == "PROP"

    assert (
        data["category"]
        == SubsystemCategory.PROPULSION.value
    )

    assert (
        data["status"]
        == SubsystemStatus.ACTIVE.value
    )


def test_from_dict() -> None:
    """
    Verify reconstruction from dictionary.
    """

    subsystem = create_subsystem()

    payload = subsystem.to_dict()

    reconstructed = Subsystem.from_dict(
        payload
    )

    assert (
        reconstructed.subsystem_id
        == subsystem.subsystem_id
    )

    assert (
        reconstructed.name
        == subsystem.name
    )

    assert (
        reconstructed.symbol
        == subsystem.symbol
    )


def test_round_trip_serialization() -> None:
    """
    Verify deterministic serialization.
    """

    subsystem = create_subsystem()

    reconstructed = (
        Subsystem.from_dict(
            subsystem.to_dict()
        )
    )

    assert (
        reconstructed.to_dict()
        == subsystem.to_dict()
    )


def test_reference_serialization() -> None:
    """
    Verify nested Reference serialization.
    """

    subsystem = create_subsystem()

    payload = subsystem.to_dict()

    assert (
        payload["source_reference"]
        is not None
    )


def test_document_serialization() -> None:
    """
    Verify nested Document serialization.
    """

    subsystem = create_subsystem()

    payload = subsystem.to_dict()

    assert (
        payload["source_document"]
        is not None
    )


def test_datetime_serialization() -> None:
    """
    Verify datetime serialization.
    """

    subsystem = create_subsystem()

    payload = subsystem.to_dict()

    assert isinstance(
        payload["created_timestamp"],
        str,
    )

    assert isinstance(
        payload["modified_timestamp"],
        str,
    )

    assert isinstance(
        payload["approved_timestamp"],
        str,
    )


def test_tuple_serialization() -> None:
    """
    Verify tuple fields become lists.
    """

    subsystem = create_subsystem()

    payload = subsystem.to_dict()

    assert isinstance(
        payload["aliases"],
        list,
    )

    assert isinstance(
        payload["child_subsystem_ids"],
        list,
    )

    assert isinstance(
        payload["engineering_disciplines"],
        list,
    )


def test_tuple_reconstruction() -> None:
    """
    Verify tuple reconstruction.
    """

    subsystem = create_subsystem()

    reconstructed = (
        Subsystem.from_dict(
            subsystem.to_dict()
        )
    )

    assert isinstance(
        reconstructed.aliases,
        tuple,
    )

    assert isinstance(
        reconstructed.child_subsystem_ids,
        tuple,
    )

    assert isinstance(
        reconstructed.engineering_disciplines,
        tuple,
    )


def test_enum_reconstruction() -> None:
    """
    Verify Enum reconstruction.
    """

    subsystem = create_subsystem()

    reconstructed = (
        Subsystem.from_dict(
            subsystem.to_dict()
        )
    )

    assert (
        reconstructed.category
        is SubsystemCategory.PROPULSION
    )

    assert (
        reconstructed.status
        is SubsystemStatus.ACTIVE
    )

    assert (
        reconstructed.system_level
        is SystemLevel.SUBSYSTEM
    )


def test_copy() -> None:
    """
    Verify immutable copy.
    """

    subsystem = create_subsystem()

    copied = subsystem.copy()

    assert copied == subsystem

    assert copied is not subsystem


def test_serialize_alias() -> None:
    """
    Verify serialize() alias.
    """

    subsystem = create_subsystem()

    assert (
        subsystem.serialize()
        == subsystem.to_dict()
    )


def test_deserialize_alias() -> None:
    """
    Verify deserialize() alias.
    """

    subsystem = create_subsystem()

    reconstructed = (
        Subsystem.deserialize(
            subsystem.to_dict()
        )
    )

    assert (
        reconstructed
        == subsystem
    )


def test_iter() -> None:
    """
    Verify iterator support.
    """

    subsystem = create_subsystem()

    items = list(subsystem)

    assert len(items) > 0

    assert isinstance(
        items[0],
        tuple,
    )


def test_len() -> None:
    """
    Verify serialized field count.
    """

    subsystem = create_subsystem()

    assert len(subsystem) == len(
        subsystem.to_dict()
    )

# ============================================================
# Query Methods
# ============================================================


def test_display_name() -> None:
    """Verify display_name()."""

    subsystem = create_subsystem()

    assert (
        subsystem.display_name()
        == "Propulsion (PROP)"
    )


def test_matches_alias() -> None:
    """Verify alias matching."""

    subsystem = create_subsystem()

    assert subsystem.matches_alias(
        "propulsion"
    )

    assert subsystem.matches_alias(
        "PROPULSION"
    )

    assert not subsystem.matches_alias(
        "Cooling"
    )


def test_matches_keyword() -> None:
    """Verify keyword matching."""

    subsystem = create_subsystem()

    assert subsystem.matches_keyword(
        "rocket"
    )

    assert subsystem.matches_keyword(
        "ROCKET"
    )

    assert not subsystem.matches_keyword(
        "battery"
    )


def test_has_reference() -> None:
    """Verify reference detection."""

    subsystem = create_subsystem()

    assert subsystem.has_reference()


def test_has_document() -> None:
    """Verify document detection."""

    subsystem = create_subsystem()

    assert subsystem.has_document()


def test_has_parent() -> None:
    """Verify parent detection."""

    subsystem = create_subsystem()

    assert not subsystem.has_parent()

    child = subsystem.copy()

    object.__setattr__(
        child,
        "parent_subsystem_id",
        "SUBSYS-ROOT",
    )

    assert child.has_parent()


def test_has_children() -> None:
    """Verify child detection."""

    subsystem = create_subsystem()

    assert not subsystem.has_children()

    parent = subsystem.copy()

    object.__setattr__(
        parent,
        "child_subsystem_ids",
        (
            "SUBSYS-002",
            "SUBSYS-003",
        ),
    )

    assert parent.has_children()


def test_is_root() -> None:
    """Verify root detection."""

    subsystem = create_subsystem()

    assert subsystem.is_root()


def test_is_leaf() -> None:
    """Verify leaf detection."""

    subsystem = create_subsystem()

    assert subsystem.is_leaf()

    parent = subsystem.copy()

    object.__setattr__(
        parent,
        "child_subsystem_ids",
        (
            "SUBSYS-002",
        ),
    )

    assert not parent.is_leaf()


def test_is_active() -> None:
    """Verify active status."""

    subsystem = create_subsystem()

    assert subsystem.is_active()


def test_is_verified() -> None:
    """Verify verified status."""

    subsystem = subsystem = create_subsystem()

    object.__setattr__(
        subsystem,
        "status",
        SubsystemStatus.VERIFIED,
    )

    assert subsystem.is_verified()


def test_is_mission_critical() -> None:
    """Verify mission critical classification."""

    subsystem = create_subsystem()

    object.__setattr__(
        subsystem,
        "criticality",
        CriticalityLevel.MISSION_CRITICAL,
    )

    assert (
        subsystem.is_mission_critical()
    )


def test_is_safety_critical() -> None:
    """Verify safety critical classification."""

    subsystem = create_subsystem()

    object.__setattr__(
        subsystem,
        "criticality",
        CriticalityLevel.SAFETY_CRITICAL,
    )

    assert (
        subsystem.is_safety_critical()
    )

# ============================================================
# Analysis Methods
# ============================================================


def test_child_count() -> None:
    """Verify child_count()."""

    subsystem = create_subsystem()

    assert subsystem.child_count() == 0

    parent = subsystem.copy()

    object.__setattr__(
        parent,
        "child_subsystem_ids",
        (
            "SUBSYS-002",
            "SUBSYS-003",
        ),
    )

    assert parent.child_count() == 2


def test_engineering_discipline_count() -> None:
    """Verify engineering discipline count."""

    subsystem = create_subsystem()

    assert (
        subsystem.engineering_discipline_count()
        == len(subsystem.engineering_disciplines)
    )


def test_supported_physics_count() -> None:
    """Verify supported physics count."""

    subsystem = create_subsystem()

    assert (
        subsystem.supported_physics_count()
        == len(subsystem.supported_physics)
    )


def test_applicable_regime_count() -> None:
    """Verify applicable regime count."""

    subsystem = create_subsystem()

    assert (
        subsystem.applicable_regime_count()
        == len(subsystem.applicable_regimes)
    )


def test_interface_count() -> None:
    """Verify interface count."""

    subsystem = create_subsystem()

    assert (
        subsystem.interface_count()
        == len(subsystem.interfaces)
    )


def test_requirement_count() -> None:
    """Verify requirement count."""

    subsystem = create_subsystem()

    assert (
        subsystem.requirement_count()
        == len(subsystem.requirements)
    )


def test_constraint_count() -> None:
    """Verify constraint count."""

    subsystem = create_subsystem()

    assert (
        subsystem.constraint_count()
        == len(subsystem.design_constraints)
    )


def test_relationship_count() -> None:
    """Verify relationship count."""

    subsystem = create_subsystem()

    expected = (
        len(subsystem.related_variable_ids)
        + len(subsystem.related_equation_ids)
        + len(subsystem.related_constant_ids)
        + len(subsystem.related_unit_ids)
        + len(subsystem.related_dimension_ids)
        + len(subsystem.related_material_ids)
        + len(subsystem.related_component_ids)
        + len(subsystem.related_simulation_ids)
    )

    assert (
        subsystem.relationship_count()
        == expected
    )


def test_alias_count() -> None:
    """Verify alias count."""

    subsystem = create_subsystem()

    assert (
        subsystem.alias_count()
        == len(subsystem.aliases)
    )


def test_common_name_count() -> None:
    """Verify common name count."""

    subsystem = create_subsystem()

    assert (
        subsystem.common_name_count()
        == len(subsystem.common_names)
    )


def test_keyword_count() -> None:
    """Verify keyword count."""

    subsystem = create_subsystem()

    assert (
        subsystem.keyword_count()
        == len(subsystem.search_keywords)
    )


def test_tag_count() -> None:
    """Verify tag count."""

    subsystem = create_subsystem()

    assert (
        subsystem.tag_count()
        == len(subsystem.tags)
    )


def test_knowledge_tag_count() -> None:
    """Verify knowledge tag count."""

    subsystem = create_subsystem()

    assert (
        subsystem.knowledge_tag_count()
        == len(subsystem.knowledge_tags)
    )


def test_ontology_term_count() -> None:
    """Verify ontology term count."""

    subsystem = create_subsystem()

    assert (
        subsystem.ontology_term_count()
        == len(subsystem.ontology_terms)
    )


def test_semantic_keyword_count() -> None:
    """Verify semantic keyword count."""

    subsystem = create_subsystem()

    assert (
        subsystem.semantic_keyword_count()
        == len(subsystem.semantic_keywords)
    )


def test_verification_document_count() -> None:
    """Verify verification document count."""

    subsystem = create_subsystem()

    assert (
        subsystem.verification_document_count()
        == len(subsystem.verification_document_ids)
    )


def test_test_case_count() -> None:
    """Verify test case count."""

    subsystem = create_subsystem()

    assert (
        subsystem.test_case_count()
        == len(subsystem.test_case_ids)
    )


def test_failure_mode_count() -> None:
    """Verify failure mode count."""

    subsystem = create_subsystem()

    assert (
        subsystem.failure_mode_count()
        == len(subsystem.failure_mode_ids)
    )


def test_hazard_count() -> None:
    """Verify hazard count."""

    subsystem = create_subsystem()

    assert (
        subsystem.hazard_count()
        == len(subsystem.hazard_ids)
    )


def test_risk_count() -> None:
    """Verify risk count."""

    subsystem = create_subsystem()

    assert (
        subsystem.risk_count()
        == len(subsystem.risk_ids)
    )


def test_cad_model_count() -> None:
    """Verify CAD model count."""

    subsystem = create_subsystem()

    assert (
        subsystem.cad_model_count()
        == len(subsystem.cad_model_ids)
    )


def test_cfd_model_count() -> None:
    """Verify CFD model count."""

    subsystem = create_subsystem()

    assert (
        subsystem.cfd_model_count()
        == len(subsystem.cfd_model_ids)
    )


def test_fem_model_count() -> None:
    """Verify FEM model count."""

    subsystem = create_subsystem()

    assert (
        subsystem.fem_model_count()
        == len(subsystem.fem_model_ids)
    )


def test_simulation_case_count() -> None:
    """Verify simulation case count."""

    subsystem = create_subsystem()

    assert (
        subsystem.simulation_case_count()
        == len(subsystem.simulation_case_ids)
    )


def test_optimization_case_count() -> None:
    """Verify optimization case count."""

    subsystem = create_subsystem()

    assert (
        subsystem.optimization_case_count()
        == len(subsystem.optimization_case_ids)
    )


def test_manufacturing_process_count() -> None:
    """Verify manufacturing process count."""

    subsystem = create_subsystem()

    assert (
        subsystem.manufacturing_process_count()
        == len(subsystem.manufacturing_processes)
    )


def test_supplier_count() -> None:
    """Verify supplier count."""

    subsystem = create_subsystem()

    assert (
        subsystem.supplier_count()
        == len(subsystem.supplier_ids)
    )


def test_hierarchy_size() -> None:
    """Verify hierarchy size."""

    subsystem = create_subsystem()

    assert subsystem.hierarchy_size() == 1

    parent = subsystem.copy()

    object.__setattr__(
        parent,
        "child_subsystem_ids",
        (
            "SUBSYS-002",
            "SUBSYS-003",
        ),
    )

    assert parent.hierarchy_size() == 3


def test_export_identifier_count() -> None:
    """Verify export identifier count."""

    subsystem = create_subsystem()

    assert (
        subsystem.export_identifier_count()
        == 0
    )

    modified = subsystem.copy()

    object.__setattr__(
        modified,
        "export_identifier",
        "EXPORT-001",
    )

    assert (
        modified.export_identifier_count()
        == 1
    )

# ============================================================
# Enterprise Behaviour
# ============================================================


def test_immutable() -> None:
    """
    Verify Subsystem is immutable.
    """

    subsystem = create_subsystem()

    with pytest.raises(
        (
            FrozenInstanceError,
            AttributeError,
        )
    ):
        subsystem.name = "Modified"  # type: ignore[misc]


def test_subsystem_equality() -> None:
    """
    Verify equality after deterministic
    round-trip reconstruction.
    """

    first = create_subsystem()

    second = Subsystem.from_dict(
        first.to_dict()
    )

    assert first == second


@pytest.mark.skip(
    reason=(
        "Hashability will be enabled after all "
        "Knowledge Foundation models become "
        "fully immutable."
    )
)
def test_subsystem_hashable() -> None:
    """
    Verify Subsystem is hashable.
    """

    subsystem = create_subsystem()

    subsystem_set = {subsystem}

    assert subsystem in subsystem_set


def test_deterministic_serialization() -> None:
    """
    Verify deterministic serialization.
    """

    subsystem = create_subsystem()

    first = subsystem.to_dict()

    second = subsystem.to_dict()

    assert first == second


def test_round_trip_identity() -> None:
    """
    Verify complete round-trip identity.
    """

    subsystem = create_subsystem()

    reconstructed = Subsystem.from_dict(
        subsystem.to_dict()
    )

    assert (
        reconstructed.to_dict()
        == subsystem.to_dict()
    )

def test_reference_identity() -> None:
    """
    Verify nested Reference survives
    round-trip serialization.
    """

    subsystem = create_subsystem()

    reconstructed = Subsystem.from_dict(
        subsystem.to_dict()
    )

    assert (
        reconstructed.source_reference
        == subsystem.source_reference
    )


def test_document_identity() -> None:
    """
    Verify nested Document survives
    round-trip serialization.
    """

    subsystem = create_subsystem()

    reconstructed = Subsystem.from_dict(
        subsystem.to_dict()
    )

    assert (
        reconstructed.source_document
        == subsystem.source_document
    )


def test_timestamp_identity() -> None:
    """
    Verify timestamps survive
    serialization.
    """

    subsystem = create_subsystem()

    reconstructed = Subsystem.from_dict(
        subsystem.to_dict()
    )

    assert (
        reconstructed.created_timestamp
        == subsystem.created_timestamp
    )

    assert (
        reconstructed.modified_timestamp
        == subsystem.modified_timestamp
    )

    assert (
        reconstructed.approved_timestamp
        == subsystem.approved_timestamp
    )


def test_enum_identity() -> None:
    """
    Verify Enum values survive
    serialization.
    """

    subsystem = create_subsystem()

    reconstructed = Subsystem.from_dict(
        subsystem.to_dict()
    )

    assert (
        reconstructed.category
        == subsystem.category
    )

    assert (
        reconstructed.status
        == subsystem.status
    )

    assert (
        reconstructed.system_level
        == subsystem.system_level
    )


def test_tuple_identity() -> None:
    """
    Verify tuple fields survive
    serialization.
    """

    subsystem = create_subsystem()

    reconstructed = Subsystem.from_dict(
        subsystem.to_dict()
    )

    assert (
        reconstructed.aliases
        == subsystem.aliases
    )

    assert (
        reconstructed.child_subsystem_ids
        == subsystem.child_subsystem_ids
    )

    assert (
        reconstructed.engineering_disciplines
        == subsystem.engineering_disciplines
    )


