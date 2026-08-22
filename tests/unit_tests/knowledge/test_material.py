"""
Unit tests for knowledge.models.material.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from typing import Any

import pytest # type: ignore[import]

from knowledge.models.document import Document
from knowledge.models.document import DocumentType
from knowledge.models.material import DomainCriticality
from knowledge.models.material import Material
from knowledge.models.material import MaterialCategory
from knowledge.models.material import MaterialClass
from knowledge.models.material import MaterialMaturityLevel
from knowledge.models.material import MaterialStatus
from knowledge.models.reference import Reference, ReferenceType

@pytest.fixture
def sample_reference() -> Reference:
    """
    Create a reusable Reference object.
    """

    return Reference(
        reference_id="REF-001",
        title="NASA Material Handbook",
        reference_type=ReferenceType.BOOK,
        authors=("NASA",),
        publication_year=2025,
    )

@pytest.fixture
def sample_document(
    sample_reference: Reference,
) -> Document:
    """
    Create a reusable Document object.
    """

    return Document(
        document_id="DOC-001",
        title="Material Specification",
        document_version_id="v1",
        document_type=DocumentType("SPECIFICATION"),
        reference=sample_reference,
        content="Material documentation.",
    )

def create_material(
    **overrides: object,
) -> Material:
    """
    Create a valid Material instance.

    Keyword arguments override the defaults.
    """

    defaults: dict[str, Any] = {

        # =====================================================
        # Identity
        # =====================================================

        "material_id": "MAT-001",

        "name": "GRCop-42",

        "short_name": "GRCop-42",

        "symbol": "CuCrNb",

        "chemical_formula": "Cu-Cr-Nb",

        "description": "Copper alloy.",

        # =====================================================
        # Classification
        # =====================================================

        "category": MaterialCategory.METAL,

        "material_class": MaterialClass.ALUMINUM_BASED,

        "status": MaterialStatus.ACTIVE,

        "maturity_level": MaterialMaturityLevel.RESEARCH,

        "criticality": DomainCriticality.HIGH,

        # =====================================================
        # Chemical
        # =====================================================

        "alloy_family": "Copper",

        "composition": {"Cu": 0.90, "Cr": 0.05, "Nb": 0.05},

        "uns_designation": "C18150",

        "astm_designation": None,

        "ams_designation": None,

        "nasa_designation": "GRCop-42",

        # =====================================================
        # Mechanical
        # =====================================================

        "density": 8890.0,

        "youngs_modulus": 128e9,

        "shear_modulus": 46e9,

        "bulk_modulus": 140e9,

        "poisson_ratio": 0.34,

        "yield_strength": 420e6,

        "ultimate_tensile_strength": 520e6,

        "compressive_strength": 600e6,

        "fatigue_strength": 250e6,

        "fracture_toughness": 45.0,

        "hardness": 160.0,

        # =====================================================
        # Thermal
        # =====================================================

        "melting_point": 1350.0,

        "thermal_conductivity": 320.0,

        "specific_heat_capacity": 385.0,

        "coefficient_thermal_expansion": 16.8e-6,

        "emissivity": 0.80,

        # =====================================================
        # Electrical
        # =====================================================

        "electrical_conductivity": 4.2e7,

        "electrical_resistivity": 2.4e-8,

        # =====================================================
        # Manufacturing
        # =====================================================

        "additive_manufacturing": True,

        "machinable": True,

        "weldable": True,

        "heat_treatable": True,

        "manufacturing_processes": (
            "LPBF",
            "HIP",
        ),

        # =====================================================
        # Compatibility
        # =====================================================

        "compatible_propellants": (
            "LOX",
            "LCH4",
        ),

        "corrosion_notes": None,

        "oxidation_behavior": None,

        "cryogenic_capable": True,

        "vacuum_compatible": True,

        # =====================================================
        # Knowledge Metadata
        # =====================================================

        "aliases": (),

        "common_names": (),

        "search_keywords": (),

        "tags": (),

        # =====================================================
        # Relationships
        # =====================================================

        "related_variable_ids": (),

        "related_equation_ids": (),

        "related_constant_ids": (),

        "related_unit_ids": (),

        "related_dimension_ids": (),

        "related_subsystem_ids": (),

        "related_engineering_domain_ids": (),

        "related_simulation_ids": (),

        # =====================================================
        # Documentation
        # =====================================================

        "source_reference": None,

        "source_document": None,

        # =====================================================
        # Repository
        # =====================================================

        "version": "1.0.0",

        "status_note": "",

        "created_timestamp": datetime.now(
            UTC,
        ),

        "modified_timestamp": None,

        "approved_timestamp": None,

        "created_by": "pytest",

        "approved_by": None,

        "revision": 1,

        "repository_path": None,

        "repository_identifier": None,

        # =====================================================
        # Knowledge Graph
        # =====================================================

        "ontology_uri": None,

        "graph_node_id": None,

        "symbolic_identifier": None,

        "embedding_identifier": None,

        "export_identifier": None,

        "llm_summary": None,

        # =====================================================
        # Engineering Ownership
        # =====================================================

        "responsible_team": None,

        "responsible_engineer": None,

        "owning_organization": None,

        "project_name": None,

        "program_name": None,

        # =====================================================
        # Verification
        # =====================================================

        "verification_status": None,

        "validation_status": None,

        "verification_method": None,

        "verification_document_ids": (),

        "test_case_ids": (),

        # =====================================================
        # AI Metadata
        # =====================================================

        "ai_summary": None,

        "ai_embedding_identifier": None,

        "ai_vector_database_id": None,

        "llm_context_identifier": None,

        "symbolic_model_identifier": None,

        # =====================================================
        # Extensions
        # =====================================================

        "custom_metadata": None,

        "extension_fields": None,
    }

    defaults.update(overrides)

    return Material(
        **defaults,
    )

# ============================================================
# Constructor Tests
# ============================================================


def test_create_material_default() -> None:
    """
    Verify that a default Material can be created.
    """

    material = create_material()

    assert material.material_id == "MAT-001"
    assert material.name == "GRCop-42"
    assert material.status is MaterialStatus.ACTIVE


def test_material_identity_fields() -> None:
    """
    Verify identity fields are stored correctly.
    """

    material = create_material(
        material_id="MAT-100",
        name="Inconel 718",
        short_name="IN718",
        symbol="Ni",
    )

    assert material.material_id == "MAT-100"
    assert material.name == "Inconel 718"
    assert material.short_name == "IN718"
    assert material.symbol == "Ni"


def test_material_classification_fields() -> None:
    """
    Verify classification fields.
    """

    material = create_material(
        category=MaterialCategory.METAL,
        material_class=MaterialClass.ALUMINUM_BASED,
        status=MaterialStatus.ACTIVE,
        maturity_level=MaterialMaturityLevel.RESEARCH,
        criticality=DomainCriticality.HIGH,
    )

    assert material.category is MaterialCategory.METAL
    assert material.material_class is MaterialClass.ALUMINUM_BASED
    assert material.status is MaterialStatus.ACTIVE
    assert (
        material.maturity_level
        is MaterialMaturityLevel.RESEARCH
    )
    assert (
        material.criticality
        is DomainCriticality.HIGH
    )


def test_material_mechanical_properties() -> None:
    """
    Verify mechanical properties.
    """

    material = create_material(
        density=8900.0,
        youngs_modulus=120e9,
        yield_strength=450e6,
    )

    assert material.density == 8900.0
    assert material.youngs_modulus == 120e9
    assert material.yield_strength == 450e6


def test_material_thermal_properties() -> None:
    """
    Verify thermal properties.
    """

    material = create_material(
        melting_point=1400.0,
        thermal_conductivity=350.0,
    )

    assert material.melting_point == 1400.0
    assert material.thermal_conductivity == 350.0


def test_material_electrical_properties() -> None:
    """
    Verify electrical properties.
    """

    material = create_material(
        electrical_conductivity=5.0e7,
        electrical_resistivity=2.1e-8,
    )

    assert material.electrical_conductivity == 5.0e7
    assert material.electrical_resistivity == 2.1e-8


def test_material_manufacturing_properties() -> None:
    """
    Verify manufacturing metadata.
    """

    material = create_material(
        additive_manufacturing=True,
        machinable=False,
        manufacturing_processes=(
            "LPBF",
            "HIP",
        ),
    )

    assert material.additive_manufacturing is True
    assert material.machinable is False
    assert material.manufacturing_processes == (
        "LPBF",
        "HIP",
    )


def test_material_compatibility_properties() -> None:
    """
    Verify compatibility metadata.
    """

    material = create_material(
        compatible_propellants=(
            "LOX",
            "RP-1",
        ),
        cryogenic_capable=True,
        vacuum_compatible=False,
    )

    assert material.compatible_propellants == (
        "LOX",
        "RP-1",
    )

    assert material.cryogenic_capable is True
    assert material.vacuum_compatible is False


def test_material_metadata_fields() -> None:
    """
    Verify metadata collections.
    """

    material = create_material(
        aliases=("Copper",),
        search_keywords=("Rocket", "Engine"),
        tags=("NASA", "Copper Alloy"),
    )

    assert material.aliases == ("Copper",)

    assert material.search_keywords == (
        "Rocket",
        "Engine",
    )

    assert material.tags == (
        "NASA",
        "Copper Alloy",
    )


def test_material_relationship_fields() -> None:
    """
    Verify relationship collections.
    """

    material = create_material(
        related_variable_ids=("VAR-1",),
        related_equation_ids=("EQ-1",),
        related_subsystem_ids=("SUB-1",),
    )

    assert material.related_variable_ids == (
        "VAR-1",
    )

    assert material.related_equation_ids == (
        "EQ-1",
    )

    assert material.related_subsystem_ids == (
        "SUB-1",
    )


def test_material_documentation_fields(
    sample_reference: Reference,
    sample_document: Document,
) -> None:
    """
    Verify documentation references.
    """

    material = create_material(
        source_reference=sample_reference,
        source_document=sample_document,
    )

    assert material.source_reference is sample_reference
    assert material.source_document is sample_document


def test_material_repository_fields() -> None:
    """
    Verify repository metadata.
    """

    material = create_material(
        version="2.0.0",
        revision=5,
        created_by="engineer",
    )

    assert material.version == "2.0.0"
    assert material.revision == 5
    assert material.created_by == "engineer"


def test_material_knowledge_graph_fields() -> None:
    """
    Verify knowledge graph metadata.
    """

    material = create_material(
        graph_node_id="NODE-001",
        ontology_uri="ontology://material",
        symbolic_identifier="MAT_SYMBOL",
    )

    assert material.graph_node_id == "NODE-001"

    assert (
        material.ontology_uri
        == "ontology://material"
    )

    assert (
        material.symbolic_identifier
        == "MAT_SYMBOL"
    )


def test_material_engineering_ownership_fields() -> None:
    """
    Verify engineering ownership fields.
    """

    material = create_material(
        responsible_team="Materials",
        responsible_engineer="John Doe",
        project_name="RLV",
    )

    assert material.responsible_team == "Materials"
    assert (
        material.responsible_engineer
        == "John Doe"
    )

    assert material.project_name == "RLV"


def test_material_verification_fields() -> None:
    """
    Verify verification metadata.
    """

    material = create_material(
        verification_status="Verified",
        validation_status="Validated",
        verification_document_ids=("DOC-1",),
        test_case_ids=("TEST-1",),
    )

    assert (
        material.verification_status
        == "Verified"
    )

    assert (
        material.validation_status
        == "Validated"
    )

    assert (
        material.verification_document_ids
        == ("DOC-1",)
    )

    assert material.test_case_ids == (
        "TEST-1",
    )


def test_material_ai_metadata_fields() -> None:
    """
    Verify AI metadata.
    """

    material = create_material(
        ai_summary="Copper alloy",
        ai_embedding_identifier="EMBED-001",
        llm_context_identifier="CTX-001",
    )

    assert material.ai_summary == "Copper alloy"

    assert (
        material.ai_embedding_identifier
        == "EMBED-001"
    )

    assert (
        material.llm_context_identifier
        == "CTX-001"
    )


def test_material_extension_fields() -> None:
    """
    Verify extension metadata.
    """

    material = create_material(
        custom_metadata={
            "source": "NASA",
        },
        extension_fields={
            "vendor": "Vendor A",
        },
    )

    assert material.custom_metadata == {
        "source": "NASA",
    }

    assert material.extension_fields == {
        "vendor": "Vendor A",
    }

# ============================================================
# Validation Tests
# ============================================================


def test_validate_valid_material() -> None:
    """
    Verify that a valid Material passes validation.
    """

    material = create_material()

    material.validate()


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        ("material_id", ""),
        ("name", ""),
        ("version", ""),
        ("created_by", ""),
    ],
)
def test_required_string_fields(
    field: str,
    value: object,
) -> None:
    """
    Required string fields shall not be empty.
    """

    kwargs = {
        field: value,
    }

    with pytest.raises(
        ValueError,
    ):
        create_material(
            **kwargs,
        )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        ("density", -1.0),
        ("youngs_modulus", -1.0),
        ("shear_modulus", -1.0),
        ("bulk_modulus", -1.0),
        ("yield_strength", -1.0),
        ("ultimate_tensile_strength", -1.0),
        ("compressive_strength", -1.0),
        ("fatigue_strength", -1.0),
        ("fracture_toughness", -1.0),
        ("hardness", -1.0),
    ],
)
def test_negative_mechanical_properties(
    field: str,
    value: float,
) -> None:
    """
    Mechanical properties shall not be negative.
    """

    kwargs = {
        field: value,
    }

    with pytest.raises(
        ValueError,
    ):
        create_material(
            **kwargs,
        )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        ("melting_point", -10.0),
        ("thermal_conductivity", -1.0),
        ("specific_heat_capacity", -1.0),
        ("coefficient_thermal_expansion", -1.0),
        ("emissivity", -0.1),
    ],
)
def test_negative_thermal_properties(
    field: str,
    value: float,
) -> None:
    """
    Thermal properties shall not be negative.
    """

    kwargs = {
        field: value,
    }

    with pytest.raises(
        ValueError,
    ):
        create_material(
            **kwargs,
        )


def test_emissivity_above_one() -> None:
    """
    Emissivity shall not exceed one.
    """

    with pytest.raises(
        ValueError,
    ):
        create_material(
            emissivity=1.2,
        )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        ("electrical_conductivity", -1.0),
        ("electrical_resistivity", -1.0),
    ],
)
def test_negative_electrical_properties(
    field: str,
    value: float,
) -> None:
    """
    Electrical properties shall not be negative.
    """

    kwargs = {
        field: value,
    }

    with pytest.raises(
        ValueError,
    ):
        create_material(
            **kwargs,
        )


def test_invalid_poisson_ratio_negative() -> None:
    """
    Poisson ratio shall not be below zero.
    """

    with pytest.raises(
        ValueError,
    ):
        create_material(
            poisson_ratio=-0.2,
        )


def test_invalid_poisson_ratio_above_limit() -> None:
    """
    Poisson ratio shall not exceed 0.5.
    """

    with pytest.raises(
        ValueError,
    ):
        create_material(
            poisson_ratio=0.75,
        )


def test_invalid_category_type() -> None:
    """
    Category must be an enum.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            category="Metal",
        )


