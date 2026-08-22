"""
COSMOS Knowledge Foundation

Quantity Model

Represents a scientific or engineering quantity together with
its numerical representation, dimensional information,
knowledge graph relationships, engineering ownership,
verification status, and AI metadata.
"""


from __future__ import annotations

import math
import re
from collections import OrderedDict
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, fields
from dataclasses import replace as dataclass_replace
from datetime import UTC, datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, cast

from knowledge.models.dimension import Dimension
from knowledge.models.document import Document
from knowledge.models.engineering_domain import EngineeringDomain
from knowledge.models.reference import Reference
from knowledge.models.subsystem import Subsystem
from knowledge.models.unit import QuantityType, Unit
from knowledge.models.variable import Variable

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9\s\-()/.,:+]*$")
_SYMBOL_PATTERN = re.compile(
    r"^[A-Za-zΑ-Ωα-ωµμρστυφχψωΔΩλγβηξπΣΠΘΦΨΧν\d_./°%+\-*^()]*$")


class QuantityCategory(str, Enum):
    """
    High-level classification of engineering quantities.
    """

    SCALAR = "SCALAR"

    VECTOR = "VECTOR"

    TENSOR = "TENSOR"

    FIELD = "FIELD"

    DIMENSIONLESS = "DIMENSIONLESS"


class MeasurementType(str, Enum):
    """
    Origin of the quantity value.
    """

    MEASURED = "MEASURED"

    CALCULATED = "CALCULATED"

    ESTIMATED = "ESTIMATED"

    SIMULATED = "SIMULATED"

    DERIVED = "DERIVED"

    EMPIRICAL = "EMPIRICAL"


class QuantityStatus(str, Enum):
    """
    Lifecycle status.
    """

    DRAFT = "DRAFT"

    ACTIVE = "ACTIVE"

    VERIFIED = "VERIFIED"

    VALIDATED = "VALIDATED"

    DEPRECATED = "DEPRECATED"

    ARCHIVED = "ARCHIVED"


class QuantityCriticality(str, Enum):
    """
    Engineering importance.
    """

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"

    SAFETY_CRITICAL = "SAFETY_CRITICAL"


class ValueRepresentation(str, Enum):
    """
    Representation of the stored value.
    """

    EXACT = "EXACT"

    APPROXIMATE = "APPROXIMATE"

    RANGE = "RANGE"

    STATISTICAL = "STATISTICAL"

    EXPERIMENTAL = "EXPERIMENTAL"