def test_invalid_material_class_type() -> None:
    """
    Material class must be an enum.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            material_class="Alloy",
        )


def test_invalid_status_type() -> None:
    """
    Status must be an enum.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            status="Active",
        )


def test_invalid_maturity_level_type() -> None:
    """
    Maturity level must be an enum.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            maturity_level="Production",
        )


def test_invalid_criticality_type() -> None:
    """
    Criticality must be an enum.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            criticality="High",
        )


def test_invalid_revision() -> None:
    """
    Revision shall be positive.
    """

    with pytest.raises(
        ValueError,
    ):
        create_material(
            revision=-1,
        )


def test_invalid_alias_type() -> None:
    """
    Aliases shall be immutable tuples.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            aliases="Copper",
        )


def test_invalid_keyword_type() -> None:
    """
    Search keywords shall be immutable tuples.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            search_keywords="Rocket",
        )


def test_invalid_tags_type() -> None:
    """
    Tags shall be immutable tuples.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            tags="NASA",
        )


def test_invalid_custom_metadata_type() -> None:
    """
    Custom metadata shall be a mapping.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            custom_metadata=[],
        )


def test_invalid_extension_fields_type() -> None:
    """
    Extension fields shall be a mapping.
    """

    with pytest.raises(
        TypeError,
    ):
        create_material(
            extension_fields=[],
        )

# ============================================================
# Serialization Tests
# ============================================================


def test_to_dict_returns_dictionary() -> None:
    """
    Verify to_dict() returns a dictionary.
    """

    material = create_material()

    data = material.to_dict()

    assert isinstance(
        data,
        dict,
    )


def test_to_dict_identity_fields() -> None:
    """
    Verify identity fields are serialized.
    """

    material = create_material()

    data = material.to_dict()

    assert data["material_id"] == material.material_id
    assert data["name"] == material.name
    assert data["short_name"] == material.short_name
    assert data["symbol"] == material.symbol
    assert (
        data["chemical_formula"]
        == material.chemical_formula
    )


def test_to_dict_classification_fields() -> None:
    """
    Verify enum fields serialize correctly.
    """

    material = create_material()

    data = material.to_dict()

    assert (
        data["category"]
        == material.category.value
    )

    assert (
        data["material_class"]
        == material.material_class.value
    )

    assert (
        data["status"]
        == material.status.value
    )

    assert (
        data["maturity_level"]
        == material.maturity_level.value
    )

    assert (
        data["criticality"]
        == material.criticality.value
    )


def test_to_dict_mechanical_properties() -> None:
    """
    Verify mechanical properties serialize.
    """

    material = create_material()

    data = material.to_dict()

    assert (
        data["density"]
        == material.density
    )

    assert (
        data["youngs_modulus"]
        == material.youngs_modulus
    )

    assert (
        data["yield_strength"]
        == material.yield_strength
    )