# ==============================================================================
# Quantity
# ==============================================================================


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Quantity:
    """
    Enterprise representation of a scientific or engineering quantity.

    A Quantity is considerably richer than a simple numerical value.
    It represents a physical quantity together with its engineering
    semantics, dimensional information, knowledge graph relationships,
    traceability, verification metadata, and AI metadata.

    The Quantity model forms one of the core abstractions of the
    COSMOS Knowledge Foundation and is intended to support:

    - Scientific calculations
    - Engineering analysis
    - Equation solving
    - Knowledge graph construction
    - AI-assisted reasoning
    - Traceability
    - Digital engineering workflows

    Notes
    -----
    All numerical values shall use SI units internally unless explicitly
    documented otherwise.

    All instances are immutable.

    Dynamic attribute creation is prohibited through ``slots=True``.
    """

    # -------------------------------------------------------------------------
    # Phase 0.5.10A Section 3
    # Identity Fields
    # -------------------------------------------------------------------------

    quantity_id: str
    """
    Globally unique identifier for the quantity.
    Example:
        QTY-000001
    """

    name: str
    """
    Human-readable engineering name.

    Example:
        Chamber Pressure
    """

    short_name: str
    """
    Canonical engineering short name.

    Example:
        Pc
    """

    symbol: str
    """
    Mathematical symbol.

    Example:
        P
        T
        rho
        mdot
    """

    description: str
    """
    Detailed engineering description.
    """

    aliases: tuple[str, ...] = ()
    """
    Alternative names used throughout literature.
    """

    search_keywords: tuple[str, ...] = ()
    """
    Keywords used by the search engine.
    """

    tags: tuple[str, ...] = ()
    """
    User-defined semantic tags.
    """

    # ==========================================================================
    # Scientific Classification
    # ==========================================================================

    category: QuantityCategory
    """
    Scalar, Vector, Tensor, etc.
    """

    measurement_type: MeasurementType
    """
    Measured, Calculated, Simulated, etc.
    """

    status: QuantityStatus
    """
    Lifecycle status.
    """

    criticality: QuantityCriticality
    """
    Engineering importance.
    """

    value_representation: ValueRepresentation
    """
    Exact, Approximate, Range, etc.
    """

    physical_quantity_name: str
    """
    Name of the SI physical quantity.

    Example:
        Pressure
        Temperature
        Density
    """

    physical_quantity_symbol: str
    """
    Standard scientific symbol.

    Example:
        P
        T
        ρ
    """

    si_quantity: bool = True
    """
    Indicates whether the quantity follows SI conventions.
    """

    derived_quantity: bool = False
    """
    True if this quantity is derived from other quantities.
    """

    vector_quantity: bool = False
    """
    Indicates whether the quantity represents a vector.
    """

    tensor_quantity: bool = False
    """
    Indicates whether the quantity represents a tensor.
    """

    dimensionless: bool = False
    """
    Indicates whether the quantity is dimensionless.
    """

    # ==========================================================================
    # Numerical Representation
    # ==========================================================================

    value: float
    """
    Primary numerical value of the quantity.
    """

    nominal_value: float | None = None
    """
    Nominal engineering value.
    """

    minimum_value: float | None = None
    """
    Minimum physically allowable value.
    """

    maximum_value: float | None = None
    """
    Maximum physically allowable value.
    """

    lower_bound: float | None = None
    """
    Lower engineering constraint.
    """

    upper_bound: float | None = None
    """
    Upper engineering constraint.
    """

    design_value: float | None = None
    """
    Engineering design value.
    """

    operating_value: float | None = None
    """
    Normal operating value.
    """

    rated_value: float | None = None
    """
    Rated value.
    """

    limit_value: float | None = None
    """
    Absolute engineering limit.
    """

    failure_value: float | None = None
    """
    Value beyond which failure occurs.
    """

    # ==========================================================================
    # Units & Dimensions
    # ==========================================================================

    unit: Unit

    dimension: Dimension

    preferred_unit: Unit | None = None

    display_unit: Unit | None = None

    conversion_unit: Unit | None = None

    # ==========================================================================
    # Precision
    # ==========================================================================

    uncertainty: float | None = None
    """
    Absolute uncertainty.
    """

    relative_uncertainty: float | None = None
    """
    Relative uncertainty (0-1).
    """

    confidence_level: float | None = None
    """
    Confidence level.

    Example:
        0.95
    """

    standard_deviation: float | None = None

    variance: float | None = None

    significant_figures: int | None = None

    decimal_places: int | None = None

    precision: float | None = None

    resolution: float | None = None

    tolerance_plus: float | None = None

    tolerance_minus: float | None = None

    tolerance_percent: float | None = None

    # ==========================================================================
    # Scientific Characteristics
    # ==========================================================================

    exact_value: bool = False

    experimentally_verified: bool = False

    analytically_verified: bool = False

    numerically_verified: bool = False

    simulated_value: bool = False

    estimated_value: bool = False

    measured_value: bool = False

    calculated_value: bool = False

    reference_value: bool = False

    benchmark_value: bool = False

    # ==========================================================================
    # Physical Constraints
    # ==========================================================================

    strictly_positive: bool = False

    non_negative: bool = False

    integer_only: bool = False

    finite_only: bool = True

    allow_nan: bool = False

    allow_infinity: bool = False

    monotonic: bool = False

    normalized: bool = False

    logarithmic_scale: bool = False

    cyclic_quantity: bool = False

    periodic_quantity: bool = False

    # ==========================================================================
    # Numerical Metadata
    # ==========================================================================

    default_value: float | None = None

    initial_value: float | None = None

    previous_value: float | None = None

    expected_value: float | None = None

    target_value: float | None = None

    measured_timestamp: datetime | None = None

    last_updated: datetime = datetime.now(
        UTC,
    )

    # ==========================================================================
    # Knowledge Foundation Relationships
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Scientific Relationships
    # --------------------------------------------------------------------------

    variable: Variable | None = None
    """
    Variable represented by this quantity.
    """

    related_variable_ids: tuple[str, ...] = ()
    """
    Related variables.
    """

    related_constant_ids: tuple[str, ...] = ()
    """
    Related engineering constants.
    """

    related_quantity_ids: tuple[str, ...] = ()
    """
    Related quantities.
    """

    related_dimension_ids: tuple[str, ...] = ()
    """
    Related dimensions.
    """

    related_unit_ids: tuple[str, ...] = ()
    """
    Related units.
    """

    related_equation_ids: tuple[str, ...] = ()
    """
    Equations using this quantity.
    """

    related_physical_law_ids: tuple[str, ...] = ()
    """
    Physical laws referencing this quantity.
    """

    related_correlation_ids: tuple[str, ...] = ()
    """
    Engineering correlations using this quantity.
    """

    related_empirical_relation_ids: tuple[str, ...] = ()
    """
    Empirical relations.
    """

    # --------------------------------------------------------------------------
    # Engineering Relationships
    # --------------------------------------------------------------------------

    engineering_domain: EngineeringDomain | None = None
    """
    Primary engineering discipline.
    """

    subsystem: Subsystem | None = None
    """
    Primary subsystem.
    """

    related_engineering_domain_ids: tuple[str, ...] = ()
    """
    Related engineering domains.
    """

    related_subsystem_ids: tuple[str, ...] = ()
    """
    Related subsystems.
    """

    related_material_ids: tuple[str, ...] = ()
    """
    Materials associated with this quantity.
    """

    related_component_ids: tuple[str, ...] = ()
    """
    Components associated with this quantity.
    """

    related_property_ids: tuple[str, ...] = ()
    """
    Engineering properties associated with this quantity.
    """

    related_process_ids: tuple[str, ...] = ()
    """
    Engineering processes.
    """

    related_manufacturing_process_ids: tuple[str, ...] = ()
    """
    Manufacturing processes.
    """

    related_boundary_condition_ids: tuple[str, ...] = ()
    """
    Boundary conditions.
    """

    related_assumption_ids: tuple[str, ...] = ()
    """
    Engineering assumptions.
    """

    related_failure_mode_ids: tuple[str, ...] = ()
    """
    Failure modes.
    """

    related_design_rule_ids: tuple[str, ...] = ()
    """
    Design rules.
    """

    # --------------------------------------------------------------------------
    # Simulation Relationships
    # --------------------------------------------------------------------------

    related_simulation_ids: tuple[str, ...] = ()
    """
    Simulations producing or consuming this quantity.
    """

    related_experiment_ids: tuple[str, ...] = ()
    """
    Experimental investigations.
    """

    validation_dataset_ids: tuple[str, ...] = ()
    """
    Validation datasets.
    """

    benchmark_dataset_ids: tuple[str, ...] = ()
    """
    Benchmark datasets.
    """

    # --------------------------------------------------------------------------
    # Knowledge Traceability
    # --------------------------------------------------------------------------

    source_reference: Reference | None = None
    """
    Primary bibliographic reference.
    """

    source_document: Document | None = None
    """
    Primary source document.
    """

    supporting_reference_ids: tuple[str, ...] = ()
    """
    Additional references supporting the quantity.
    """

    supporting_document_ids: tuple[str, ...] = ()
    """
    Additional supporting documents.
    """

    citation_ids: tuple[str, ...] = ()
    """
    Citation identifiers.
    """

    bibliography_entries: tuple[str, ...] = ()
    """
    Bibliographic references.
    """

    external_reference_ids: tuple[str, ...] = ()
    """
    External database identifiers.
    """

    doi: str | None = None
    """
    DOI of the primary source, if applicable.
    """

    source_url: str | None = None
    """
    Original source URL.
    """

    source_section: str | None = None
    """
    Section of the source document.
    """

    source_page: str | None = None
    """
    Page reference.
    """

    source_equation_number: str | None = None
    """
    Source equation identifier.
    """

    # ==========================================================================
    # Repository Metadata
    # ==========================================================================

    version: str = "1.0.0"
    """
    Object schema version.
    """

    revision: int = 1
    """
    Internal revision number.
    """

    revision_notes: str | None = None
    """
    Summary of changes introduced in this revision.
    """

    created_by: str = "COSMOS"
    """
    Creator of the quantity.
    """

    created_timestamp: datetime = datetime.now(
        UTC,
    )
    """
    Creation timestamp (UTC).
    """

    modified_by: str | None = None
    """
    Last user or process modifying the quantity.
    """

    modified_timestamp: datetime | None = None
    """
    Last modification timestamp.
    """

    approved_by: str | None = None
    """
    Engineering approver.
    """

    approved_timestamp: datetime | None = None
    """
    Approval timestamp.
    """

    reviewed_by: str | None = None
    """
    Engineering reviewer.
    """

    reviewed_timestamp: datetime | None = None
    """
    Review timestamp.
    """

    repository_identifier: str | None = None
    """
    Repository-specific identifier.

    Example:
        REPO-QTY-000124
    """

    repository_path: str | None = None
    """
    Logical repository location.

    Example:
        knowledge/thermodynamics/pressure/
    """

    repository_branch: str | None = None
    """
    Repository branch.

    Example:
        main
        development
        feature/cryogenics
    """

    baseline_identifier: str | None = None
    """
    Engineering configuration baseline.
    """

    configuration_identifier: str | None = None
    """
    Configuration-management identifier.
    """

    lifecycle_state: str | None = None
    """
    Current engineering lifecycle state.

    Examples:
        Draft
        Released
        Deprecated
    """

    change_request_identifier: str | None = None
    """
    Engineering change request.
    """

    change_order_identifier: str | None = None
    """
    Engineering change order.
    """

    release_identifier: str | None = None
    """
    Software or engineering release identifier.
    """

    checksum: str | None = None
    """
    Object checksum used for integrity verification.
    """

    export_identifier: str | None = None
    """
    Export identifier used by downstream systems.
    """

    import_identifier: str | None = None
    """
    Identifier from the originating system.
    """

    archived: bool = False
    """
    Indicates whether this quantity has been archived.
    """

    locked: bool = False
    """
    Indicates whether editing is prohibited.
    """

    read_only: bool = False
    """
    Indicates whether the quantity is read-only.
    """

    # ==========================================================================
    # Knowledge Graph Metadata
    # ==========================================================================

    graph_node_id: str | None = None
    """
    Globally unique knowledge graph node identifier.
    """

    graph_namespace: str = "COSMOS"
    """
    Knowledge graph namespace.
    """

    ontology_identifier: str | None = None
    """
    Ontology identifier.

    Example:
        ontology.quantity.pressure
    """

    ontology_uri: str | None = None
    """
    URI of the ontology entity.
    """

    ontology_version: str | None = None
    """
    Ontology version.
    """

    semantic_identifier: str | None = None
    """
    Globally unique semantic identifier.
    """

    symbolic_identifier: str | None = None
    """
    Mathematical symbolic identifier.

    Example:
        Pc
        mdot
        T0
    """

    canonical_identifier: str | None = None
    """
    Canonical engineering identifier.
    """

    universal_identifier: str | None = None
    """
    Stable identifier across repositories.
    """

    namespace_identifier: str | None = None
    """
    Namespace identifier.
    """

    graph_label: str | None = None
    """
    Human-readable graph label.
    """

    graph_category: str = "Quantity"
    """
    Graph node category.
    """

    graph_type: str = "ScientificQuantity"
    """
    Knowledge graph type.
    """

    parent_node_identifier: str | None = None
    """
    Parent graph node.
    """

    root_node_identifier: str | None = None
    """
    Root ontology node.
    """

    child_node_identifiers: tuple[str, ...] = ()
    """
    Child graph nodes.
    """

    incoming_relationship_identifiers: tuple[str, ...] = ()
    """
    Incoming graph edges.
    """

    outgoing_relationship_identifiers: tuple[str, ...] = ()
    """
    Outgoing graph edges.
    """

    semantic_tags: tuple[str, ...] = ()
    """
    Ontology semantic tags.
    """

    ontology_classes: tuple[str, ...] = ()
    """
    Ontology class membership.
    """

    ontology_superclasses: tuple[str, ...] = ()
    """
    Parent ontology classes.
    """

    ontology_subclasses: tuple[str, ...] = ()
    """
    Child ontology classes.
    """

    inferred_relationships: tuple[str, ...] = ()
    """
    AI or ontology inferred relationships.
    """

    reasoning_enabled: bool = True
    """
    Indicates whether reasoning engines
    may infer relationships involving
    this quantity.
    """

    searchable: bool = True
    """
    Indicates whether this node should
    participate in semantic search.
    """

    indexable: bool = True
    """
    Indicates whether this node should
    participate in indexing.
    """

    graph_embedding_identifier: str | None = None
    """
    Identifier of graph embedding.
    """

    semantic_embedding_identifier: str | None = None
    """
    Identifier of semantic embedding.
    """

    vector_database_identifier: str | None = None
    """
    External vector database identifier.
    """

    ontology_metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    Additional ontology metadata.
    """

    graph_metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    Additional graph metadata.
    """

    # ==========================================================================
    # Engineering Ownership
    # ==========================================================================

    responsible_team: str | None = None
    """
    Engineering team responsible for this quantity.

    Example:
        Propulsion Team
    """

    responsible_engineer: str | None = None
    """
    Primary engineer responsible for the quantity.
    """

    technical_lead: str | None = None
    """
    Technical lead responsible for approval.
    """

    chief_engineer: str | None = None
    """
    Chief engineer responsible for this engineering area.
    """

    owning_department: str | None = None
    """
    Department owning this quantity.
    """

    owning_organization: str | None = None
    """
    Organization responsible for maintaining this quantity.
    """

    project_name: str | None = None
    """
    Engineering project.

    Example:
        COSMOS RLV
    """

    project_identifier: str | None = None
    """
    Project identifier.
    """

    program_name: str | None = None
    """
    Engineering program.

    Example:
        Reusable Launch Vehicle
    """

    program_identifier: str | None = None
    """
    Program identifier.
    """

    mission_name: str | None = None
    """
    Mission associated with the quantity.
    """

    mission_identifier: str | None = None
    """
    Mission identifier.
    """

    vehicle_name: str | None = None
    """
    Vehicle using this quantity.
    """

    vehicle_identifier: str | None = None
    """
    Vehicle identifier.
    """

    component_owner: str | None = None
    """
    Component owner.
    """

    subsystem_owner: str | None = None
    """
    Subsystem owner.
    """

    engineering_discipline: str | None = None
    """
    Primary engineering discipline.

    Examples:
        Thermodynamics
        Propulsion
        Structures
    """

    engineering_phase: str | None = None
    """
    Engineering lifecycle phase.

    Examples:
        Concept
        Preliminary Design
        Critical Design
        Qualification
        Flight
    """

    maturity_level: str | None = None
    """
    Engineering maturity level.
    """

    technology_readiness_level: int | None = None
    """
    Technology Readiness Level (TRL).

    Valid values:
        1–9
    """

    manufacturing_readiness_level: int | None = None
    """
    Manufacturing Readiness Level (MRL).

    Valid values:
        1–10
    """

    operational_readiness_level: int | None = None
    """
    Operational Readiness Level (ORL).
    """

    configuration_owner: str | None = None
    """
    Configuration owner.
    """

    export_controlled: bool = False
    """
    Indicates whether the quantity is subject to
    export control regulations.
    """

    proprietary: bool = False
    """
    Indicates whether the quantity is proprietary.
    """

    classified: bool = False
    """
    Indicates whether the quantity contains
    classified information.
    """

    safety_critical: bool = False
    """
    Indicates whether the quantity is
    safety critical.
    """

    mission_critical: bool = False
    """
    Indicates whether the quantity is
    mission critical.
    """

    flight_critical: bool = False
    """
    Indicates whether the quantity is
    flight critical.
    """

    quality_level: str | None = None
    """
    Engineering quality classification.
    """

    certification_authority: str | None = None
    """
    Organization responsible for certification.
    """

    certification_identifier: str | None = None
    """
    Certification reference identifier.
    """

    engineering_notes: str | None = None
    """
    Engineering notes associated with this quantity.
    """

    # ==========================================================================
    # Verification & Validation
    # ==========================================================================

    verification_status: str | None = None
    """
    Verification status.

    Examples:
        Pending
        Verified
        Failed
    """

    validation_status: str | None = None
    """
    Validation status.

    Examples:
        Pending
        Validated
        Rejected
    """

    verification_method: str | None = None
    """
    Verification method.

    Examples:
        Analytical
        Numerical
        Software Test
        Inspection
    """

    validation_method: str | None = None
    """
    Validation method.

    Examples:
        Experiment
        Hot Fire Test
        NASA Benchmark
        CFD Comparison
    """

    verification_reference: Reference | None = None
    """
    Primary verification reference.
    """

    validation_reference: Reference | None = None
    """
    Primary validation reference.
    """

    verification_document: Document | None = None
    """
    Verification document.
    """

    validation_document: Document | None = None
    """
    Validation document.
    """

    verification_date: datetime | None = None
    """
    Date of verification.
    """

    validation_date: datetime | None = None
    """
    Date of validation.
    """

    verified_by: str | None = None
    """
    Engineer performing verification.
    """

    validated_by: str | None = None
    """
    Engineer performing validation.
    """

    reviewer: str | None = None
    """
    Independent technical reviewer.
    """

    approver: str | None = None
    """
    Engineering approver.
    """

    verification_level: str | None = None
    """
    Engineering verification level.
    """

    validation_level: str | None = None
    """
    Engineering validation level.
    """

    confidence_score: float | None = None
    """
    Engineering confidence score.

    Expected range:
        0.0 - 1.0
    """

    evidence_score: float | None = None
    """
    Strength of supporting evidence.

    Expected range:
        0.0 - 1.0
    """

    quality_score: float | None = None
    """
    Overall engineering quality score.

    Expected range:
        0.0 - 1.0
    """

    uncertainty_verified: bool = False
    """
    Indicates whether uncertainty has been verified.
    """

    units_verified: bool = False
    """
    Indicates whether units have been verified.
    """

    dimensions_verified: bool = False
    """
    Indicates whether dimensions have been verified.
    """

    equation_verified: bool = False
    """
    Indicates whether governing equations
    have been verified.
    """

    experimentally_validated: bool = False
    """
    Indicates whether experimental validation
    exists.
    """

    independently_verified: bool = False
    """
    Indicates whether an independent verification
    has been completed.
    """

    peer_reviewed: bool = False
    """
    Indicates whether this quantity has undergone
    peer review.
    """

    benchmarked: bool = False
    """
    Indicates whether benchmark data exists.
    """

    certified: bool = False
    """
    Indicates whether the quantity is certified
    for engineering use.
    """

    traceable: bool = True
    """
    Indicates whether complete engineering
    traceability exists.
    """

    assumptions_verified: bool = False
    """
    Indicates whether all engineering assumptions
    have been verified.
    """

    verification_notes: str | None = None
    """
    Engineering verification notes.
    """

    validation_notes: str | None = None
    """
    Engineering validation notes.
    """

    evidence_summary: str | None = None
    """
    Summary of supporting engineering evidence.
    """

    known_limitations: str | None = None
    """
    Known engineering limitations.
    """

    recommended_usage: str | None = None
    """
    Engineering recommendations for use.
    """

    prohibited_usage: str | None = None
    """
    Engineering scenarios where this quantity
    should not be used.
    """

    # ==========================================================================
    # AI Metadata
    # ==========================================================================

    llm_summary: str | None = None
    """
    AI-generated summary of the quantity.

    This field is informational only and shall never be treated
    as engineering truth.
    """

    engineering_summary: str | None = None
    """
    Human-reviewed engineering summary.
    """

    extracted_keywords: tuple[str, ...] = ()
    """
    Keywords extracted from source documents.
    """

    semantic_keywords: tuple[str, ...] = ()
    """
    AI-generated semantic keywords.
    """

    embedding_identifier: str | None = None
    """
    Identifier of the semantic embedding.
    """

    embedding_model: str | None = None
    """
    Embedding model used to generate vectors.
    """

    embedding_version: str | None = None
    """
    Version of the embedding model.
    """

    embedding_timestamp: datetime | None = None
    """
    Timestamp of embedding generation.
    """

    vector_dimension: int | None = None
    """
    Dimension of the embedding vector.
    """

    ai_confidence: float | None = None
    """
    Confidence score assigned by AI.

    Expected range:
        0.0–1.0
    """

    ai_verified: bool = False
    """
    Indicates whether AI-generated metadata has been
    reviewed by an engineer.
    """

    semantic_similarity_threshold: float | None = None
    """
    Similarity threshold used during semantic retrieval.
    """

    retrieval_score: float | None = None
    """
    Retrieval relevance score.
    """

    ontology_alignment_score: float | None = None
    """
    Alignment score with the engineering ontology.
    """

    reasoning_score: float | None = None
    """
    Confidence score assigned by the reasoning engine.
    """

    searchable_by_ai: bool = True
    """
    Indicates whether AI systems may index this quantity.
    """

    semantic_indexed: bool = False
    """
    Indicates whether semantic indexing has been completed.
    """

    graph_indexed: bool = False
    """
    Indicates whether graph indexing has been completed.
    """

    ai_annotations: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    AI-generated annotations.

    These annotations are informative only and must not
    replace engineering metadata.
    """

    ai_metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    Additional AI metadata.
    """

    # ==========================================================================
    # Extension Fields
    # ==========================================================================

    custom_metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    User-defined metadata.

    Reserved for future extensions while maintaining
    forward compatibility.
    """

    extension_fields: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    Vendor- or application-specific extension fields.
    """

    custom_attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    Additional engineering attributes not covered by the
    core schema.
    """

    plugin_metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    """
    Metadata used by COSMOS plugins and external tools.
    """

    external_identifiers: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    """
    Mapping of identifiers used by external systems.

    Example:
        {
            "NASA": "...",
            "NIST": "...",
            "ANSYS": "...",
        }
    }

    """

    # ==========================================================================
    # Internal Metadata
    # ==========================================================================

    schema_version: str = "1.0.0"
    """
    Quantity schema version.
    """

    cosmos_version: str = "0.1"
    """
    Minimum COSMOS version supporting this schema.
    """

    # ==========================================================================
    # Dataclass Lifecycle
    # ==========================================================================

    def __post_init__(self) -> None:
        """
        Validate the quantity after construction.

        Because Quantity is an immutable dataclass, every invariant must be
        verified immediately after instantiation.
        """
        self.validate()

    # ==========================================================================
    # Public Validation API
    # ==========================================================================

    def validate(self) -> None:
        """
        Validate all quantity metadata.

        Validation is performed in deterministic stages so that failures are
        reproducible and easy to diagnose.
        """

        self._validate_identity()

        self._validate_classification()

        self._validate_numerical_representation()

        self._validate_units_and_dimension()

        self._validate_relationships()

        self._validate_repository_metadata()

        self._validate_graph_metadata()

        self._validate_engineering_metadata()

        self._validate_verification_metadata()

        self._validate_ai_metadata()

        self._validate_extensions()

        self._validate_cross_consistency()

        # ------------------------------------------------------------------
        # quantity_id
        # ------------------------------------------------------------------

        if not isinstance(self.quantity_id, str):
            raise TypeError(
                "quantity_id must be a string."
            )

        if not self.quantity_id.strip():
            raise ValueError(
                "quantity_id cannot be blank."
            )

        # ------------------------------------------------------------------
        # name
        # ------------------------------------------------------------------

        if not isinstance(self.name, str):
            raise TypeError(
                "name must be a string."
            )

        if not self.name.strip():
            raise ValueError(
                "name cannot be blank."
            )

        # ------------------------------------------------------------------
        # short_name
        # ------------------------------------------------------------------

        if not isinstance(self.short_name, str):
            raise TypeError(
                "short_name must be a string."
            )

        if not self.short_name.strip():
            raise ValueError(
                "short_name cannot be blank."
            )

        # ------------------------------------------------------------------
        # symbol
        # ------------------------------------------------------------------

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )

        # ------------------------------------------------------------------
        # description
        # ------------------------------------------------------------------

        if not isinstance(self.description, str):
            raise TypeError(
                "description must be a string."
            )

        if not self.description.strip():
            raise ValueError(
                "description cannot be blank."
            )

        # ------------------------------------------------------------------
        # aliases
        # ------------------------------------------------------------------

        if not isinstance(self.aliases, tuple):
            raise TypeError(
                "aliases must be a tuple."
            )

        for alias in self.aliases:

            if not isinstance(alias, str):
                raise TypeError(
                    "Each alias must be a string."
                )

            if not alias.strip():
                raise ValueError(
                    "Aliases cannot contain blank strings."
                )

        # ------------------------------------------------------------------
        # search_keywords
        # ------------------------------------------------------------------

        if not isinstance(
            self.search_keywords,
            tuple,
        ):
            raise TypeError(
                "search_keywords must be a tuple."
            )

        for keyword in self.search_keywords:

            if not isinstance(keyword, str):
                raise TypeError(
                    "Each search keyword must be a string."
                )

            if not keyword.strip():
                raise ValueError(
                    "Search keywords cannot contain blank strings."
                )

        # ------------------------------------------------------------------
        # tags
        # ------------------------------------------------------------------

        if not isinstance(
            self.tags,
            tuple,
        ):
            raise TypeError(
                "tags must be a tuple."
            )

        for tag in self.tags:

            if not isinstance(tag, str):
                raise TypeError(
                    "Each tag must be a string."
                )

            if not tag.strip():
                raise ValueError(
                    "Tags cannot contain blank strings."
                )

        # ------------------------------------------------------------------
        # Engineering consistency
        # ------------------------------------------------------------------

        if self.short_name == self.name:
            raise ValueError(
                "short_name should be an engineering abbreviation "
                "and should not be identical to name."
            )

        if self.symbol == self.name:
            raise ValueError(
                "symbol should not be identical to name."
            )

        if self.symbol == self.short_name and len(
            self.symbol
        ) > 10:
            raise ValueError(
                "Engineering symbols should remain concise."
            )

        # ------------------------------------------------------------------
        # Duplicate detection
        # ------------------------------------------------------------------

        if len(self.aliases) != len(set(self.aliases)):
            raise ValueError(
                "Duplicate aliases are not permitted."
            )

        if len(self.search_keywords) != len(
            set(self.search_keywords)
        ):
            raise ValueError(
                "Duplicate search keywords are not permitted."
            )

        if len(self.tags) != len(set(self.tags)):
            raise ValueError(
                "Duplicate tags are not permitted."
            )

        # ------------------------------------------------------------------
        # Recommended engineering limits
        # ------------------------------------------------------------------

        if len(self.quantity_id) > 128:
            raise ValueError(
                "quantity_id exceeds the maximum supported length."
            )

        if len(self.name) > 256:
            raise ValueError(
                "name exceeds the maximum supported length."
            )

        if len(self.short_name) > 64:
            raise ValueError(
                "short_name exceeds the maximum supported length."
            )

        if len(self.symbol) > 32:
            raise ValueError(
                "symbol exceeds the maximum supported length."
            )

        if len(self.description) > 4096:
            raise ValueError(
                "description exceeds the maximum supported length."
            )

    def _validate_classification(self) -> None:
        """
        Validate scientific classification metadata.

        This validation ensures that the engineering classification of the
        quantity is internally consistent.
        """

        # ------------------------------------------------------------------
        # Enumeration validation
        # ------------------------------------------------------------------

        if not isinstance(
            self.category,
            QuantityCategory,
        ):
            raise TypeError(
                "category must be a QuantityCategory."
            )

        if not isinstance(
            self.measurement_type,
            MeasurementType,
        ):
            raise TypeError(
                "measurement_type must be a MeasurementType."
            )

        if not isinstance(
            self.status,
            QuantityStatus,
        ):
            raise TypeError(
                "status must be a QuantityStatus."
            )

        if not isinstance(
            self.criticality,
            QuantityCriticality,
        ):
            raise TypeError(
                "criticality must be a QuantityCriticality."
            )

        if not isinstance(
            self.value_representation,
            ValueRepresentation,
        ):
            raise TypeError(
                "value_representation must be a ValueRepresentation."
            )

        # ------------------------------------------------------------------
        # Physical quantity metadata
        # ------------------------------------------------------------------

        if not isinstance(
            self.physical_quantity_name,
            str,
        ):
            raise TypeError(
                "physical_quantity_name must be a string."
            )

        if not self.physical_quantity_name.strip():
            raise ValueError(
                "physical_quantity_name cannot be blank."
            )

        if not isinstance(
            self.physical_quantity_symbol,
            str,
        ):
            raise TypeError(
                "physical_quantity_symbol must be a string."
            )

        if not self.physical_quantity_symbol.strip():
            raise ValueError(
                "physical_quantity_symbol cannot be blank."
            )

        # ------------------------------------------------------------------
        # Boolean flag validation
        # ------------------------------------------------------------------

        boolean_fields = (
            ("si_quantity", self.si_quantity),
            ("derived_quantity", self.derived_quantity),
            ("vector_quantity", self.vector_quantity),
            ("tensor_quantity", self.tensor_quantity),
            ("dimensionless", self.dimensionless),
        )

        for field_name, value in boolean_fields:

            if not isinstance(value, bool):
                raise TypeError(
                    f"{field_name} must be a bool."
                )

        # ------------------------------------------------------------------
        # Category consistency
        # ------------------------------------------------------------------

        if (
            self.category
            is QuantityCategory.SCALAR
            and self.vector_quantity
        ):
            raise ValueError(
                "Scalar quantities cannot be marked as vectors."
            )

        if (
            self.category
            is QuantityCategory.SCALAR
            and self.tensor_quantity
        ):
            raise ValueError(
                "Scalar quantities cannot be marked as tensors."
            )

        if (
            self.category
            is QuantityCategory.VECTOR
            and not self.vector_quantity
        ):
            raise ValueError(
                "Vector quantities must set vector_quantity=True."
            )

        if (
            self.category
            is QuantityCategory.TENSOR
            and not self.tensor_quantity
        ):
            raise ValueError(
                "Tensor quantities must set tensor_quantity=True."
            )

        if (
            self.category
            is QuantityCategory.DIMENSIONLESS
            and not self.dimensionless
        ):
            raise ValueError(
                "Dimensionless quantities must set dimensionless=True."
            )

        # ------------------------------------------------------------------
        # Mutually exclusive states
        # ------------------------------------------------------------------

        if (
            self.vector_quantity
            and self.tensor_quantity
        ):
            raise ValueError(
                "A quantity cannot simultaneously be both "
                "a vector and a tensor."
            )

        # ------------------------------------------------------------------
        # Measurement consistency
        # ------------------------------------------------------------------

        if (
            self.measurement_type
            is MeasurementType.MEASURED
            and self.value_representation
            is ValueRepresentation.EXACT
        ):
            raise ValueError(
                "Measured quantities cannot be classified as EXACT."
            )

        if (
            self.measurement_type
            is MeasurementType.ESTIMATED
            and self.value_representation
            is ValueRepresentation.EXACT
        ):
            raise ValueError(
                "Estimated quantities cannot be classified as EXACT."
            )

        if (
            self.measurement_type
            is MeasurementType.EMPIRICAL
            and self.value_representation
            is ValueRepresentation.EXACT
        ):
            raise ValueError(
                "Empirical quantities cannot be classified as EXACT."
            )

        # ------------------------------------------------------------------
        # Identifier consistency
        # ------------------------------------------------------------------

        if (
            self.dimensionless
            and self.physical_quantity_symbol.strip() == ""
        ):
            raise ValueError(
                "Dimensionless quantities must define a symbol."
            )

        if (
            len(self.physical_quantity_name)
            > 256
        ):
            raise ValueError(
                "physical_quantity_name exceeds the maximum length."
            )

        if (
            len(self.physical_quantity_symbol)
            > 32
        ):
            raise ValueError(
                "physical_quantity_symbol exceeds the maximum length."
            )

    def _validate_numerical_representation(self) -> None:
        """
        Validate the numerical representation of the quantity.

        This validation ensures that all numerical values,
        engineering limits, tolerances, uncertainty metadata,
        and physical constraints are internally consistent.
        """

        # ------------------------------------------------------------------
        # Primary numerical value
        # ------------------------------------------------------------------

        if not isinstance(
            self.value,
            (int, float),
        ):
            raise TypeError(
                "value must be a real number."
            )

        # ------------------------------------------------------------------
        # Optional numerical fields
        # ------------------------------------------------------------------

        optional_numeric_fields = (
            ("nominal_value", self.nominal_value),
            ("minimum_value", self.minimum_value),
            ("maximum_value", self.maximum_value),
            ("lower_bound", self.lower_bound),
            ("upper_bound", self.upper_bound),
            ("design_value", self.design_value),
            ("operating_value", self.operating_value),
            ("rated_value", self.rated_value),
            ("limit_value", self.limit_value),
            ("failure_value", self.failure_value),
            ("default_value", self.default_value),
            ("initial_value", self.initial_value),
            ("previous_value", self.previous_value),
            ("expected_value", self.expected_value),
            ("target_value", self.target_value),
            ("uncertainty", self.uncertainty),
            ("relative_uncertainty", self.relative_uncertainty),
            ("confidence_level", self.confidence_level),
            ("standard_deviation", self.standard_deviation),
            ("variance", self.variance),
            ("precision", self.precision),
            ("resolution", self.resolution),
            ("tolerance_plus", self.tolerance_plus),
            ("tolerance_minus", self.tolerance_minus),
            ("tolerance_percent", self.tolerance_percent),
        )

        for field_name, value in optional_numeric_fields:

            if (
                value is not None
                and
                not isinstance(
                    value,
                    (int, float),
                )
            ):
                raise TypeError(
                    f"{field_name} must be a real number."
                )

        # ------------------------------------------------------------------
        # Integer fields
        # ------------------------------------------------------------------

        integer_fields = (
            ("significant_figures", self.significant_figures),
            ("decimal_places", self.decimal_places),
        )

        for field_name, value in integer_fields:

            if (
                value is not None
                and
                not isinstance(
                    value,
                    int,
                )
            ):
                raise TypeError(
                    f"{field_name} must be an integer."
                )

        # ------------------------------------------------------------------
        # Range consistency
        # ------------------------------------------------------------------

        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.minimum_value > self.maximum_value
        ):
            raise ValueError(
                "minimum_value cannot exceed maximum_value."
            )

        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and self.lower_bound > self.upper_bound
        ):
            raise ValueError(
                "lower_bound cannot exceed upper_bound."
            )

        # ------------------------------------------------------------------
        # Current value inside limits
        # ------------------------------------------------------------------

        if (
            self.minimum_value is not None
            and self.value < self.minimum_value
        ):
            raise ValueError(
                "value is below minimum_value."
            )

        if (
            self.maximum_value is not None
            and self.value > self.maximum_value
        ):
            raise ValueError(
                "value exceeds maximum_value."
            )

        if (
            self.lower_bound is not None
            and self.value < self.lower_bound
        ):
            raise ValueError(
                "value is below lower_bound."
            )

        if (
            self.upper_bound is not None
            and self.value > self.upper_bound
        ):
            raise ValueError(
                "value exceeds upper_bound."
            )

        # ------------------------------------------------------------------
        # Physical constraints
        # ------------------------------------------------------------------

        if (
            self.strictly_positive
            and self.value <= 0.0
        ):
            raise ValueError(
                "value must be strictly positive."
            )

        if (
            self.non_negative
            and self.value < 0.0
        ):
            raise ValueError(
                "value cannot be negative."
            )

        if (
            self.integer_only
            and not float(self.value).is_integer()
        ):
            raise ValueError(
                "value must be an integer."
            )

        # ------------------------------------------------------------------
        # Floating-point constraints
        # ------------------------------------------------------------------

        if (
            not self.allow_nan
            and math.isnan(self.value)
        ):
            raise ValueError(
                "NaN values are not permitted."
            )

        if (
            not self.allow_infinity
            and math.isinf(self.value)
        ):
            raise ValueError(
                "Infinite values are not permitted."
            )

        # ------------------------------------------------------------------
        # Statistical consistency
        # ------------------------------------------------------------------

        if (
            self.uncertainty is not None
            and self.uncertainty < 0.0
        ):
            raise ValueError(
                "uncertainty cannot be negative."
            )

        if (
            self.relative_uncertainty is not None
            and not (
                0.0
                <= self.relative_uncertainty
                <= 1.0
            )
        ):
            raise ValueError(
                "relative_uncertainty must lie between "
                "0 and 1."
            )

        if (
            self.confidence_level is not None
            and not (
                0.0
                <= self.confidence_level
                <= 1.0
            )
        ):
            raise ValueError(
                "confidence_level must lie between "
                "0 and 1."
            )

        if (
            self.standard_deviation is not None
            and self.standard_deviation < 0.0
        ):
            raise ValueError(
                "standard_deviation cannot be negative."
            )

        if (
            self.variance is not None
            and self.variance < 0.0
        ):
            raise ValueError(
                "variance cannot be negative."
            )

        # ------------------------------------------------------------------
        # Precision
        # ------------------------------------------------------------------

        if (
            self.significant_figures is not None
            and self.significant_figures < 1
        ):
            raise ValueError(
                "significant_figures must be at least 1."
            )

        if (
            self.decimal_places is not None
            and self.decimal_places < 0
        ):
            raise ValueError(
                "decimal_places cannot be negative."
            )

        if (
            self.precision is not None
            and self.precision <= 0.0
        ):
            raise ValueError(
                "precision must be positive."
            )

        if (
            self.resolution is not None
            and self.resolution <= 0.0
        ):
            raise ValueError(
                "resolution must be positive."
            )

        # ------------------------------------------------------------------
        # Tolerances
        # ------------------------------------------------------------------

        if (
            self.tolerance_plus is not None
            and self.tolerance_plus < 0.0
        ):
            raise ValueError(
                "tolerance_plus cannot be negative."
            )

        if (
            self.tolerance_minus is not None
            and self.tolerance_minus < 0.0
        ):
            raise ValueError(
                "tolerance_minus cannot be negative."
            )

        if (
            self.tolerance_percent is not None
            and not (
                0.0
                <= self.tolerance_percent
                <= 100.0
            )
        ):
            raise ValueError(
                "tolerance_percent must lie between "
                "0 and 100."
            )

        # ------------------------------------------------------------------
        # Timestamp
        # ------------------------------------------------------------------

        if (
            self.measured_timestamp is not None
            and not isinstance(
                self.measured_timestamp,
                datetime,
            )
        ):
            raise TypeError(
                "measured_timestamp must be a datetime."
            )

        if not isinstance(
            self.last_updated,
            datetime,
        ):
            raise TypeError(
                "last_updated must be a datetime."
            )

    def _validate_units_and_dimension(self) -> None:
        """
        Validate units and dimensional information.

        This validation ensures that every Quantity has valid
        engineering units and dimensional metadata.
        """

        # ------------------------------------------------------------------
        # Primary objects
        # ------------------------------------------------------------------

        if not isinstance(
            self.unit,
            Unit,
        ):
            raise TypeError(
                "unit must be a Unit instance."
            )

        if not isinstance(
            self.dimension,
            Dimension,
        ):
            raise TypeError(
                "dimension must be a Dimension instance."
            )

        # ------------------------------------------------------------------
        # Optional Unit objects
        # ------------------------------------------------------------------

        optional_units = (
            ("preferred_unit", self.preferred_unit),
            ("display_unit", self.display_unit),
            ("conversion_unit", self.conversion_unit),
        )

        for field_name, value in optional_units:

            if (
                value is not None
                and
                not isinstance(
                    value,
                    Unit,
                )
            ):
                raise TypeError(
                    f"{field_name} must be a Unit."
                )

        # ------------------------------------------------------------------
        # SI consistency
        # ------------------------------------------------------------------

        if (
            self.si_quantity
            and self.preferred_unit is not None
            and hasattr(
                self.preferred_unit,
                "is_si_unit",
            )
            and not getattr(self.preferred_unit, "is_si_unit", False)
        ):
            raise ValueError(
                "SI quantities must use an SI preferred unit."
            )

        # ------------------------------------------------------------------
        # Dimensionless quantities
        # ------------------------------------------------------------------

        if self.dimensionless:

            if hasattr(
                self.dimension,
                "is_dimensionless",
            ):
                if not self.dimension.is_dimensionless:
                    raise ValueError(
                        "Dimensionless quantities require a "
                        "dimensionless Dimension."
                    )

        # ------------------------------------------------------------------
        # Unit compatibility
        # ------------------------------------------------------------------

        compatible_units = (
            self.preferred_unit,
            self.display_unit,
            self.conversion_unit,
        )

        for candidate in compatible_units:

            if candidate is None:
                continue

            if (
                hasattr(
                    candidate,
                    "dimension",
                )
                and
                candidate.dimension != self.dimension
            ):
                raise ValueError(
                    "Unit dimension is inconsistent with "
                    "quantity dimension."
                )

        # ------------------------------------------------------------------
        # Duplicate unit references
        # ------------------------------------------------------------------

        if (
            self.preferred_unit is not None
            and self.display_unit is not None
            and self.preferred_unit == self.display_unit
        ):
            pass

        if (
            self.display_unit is not None
            and self.conversion_unit is not None
            and self.display_unit == self.conversion_unit
        ):
            pass

        # ------------------------------------------------------------------
        # Canonical engineering checks
        # ------------------------------------------------------------------

        if (
            self.dimensionless
            and hasattr(
                self.unit,
                "symbol",
            )
        ):
            if self.unit.symbol.strip() == "":
                raise ValueError(
                    "Dimensionless quantities still require "
                    "a valid unit representation."
                )

        # ------------------------------------------------------------------
        # Future dimensional analysis hook
        # ------------------------------------------------------------------

        #
        # Future versions of COSMOS will perform complete
        # dimensional analysis here.
        #
        # Examples:
        #
        # Pressure
        #      M L^-1 T^-2
        #
        # Density
        #      M L^-3
        #
        # Heat Flux
        #      M T^-3
        #
        # The physics engine will eventually verify that
        # every assigned Unit has exactly the same Dimension.
        #

    def _validate_relationships(self) -> None:
        """
        Validate engineering relationships.

        This validation ensures that all Knowledge Foundation
        relationships are structurally valid and internally
        consistent.
        """

        # ==============================================================
        # Primary object references
        # ==============================================================

        if (
            self.variable is not None
            and not isinstance(
                self.variable,
                Variable,
            )
        ):
            raise TypeError(
                "variable must be a Variable instance."
            )

        if (
            self.engineering_domain is not None
            and not isinstance(
                self.engineering_domain,
                EngineeringDomain,
            )
        ):
            raise TypeError(
                "engineering_domain must be an "
                "EngineeringDomain instance."
            )

        if (
            self.subsystem is not None
            and not isinstance(
                self.subsystem,
                Subsystem,
            )
        ):
            raise TypeError(
                "subsystem must be a Subsystem instance."
            )

        if (
            self.source_reference is not None
            and not isinstance(
                self.source_reference,
                Reference,
            )
        ):
            raise TypeError(
                "source_reference must be a Reference instance."
            )

        if (
            self.source_document is not None
            and not isinstance(
                self.source_document,
                Document,
            )
        ):
            raise TypeError(
                "source_document must be a Document instance."
            )

        # ==============================================================
        # Identifier collections
        # ==============================================================

        relationship_fields = (
            ("related_variable_ids", self.related_variable_ids),
            ("related_constant_ids", self.related_constant_ids),
            ("related_quantity_ids", self.related_quantity_ids),
            ("related_dimension_ids", self.related_dimension_ids),
            ("related_unit_ids", self.related_unit_ids),
            ("related_equation_ids", self.related_equation_ids),
            (
                "related_physical_law_ids",
                self.related_physical_law_ids,
            ),
            (
                "related_correlation_ids",
                self.related_correlation_ids,
            ),
            (
                "related_empirical_relation_ids",
                self.related_empirical_relation_ids,
            ),
            (
                "related_engineering_domain_ids",
                self.related_engineering_domain_ids,
            ),
            (
                "related_subsystem_ids",
                self.related_subsystem_ids,
            ),
            (
                "related_material_ids",
                self.related_material_ids,
            ),
            (
                "related_component_ids",
                self.related_component_ids,
            ),
            (
                "related_property_ids",
                self.related_property_ids,
            ),
            (
                "related_process_ids",
                self.related_process_ids,
            ),
            (
                "related_manufacturing_process_ids",
                self.related_manufacturing_process_ids,
            ),
            (
                "related_boundary_condition_ids",
                self.related_boundary_condition_ids,
            ),
            (
                "related_assumption_ids",
                self.related_assumption_ids,
            ),
            (
                "related_failure_mode_ids",
                self.related_failure_mode_ids,
            ),
            (
                "related_design_rule_ids",
                self.related_design_rule_ids,
            ),
            (
                "related_simulation_ids",
                self.related_simulation_ids,
            ),
            (
                "related_experiment_ids",
                self.related_experiment_ids,
            ),
            (
                "validation_dataset_ids",
                self.validation_dataset_ids,
            ),
            (
                "benchmark_dataset_ids",
                self.benchmark_dataset_ids,
            ),
            (
                "supporting_reference_ids",
                self.supporting_reference_ids,
            ),
            (
                "supporting_document_ids",
                self.supporting_document_ids,
            ),
            ("citation_ids", self.citation_ids),
            (
                "bibliography_entries",
                self.bibliography_entries,
            ),
            (
                "external_reference_ids",
                self.external_reference_ids,
            ),
        )

        for field_name, values in relationship_fields:

            if not isinstance(values, tuple):
                raise TypeError(
                    f"{field_name} must be a tuple."
                )

            seen: set[str] = set()

            for identifier in values:

                if not isinstance(identifier, str):
                    raise TypeError(
                        f"Each identifier in "
                        f"{field_name} must be a string."
                    )

                if not identifier.strip():
                    raise ValueError(
                        f"{field_name} cannot contain "
                        "blank identifiers."
                    )

                if identifier in seen:
                    raise ValueError(
                        f"Duplicate identifier "
                        f"'{identifier}' found in "
                        f"{field_name}."
                    )

                seen.add(identifier)

        # ==============================================================
        # Source metadata
        # ==============================================================

        optional_strings = (
            ("doi", self.doi),
            ("source_url", self.source_url),
            ("source_section", self.source_section),
            ("source_page", self.source_page),
            (
                "source_equation_number",
                self.source_equation_number,
            ),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

        # ==============================================================
        # Cross-reference consistency
        # ==============================================================

        if (
            self.source_reference is None
            and self.doi is not None
        ):
            raise ValueError(
                "A DOI cannot be supplied without a "
                "source_reference."
            )

        if (
            self.source_document is None
            and self.source_section is not None
        ):
            raise ValueError(
                "source_section requires a "
                "source_document."
            )

        if (
            self.source_document is None
            and self.source_page is not None
        ):
            raise ValueError(
                "source_page requires a "
                "source_document."
            )

        if (
            self.source_document is None
            and self.source_equation_number is not None
        ):
            raise ValueError(
                "source_equation_number requires "
                "a source_document."
            )

        # ==============================================================
        # Future semantic validation hook
        # ==============================================================

        #
        # Future versions of COSMOS will validate:
        #
        # - Repository existence
        # - Graph connectivity
        # - Ontology consistency
        # - Circular dependencies
        # - Broken references
        # - Knowledge graph integrity
        #

    def _validate_graph_metadata(self) -> None:
        """
        Validate Knowledge Graph metadata.

        This validation ensures that graph metadata,
        ontology metadata, semantic metadata,
        and indexing metadata are internally
        consistent.
        """

        # ==============================================================
        # Optional string fields
        # ==============================================================

        optional_strings = (
            ("graph_node_id", self.graph_node_id),
            ("graph_namespace", self.graph_namespace),
            ("ontology_identifier", self.ontology_identifier),
            ("ontology_uri", self.ontology_uri),
            ("ontology_version", self.ontology_version),
            ("semantic_identifier", self.semantic_identifier),
            ("symbolic_identifier", self.symbolic_identifier),
            ("canonical_identifier", self.canonical_identifier),
            ("universal_identifier", self.universal_identifier),
            ("namespace_identifier", self.namespace_identifier),
            ("graph_label", self.graph_label),
            ("graph_category", self.graph_category),
            ("graph_type", self.graph_type),
            ("parent_node_identifier", self.parent_node_identifier),
            ("root_node_identifier", self.root_node_identifier),
            ("graph_embedding_identifier", self.graph_embedding_identifier),
            (
                "semantic_embedding_identifier",
                self.semantic_embedding_identifier,
            ),
            (
                "vector_database_identifier",
                self.vector_database_identifier,
            ),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

        # ==============================================================
        # Tuple collections
        # ==============================================================

        tuple_fields = (
            (
                "child_node_identifiers",
                self.child_node_identifiers,
            ),
            (
                "incoming_relationship_identifiers",
                self.incoming_relationship_identifiers,
            ),
            (
                "outgoing_relationship_identifiers",
                self.outgoing_relationship_identifiers,
            ),
            (
                "semantic_tags",
                self.semantic_tags,
            ),
            (
                "ontology_classes",
                self.ontology_classes,
            ),
            (
                "ontology_superclasses",
                self.ontology_superclasses,
            ),
            (
                "ontology_subclasses",
                self.ontology_subclasses,
            ),
            (
                "inferred_relationships",
                self.inferred_relationships,
            ),
        )

        for field_name, values in tuple_fields:

            if not isinstance(values, tuple):
                raise TypeError(
                    f"{field_name} must be a tuple."
                )

            seen: set[str] = set()

            for value in values:

                if not isinstance(value, str):
                    raise TypeError(
                        f"Each value in {field_name} "
                        "must be a string."
                    )

                if not value.strip():
                    raise ValueError(
                        f"{field_name} cannot contain "
                        "blank strings."
                    )

                if value in seen:
                    raise ValueError(
                        f"Duplicate value '{value}' "
                        f"found in {field_name}."
                    )

                seen.add(value)

        # ==============================================================
        # Boolean fields
        # ==============================================================

        boolean_fields = (
            ("reasoning_enabled", self.reasoning_enabled),
            ("searchable", self.searchable),
            ("indexable", self.indexable),
        )

        for bool_field_name, bool_value in boolean_fields:

            if not isinstance(bool_value, bool):
                raise TypeError(
                    f"{bool_field_name} must be a bool."
                )

        # ==============================================================
        # Mapping metadata
        # ==============================================================

        mapping_fields = (
            (
                "ontology_metadata",
                self.ontology_metadata,
            ),
            (
                "graph_metadata",
                self.graph_metadata,
            ),
        )

        for mapping_field_name, mapping_value in mapping_fields:

            if not isinstance(mapping_value, Mapping):
                raise TypeError(
                    f"{mapping_field_name} must implement "
                    "Mapping."
                )

        # ==============================================================
        # Graph consistency
        # ==============================================================

        if (
            self.searchable
            and not self.indexable
        ):
            raise ValueError(
                "Searchable graph nodes must also "
                "be indexable."
            )

        if (
            self.reasoning_enabled
            and self.graph_node_id is None
        ):
            raise ValueError(
                "Reasoning-enabled quantities "
                "require a graph_node_id."
            )

        if (
            self.reasoning_enabled
            and self.semantic_identifier is None
        ):
            raise ValueError(
                "Reasoning-enabled quantities "
                "require a semantic_identifier."
            )

        if (
            self.ontology_uri is not None
            and self.ontology_identifier is None
        ):
            raise ValueError(
                "ontology_uri requires an "
                "ontology_identifier."
            )

        if (
            self.parent_node_identifier is not None
            and self.root_node_identifier is None
        ):
            raise ValueError(
                "A parent node requires a "
                "root node."
            )

        # ==============================================================
        # Graph category
        # ==============================================================

        if self.graph_category != "Quantity":
            raise ValueError(
                "graph_category must be "
                "'Quantity'."
            )

        if self.graph_type != "ScientificQuantity":
            raise ValueError(
                "graph_type must be "
                "'ScientificQuantity'."
            )

        # ==============================================================
        # Future graph validation
        # ==============================================================

        #
        # Future versions of COSMOS will additionally verify:
        #
        # • ontology inheritance
        # • graph cycles
        # • orphan nodes
        # • semantic consistency
        # • RDF/OWL compatibility
        # • Neo4j schema validation
        # • vector index integrity
        # • reasoning graph completeness
        #

    def _validate_engineering_metadata(self) -> None:
        """
        Validate engineering ownership metadata.

        This validation ensures that ownership,
        lifecycle, readiness, certification,
        and engineering governance metadata
        are internally consistent.
        """

        # ==============================================================
        # Optional string fields
        # ==============================================================

        optional_strings = (
            ("responsible_team", self.responsible_team),
            ("responsible_engineer", self.responsible_engineer),
            ("technical_lead", self.technical_lead),
            ("chief_engineer", self.chief_engineer),
            ("owning_department", self.owning_department),
            ("owning_organization", self.owning_organization),
            ("project_name", self.project_name),
            ("project_identifier", self.project_identifier),
            ("program_name", self.program_name),
            ("program_identifier", self.program_identifier),
            ("mission_name", self.mission_name),
            ("mission_identifier", self.mission_identifier),
            ("vehicle_name", self.vehicle_name),
            ("vehicle_identifier", self.vehicle_identifier),
            ("component_owner", self.component_owner),
            ("subsystem_owner", self.subsystem_owner),
            ("engineering_discipline", self.engineering_discipline),
            ("engineering_phase", self.engineering_phase),
            ("maturity_level", self.maturity_level),
            ("configuration_owner", self.configuration_owner),
            ("quality_level", self.quality_level),
            ("certification_authority", self.certification_authority),
            ("certification_identifier", self.certification_identifier),
            ("engineering_notes", self.engineering_notes),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

        # ==============================================================
        # Readiness Levels
        # ==============================================================

        readiness_levels = (
            (
                "technology_readiness_level",
                self.technology_readiness_level,
                1,
                9,
            ),
            (
                "manufacturing_readiness_level",
                self.manufacturing_readiness_level,
                1,
                10,
            ),
            (
                "operational_readiness_level",
                self.operational_readiness_level,
                1,
                10,
            ),
        )

        for (
            level_name,
            level_value,
            minimum,
            maximum,
        ) in readiness_levels:

            if level_value is None:
                continue

            if not isinstance(level_value, int):
                raise TypeError(
                    f"{level_name} must be an integer."
                )

            if not minimum <= level_value <= maximum:
                raise ValueError(
                    f"{level_name} must be between "
                    f"{minimum} and {maximum}."
                )

        # ==============================================================
        # Boolean fields
        # ==============================================================

        boolean_fields = (
            ("export_controlled", self.export_controlled),
            ("proprietary", self.proprietary),
            ("classified", self.classified),
            ("safety_critical", self.safety_critical),
            ("mission_critical", self.mission_critical),
            ("flight_critical", self.flight_critical),
        )

        for bool_field_name, bool_value in boolean_fields:

            if not isinstance(bool_value, bool):
                raise TypeError(
                    f"{bool_field_name} must be a bool."
                )

        # ==============================================================
        # Engineering Consistency
        # ==============================================================

        if (
            self.flight_critical
            and not self.mission_critical
        ):
            raise ValueError(
                "Flight-critical quantities must also "
                "be mission-critical."
            )

        if (
            self.mission_critical
            and not self.safety_critical
        ):
            raise ValueError(
                "Mission-critical quantities should "
                "also be safety-critical."
            )

        if (
            self.certification_identifier is not None
            and self.certification_authority is None
        ):
            raise ValueError(
                "A certification identifier requires "
                "a certification authority."
            )

        if (
            self.project_identifier is not None
            and self.project_name is None
        ):
            raise ValueError(
                "project_identifier requires "
                "project_name."
            )

        if (
            self.program_identifier is not None
            and self.program_name is None
        ):
            raise ValueError(
                "program_identifier requires "
                "program_name."
            )

        if (
            self.vehicle_identifier is not None
            and self.vehicle_name is None
        ):
            raise ValueError(
                "vehicle_identifier requires "
                "vehicle_name."
            )

        if (
            self.mission_identifier is not None
            and self.mission_name is None
        ):
            raise ValueError(
                "mission_identifier requires "
                "mission_name."
            )

        # ==============================================================
        # Future Engineering Governance
        # ==============================================================

        #
        # Future COSMOS releases will validate:
        #
        # • PLM ownership
        # • Team directory integration
        # • Configuration management
        # • Engineering approval workflows
        # • Digital thread completeness
        # • Program hierarchy validation
        # • Organizational consistency
        #

    def _validate_verification_metadata(self) -> None:
        """
        Validate verification and validation metadata.

        This validation ensures that engineering verification,
        validation, confidence, evidence, certification,
        and traceability metadata are internally consistent.
        """

        # ==============================================================
        # Optional string fields
        # ==============================================================

        optional_strings = (
            ("verification_status", self.verification_status),
            ("validation_status", self.validation_status),
            ("verification_method", self.verification_method),
            ("validation_method", self.validation_method),
            ("verified_by", self.verified_by),
            ("validated_by", self.validated_by),
            ("reviewer", self.reviewer),
            ("approver", self.approver),
            ("verification_level", self.verification_level),
            ("validation_level", self.validation_level),
            ("verification_notes", self.verification_notes),
            ("validation_notes", self.validation_notes),
            ("evidence_summary", self.evidence_summary),
            ("known_limitations", self.known_limitations),
            ("recommended_usage", self.recommended_usage),
            ("prohibited_usage", self.prohibited_usage),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

        # ==============================================================
        # Reference objects
        # ==============================================================

        reference_fields = (
            (
                "verification_reference",
                self.verification_reference,
            ),
            (
                "validation_reference",
                self.validation_reference,
            ),
        )

        for ref_field_name, ref_value in reference_fields:

            if ref_value is None:
                continue

            if not isinstance(ref_value, Reference):
                raise TypeError(
                    f"{ref_field_name} must be a Reference."
                )

        document_fields = (
            (
                "verification_document",
                self.verification_document,
            ),
            (
                "validation_document",
                self.validation_document,
            ),
        )

        for doc_field_name, doc_value in document_fields:

            if doc_value is None:
                continue

            if not isinstance(doc_value, Document):
                raise TypeError(
                    f"{doc_field_name} must be a Document."
                )

        # ==============================================================
        # Datetime validation
        # ==============================================================

        datetime_fields = (
            (
                "verification_date",
                self.verification_date,
            ),
            (
                "validation_date",
                self.validation_date,
            ),
        )

        for dt_field_name, dt_value in datetime_fields:

            if dt_value is None:
                continue

            if not isinstance(dt_value, datetime):
                raise TypeError(
                    f"{dt_field_name} must be a datetime."
                )

        # ==============================================================
        # Confidence metrics
        # ==============================================================

        score_fields = (
            (
                "confidence_score",
                self.confidence_score,
            ),
            (
                "evidence_score",
                self.evidence_score,
            ),
            (
                "quality_score",
                self.quality_score,
            ),
        )

        for score_field_name, score_value in score_fields:

            if score_value is None:
                continue

            if not isinstance(score_value, (int, float)):
                raise TypeError(
                    f"{score_field_name} must be numeric."
                )

            if not 0.0 <= score_value <= 1.0:
                raise ValueError(
                    f"{score_field_name} must lie between "
                    "0.0 and 1.0."
                )

        # ==============================================================
        # Boolean validation
        # ==============================================================

        boolean_fields = (
            (
                "uncertainty_verified",
                self.uncertainty_verified,
            ),
            (
                "units_verified",
                self.units_verified,
            ),
            (
                "dimensions_verified",
                self.dimensions_verified,
            ),
            (
                "equation_verified",
                self.equation_verified,
            ),
            (
                "experimentally_validated",
                self.experimentally_validated,
            ),
            (
                "independently_verified",
                self.independently_verified,
            ),
            (
                "peer_reviewed",
                self.peer_reviewed,
            ),
            (
                "benchmarked",
                self.benchmarked,
            ),
            (
                "certified",
                self.certified,
            ),
            (
                "traceable",
                self.traceable,
            ),
            (
                "assumptions_verified",
                self.assumptions_verified,
            ),
        )

        for bool_field_name, bool_value in boolean_fields:

            if not isinstance(bool_value, bool):
                raise TypeError(
                    f"{bool_field_name} must be a bool."
                )

        # ==============================================================
        # Verification consistency
        # ==============================================================

        if (
            self.verification_reference is not None
            and self.verification_document is None
        ):
            raise ValueError(
                "verification_reference requires "
                "verification_document."
            )

        if (
            self.validation_reference is not None
            and self.validation_document is None
        ):
            raise ValueError(
                "validation_reference requires "
                "validation_document."
            )

        if (
            self.verified_by is not None
            and self.verification_date is None
        ):
            raise ValueError(
                "verified_by requires "
                "verification_date."
            )

        if (
            self.validated_by is not None
            and self.validation_date is None
        ):
            raise ValueError(
                "validated_by requires "
                "validation_date."
            )

        # ==============================================================
        # Engineering consistency
        # ==============================================================

        if (
            self.certified
            and not self.traceable
        ):
            raise ValueError(
                "Certified quantities must be traceable."
            )

        if (
            self.certified
            and not self.peer_reviewed
        ):
            raise ValueError(
                "Certified quantities should be "
                "peer reviewed."
            )

        if (
            self.experimentally_validated
            and self.validation_method is None
        ):
            raise ValueError(
                "Experimental validation requires "
                "a validation_method."
            )

        if (
            self.equation_verified
            and not self.units_verified
        ):
            raise ValueError(
                "Equation verification requires "
                "verified units."
            )

        if (
            self.equation_verified
            and not self.dimensions_verified
        ):
            raise ValueError(
                "Equation verification requires "
                "verified dimensions."
            )

        if (
            self.independently_verified
            and self.reviewer is None
        ):
            raise ValueError(
                "Independent verification requires "
                "a reviewer."
            )

        # ==============================================================
        # Future engineering verification
        # ==============================================================

        #
        # Future versions of COSMOS will additionally validate:
        #
        # • NASA benchmark compliance
        # • Experimental campaign linkage
        # • Test stand traceability
        # • Digital thread completeness
        # • Certification workflows
        # • Standards compliance (NASA, ESA, ISO, ASME)
        # • Automatic V&V report generation
        #

    def _validate_ai_metadata(self) -> None:
        """
        Validate AI metadata.

        AI metadata is informative only and shall never replace
        authoritative engineering metadata.
        """

        # ==============================================================
        # Optional string fields
        # ==============================================================

        optional_strings = (
            ("llm_summary", self.llm_summary),
            ("engineering_summary", self.engineering_summary),
            ("embedding_identifier", self.embedding_identifier),
            ("embedding_model", self.embedding_model),
            ("embedding_version", self.embedding_version),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

        # ==============================================================
        # Tuple fields
        # ==============================================================

        tuple_fields = (
            ("extracted_keywords", self.extracted_keywords),
            ("semantic_keywords", self.semantic_keywords),
        )

        for field_name, values in tuple_fields:

            if not isinstance(values, tuple):
                raise TypeError(
                    f"{field_name} must be a tuple."
                )

            seen: set[str] = set()

            for value in values:

                if not isinstance(value, str):
                    raise TypeError(
                        f"Each value in {field_name} "
                        "must be a string."
                    )

                if not value.strip():
                    raise ValueError(
                        f"{field_name} cannot contain "
                        "blank strings."
                    )

                if value in seen:
                    raise ValueError(
                        f"Duplicate value '{value}' "
                        f"found in {field_name}."
                    )

                seen.add(value)

        # ==============================================================
        # Datetime
        # ==============================================================

        if (
            self.embedding_timestamp is not None
            and
            not isinstance(
                self.embedding_timestamp,
                datetime,
            )
        ):
            raise TypeError(
                "embedding_timestamp must be a datetime."
            )

        # ==============================================================
        # Numeric fields
        # ==============================================================

        score_fields = (
            ("ai_confidence", self.ai_confidence),
            (
                "semantic_similarity_threshold",
                self.semantic_similarity_threshold,
            ),
            ("retrieval_score", self.retrieval_score),
            (
                "ontology_alignment_score",
                self.ontology_alignment_score,
            ),
            ("reasoning_score", self.reasoning_score),
        )

        for score_field_name, score_value in score_fields:

            if score_value is None:
                continue

            if not isinstance(
                score_value,
                (int, float),
            ):
                raise TypeError(
                    f"{score_field_name} must be numeric."
                )

            if not 0.0 <= score_value <= 1.0:
                raise ValueError(
                    f"{score_field_name} must lie between "
                    "0.0 and 1.0."
                )

        # ==============================================================
        # Vector dimension
        # ==============================================================

        if self.vector_dimension is not None:

            if not isinstance(
                self.vector_dimension,
                int,
            ):
                raise TypeError(
                    "vector_dimension must be an integer."
                )

            if self.vector_dimension <= 0:
                raise ValueError(
                    "vector_dimension must be positive."
                )

        # ==============================================================
        # Boolean fields
        # ==============================================================

        boolean_fields = (
            ("ai_verified", self.ai_verified),
            ("searchable_by_ai", self.searchable_by_ai),
            ("semantic_indexed", self.semantic_indexed),
            ("graph_indexed", self.graph_indexed),
        )

        for bool_field_name, bool_value in boolean_fields:

            if not isinstance(bool_value, bool):
                raise TypeError(
                    f"{bool_field_name} must be a bool."
                )

        # ==============================================================
        # AI consistency
        # ==============================================================

        if (
            self.semantic_indexed
            and self.embedding_identifier is None
        ):
            raise ValueError(
                "Semantic indexing requires an "
                "embedding_identifier."
            )

        if (
            self.graph_indexed
            and self.graph_embedding_identifier is None
        ):
            raise ValueError(
                "Graph indexing requires a "
                "graph_embedding_identifier."
            )

        if (
            self.embedding_identifier is not None
            and self.embedding_model is None
        ):
            raise ValueError(
                "embedding_identifier requires "
                "embedding_model."
            )

        if (
            self.embedding_model is not None
            and self.embedding_version is None
        ):
            raise ValueError(
                "embedding_model requires "
                "embedding_version."
            )

        if (
            self.ai_verified
            and self.ai_confidence is None
        ):
            raise ValueError(
                "Verified AI metadata requires "
                "an ai_confidence score."
            )

    # ==============================================================
    # Extension Field Validation
    # ==============================================================

    def _validate_extensions(self) -> None:
        """
        Validate extension metadata.

        Extension metadata enables future schema evolution while
        preserving the integrity of the core Quantity model.
        """

        mapping_fields = (
            ("ai_annotations", self.ai_annotations),
            ("ai_metadata", self.ai_metadata),
            ("custom_metadata", self.custom_metadata),
            ("extension_fields", self.extension_fields),
            ("custom_attributes", self.custom_attributes),
            ("plugin_metadata", self.plugin_metadata),
            (
                "external_identifiers",
                self.external_identifiers,
            ),
        )

        for field_name, mapping in mapping_fields:

            if not isinstance(mapping, Mapping):
                raise TypeError(
                    f"{field_name} must implement Mapping."
                )

        # ==============================================================
        # External identifiers
        # ==============================================================

        for (
            system_name,
            identifier,
        ) in self.external_identifiers.items():

            if not isinstance(system_name, str):
                raise TypeError(
                    "External identifier keys "
                    "must be strings."
                )

            if not isinstance(identifier, str):
                raise TypeError(
                    "External identifier values "
                    "must be strings."
                )

            if not system_name.strip():
                raise ValueError(
                    "External identifier keys "
                    "cannot be blank."
                )

            if not identifier.strip():
                raise ValueError(
                    "External identifier values "
                    "cannot be blank."
                )

        # ==============================================================
        # Schema metadata
        # ==============================================================

        if not isinstance(
            self.schema_version,
            str,
        ):
            raise TypeError(
                "schema_version must be a string."
            )

        if not self.schema_version.strip():
            raise ValueError(
                "schema_version cannot be blank."
            )

        if not isinstance(
            self.cosmos_version,
            str,
        ):
            raise TypeError(
                "cosmos_version must be a string."
            )

        if not self.cosmos_version.strip():
            raise ValueError(
                "cosmos_version cannot be blank."
            )

        # ==============================================================
        # Future Extension Validation
        # ==============================================================

        #
        # Future COSMOS releases may validate:
        #
        # • Plugin compatibility
        # • Schema migration rules
        # • AI provider compatibility
        # • Embedding model compatibility
        # • Vector database integration
        # • Ontology synchronization
        # • Distributed knowledge graph metadata
        #

    def _validate_repository_metadata(self) -> None:
        """
        Validate repository metadata.

        This validation ensures that repository metadata,
        configuration management information, lifecycle
        state, and revision history are internally
        consistent.
        """

        # ==============================================================
        # Required string fields
        # ==============================================================

        if not isinstance(self.version, str):
            raise TypeError(
                "version must be a string."
            )

        if not self.version.strip():
            raise ValueError(
                "version cannot be blank."
            )

        if not isinstance(self.created_by, str):
            raise TypeError(
                "created_by must be a string."
            )

        if not self.created_by.strip():
            raise ValueError(
                "created_by cannot be blank."
            )

        # ==============================================================
        # Revision
        # ==============================================================

        if not isinstance(self.revision, int):
            raise TypeError(
                "revision must be an integer."
            )

        if self.revision < 1:
            raise ValueError(
                "revision must be at least 1."
            )

        # ==============================================================
        # Optional string fields
        # ==============================================================

        optional_strings = (
            ("revision_notes", self.revision_notes),
            ("modified_by", self.modified_by),
            ("approved_by", self.approved_by),
            ("reviewed_by", self.reviewed_by),
            (
                "repository_identifier",
                self.repository_identifier,
            ),
            (
                "repository_path",
                self.repository_path,
            ),
            (
                "repository_branch",
                self.repository_branch,
            ),
            (
                "baseline_identifier",
                self.baseline_identifier,
            ),
            (
                "configuration_identifier",
                self.configuration_identifier,
            ),
            (
                "lifecycle_state",
                self.lifecycle_state,
            ),
            (
                "change_request_identifier",
                self.change_request_identifier,
            ),
            (
                "change_order_identifier",
                self.change_order_identifier,
            ),
            (
                "release_identifier",
                self.release_identifier,
            ),
            ("checksum", self.checksum),
            (
                "export_identifier",
                self.export_identifier,
            ),
            (
                "import_identifier",
                self.import_identifier,
            ),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

        # ==============================================================
        # Datetime fields
        # ==============================================================

        if not isinstance(
            self.created_timestamp,
            datetime,
        ):
            raise TypeError(
                "created_timestamp must be a datetime."
            )

        datetime_fields = (
            (
                "modified_timestamp",
                self.modified_timestamp,
            ),
            (
                "approved_timestamp",
                self.approved_timestamp,
            ),
            (
                "reviewed_timestamp",
                self.reviewed_timestamp,
            ),
        )

        for dt_field_name, dt_value in datetime_fields:

            if dt_value is None:
                continue

            if not isinstance(
                dt_value,
                datetime,
            ):
                raise TypeError(
                    f"{dt_field_name} must be a datetime."
                )

        # ==============================================================
        # Boolean fields
        # ==============================================================

        boolean_fields = (
            ("archived", self.archived),
            ("locked", self.locked),
            ("read_only", self.read_only),
        )

        for bool_field_name, bool_value in boolean_fields:

            if not isinstance(bool_value, bool):
                raise TypeError(
                    f"{bool_field_name} must be a bool."
                )

        # ==============================================================
        # Lifecycle consistency
        # ==============================================================

        if (
            self.modified_by is not None
            and self.modified_timestamp is None
        ):
            raise ValueError(
                "modified_by requires "
                "modified_timestamp."
            )

        if (
            self.modified_timestamp is not None
            and self.modified_by is None
        ):
            raise ValueError(
                "modified_timestamp requires "
                "modified_by."
            )

        if (
            self.reviewed_by is not None
            and self.reviewed_timestamp is None
        ):
            raise ValueError(
                "reviewed_by requires "
                "reviewed_timestamp."
            )

        if (
            self.reviewed_timestamp is not None
            and self.reviewed_by is None
        ):
            raise ValueError(
                "reviewed_timestamp requires "
                "reviewed_by."
            )

        if (
            self.approved_by is not None
            and self.approved_timestamp is None
        ):
            raise ValueError(
                "approved_by requires "
                "approved_timestamp."
            )

        if (
            self.approved_timestamp is not None
            and self.approved_by is None
        ):
            raise ValueError(
                "approved_timestamp requires "
                "approved_by."
            )

        # ==============================================================
        # Timestamp ordering
        # ==============================================================

        if (
            self.modified_timestamp is not None
            and self.modified_timestamp
            < self.created_timestamp
        ):
            raise ValueError(
                "modified_timestamp cannot precede "
                "created_timestamp."
            )

        if (
            self.reviewed_timestamp is not None
            and self.reviewed_timestamp
            < self.created_timestamp
        ):
            raise ValueError(
                "reviewed_timestamp cannot precede "
                "created_timestamp."
            )

        if (
            self.approved_timestamp is not None
            and self.approved_timestamp
            < self.created_timestamp
        ):
            raise ValueError(
                "approved_timestamp cannot precede "
                "created_timestamp."
            )

        # ==============================================================
        # Repository consistency
        # ==============================================================

        if (
            self.repository_path is not None
            and self.repository_identifier is None
        ):
            raise ValueError(
                "repository_path requires "
                "repository_identifier."
            )

        if (
            self.repository_branch is not None
            and self.repository_identifier is None
        ):
            raise ValueError(
                "repository_branch requires "
                "repository_identifier."
            )

        if (
            self.change_order_identifier is not None
            and self.change_request_identifier is None
        ):
            raise ValueError(
                "change_order_identifier requires "
                "change_request_identifier."
            )

        # ==============================================================
        # Archive consistency
        # ==============================================================

        if (
            self.archived
            and not self.read_only
        ):
            raise ValueError(
                "Archived quantities must be "
                "read-only."
            )

        if (
            self.locked
            and not self.read_only
        ):
            raise ValueError(
                "Locked quantities must be "
                "read-only."
            )

        # ==============================================================
        # Future Repository Validation
        # ==============================================================

        #
        # Future versions of COSMOS will validate:
        #
        # • Git commit identifiers
        # • Digital thread identifiers
        # • Engineering baselines
        # • PLM integration
        # • Repository synchronization
        # • Change approval workflows
        # • Release management
        # • Configuration management rules
        #

    def _validate_cross_consistency(self) -> None:
        """
        Validate consistency across all sections of the Quantity model.

        This method validates engineering invariants that span
        multiple validation domains.

        Unlike the individual validation methods, this validator
        verifies that the Quantity behaves as one coherent
        engineering object.
        """

        # ==============================================================
        # Numerical Representation ↔ Classification
        # ==============================================================

        if (
            self.measurement_type
            is MeasurementType.MEASURED
            and not self.measured_value
        ):
            raise ValueError(
                "Measured quantities must set "
                "measured_value=True."
            )

        if (
            self.measurement_type
            is MeasurementType.CALCULATED
            and not self.calculated_value
        ):
            raise ValueError(
                "Calculated quantities must set "
                "calculated_value=True."
            )

        if (
            self.measurement_type
            is MeasurementType.SIMULATED
            and not self.simulated_value
        ):
            raise ValueError(
                "Simulated quantities must set "
                "simulated_value=True."
            )

        if (
            self.measurement_type
            is MeasurementType.ESTIMATED
            and not self.estimated_value
        ):
            raise ValueError(
                "Estimated quantities must set "
                "estimated_value=True."
            )

        # ==============================================================
        # Exact values
        # ==============================================================

        if self.exact_value:

            if (
                self.uncertainty is not None
                and self.uncertainty != 0.0
            ):
                raise ValueError(
                    "Exact quantities cannot have "
                    "non-zero uncertainty."
                )

            if (
                self.standard_deviation is not None
                and self.standard_deviation != 0.0
            ):
                raise ValueError(
                    "Exact quantities cannot have "
                    "a standard deviation."
                )

        # ==============================================================
        # Dimension consistency
        # ==============================================================

        if (
            self.dimensionless
            and hasattr(
                self.dimension,
                "is_dimensionless",
            )
            and not self.dimension.is_dimensionless
        ):
            raise ValueError(
                "Dimensionless quantities require "
                "a dimensionless Dimension."
            )

        # ==============================================================
        # Verification ↔ Engineering Quality
        # ==============================================================

        if (
            self.certified
            and self.confidence_score is not None
            and self.confidence_score < 0.90
        ):
            raise ValueError(
                "Certified quantities require "
                "confidence >= 0.90."
            )

        if (
            self.certified
            and self.quality_score is not None
            and self.quality_score < 0.90
        ):
            raise ValueError(
                "Certified quantities require "
                "quality >= 0.90."
            )

        if (
            self.certified
            and not self.peer_reviewed
        ):
            raise ValueError(
                "Certified quantities must be "
                "peer reviewed."
            )

        if (
            self.certified
            and not self.traceable
        ):
            raise ValueError(
                "Certified quantities must be "
                "traceable."
            )

        # ==============================================================
        # Experimental consistency
        # ==============================================================

        if (
            self.experimentally_validated
            and self.validation_reference is None
        ):
            raise ValueError(
                "Experimental validation requires "
                "a validation reference."
            )

        if (
            self.experimentally_validated
            and self.validation_document is None
        ):
            raise ValueError(
                "Experimental validation requires "
                "a validation document."
            )

        # ==============================================================
        # Repository ↔ Engineering Lifecycle
        # ==============================================================

        if (
            self.approved_by is not None
            and self.validation_status is None
        ):
            raise ValueError(
                "Approved quantities require "
                "a validation status."
            )

        if (
            self.lifecycle_state is not None
            and self.archived
            and self.lifecycle_state.lower() != "archived"
        ):
            raise ValueError(
                "Archived quantities must use "
                "the Archived lifecycle state."
            )

        # ==============================================================
        # Knowledge Graph ↔ AI
        # ==============================================================

        if (
            self.semantic_indexed
            and not self.searchable_by_ai
        ):
            raise ValueError(
                "Semantic indexing requires "
                "AI searchability."
            )

        if (
            self.graph_indexed
            and not self.indexable
        ):
            raise ValueError(
                "Graph indexing requires "
                "indexable=True."
            )

        if (
            self.reasoning_enabled
            and not self.searchable
        ):
            raise ValueError(
                "Reasoning-enabled quantities "
                "must be searchable."
            )

        # ==============================================================
        # Engineering ownership
        # ==============================================================

        if (
            self.flight_critical
            and self.technology_readiness_level
            is not None
            and self.technology_readiness_level < 6
        ):
            raise ValueError(
                "Flight-critical quantities should "
                "have TRL >= 6."
            )

        # ==============================================================
        # Engineering metadata
        # ==============================================================

        if (
            self.project_name is not None
            and self.program_name is None
        ):
            raise ValueError(
                "Projects must belong to "
                "a program."
            )

        if (
            self.mission_name is not None
            and self.vehicle_name is None
        ):
            raise ValueError(
                "Missions must reference "
                "a vehicle."
            )

        # ==============================================================
        # AI metadata
        # ==============================================================

        if (
            self.ai_verified
            and self.engineering_summary is None
        ):
            raise ValueError(
                "Verified AI metadata requires "
                "an engineering_summary."
            )

        if (
            self.embedding_identifier is not None
            and self.vector_dimension is None
        ):
            raise ValueError(
                "Embedding identifiers require "
                "a vector dimension."
            )

        # ==============================================================
        # Future Enterprise Validation
        # ==============================================================

        #
        # Future COSMOS releases will additionally validate:
        #
        # • Physics consistency
        # • Dimensional analysis
        # • Ontology consistency
        # • Repository integrity
        # • Digital thread completeness
        # • Solver compatibility
        # • Simulation compatibility
        # • Knowledge graph completeness
        # • AI reasoning consistency
        # • PLM integration
        #

    def _validate_identity(self) -> None:
        """
        Validate the complete engineering identity of the quantity.

        Identity validation is intentionally decomposed into multiple
        focused validation stages to improve maintainability,
        readability, unit testing, and future extensibility.

        Every Quantity within COSMOS must possess a complete,
        unique, searchable, and scientifically meaningful identity.
        """

        self._validate_required_identity_fields()

        self._validate_identity_strings()

        self._validate_identifier()

        self._validate_name()

        self._validate_symbol()

        self._validate_aliases()

        self._validate_search_keywords()

        self._validate_tags()

        self._validate_identity_lengths()

        self._validate_identity_duplicates()

        self._validate_identity_consistency()

    def _validate_required_identity_fields(self) -> None:
        """Validate that every mandatory identity field exists."""

        required_fields = (
            ("quantity_id", self.quantity_id),
            ("name", self.name),
            ("short_name", self.short_name),
            ("symbol", self.symbol),
            ("description", self.description),
            ("physical_quantity_name", self.physical_quantity_name),
            ("physical_quantity_symbol", self.physical_quantity_symbol),
        )

        for field_name, value in required_fields:
            if value is None:
                raise ValueError(f"{field_name} cannot be None.")
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be blank.")

    def _validate_identity_strings(self) -> None:
        """Validate identity strings for formatting and whitespace."""

        fields = (
            ("quantity_id", self.quantity_id),
            ("name", self.name),
            ("short_name", self.short_name),
            ("symbol", self.symbol),
            ("description", self.description),
            ("physical_quantity_name", self.physical_quantity_name),
            ("physical_quantity_symbol", self.physical_quantity_symbol),
        )

        for field_name, value in fields:
            if value != value.strip():
                raise ValueError(
                    f"{field_name} cannot contain leading or trailing whitespace."
                )
            if any(ch in value for ch in ('\n', '\r', '\t')):
                raise ValueError(f"{field_name} cannot contain control characters.")
            if "  " in value:
                raise ValueError(f"{field_name} cannot contain consecutive spaces.")

    def _validate_identifier(self) -> None:
        """Validate the engineering identifier."""

        if not _IDENTIFIER_PATTERN.fullmatch(self.quantity_id):
            raise ValueError("quantity_id contains invalid characters.")
        if self.quantity_id.startswith(".") or self.quantity_id.endswith("."):
            raise ValueError("quantity_id cannot begin or end with '.'.")

        reserved = {"NULL", "NONE", "UNKNOWN", "UNDEFINED", "DEFAULT"}
        if self.quantity_id.upper() in reserved:
            raise ValueError("quantity_id uses a reserved identifier.")

    def _validate_name(self) -> None:
        """Validate engineering names."""

        names = (
            ("name", self.name),
            ("short_name", self.short_name),
            ("physical_quantity_name", self.physical_quantity_name),
        )
        reserved = {"unknown", "undefined", "null", "none", "default", "temp", "test"}

        for field_name, value in names:
            if not _NAME_PATTERN.fullmatch(value):
                raise ValueError(f"{field_name} contains invalid characters.")
            if value.lower() in reserved:
                raise ValueError(f"{field_name} uses a reserved engineering name.")
            if value[0].isdigit():
                raise ValueError(f"{field_name} cannot begin with a digit.")
            if value.endswith("."):
                raise ValueError(f"{field_name} cannot end with '.'.")
            if "--" in value or "__" in value:
                raise ValueError(f"{field_name} contains repeated separators.")

        if self.name.casefold() == self.short_name.casefold():
            raise ValueError("short_name should differ from name.")
        if (
            self.name.casefold() == self.physical_quantity_name.casefold()
            and len(self.name) < 3
        ):
            raise ValueError("Engineering names are too short.")

    def _validate_symbol(self) -> None:
        """Validate engineering and scientific symbols."""

        symbols = (
            ("symbol", self.symbol),
            ("physical_quantity_symbol", self.physical_quantity_symbol),
        )
        reserved = {"unknown", "undefined", "null", "none"}

        for field_name, value in symbols:
            if not _SYMBOL_PATTERN.fullmatch(value):
                raise ValueError(f"{field_name} contains invalid characters.")
            if value.casefold() in reserved:
                raise ValueError(f"{field_name} uses a reserved symbol.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be blank.")

        if self.symbol.casefold() == self.name.casefold():
            raise ValueError("symbol should not equal name.")
        if self.symbol.casefold() == self.description.casefold():
            raise ValueError("symbol should not equal description.")
        if len(self.symbol) > 32:
            raise ValueError("Engineering symbols should remain concise.")
        if len(self.physical_quantity_symbol) > 32:
            raise ValueError("physical_quantity_symbol is too long.")

    def _validate_aliases(self) -> None:
        """Validate engineering aliases."""

        if not isinstance(self.aliases, tuple):
            raise TypeError("aliases must be a tuple.")

        reserved_aliases = {
            "unknown", "undefined", "none", "null", "default", "temp", "test",
        }
        canonical_identity = {
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
            self.symbol.casefold(),
            self.physical_quantity_name.casefold(),
            self.physical_quantity_symbol.casefold(),
        }
        normalized_aliases: set[str] = set()

        for alias in self.aliases:
            if not isinstance(alias, str):
                raise TypeError("Each alias must be a string.")
            cleaned = alias.strip()
            if not cleaned:
                raise ValueError("Aliases cannot contain blank values.")
            if len(cleaned) < 2 or len(cleaned) > 128:
                raise ValueError(f"Alias '{cleaned}' has invalid length.")
            if not _NAME_PATTERN.fullmatch(cleaned):
                raise ValueError(f"Alias '{cleaned}' contains invalid characters.")
            lowered = cleaned.casefold()
            if lowered in reserved_aliases:
                raise ValueError(f"Alias '{cleaned}' is reserved.")
            if lowered in normalized_aliases:
                raise ValueError(f"Duplicate alias '{cleaned}'.")
            if lowered in canonical_identity:
                raise ValueError(
                    f"Alias '{cleaned}' duplicates a canonical identity field."
                )
            normalized_aliases.add(lowered)

        if len(self.aliases) > 100:
            raise ValueError("A Quantity may define at most 100 aliases.")

    def _validate_search_keywords(self) -> None:
        """Validate search keywords."""

        if not isinstance(self.search_keywords, tuple):
            raise TypeError("search_keywords must be a tuple.")

        reserved_keywords = {"unknown", "undefined", "null", "none", "default"}
        canonical_identity = {
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
        }
        normalized_keywords: set[str] = set()

        for keyword in self.search_keywords:
            if not isinstance(keyword, str):
                raise TypeError("Each search keyword must be a string.")
            cleaned = keyword.strip()
            if not cleaned:
                raise ValueError("Search keywords cannot be blank.")
            if len(cleaned) < 2 or len(cleaned) > 64:
                raise ValueError(f"Keyword '{cleaned}' has invalid length.")
            if cleaned.startswith("-") or cleaned.endswith("-"):
                raise ValueError(f"Keyword '{cleaned}' has invalid hyphen placement.")
            lowered = cleaned.casefold()
            if lowered in reserved_keywords:
                raise ValueError(f"Keyword '{cleaned}' is reserved.")
            if lowered in canonical_identity:
                raise ValueError(
                    f"Keyword '{cleaned}' duplicates a canonical identity field."
                )
            if lowered in normalized_keywords:
                raise ValueError(f"Duplicate search keyword '{cleaned}'.")
            normalized_keywords.add(lowered)

        if len(self.search_keywords) > 200:
            raise ValueError("A Quantity may define at most 200 search keywords.")

    def _validate_tags(self) -> None:
        """Validate engineering tags."""

        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be a tuple.")

        reserved_tags = {
            "unknown", "undefined", "none", "null", "default",
            "misc", "temporary", "temp", "test",
        }
        canonical_identity = {
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
            self.symbol.casefold(),
            self.physical_quantity_name.casefold(),
            self.physical_quantity_symbol.casefold(),
        }
        normalized_tags: set[str] = set()

        for tag in self.tags:
            if not isinstance(tag, str):
                raise TypeError("Each tag must be a string.")
            cleaned = tag.strip()
            if not cleaned:
                raise ValueError("Tags cannot contain blank values.")
            if len(cleaned) < 2 or len(cleaned) > 64:
                raise ValueError(f"Tag '{cleaned}' has invalid length.")
            if not _NAME_PATTERN.fullmatch(cleaned):
                raise ValueError(f"Tag '{cleaned}' contains invalid characters.")
            if cleaned != tag:
                raise ValueError(f"Tag '{tag}' contains leading or trailing whitespace.")
            lowered = cleaned.casefold()
            if lowered in reserved_tags:
                raise ValueError(f"Tag '{cleaned}' is reserved.")
            if lowered in normalized_tags:
                raise ValueError(f"Duplicate tag '{cleaned}'.")
            if lowered in canonical_identity:
                raise ValueError(f"Tag '{cleaned}' duplicates a canonical identity field.")
            normalized_tags.add(lowered)

        if len(self.tags) > 100:
            raise ValueError("A Quantity may define at most 100 tags.")

    def _validate_identity_lengths(self) -> None:
        """Validate length constraints for identity fields."""

        field_limits = (
            ("quantity_id", self.quantity_id, 128),
            ("name", self.name, 256),
            ("short_name", self.short_name, 64),
            ("symbol", self.symbol, 32),
            ("physical_quantity_name", self.physical_quantity_name, 256),
            ("physical_quantity_symbol", self.physical_quantity_symbol, 32),
            ("description", self.description, 4096),
        )

        for field_name, value, maximum_length in field_limits:
            if len(value) == 0:
                raise ValueError(f"{field_name} cannot be empty.")
            if len(value) > maximum_length:
                raise ValueError(
                    f"{field_name} exceeds the maximum supported length "
                    f"of {maximum_length} characters."
                )

        if len(self.aliases) > 100:
            raise ValueError("A Quantity may define at most 100 aliases.")
        if len(self.search_keywords) > 200:
            raise ValueError("A Quantity may define at most 200 search keywords.")
        if len(self.tags) > 100:
            raise ValueError("A Quantity may define at most 100 tags.")

    def _validate_identity_duplicates(self) -> None:
        """Validate duplicate values across identity collections."""

        collections = (
            ("aliases", self.aliases),
            ("search_keywords", self.search_keywords),
            ("tags", self.tags),
        )

        for collection_name, values in collections:
            normalized: set[str] = set()
            for value in values:
                lowered = value.casefold()
                if lowered in normalized:
                    raise ValueError(
                        f"Duplicate value '{value}' found in {collection_name}."
                    )
                normalized.add(lowered)

        alias_set = {value.casefold() for value in self.aliases}
        keyword_set = {value.casefold() for value in self.search_keywords}
        tag_set = {value.casefold() for value in self.tags}

        duplicate_alias_keywords = alias_set & keyword_set
        if duplicate_alias_keywords:
            raise ValueError(
                "Aliases and search_keywords contain duplicate values: "
                f"{sorted(duplicate_alias_keywords)}"
            )

        duplicate_alias_tags = alias_set & tag_set
        if duplicate_alias_tags:
            raise ValueError(
                "Aliases and tags contain duplicate values: "
                f"{sorted(duplicate_alias_tags)}"
            )

        duplicate_keyword_tags = keyword_set & tag_set
        if duplicate_keyword_tags:
            raise ValueError(
                "search_keywords and tags contain duplicate values: "
                f"{sorted(duplicate_keyword_tags)}"
            )

    def _validate_identity_consistency(self) -> None:
        """Validate consistency between all identity fields."""

        if self.name.casefold() == self.short_name.casefold():
            raise ValueError("short_name must differ from name.")
        if self.name.casefold() == self.symbol.casefold():
            raise ValueError("symbol must differ from name.")
        if (
            self.physical_quantity_name.casefold() == self.name.casefold()
            and self.category is not QuantityCategory.SCALAR
        ):
            raise ValueError(
                "physical_quantity_name should provide additional scientific meaning."
            )
        if self.symbol.casefold() == self.physical_quantity_symbol.casefold():
            raise ValueError("symbol and physical_quantity_symbol must differ.")
        if len(self.symbol) > len(self.name):
            raise ValueError("Engineering symbols should normally be shorter than names.")
        if self.description.casefold() == self.name.casefold():
            raise ValueError("description cannot duplicate name.")
        if self.description.casefold() == self.short_name.casefold():
            raise ValueError("description cannot duplicate short_name.")

        canonical_values = (
            self.quantity_id.casefold(),
            self.name.casefold(),
            self.short_name.casefold(),
            self.symbol.casefold(),
            self.physical_quantity_name.casefold(),
            self.physical_quantity_symbol.casefold(),
        )
        if len(canonical_values) != len(set(canonical_values)):
            raise ValueError("Canonical identity fields must all be unique.")

        if len(self.search_keywords) == 0 and len(self.aliases) == 0:
            raise ValueError("At least one alias or search keyword must be provided.")

        if len(self.name.split()) > 10:
            raise ValueError("Engineering names should remain concise.")
        if len(self.description.split()) < 5:
            raise ValueError(
                "description is too short to adequately describe the quantity."
            )
    # Identity & Display Properties
    # ==================================================================

    @property
    def display_name(self) -> str:
        """
        Human-readable display name.
        """
        return self.name

    @property
    def canonical_name(self) -> str:
        """
        Canonical engineering name.

        Returns the primary engineering name used throughout
        the COSMOS Knowledge Foundation.
        """
        return self.name

    @property
    def qualified_name(self) -> str:
        """
        Fully-qualified engineering name.
        """

        if self.engineering_domain is None:
            return self.name

        return (
            f"{self.engineering_domain.name}"
            f"::{self.name}"
        )

    @property
    def engineering_name(self) -> str:
        """
        Engineering display name.
        """

        return (
            f"{self.name} "
            f"({self.symbol})"
        )

    @property
    def scientific_name(self) -> str:
        """
        Scientific quantity name.
        """

        return (
            f"{self.physical_quantity_name} "
            f"({self.physical_quantity_symbol})"
        )

    @property
    def short_display_name(self) -> str:
        """
        Short display name.
        """

        return (
            f"{self.short_name} "
            f"({self.symbol})"
        )

    @property
    def display_symbol(self) -> str:
        """
        Preferred display symbol.
        """

        return self.symbol

    # ==================================================================
    # Python Display Methods
    # ==================================================================

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            f"{self.name} "
            f"[{self.symbol}] = "
            f"{self.value} "
            f"{self.unit.symbol}"
        )

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return (
            "Quantity("
            f"quantity_id={self.quantity_id!r}, "
            f"name={self.name!r}, "
            f"value={self.value!r}, "
            f"unit={self.unit.symbol!r})"
        )

    # ==================================================================
    # Identity Methods
    # ==================================================================

    def identity_key(self) -> tuple[str, str]:
        """
        Return the canonical identity key.

        Returns
        -------
        tuple[str, str]
            (quantity_id, canonical_name)
        """

        return (
            self.quantity_id,
            self.canonical_name,
        )

    def identity_hash(self) -> int:
        """
        Stable identity hash.

        Returns
        -------
        int
        """

        return hash(
            (
                self.quantity_id,
                self.name,
                self.symbol,
            )
        )

    def display_tuple(
        self,
    ) -> tuple[str, str, float, str]:
        """
        Compact display tuple.

        Returns
        -------
        tuple
        """

        return (
            self.name,
            self.symbol,
            self.value,
            self.unit.symbol,
        )

    # ==================================================================
    # Summary Methods
    # ==================================================================

    def identity_summary(self) -> str:
        """
        Return an identity summary.
        """

        return (
            f"{self.name} "
            f"({self.symbol}) "
            f"[{self.quantity_id}]"
        )

    def format_engineering_summary(self) -> str:
        """
        Return an engineering summary.
        """

        return (
            f"{self.engineering_name}\n"
            f"Category : {self.category.name}\n"
            f"Value    : {self.value}\n"
            f"Unit     : {self.unit.symbol}\n"
            f"Domain   : "
            f"{self.engineering_domain.name if self.engineering_domain else 'N/A'}")

    def scientific_summary(self) -> str:
        """
        Return a scientific summary.
        """

        return (
            f"{self.physical_quantity_name}\n"
            f"Symbol      : {self.physical_quantity_symbol}\n"
            f"Dimension   : {self.dimension}\n"
            f"Unit        : {self.unit.symbol}"
        )

    def compact_repository_summary(self) -> str:
        """
        Return repository information.
        """

        return (
            f"Repository ID : "
            f"{self.repository_identifier}\n"
            f"Version       : "
            f"{self.version}\n"
            f"Revision      : "
            f"{self.revision}"
        )

    def graph_summary(self) -> str:
        """
        Return Knowledge Graph information.
        """

        return (
            f"Graph Node : "
            f"{self.graph_node_id}\n"
            f"Ontology   : "
            f"{self.ontology_identifier}\n"
            f"Searchable : "
            f"{self.searchable}"
        )

    # ==================================================================
    # Export Methods
    # ==================================================================

    def to_display_string(self) -> str:
        """
        Return a formatted display string.
        """

        return str(self)

    def to_text(self) -> str:
        """
        Plain-text representation.
        """

        return self.format_engineering_summary()

    def to_console(self) -> str:
        """
        Console-friendly representation.
        """

        return (
            "=" * 70
            + "\n"
            + self.format_engineering_summary()
            + "\n"
            + "=" * 70
        )

    def to_markdown(self) -> str:
        """
        Markdown representation.
        """

        return (
            f"# {self.name}\n\n"
            f"- **Symbol:** {self.symbol}\n"
            f"- **Value:** {self.value}\n"
            f"- **Unit:** {self.unit.symbol}\n"
            f"- **Category:** {self.category.name}\n"
            f"- **Quantity ID:** {self.quantity_id}\n"
        )

    # ==================================================================
    # Scientific Classification Methods
    # ==================================================================

    @property
    def is_scalar(self) -> bool:
        """
        Return True if this is a scalar quantity.
        """
        return self.category is QuantityCategory.SCALAR

    @property
    def is_vector(self) -> bool:
        """
        Return True if this is a vector quantity.
        """
        return self.category is QuantityCategory.VECTOR

    @property
    def is_tensor(self) -> bool:
        """
        Return True if this is a tensor quantity.
        """
        return self.category is QuantityCategory.TENSOR

    @property
    def is_dimensionless(self) -> bool:
        """
        Return True if the quantity is dimensionless.
        """
        return self.dimensionless

    @property
    def is_base_quantity(self) -> bool:
        """
        Return True if this is an SI base quantity.
        """
        return self.dimension.is_base_dimension

    @property
    def is_derived_quantity(self) -> bool:
        """
        Return True if this is an SI derived quantity.
        """
        return self.dimension.is_derived_dimension

    @property
    def is_measured(self) -> bool:
        """
        Return True if experimentally measured.
        """
        return (
            self.measurement_type
            is MeasurementType.MEASURED
        )

    @property
    def is_calculated(self) -> bool:
        """
        Return True if analytically calculated.
        """
        return (
            self.measurement_type
            is MeasurementType.CALCULATED
        )

    @property
    def is_simulated(self) -> bool:
        """
        Return True if produced by simulation.
        """
        return (
            self.measurement_type
            is MeasurementType.SIMULATED
        )

    @property
    def is_estimated(self) -> bool:
        """
        Return True if estimated.
        """
        return (
            self.measurement_type
            is MeasurementType.ESTIMATED
        )

    @property
    def is_exact(self) -> bool:
        """
        Return True if mathematically exact.
        """
        return self.exact_value

    @property
    def has_uncertainty(self) -> bool:
        """
        Return True if uncertainty exists.
        """
        return self.uncertainty is not None

    @property
    def has_limits(self) -> bool:
        """
        Return True if limits are defined.
        """
        return (
            self.minimum_value is not None
            or self.maximum_value is not None
        )

    @property
    def effective_tolerance(self) -> float | None:
        """
        Return the effective symmetric tolerance, if defined.
        """

        candidates: list[float] = []

        if self.tolerance_plus is not None:
            candidates.append(self.tolerance_plus)

        if self.tolerance_minus is not None:
            candidates.append(self.tolerance_minus)

        if (
            self.tolerance_percent is not None
            and self.nominal_value is not None
        ):
            candidates.append(
                abs(self.nominal_value)
                * self.tolerance_percent
                / 100.0
            )

        if not candidates:
            return None

        return max(candidates)

    @property
    def has_tolerance(self) -> bool:
        """
        Return True if tolerance is defined.
        """
        return self.effective_tolerance is not None

    @property
    def uses_si_units(self) -> bool:
        """
        Return True if the unit belongs to SI.

        Assumes Unit exposes an `is_si` property.
        """

        return bool(
            getattr(
                self.unit,
                "is_si",
                False,
            )
        )

    @property
    def scientific_signature(self) -> tuple[
        QuantityCategory,
        QuantityType,
        MeasurementType,
    ]:
        """
        Return the scientific classification signature.
        """

        return (
            self.category,
            self.unit.quantity_type,
            self.measurement_type,
        )

    # ==================================================================
    # Scientific Classification Summaries
    # ==================================================================

    def classification_summary(self) -> str:
        """
        Return a scientific classification summary.
        """

        return (
            f"Category          : {self.category.name}\n"
            f"Quantity Type     : {self.unit.quantity_type.name}\n"
            f"Measurement Type  : {self.measurement_type.name}"
        )

    def scientific_category(self) -> str:
        """
        Return a compact scientific category.
        """

        return (
            f"{self.category.name} | "
            f"{self.unit.quantity_type.name}"
        )

    def measurement_summary(self) -> str:
        """
        Return measurement information.
        """

        return (
            f"Measurement Type : "
            f"{self.measurement_type.name}\n"
            f"Measured         : {self.is_measured}\n"
            f"Calculated       : {self.is_calculated}\n"
            f"Simulated        : {self.is_simulated}\n"
            f"Estimated        : {self.is_estimated}"
        )

    def numerical_classification_summary(self) -> str:
        """
        Return numerical classification.
        """

        return (
            f"Exact Value      : {self.is_exact}\n"
            f"Has Limits       : {self.has_limits}\n"
            f"Has Uncertainty  : {self.has_uncertainty}\n"
            f"Has Tolerance    : {self.has_tolerance}"
        )

    def physics_summary(self) -> str:
        """
        Return a concise physics summary.
        """

        return (
            f"Physical Quantity : "
            f"{self.physical_quantity_name}\n"
            f"Symbol            : "
            f"{self.physical_quantity_symbol}\n"
            f"Dimensionless     : "
            f"{self.is_dimensionless}\n"
            f"SI Quantity       : "
            f"{self.uses_si_units}"
        )

    def scientific_overview(self) -> str:
        """
        Return a complete scientific overview.
        """

        return (
            "=" * 70
            + "\nSCIENTIFIC CLASSIFICATION\n"
            + "=" * 70
            + "\n"
            + self.classification_summary()
            + "\n\n"
            + self.measurement_summary()
            + "\n\n"
            + self.numerical_classification_summary()
            + "\n\n"
            + self.physics_summary()
        )

    # ==================================================================
    # Numerical & Statistical Methods
    # ==================================================================

    @property
    def span(self) -> float | None:
        """
        Return the numerical span (maximum - minimum).

        Returns
        -------
        float | None
            None if limits are incomplete.
        """

        if (
            self.minimum_value is None
            or self.maximum_value is None
        ):
            return None

        return self.maximum_value - self.minimum_value

    @property
    def midpoint(self) -> float | None:
        """
        Return the midpoint of the allowable range.
        """

        if (
            self.minimum_value is None
            or self.maximum_value is None
        ):
            return None

        return (
            self.minimum_value
            + self.maximum_value
        ) / 2.0

    @property
    def computed_relative_uncertainty(self) -> float | None:
        """
        Relative uncertainty.

        Returns
        -------
        float | None
        """

        if (
            self.uncertainty is None
            or self.value == 0.0
        ):
            return None

        return abs(self.uncertainty / self.value)

    @property
    def uncertainty_percent(self) -> float | None:
        """
        Uncertainty expressed as percent.
        """

        relative = self.computed_relative_uncertainty

        if relative is None:
            return None

        return relative * 100.0

    @property
    def coefficient_of_variation(self) -> float | None:
        """
        Standard deviation divided by mean.
        """

        if (
            self.standard_deviation is None
            or self.value == 0.0
        ):
            return None

        return (
            self.standard_deviation
            / abs(self.value)
        )

    # ==============================================================
    # Numerical Queries
    # ==============================================================

    def is_within_limits(
        self,
        value: float,
    ) -> bool:
        """
        Return True if a value lies within the allowable limits.
        """

        if (
            self.minimum_value is not None
            and value < self.minimum_value
        ):
            return False

        if (
            self.maximum_value is not None
            and value > self.maximum_value
        ):
            return False

        return True

    def is_nominal(
        self,
        tolerance_multiplier: float = 1.0,
    ) -> bool:
        """
        Return True if the stored value is within tolerance.
        """

        if self.effective_tolerance is None:
            return True

        if self.nominal_value is None:
            return True

        deviation = abs(
            self.value
            - self.nominal_value
        )

        return (
            deviation
            <= self.effective_tolerance
            * tolerance_multiplier
        )

    def absolute_error(
        self,
        reference_value: float,
    ) -> float:
        """
        Compute absolute error.
        """

        return abs(
            self.value
            - reference_value
        )

    def relative_error(
        self,
        reference_value: float,
    ) -> float:
        """
        Compute relative error.

        Raises
        ------
        ZeroDivisionError
            If the reference value is zero.
        """

        if reference_value == 0.0:
            raise ZeroDivisionError(
                "Reference value cannot be zero."
            )

        return (
            abs(
                self.value
                - reference_value
            )
            / abs(reference_value)
        )

    def percent_error(
        self,
        reference_value: float,
    ) -> float:
        """
        Compute percentage error.
        """

        return (
            self.relative_error(reference_value)
            * 100.0
        )

    # ==============================================================
    # Range Operations
    # ==============================================================

    def clamp(
        self,
        value: float,
    ) -> float:
        """
        Clamp a value to the allowable limits.
        """

        if (
            self.minimum_value is not None
            and value < self.minimum_value
        ):
            value = self.minimum_value

        if (
            self.maximum_value is not None
            and value > self.maximum_value
        ):
            value = self.maximum_value

        return value

    def normalize(
        self,
        value: float,
    ) -> float:
        """
        Normalize a value to [0, 1].

        Raises
        ------
        ValueError
            If limits are unavailable.
        """

        if (
            self.minimum_value is None
            or self.maximum_value is None
        ):
            raise ValueError(
                "Normalization requires both "
                "minimum_value and maximum_value."
            )

        span = self.maximum_value - self.minimum_value

        if span == 0.0:
            raise ValueError(
                "Normalization span is zero."
            )

        return (
            value
            - self.minimum_value
        ) / span

    # ==============================================================
    # Statistical Summary
    # ==============================================================

    def statistics_summary(self) -> str:
        """
        Return a numerical summary.
        """

        return (
            f"Value                  : {self.value}\n"
            f"Nominal                : {self.nominal_value}\n"
            f"Minimum                : {self.minimum_value}\n"
            f"Maximum                : {self.maximum_value}\n"
            f"Tolerance              : {self.effective_tolerance}\n"
            f"Uncertainty            : {self.uncertainty}\n"
            f"Std. Deviation         : {self.standard_deviation}\n"
            f"Relative Uncertainty   : "
            f"{self.computed_relative_uncertainty}\n"
            f"Uncertainty (%)        : "
            f"{self.uncertainty_percent}\n"
            f"Coefficient Variation  : "
            f"{self.coefficient_of_variation}"
        )

    def numerical_summary(self) -> str:
        """
        Return a concise numerical overview.
        """

        return (
            "=" * 70
            + "\nNUMERICAL SUMMARY\n"
            + "=" * 70
            + "\n"
            + self.statistics_summary()
        )

    # ==================================================================
    # Units & Dimensional Analysis Methods
    # ==================================================================

    @property
    def has_unit(self) -> bool:
        """
        Return True if a unit is associated with this quantity.
        """
        return self.unit is not None

    @property
    def has_dimension(self) -> bool:
        """
        Return True if a dimension is associated with this quantity.
        """
        return self.dimension is not None

    @property
    def is_unitless(self) -> bool:
        """
        Return True if the quantity has no unit.
        """
        return not self.has_unit

    @property
    def is_dimensionally_valid(self) -> bool:
        """
        Return True if both a Unit and Dimension exist.

        Actual dimensional verification is delegated to the
        Dimension model.
        """
        return (
            self.has_unit
            and self.has_dimension
        )

    @property
    def dimensional_signature(self) -> str:
        """
        Return the dimensional signature.

        Examples
        --------
        M
        L
        T
        M L T^-2
        """

        if self.dimension is None:
            return "Undefined"

        return str(self.dimension)

    @property
    def unit_symbol(self) -> str:
        """
        Return the preferred unit symbol.
        """

        if self.unit is None:
            return ""

        return self.unit.symbol

    @property
    def unit_name(self) -> str:
        """
        Return the preferred unit name.
        """

        if self.unit is None:
            return ""

        return self.unit.name

    # ==============================================================
    # Unit Comparison
    # ==============================================================

    def same_unit(
        self,
        other: "Quantity",
    ) -> bool:
        """
        Return True if both quantities use the same unit.
        """

        return self.unit == other.unit

    def same_dimension(
        self,
        other: "Quantity",
    ) -> bool:
        """
        Return True if both quantities share the same dimension.
        """

        return self.dimension == other.dimension

    def is_dimensionally_compatible(
        self,
        other: "Quantity",
    ) -> bool:
        """
        Return True if both quantities are dimensionally compatible.

        Compatibility checking is delegated to the Dimension
        implementation whenever available.
        """

        if (
            self.dimension is None
            or other.dimension is None
        ):
            return False

        compatibility = getattr(
            self.dimension,
            "is_compatible_with",
            None,
        )

        if callable(compatibility):
            return cast(bool, compatibility(other.dimension))

        return self.dimension == other.dimension

    def is_unit_convertible(
        self,
        other: "Quantity",
    ) -> bool:
        """
        Return True if both quantities are unit-convertible.

        Conversion logic is delegated to the Unit model.
        """

        if (
            self.unit is None
            or other.unit is None
        ):
            return False

        converter = getattr(
            self.unit,
            "is_convertible_to",
            None,
        )

        if callable(converter):
            return cast(bool, converter(other.unit))

        return self.same_dimension(other)

    # ==============================================================
    # Delegated Conversion
    # ==============================================================

    def convert_to(
        self,
        target_unit: Unit,
    ) -> "Quantity":
        """
        Convert this Quantity to another unit.

        Actual conversion is delegated to the Unit model.
        """

        if self.unit is None:
            raise ValueError(
                "Cannot convert a quantity "
                "without a unit."
            )

        converter = getattr(
            self.unit,
            "convert_value",
            None,
        )

        if not callable(converter):
            raise NotImplementedError(
                "Unit conversion is not "
                "implemented by the Unit model."
            )

        converted_value = converter(
            self.value,
            target_unit,
        )

        return dataclass_replace(
            self,
            value=converted_value,
            unit=target_unit,
        )

    # ==============================================================
    # Reporting
    # ==============================================================

    def unit_summary(self) -> str:
        """
        Return a summary of unit information.
        """

        if self.unit is None:
            return "No unit assigned."

        return (
            f"Name        : {self.unit.name}\n"
            f"Symbol      : {self.unit.symbol}\n"
            f"SI Unit     : "
            f"{getattr(self.unit, 'is_si', 'Unknown')}"
        )

    def dimension_summary(self) -> str:
        """
        Return a summary of dimensional information.
        """

        if self.dimension is None:
            return "No dimension assigned."

        return (
            f"Dimension   : {self.dimension}\n"
            f"Signature   : "
            f"{self.dimensional_signature}"
        )

    def physics_signature(self) -> str:
        """
        Return the physical signature of the quantity.
        """

        return (
            f"{self.name}\n"
            f"Value      : {self.value}\n"
            f"Unit       : {self.unit_symbol}\n"
            f"Dimension  : "
            f"{self.dimensional_signature}"
        )

    def unit_report(self) -> str:
        """
        Return a complete unit and dimension report.
        """

        return (
            "=" * 70
            + "\nUNITS & DIMENSIONS\n"
            + "=" * 70
            + "\n"
            + self.unit_summary()
            + "\n\n"
            + self.dimension_summary()
        )

    # ==================================================================
    # Knowledge Foundation Relationship Methods
    # ==================================================================

    @property
    def has_variable(self) -> bool:
        """
        Return True if a Variable is associated with this Quantity.
        """
        return self.variable is not None

    @property
    def has_equation(self) -> bool:
        """
        Return True if an Equation is associated with this Quantity.
        """
        return len(self.related_equation_ids) > 0

    @property
    def has_reference(self) -> bool:
        """
        Return True if a Reference is associated with this Quantity.
        """
        return self.source_reference is not None

    @property
    def has_document(self) -> bool:
        """
        Return True if a Document is associated with this Quantity.
        """
        return self.source_document is not None

    @property
    def has_domain(self) -> bool:
        """
        Return True if an EngineeringDomain is associated with this Quantity.
        """
        return self.engineering_domain is not None

    @property
    def has_subsystem(self) -> bool:
        """
        Return True if a Subsystem is associated with this Quantity.
        """
        return self.subsystem is not None

    # ==============================================================
    # Relationship Counts
    # ==============================================================

    @property
    def relationship_count(self) -> int:
        """
        Return the total number of directly associated
        engineering knowledge objects.
        """

        relationships = (
            self.has_variable,
            self.has_equation,
            self.has_reference,
            self.has_document,
            self.has_domain,
            self.has_subsystem,
        )

        return sum(relationships)

    # ==============================================================
    # Relationship Access
    # ==============================================================

    def related_objects(self) -> dict[str, object]:
        """
        Return all directly related knowledge objects.

        Returns
        -------
        dict[str, object]
        """

        return {
            "variable": self.variable,
            "equation_ids": self.related_equation_ids,
            "reference": self.source_reference,
            "document": self.source_document,
            "engineering_domain": self.engineering_domain,
            "subsystem": self.subsystem,
        }

    def relationship_names(self) -> tuple[str, ...]:
        """
        Return the names of populated relationships.
        """

        names: list[str] = []

        if self.has_variable:
            names.append("Variable")

        if self.has_equation:
            names.append("Equation")

        if self.has_reference:
            names.append("Reference")

        if self.has_document:
            names.append("Document")

        if self.has_domain:
            names.append("EngineeringDomain")

        if self.has_subsystem:
            names.append("Subsystem")

        return tuple(names)

    # ==============================================================
    # Traceability
    # ==============================================================

    def traceability_summary(self) -> str:
        """
        Return engineering traceability information.
        """

        return (
            f"Reference            : "
            f"{self.has_reference}\n"
            f"Document             : "
            f"{self.has_document}\n"
            f"Equation             : "
            f"{self.has_equation}\n"
            f"Variable             : "
            f"{self.has_variable}\n"
            f"Engineering Domain   : "
            f"{self.has_domain}\n"
            f"Subsystem            : "
            f"{self.has_subsystem}"
        )

    def citation_summary(self) -> str:
        """
        Return citation information.
        """

        if self.source_reference is None:
            return "No reference assigned."

        return str(self.source_reference)

    def document_summary(self) -> str:
        """
        Return document information.
        """

        if self.source_document is None:
            return "No document assigned."

        title = getattr(
            self.source_document,
            "title",
            "Unknown",
        )

        identifier = getattr(
            self.source_document,
            "document_id",
            "Unknown",
        )

        return (
            f"Document ID : {identifier}\n"
            f"Title       : {title}"
        )

    def equation_summary(self) -> str:
        """
        Return equation information.
        """

        if not self.related_equation_ids:
            return "No equation assigned."

        return (
            "Equation IDs : "
            + ", ".join(self.related_equation_ids)
        )

    def variable_summary(self) -> str:
        """
        Return variable information.
        """

        if self.variable is None:
            return "No variable assigned."

        variable_name = getattr(
            self.variable,
            "name",
            "Unknown",
        )

        variable_symbol = getattr(
            self.variable,
            "symbol",
            "Unknown",
        )

        return (
            f"Variable : {variable_name}\n"
            f"Symbol   : {variable_symbol}"
        )

    # ==============================================================
    # Knowledge Overview
    # ==============================================================

    def knowledge_summary(self) -> str:
        """
        Return a high-level summary of all knowledge
        relationships associated with this Quantity.
        """

        return (
            "=" * 70
            + "\nKNOWLEDGE FOUNDATION\n"
            + "=" * 70
            + "\n"
            + f"Relationships : {self.relationship_count}\n\n"
            + self.traceability_summary()
        )

    def relationship_report(self) -> str:
        """
        Return a complete relationship report.
        """

        sections = [
            "=" * 70,
            "KNOWLEDGE RELATIONSHIPS",
            "=" * 70,
            "",
            self.variable_summary(),
            "",
            self.equation_summary(),
            "",
            self.document_summary(),
            "",
            self.citation_summary(),
        ]

        return "\n".join(sections)

    # ==================================================================
    # Engineering Metadata Methods
    # ==================================================================

    @property
    def is_verified(self) -> bool:
        """
        Return True if the quantity has been verified.
        """
        return (
            self.verification_status is not None
            and self.verification_status.casefold() == "verified"
        )

    @property
    def is_validated(self) -> bool:
        """
        Return True if the quantity has been validated.
        """
        return (
            self.validation_status is not None
            and self.validation_status.casefold() == "validated"
        )

    @property
    def is_certified(self) -> bool:
        """
        Return True if the quantity is certified.
        """
        return self.certified

    @property
    def is_traceable(self) -> bool:
        """
        Return True if engineering traceability exists.
        """
        return self.traceable

    @property
    def is_peer_reviewed(self) -> bool:
        """
        Return True if peer reviewed.
        """
        return self.peer_reviewed

    @property
    def is_experimentally_validated(self) -> bool:
        """
        Return True if experimentally validated.
        """
        return self.experimentally_validated

    @property
    def is_independently_verified(self) -> bool:
        """
        Return True if independently verified.
        """
        return self.independently_verified

    # ==============================================================
    # Criticality
    # ==============================================================

    @property
    def is_safety_critical(self) -> bool:
        """
        Return True if safety critical.
        """
        return self.safety_critical

    @property
    def is_mission_critical(self) -> bool:
        """
        Return True if mission critical.
        """
        return self.mission_critical

    @property
    def is_flight_critical(self) -> bool:
        """
        Return True if flight critical.
        """
        return self.flight_critical

    @property
    def criticality_level(self) -> str:
        """
        Return the highest engineering criticality.
        """

        if self.flight_critical:
            return "Flight Critical"

        if self.mission_critical:
            return "Mission Critical"

        if self.safety_critical:
            return "Safety Critical"

        return "Standard"

    # ==============================================================
    # Readiness
    # ==============================================================

    @property
    def readiness_summary(self) -> dict[str, int | None]:
        """
        Return engineering readiness levels.
        """

        return {
            "TRL": self.technology_readiness_level,
            "MRL": self.manufacturing_readiness_level,
            "ORL": self.operational_readiness_level,
        }

    @property
    def average_readiness_level(self) -> float | None:
        """
        Return the average engineering readiness level.
        """

        values = [
            value
            for value in (
                self.technology_readiness_level,
                self.manufacturing_readiness_level,
                self.operational_readiness_level,
            )
            if value is not None
        ]

        if not values:
            return None

        return sum(values) / len(values)

    # ==============================================================
    # Ownership
    # ==============================================================

    @property
    def has_owner(self) -> bool:
        """
        Return True if an owner exists.
        """

        return any(
            (
                self.responsible_engineer,
                self.technical_lead,
                self.chief_engineer,
            )
        )

    def owner_summary(self) -> str:
        """
        Return ownership information.
        """

        return (
            f"Responsible Engineer : "
            f"{self.responsible_engineer or 'N/A'}\n"
            f"Technical Lead       : "
            f"{self.technical_lead or 'N/A'}\n"
            f"Chief Engineer       : "
            f"{self.chief_engineer or 'N/A'}\n"
            f"Team                 : "
            f"{self.responsible_team or 'N/A'}"
        )

    # ==============================================================
    # Engineering Quality
    # ==============================================================

    def engineering_status(self) -> str:
        """
        Return a concise engineering status.
        """

        return (
            f"Verified   : {self.is_verified}\n"
            f"Validated  : {self.is_validated}\n"
            f"Certified  : {self.is_certified}\n"
            f"Traceable  : {self.is_traceable}"
        )

    def quality_summary(self) -> str:
        """
        Return engineering quality metrics.
        """

        return (
            f"Confidence Score : "
            f"{self.confidence_score}\n"
            f"Evidence Score   : "
            f"{self.evidence_score}\n"
            f"Quality Score    : "
            f"{self.quality_score}\n"
            f"Peer Reviewed    : "
            f"{self.is_peer_reviewed}\n"
            f"Independent V&V  : "
            f"{self.is_independently_verified}"
        )

    def criticality_summary(self) -> str:
        """
        Return engineering criticality information.
        """

        return (
            f"Criticality Level : "
            f"{self.criticality_level}\n"
            f"Safety Critical   : "
            f"{self.is_safety_critical}\n"
            f"Mission Critical  : "
            f"{self.is_mission_critical}\n"
            f"Flight Critical   : "
            f"{self.is_flight_critical}"
        )

    def lifecycle_summary(self) -> str:
        """
        Return lifecycle information.
        """

        return (
            f"Lifecycle State : "
            f"{self.lifecycle_state or 'N/A'}\n"
            f"Version         : "
            f"{self.version}\n"
            f"Revision        : "
            f"{self.revision}\n"
            f"Archived        : "
            f"{self.archived}\n"
            f"Locked          : "
            f"{self.locked}"
        )

    # ==============================================================
    # Enterprise Engineering Report
    # ==============================================================

    def engineering_report(self) -> str:
        """
        Return a complete engineering report.
        """

        sections = [
            "=" * 72,
            "ENGINEERING METADATA",
            "=" * 72,
            "",
            self.engineering_status(),
            "",
            self.quality_summary(),
            "",
            self.criticality_summary(),
            "",
            self.owner_summary(),
            "",
            self.lifecycle_summary(),
            "",
            f"Readiness Levels : {self.readiness_summary}",
        ]

        return "\n".join(sections)

    # ==================================================================
    # Repository, Search & Knowledge Graph Methods
    # ==================================================================

    @property
    def repository_key(self) -> str:
        """
        Return the canonical repository key.
        """

        return (
            self.repository_identifier
            or self.quantity_id
        )

    @property
    def repository_location(self) -> str:
        """
        Return the repository location.
        """

        if self.repository_path is None:
            return "Unknown"

        return self.repository_path

    @property
    def graph_identifier(self) -> str:
        """
        Return the Knowledge Graph node identifier.
        """

        return (
            self.graph_node_id
            or self.quantity_id
        )

    @property
    def ontology_key(self) -> str:
        """
        Return the ontology identifier.
        """

        return (
            self.ontology_identifier
            or self.quantity_id
        )

    @property
    def semantic_key(self) -> str:
        """
        Return the semantic embedding identifier.
        """

        return (
            self.embedding_identifier
            or self.quantity_id
        )

    @property
    def is_repository_managed(self) -> bool:
        """
        Return True if repository metadata exists.
        """

        return self.repository_identifier is not None

    @property
    def is_graph_node(self) -> bool:
        """
        Return True if the quantity participates in
        the Knowledge Graph.
        """

        return self.graph_node_id is not None

    @property
    def is_semantically_indexed(self) -> bool:
        """
        Return True if semantic indexing exists.
        """

        return self.semantic_indexed

    @property
    def is_graph_indexed(self) -> bool:
        """
        Return True if graph indexing exists.
        """

        return self.graph_indexed

    @property
    def is_ai_searchable(self) -> bool:
        """
        Return True if searchable by AI.
        """

        return self.searchable_by_ai

    @property
    def search_term_count(self) -> int:
        """
        Return the total number of searchable terms.
        """

        return (
            len(self.aliases)
            + len(self.search_keywords)
            + len(self.tags)
        )

    # ==============================================================
    # Search Methods
    # ==============================================================

    def searchable_terms(self) -> tuple[str, ...]:
        """
        Return every searchable engineering term.
        """

        terms: set[str] = {
            self.name,
            self.short_name,
            self.symbol,
            self.physical_quantity_name,
            self.physical_quantity_symbol,
        }

        terms.update(self.aliases)
        terms.update(self.search_keywords)
        terms.update(self.tags)

        return tuple(sorted(terms))

    def matches_search_term(
        self,
        term: str,
        *,
        case_sensitive: bool = False,
    ) -> bool:
        """
        Return True if a search term matches this quantity.
        """

        if case_sensitive:

            return term in self.searchable_terms()

        term = term.casefold()

        return any(
            candidate.casefold() == term
            for candidate in self.searchable_terms()
        )

    # ==============================================================
    # Repository Metadata
    # ==============================================================

    def repository_summary(self) -> str:
        """
        Return repository information.
        """

        return (
            f"Repository ID : "
            f"{self.repository_identifier or 'N/A'}\n"
            f"Repository Path : "
            f"{self.repository_path or 'N/A'}\n"
            f"Version : {self.version}\n"
            f"Revision : {self.revision}"
        )

    def semantic_summary(self) -> str:
        """
        Return semantic indexing information.
        """

        return (
            f"Semantic Indexed : "
            f"{self.semantic_indexed}\n"
            f"AI Searchable    : "
            f"{self.searchable_by_ai}\n"
            f"Embedding ID     : "
            f"{self.embedding_identifier or 'N/A'}\n"
            f"Embedding Model  : "
            f"{self.embedding_model or 'N/A'}"
        )

    def ontology_summary(self) -> str:
        """
        Return ontology metadata.
        """

        return (
            f"Ontology Identifier : "
            f"{self.ontology_identifier or 'N/A'}\n"
            f"Graph Indexed       : "
            f"{self.graph_indexed}\n"
            f"Graph Node          : "
            f"{self.graph_node_id or 'N/A'}"
        )

    def knowledge_graph_summary(self) -> str:
        """
        Return Knowledge Graph information.
        """

        return (
            f"Graph Node ID : "
            f"{self.graph_node_id or 'N/A'}\n"
            f"Ontology ID   : "
            f"{self.ontology_identifier or 'N/A'}\n"
            f"Semantic ID   : "
            f"{self.embedding_identifier or 'N/A'}"
        )

    # ==============================================================
    # Complete Repository Report
    # ==============================================================

    def repository_report(self) -> str:
        """
        Return a complete repository and graph report.
        """

        sections = [
            "=" * 72,
            "REPOSITORY & KNOWLEDGE GRAPH",
            "=" * 72,
            "",
            self.repository_summary(),
            "",
            self.semantic_summary(),
            "",
            self.ontology_summary(),
            "",
            self.knowledge_graph_summary(),
            "",
            f"Search Terms : {self.search_term_count}",
        ]

        return "\n".join(sections)

    # ==================================================================
    # Utility, Copy & Comparison Methods
    # ==================================================================

    def copy(self) -> "Quantity":
        """
        Return a shallow copy of the Quantity.
        """

        return dataclass_replace(self)

    def clone(self) -> "Quantity":
        """
        Alias for copy().
        """

        return self.copy()

    def deep_copy(self) -> "Quantity":
        """
        Return a deep copy.
        """

        return deepcopy(self)

    def replace(
        self,
        **changes: object,
    ) -> "Quantity":
        """
        Return a new Quantity with selected fields replaced.
        """

        return dataclass_replace(
            self,
            **cast(Any, changes),
        )

    # ==============================================================
    # Equality
    # ==============================================================

    def identity_equals(
        self,
        other: object,
    ) -> bool:
        """
        Compare engineering identity.
        """

        if not isinstance(
            other,
            Quantity,
        ):
            return False

        return (
            self.quantity_id
            == other.quantity_id
        )

    def scientific_equals(
        self,
        other: object,
    ) -> bool:
        """
        Compare scientific meaning.
        """

        if not isinstance(
            other,
            Quantity,
        ):
            return False

        return (
            self.dimension
            == other.dimension
            and
            self.unit
            == other.unit
            and
            self.value
            == other.value
        )

    def engineering_equals(
        self,
        other: object,
    ) -> bool:
        """
        Compare engineering metadata.
        """

        if not isinstance(
            other,
            Quantity,
        ):
            return False

        return (
            self.identity_equals(other)
            and
            self.scientific_equals(other)
            and
            self.version
            == other.version
            and
            self.revision
            == other.revision
        )

    def matches(
        self,
        other: object,
    ) -> bool:
        """
        Alias for engineering comparison.
        """

        return self.engineering_equals(other)

    # ==============================================================
    # Difference Reporting
    # ==============================================================

    def compare_identity(
        self,
        other: "Quantity",
    ) -> dict[str, tuple[object, object]]:
        """
        Compare identity fields.
        """

        differences: dict[
            str,
            tuple[object, object],
        ] = {}

        fields = (
            "quantity_id",
            "name",
            "short_name",
            "symbol",
        )

        for attr_name in fields:

            lhs = getattr(self, attr_name)
            rhs = getattr(other, attr_name)

            if lhs != rhs:
                differences[attr_name] = (
                    lhs,
                    rhs,
                )

        return differences

    def compare_scientific(
        self,
        other: "Quantity",
    ) -> dict[str, tuple[object, object]]:
        """
        Compare scientific properties.
        """

        differences: dict[
            str,
            tuple[object, object],
        ] = {}

        fields = (
            "value",
            "unit",
            "dimension",
            "category",
            "measurement_type",
        )

        for attr_name in fields:

            lhs = getattr(self, attr_name)
            rhs = getattr(other, attr_name)

            if lhs != rhs:
                differences[attr_name] = (
                    lhs,
                    rhs,
                )

        return differences

    def compare_engineering(
        self,
        other: "Quantity",
    ) -> dict[str, tuple[object, object]]:
        """
        Compare engineering metadata.
        """

        differences: dict[
            str,
            tuple[object, object],
        ] = {}

        fields = (
            "version",
            "revision",
            "verification_status",
            "validation_status",
            "certified",
            "traceable",
        )

        for attr_name in fields:

            lhs = getattr(self, attr_name)
            rhs = getattr(other, attr_name)

            if lhs != rhs:
                differences[attr_name] = (
                    lhs,
                    rhs,
                )

        return differences

    def diff(
        self,
        other: "Quantity",
    ) -> dict[
        str,
        dict[str, tuple[object, object]],
    ]:
        """
        Return complete differences.
        """

        return {
            "identity":
                self.compare_identity(other),
            "scientific":
                self.compare_scientific(other),
            "engineering":
                self.compare_engineering(other),
        }

    # ==============================================================
    # Serialization Helpers
    # ==============================================================

    def to_dict(self) -> dict[str, object]:
        """
        Convert to dictionary.
        """

        result: dict[str, object] = {}
        for quantity_field in fields(self):
            value = getattr(self, quantity_field.name)
            if isinstance(value, MappingProxyType):
                value = dict(value)
            result[quantity_field.name] = value
        return result

    def pretty_print(self) -> str:
        """
        Pretty formatted representation.
        """

        lines = [
            "=" * 72,
            "QUANTITY",
            "=" * 72,
        ]

        for key, value in self.to_dict().items():

            lines.append(
                f"{key:<35} : {value}"
            )

        return "\n".join(lines)

    # ==============================================================
    # Hash Helpers
    # ==============================================================

    def engineering_key(self) -> tuple[
        str,
        str,
        int,
    ]:
        """
        Stable engineering key.
        """

        return (
            self.quantity_id,
            self.version,
            self.revision,
        )

    def scientific_key(self) -> tuple[
        str,
        object,
        object,
    ]:
        """
        Stable scientific key.
        """

        return (
            self.name,
            self.dimension,
            self.unit,
        )

    # ==============================================================
    # Complete Comparison
    # ==============================================================

    def compare(
        self,
        other: "Quantity",
    ) -> str:
        """
        Human-readable comparison.
        """

        report = [
            "=" * 72,
            "QUANTITY COMPARISON",
            "=" * 72,
            "",
            f"Identity Equal     : {self.identity_equals(other)}",
            f"Scientific Equal   : {self.scientific_equals(other)}",
            f"Engineering Equal  : {self.engineering_equals(other)}",
            "",
            "Differences:",
            str(self.diff(other)),
        ]

        return "\n".join(report)

    # ==============================================================
    # Dictionary Serialization
    # ==============================================================

    def to_ordered_dict(
        self,
    ) -> OrderedDict[str, object]:
        """
        Return an ordered dictionary.

        Ordering improves deterministic exports and
        reproducible serialization.
        """

        return OrderedDict(
            sorted(
                self.to_dict().items()
            )
        )

    def to_identity_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize only identity information.
        """

        return {
            "quantity_id": self.quantity_id,
            "name": self.name,
            "short_name": self.short_name,
            "symbol": self.symbol,
            "description": self.description,
            "aliases": self.aliases,
            "search_keywords": self.search_keywords,
            "tags": self.tags,
        }

    def to_scientific_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize scientific information.
        """

        return {
            "value": self.value,
            "unit": self.unit,
            "dimension": self.dimension,
            "quantity_type": self.unit.quantity_type,
            "category": self.category,
            "measurement_type": self.measurement_type,
            "minimum_value": self.minimum_value,
            "maximum_value": self.maximum_value,
            "nominal_value": self.nominal_value,
            "tolerance_plus": self.tolerance_plus,
            "tolerance_minus": self.tolerance_minus,
            "tolerance_percent": self.tolerance_percent,
            "effective_tolerance": self.effective_tolerance,
            "uncertainty": self.uncertainty,
            "standard_deviation": self.standard_deviation,
        }

    def to_engineering_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize engineering metadata.
        """

        return {
            "verification_status": self.verification_status,
            "validation_status": self.validation_status,
            "certified": self.certified,
            "traceable": self.traceable,
            "peer_reviewed": self.peer_reviewed,
            "confidence_score": self.confidence_score,
            "quality_score": self.quality_score,
            "technology_readiness_level":
                self.technology_readiness_level,
            "manufacturing_readiness_level":
                self.manufacturing_readiness_level,
            "operational_readiness_level":
                self.operational_readiness_level,
        }

    def to_repository_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize repository metadata.
        """

        return {
            "repository_identifier":
                self.repository_identifier,
            "repository_path":
                self.repository_path,
            "repository_branch":
                self.repository_branch,
            "version": self.version,
            "revision": self.revision,
            "created_timestamp":
                self.created_timestamp,
            "modified_timestamp":
                self.modified_timestamp,
            "created_by":
                self.created_by,
            "modified_by":
                self.modified_by,
        }

    def to_graph_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize graph metadata.
        """

        return {
            "graph_node_id":
                self.graph_node_id,
            "graph_indexed":
                self.graph_indexed,
            "ontology_identifier":
                self.ontology_identifier,
            "searchable":
                self.searchable,
            "indexable":
                self.indexable,
            "reasoning_enabled":
                self.reasoning_enabled,
        }

    def to_ai_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize AI metadata.
        """

        return {
            "embedding_identifier":
                self.embedding_identifier,
            "embedding_model":
                self.embedding_model,
            "embedding_version":
                self.embedding_version,
            "embedding_timestamp":
                self.embedding_timestamp,
            "semantic_indexed":
                self.semantic_indexed,
            "graph_indexed":
                self.graph_indexed,
            "searchable_by_ai":
                self.searchable_by_ai,
            "ai_verified":
                self.ai_verified,
            "ai_confidence":
                self.ai_confidence,
        }

    def to_metadata_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize metadata only.
        """

        return {
            "schema_version":
                self.schema_version,
            "cosmos_version":
                self.cosmos_version,
            "custom_metadata":
                self.custom_metadata,
            "extension_fields":
                self.extension_fields,
            "plugin_metadata":
                self.plugin_metadata,
            "external_identifiers":
                self.external_identifiers,
        }

    def to_summary_dict(
        self,
    ) -> dict[str, object]:
        """
        Compact serialization.
        """

        return {
            "quantity_id":
                self.quantity_id,
            "name":
                self.name,
            "symbol":
                self.symbol,
            "value":
                self.value,
            "unit":
                self.unit.symbol,
        }

    def to_minimal_dict(
        self,
    ) -> dict[str, object]:
        """
        Minimal serialization.

        Suitable for lightweight caches,
        indexing, and summaries.
        """

        return {
            "quantity_id":
                self.quantity_id,
            "value":
                self.value,
        }

    def to_full_dict(
        self,
    ) -> dict[str, object]:
        """
        Complete serialization.

        Alias of the canonical serializer.
        """

        return self.to_dict()
    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Quantity":
        """Construct a Quantity from a dictionary."""

        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        return cls(**cast(Any, dict(data)))


# ==============================================================================
# Typed Result Models (Temporary)
# ==============================================================================


@dataclass(frozen=True, slots=True)
class BaseResult:
  ...


@dataclass(frozen=True, slots=True)
class ValidationResult(BaseResult):
  ...


@dataclass(frozen=True, slots=True)
class ComparisonResult(BaseResult):
  ...


@dataclass(frozen=True, slots=True)
class AnalysisResult(BaseResult):
  ...