def test_to_dict_thermal_properties() -> None:
    """
    Verify thermal properties serialize.
    """

    material = create_material()

    data = material.to_dict()

    assert (
        data["melting_point"]
        == material.melting_point
    )

    assert (
        data["thermal_conductivity"]
        == material.thermal_conductivity
    )


def test_to_dict_electrical_properties() -> None:
    """
    Verify electrical properties serialize.
    """

    material = create_material()

    data = material.to_dict()

    assert (
        data["electrical_conductivity"]
        == material.electrical_conductivity
    )

    assert (
        data["electrical_resistivity"]
        == material.electrical_resistivity
    )


def test_to_dict_manufacturing() -> None:
    """
    Verify manufacturing fields serialize.
    """

    material = create_material()

    data = material.to_dict()

    assert (
        data["manufacturing_processes"]
        == list(
            material.manufacturing_processes
        )
    )


def test_to_dict_relationships() -> None:
    """
    Verify relationship collections serialize.
    """

    material = create_material(
        related_variable_ids=(
            "VAR1",
            "VAR2",
        ),
    )

    data = material.to_dict()

    assert (
        data["related_variable_ids"]
        == [
            "VAR1",
            "VAR2",
        ]
    )


def test_to_dict_metadata() -> None:
    """
    Verify metadata collections serialize.
    """

    material = create_material(
        aliases=(
            "Copper",
        ),
        tags=(
            "NASA",
        ),
    )

    data = material.to_dict()

    assert data["aliases"] == [
        "Copper",
    ]

    assert data["tags"] == [
        "NASA",
    ]


def test_to_dict_reference_serialization(
    sample_reference: Reference,
) -> None:
    """
    Verify Reference objects serialize.
    """

    material = create_material(
        source_reference=sample_reference,
    )

    data = material.to_dict()

    assert isinstance(
        data["source_reference"],
        dict,
    )


def test_to_dict_document_serialization(
    sample_document: Document,
) -> None:
    """
    Verify Document objects serialize.
    """

    material = create_material(
        source_document=sample_document,
    )

    data = material.to_dict()

    assert isinstance(
        data["source_document"],
        dict,
    )


def test_to_dict_datetime_serialization() -> None:
    """
    Verify datetime objects serialize to ISO-8601.
    """

    timestamp = datetime.now(
        UTC,
    )

    material = create_material(
        created_timestamp=timestamp,
    )

    data = material.to_dict()

    assert (
        data["created_timestamp"]
        == timestamp.isoformat()
    )


def test_to_dict_mapping_serialization() -> None:
    """
    Verify mapping fields serialize.
    """

    material = create_material(
        custom_metadata={
            "source": "NASA",
        },
    )

    data = material.to_dict()

    assert (
        data["custom_metadata"]
        == {
            "source": "NASA",
        }
    )


def test_serialize_returns_dictionary() -> None:
    """
    Verify serialize() returns a dictionary.
    """

    material = create_material()

    serialized = material.serialize()

    assert isinstance(
        serialized,
        dict,
    )


def test_serialize_matches_to_dict() -> None:
    """
    Verify serialize() delegates to to_dict().
    """

    material = create_material()

    assert (
        material.serialize()
        == material.to_dict()
    )


def test_serialization_is_deterministic() -> None:
    """
    Serializing twice shall produce identical results.
    """

    material = create_material()

    assert (
        material.to_dict()
        == material.to_dict()
    )


def test_serialization_preserves_none_values() -> None:
    """
    Optional None fields shall remain None.
    """

    material = create_material(
        approved_by=None,
        ontology_uri=None,
    )

    data = material.to_dict()

    assert (
        data["approved_by"]
        is None
    )

    assert (
        data["ontology_uri"]
        is None
    )

# ============================================================
# Deserialization Tests
# ============================================================


def test_from_dict_returns_material() -> None:
    """
    Verify from_dict() returns a Material instance.
    """

    material = create_material()

    data = material.to_dict()

    reconstructed = Material.from_dict(
        data,
    )

    assert isinstance(
        reconstructed,
        Material,
    )


def test_round_trip_serialization() -> None:
    """
    Verify serialization/deserialization round-trip.
    """

    original = create_material()

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert (
        reconstructed.to_dict()
        == original.to_dict()
    )


def test_deserialize_identity_fields() -> None:
    """
    Verify identity fields are reconstructed.
    """

    original = create_material()

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert reconstructed.material_id == original.material_id
    assert reconstructed.name == original.name
    assert reconstructed.short_name == original.short_name
    assert reconstructed.symbol == original.symbol
    assert (
        reconstructed.chemical_formula
        == original.chemical_formula
    )


def test_deserialize_classification() -> None:
    """
    Verify enum reconstruction.
    """

    reconstructed = Material.from_dict(
        create_material().to_dict(),
    )

    assert isinstance(
        reconstructed.category,
        MaterialCategory,
    )

    assert isinstance(
        reconstructed.material_class,
        MaterialClass,
    )

    assert isinstance(
        reconstructed.status,
        MaterialStatus,
    )

    assert isinstance(
        reconstructed.maturity_level,
        MaterialMaturityLevel,
    )

    assert isinstance(
        reconstructed.criticality,
        DomainCriticality,
    )


def test_deserialize_mechanical_properties() -> None:
    """
    Verify mechanical properties.
    """

    original = create_material()

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert reconstructed.density == original.density
    assert (
        reconstructed.youngs_modulus
        == original.youngs_modulus
    )

    assert (
        reconstructed.yield_strength
        == original.yield_strength
    )


def test_deserialize_thermal_properties() -> None:
    """
    Verify thermal properties.
    """

    original = create_material()

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert (
        reconstructed.melting_point
        == original.melting_point
    )

    assert (
        reconstructed.thermal_conductivity
        == original.thermal_conductivity
    )


def test_deserialize_electrical_properties() -> None:
    """
    Verify electrical properties.
    """

    original = create_material()

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert (
        reconstructed.electrical_conductivity
        == original.electrical_conductivity
    )

    assert (
        reconstructed.electrical_resistivity
        == original.electrical_resistivity
    )


def test_deserialize_manufacturing() -> None:
    """
    Verify manufacturing collections.
    """

    reconstructed = Material.from_dict(
        create_material().to_dict(),
    )

    assert isinstance(
        reconstructed.manufacturing_processes,
        tuple,
    )


def test_deserialize_relationships() -> None:
    """
    Verify relationship collections.
    """

    original = create_material(
        related_variable_ids=(
            "VAR1",
            "VAR2",
        ),
    )

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert (
        reconstructed.related_variable_ids
        == (
            "VAR1",
            "VAR2",
        )
    )


def test_deserialize_metadata() -> None:
    """
    Verify metadata collections.
    """

    original = create_material(
        aliases=("Copper",),
        tags=("NASA",),
    )

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert reconstructed.aliases == (
        "Copper",
    )

    assert reconstructed.tags == (
        "NASA",
    )


def test_deserialize_reference(
    sample_reference: Reference,
) -> None:
    """
    Verify Reference reconstruction.
    """

    original = create_material(
        source_reference=sample_reference,
    )

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert isinstance(
        reconstructed.source_reference,
        Reference,
    )


def test_deserialize_document(
    sample_document: Document,
) -> None:
    """
    Verify Document reconstruction.
    """

    original = create_material(
        source_document=sample_document,
    )

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert isinstance(
        reconstructed.source_document,
        Document,
    )


def test_deserialize_datetime() -> None:
    """
    Verify datetime reconstruction.
    """

    original = create_material()

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert isinstance(
        reconstructed.created_timestamp,
        datetime,
    )


def test_deserialize_mapping() -> None:
    """
    Verify mapping reconstruction.
    """

    original = create_material(
        custom_metadata={
            "key": "value",
        },
    )

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert (
        reconstructed.custom_metadata
        == {
            "key": "value",
        }
    )


def test_deserialize_none_values() -> None:
    """
    Verify optional None values remain None.
    """

    original = create_material(
        approved_by=None,
        ontology_uri=None,
    )

    reconstructed = Material.from_dict(
        original.to_dict(),
    )

    assert reconstructed.approved_by is None
    assert reconstructed.ontology_uri is None


def test_deserialize_invalid_category() -> None:
    """
    Invalid enum values shall raise ValueError.
    """

    data = create_material().to_dict()

    data["category"] = "INVALID"

    with pytest.raises(
        ValueError,
    ):
        Material.from_dict(
            data,
        )


def test_deserialize_missing_required_field() -> None:
    """
    Missing required fields shall raise KeyError.
    """

    data = create_material().to_dict()

    del data["material_id"]

    with pytest.raises(
        KeyError,
    ):
        Material.from_dict(
            data,
        )


def test_deserialize_invalid_numeric_type() -> None:
    """
    Invalid numeric values shall raise TypeError.
    """

    data = create_material().to_dict()

    data["density"] = "high"

    with pytest.raises(
        TypeError,
    ):
        Material.from_dict(
            data,
        )


def test_deserialize_wrapper() -> None:
    """
    Verify deserialize() delegates to from_dict().
    """

    material = create_material()

    reconstructed = Material.deserialize(
        material.to_dict(),
    )

    assert isinstance(
        reconstructed,
        Material,
    )


def test_deserialize_wrapper_matches_from_dict() -> None:
    """
    deserialize() shall match from_dict().
    """

    material = create_material()

    assert (
        Material.deserialize(
            material.to_dict(),
        ).to_dict()
        ==
        Material.from_dict(
            material.to_dict(),
        ).to_dict()
    )

# ============================================================
# Convenience Method Tests
# ============================================================


def test_copy_returns_new_instance() -> None:
    """
    Verify copy() returns a new Material instance.
    """

    material = create_material()

    copied = material.copy()

    assert copied is not material
    assert copied == material


def test_copy_round_trip() -> None:
    """
    Verify copied Material serializes identically.
    """

    material = create_material()

    copied = material.copy()

    assert copied.to_dict() == material.to_dict()


def test_iter_returns_serialized_items() -> None:
    """
    Verify __iter__ delegates to to_dict().
    """

    material = create_material()

    assert dict(material) == material.to_dict()


def test_len_matches_serialized_dictionary() -> None:
    """
    Verify __len__ delegates to to_dict().
    """

    material = create_material()

    assert len(material) == len(material.to_dict())


def test_serialize_deserialize_cycle() -> None:
    """
    Verify serialize()/deserialize() round-trip.
    """

    material = create_material()

    reconstructed = Material.deserialize(
        material.serialize(),
    )

    assert reconstructed.to_dict() == material.to_dict()


# ============================================================
# Query Method Tests
# ============================================================


def test_display_name_prefers_short_name() -> None:
    """
    Verify display_name() prefers short_name.
    """

    material = create_material(
        short_name="GRCop-42",
    )

    assert material.display_name() == "GRCop-42"

    def test_display_name_falls_back_to_name() -> None:

     def display_name(self) -> str:
        """
        Get the display name of the material.

        Returns:
            str: The short name if available, otherwise the full name.
        """
        return self.short_name or self.name


def test_matches_alias_true() -> None:
    """
    Verify alias lookup succeeds.
    """

    material = create_material(
        aliases=(
            "Copper Alloy",
            "GRCOP42",
        ),
    )

    assert material.matches_alias(
        "grcop42",
    )


def test_matches_alias_false() -> None:
    """
    Verify alias lookup fails.
    """

    material = create_material()

    assert not material.matches_alias(
        "Titanium",
    )


def test_matches_keyword_true() -> None:
    """
    Verify keyword lookup succeeds.
    """

    material = create_material(
        search_keywords=(
            "Rocket",
            "Cryogenic",
        ),
    )

    assert material.matches_keyword(
        "rocket",
    )


def test_matches_keyword_false() -> None:
    """
    Verify keyword lookup fails.
    """

    material = create_material()

    assert not material.matches_keyword(
        "Automobile",
    )


def test_has_reference() -> None:
    """
    Verify has_reference().
    """

    material = create_material()

    assert not material.has_reference()


def test_has_document() -> None:
    """
    Verify has_document().
    """

    material = create_material()

    assert not material.has_document()


def test_is_active() -> None:
    """
    Verify is_active().
    """

    material = create_material()

    assert material.is_active()


def test_is_verified_true() -> None:
    """
    Verify verified materials.
    """

    material = create_material(
        verification_status="Verified",
    )

    assert material.is_verified()


def test_is_verified_false() -> None:
    """
    Verify unverified materials.
    """

    material = create_material(
        verification_status="Pending",
    )

    assert not material.is_verified()


def test_is_cryogenic_capable() -> None:
    """
    Verify cryogenic capability.
    """

    material = create_material(
        cryogenic_capable=True,
    )

    assert material.is_cryogenic_capable()


def test_is_vacuum_compatible() -> None:
    """
    Verify vacuum compatibility.
    """

    material = create_material(
        vacuum_compatible=True,
    )

    assert material.is_vacuum_compatible()


# ============================================================
# Analysis Method Tests
# ============================================================


def test_alias_count() -> None:
    """
    Verify alias_count().
    """

    material = create_material(
        aliases=("A", "B", "C"),
    )

    assert material.alias_count() == 3


def test_keyword_count() -> None:
    """
    Verify keyword_count().
    """

    material = create_material(
        search_keywords=(
            "Rocket",
            "Cryogenic",
        ),
    )

    assert material.keyword_count() == 2


def test_tag_count() -> None:
    """
    Verify tag_count().
    """

    material = create_material(
        tags=("A", "B"),
    )

    assert material.tag_count() == 2


def test_manufacturing_process_count() -> None:
    """
    Verify manufacturing_process_count().
    """

    material = create_material(
        manufacturing_processes=(
            "LPBF",
            "HIP",
            "Machining",
        ),
    )

    assert (
        material.manufacturing_process_count()
        == 3
    )


def test_compatible_propellant_count() -> None:
    """
    Verify compatible_propellant_count().
    """

    material = create_material(
        compatible_propellants=(
            "LOX",
            "LCH4",
            "LH2",
        ),
    )

    assert (
        material.compatible_propellant_count()
        == 3
    )


def test_relationship_count() -> None:
    """
    Verify relationship_count().
    """

    material = create_material(
        related_variable_ids=("V1",),
        related_equation_ids=("E1",),
        related_constant_ids=("C1",),
        related_unit_ids=("U1",),
        related_dimension_ids=("D1",),
        related_subsystem_ids=("S1",),
        related_engineering_domain_ids=("ED1",),
        related_simulation_ids=("SIM1",),
    )

    assert (
        material.relationship_count()
        == 8
    )


def test_verification_document_count() -> None:
    """
    Verify verification_document_count().
    """

    material = create_material(
        verification_document_ids=(
            "DOC1",
            "DOC2",
        ),
    )

    assert (
        material.verification_document_count()
        == 2
    )


def test_test_case_count() -> None:
    """
    Verify test_case_count().
    """

    material = create_material(
        test_case_ids=(
            "TEST1",
            "TEST2",
            "TEST3",
        ),
    )

    assert (
        material.test_case_count()
        == 3
    )

# ============================================================
# Edge Case Tests
# ============================================================


def test_empty_material_collections() -> None:
    """
    Verify empty tuple collections are handled correctly.
    """

    material = create_material(
        aliases=(),
        search_keywords=(),
        tags=(),
        manufacturing_processes=(),
        compatible_propellants=(),
    )

    assert material.alias_count() == 0
    assert material.keyword_count() == 0
    assert material.tag_count() == 0
    assert (
        material.manufacturing_process_count()
        == 0
    )
    assert (
        material.compatible_propellant_count()
        == 0
    )


def test_optional_fields_none() -> None:
    """
    Verify optional fields accept None.
    """

    material = create_material(
        source_reference=None,
        source_document=None,
        approved_by=None,
        ontology_uri=None,
        graph_node_id=None,
        ai_summary=None,
    )

    assert material.source_reference is None
    assert material.source_document is None
    assert material.approved_by is None
    assert material.ontology_uri is None
    assert material.graph_node_id is None
    assert material.ai_summary is None


def test_empty_mapping_fields() -> None:
    """
    Verify empty mapping fields.
    """

    material = create_material(
        custom_metadata={},
        extension_fields={},
    )

    assert material.custom_metadata == {}
    assert material.extension_fields == {}


def test_large_relationship_lists() -> None:
    """
    Verify large relationship collections.
    """

    values = tuple(
        f"VAR{i}"
        for i in range(
            100,
        )
    )

    material = create_material(
        related_variable_ids=values,
    )

    assert (
        len(
            material.related_variable_ids
        )
        == 100
    )


def test_material_is_immutable() -> None:
    """
    Verify Material is immutable.
    """

    material = create_material()

    with pytest.raises(
        AttributeError,
    ):
        material.name = "Changed" # type: ignore[misc]


def test_copy_preserves_immutability() -> None:
    """
    Verify copied object is also immutable.
    """

    copied = create_material().copy()

    with pytest.raises(
        AttributeError,
    ):
        copied.name = "Changed" # type: ignore[misc]


def test_round_trip_with_optional_fields_none() -> None:
    """
    Verify serialization round-trip with None values.
    """

    material = create_material(
        approved_by=None,
        ontology_uri=None,
        ai_summary=None,
    )

    reconstructed = Material.from_dict(
        material.to_dict(),
    )

    assert (
        reconstructed.to_dict()
        == material.to_dict()
    )


def test_relationship_count_empty() -> None:
    """
    Verify relationship_count() with no relationships.
    """

    material = create_material()

    assert (
        material.relationship_count()
        == 0
    )


# ============================================================
# Regression Tests
# ============================================================


def test_multiple_serialization_cycles() -> None:
    """
    Verify repeated serialization is stable.
    """

    material = create_material()

    for _ in range(
        10,
    ):

        material = Material.from_dict(
            material.to_dict(),
        )

    assert (
        material.material_id
        == "MAT-001"
    )


def test_copy_serialization_regression() -> None:
    """
    Verify copy() never changes serialized output.
    """

    material = create_material()

    copied = material.copy()

    assert (
        copied.serialize()
        == material.serialize()
    )


def test_dictionary_conversion_regression() -> None:
    """
    Verify dict(Material) remains identical to to_dict().
    """

    material = create_material()

    assert (
        dict(material)
        == material.to_dict()
    )


def test_len_regression() -> None:
    """
    Verify __len__ remains synchronized with serialization.
    """

    material = create_material()

    assert (
        len(material)
        == len(material.serialize())
    )


def test_deserialize_serialize_regression() -> None:
    """
    Verify deserialize/serialize consistency.
    """

    material = create_material()

    reconstructed = Material.deserialize(
        material.serialize(),
    )

    assert (
        reconstructed.serialize()
        == material.serialize()
    )


def test_display_name_regression() -> None:
    """
    Verify display_name() remains deterministic.
    """

    material = create_material()

    assert (
        material.display_name()
        == material.display_name()
    )


def test_hash_equality_regression() -> None:
    """
    Verify equal Materials remain equal after round-trip.
    """

    material = create_material()

    reconstructed = Material.from_dict(
        material.to_dict(),
    )

    assert material == reconstructed


def test_serialization_is_idempotent() -> None:
    """
    Verify serialization is idempotent.
    """

    material = create_material()

    first = material.to_dict()

    second = Material.from_dict(
        first,
    ).to_dict()

    assert first == second