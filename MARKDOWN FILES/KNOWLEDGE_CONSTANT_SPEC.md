KNOWLEDGE_CONSTANT_SPEC.md (Enterprise v1.0)
1. Purpose

The Constant model represents a validated, immutable engineering constant.

Every physical constant, empirical constant, material constant, thermodynamic constant, numerical constant, and engineering correlation coefficient shall be represented by a Constant object.

The Constant model shall be the single source of truth for engineering constants throughout COSMOS.

No module shall define duplicate constants.

2. Design Goals

The Constant model shall be:

Immutable
Thread-safe
Fully validated
Serializable
Deterministic
Type-safe
Unit-aware
AI-searchable
Knowledge Foundation compatible
Repository-ready
Future symbolic mathematics ready
3. Architectural Position
Reference
        │
        ▼
Document
        │
        ▼
Variable
        │
        ▼
Constant
        │
        ▼
Equation
        │
        ▼
Physics Engines

Unlike Variable, a Constant represents a quantity whose value does not change during evaluation.

4. Responsibilities

The Constant model shall provide:

Identity
Numerical value
Unit definition
Engineering metadata
Provenance
Validation
Serialization
Analysis methods
Future symbolic integration

The Constant model shall not:

Evaluate expressions
Solve equations
Perform unit conversion
Query repositories
Parse documents
Read databases
Perform symbolic algebra
5. Identity

Required fields:

constant_id
name
symbol
description

Example:

CONST-R-001

Universal Gas Constant

R

Universal gas constant
6. Numerical Information

Required:

value

Optional:

default_value
minimum_value
maximum_value
precision
uncertainty
significant_figures

Example

8.31446261815324
7. Units

Required

si_unit
dimension

Optional

display_unit

Future compatibility

Pint
Astropy Units
8. Classification

Required

ConstantType

Recommended enum

PHYSICAL

THERMODYNAMIC

MATERIAL

CHEMICAL

NUMERICAL

EMPIRICAL

ASTRONOMICAL

MATHEMATICAL

UNIVERSAL

USER_DEFINED
9. Engineering Domain

Enum

THERMODYNAMICS

FLUID_MECHANICS

COMBUSTION

HEAT_TRANSFER

CRYOGENICS

GAS_DYNAMICS

STRUCTURES

CFD

OPTIMIZATION

MATERIALS

CONTROLS

RELIABILITY

GENERAL
10. Provenance

Optional

source_reference

source_document

equation_ids

This enables complete traceability.

11. Engineering Metadata

Optional

subsystem

discipline

physical_meaning

engineering_notes

applicable_system
12. AI Metadata

Optional

aliases

common_names

search_keywords

Used for:

AI retrieval
Knowledge search
NLP
Semantic indexing
13. Lifecycle

Enum

ConstantStatus

DRAFT

VALIDATED

APPROVED

DEPRECATED

OBSOLETE
14. Validation

Implement

__post_init__()

validate()

_validate_constant_id()

_validate_name()

_validate_symbol()

_validate_value()

_validate_units()

_validate_bounds()

_validate_reference()

_validate_document()

_validate_aliases()

_validate_common_names()

_validate_search_keywords()

_validate_metadata()

Fail-fast.

No silent failures.

15. Serialization

Implement

to_dict()

from_dict()

Requirements:

deterministic ordering
nested serialization
enum reconstruction
tuple reconstruction
16. Query Methods

Implement

has_value()

uses_si_units()

matches_alias()

matches_keyword()

display_name()

is_physical()

is_empirical()

is_user_defined()

is_dimensionless()

Pure functions only.

17. Future Analysis Methods

Later versions should support:

relative_uncertainty()

absolute_uncertainty()

is_exact()

is_measured()

compatible_with()

same_dimension_as()
18. Repository Integration

Compatible with

ConstantRepository

Future capabilities

lookup
indexing
search
versioning
19. Symbolic Mathematics

Future support

SymPy
NASA CEA
RocketCEA
OpenMDAO
OpenFOAM

No implementation in v1.0.

20. Thread Safety

Implementation

@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)

No mutable state.

21. Performance

Target complexities

Construction     O(n)

Validation       O(n)

Serialization    O(n)

Lookup           O(1)

Queries          O(1)
22. Testing

Minimum unit tests

Construction
valid constant
invalid id
invalid name
invalid symbol
invalid value
Validation
invalid units
invalid bounds
invalid aliases
invalid metadata
Serialization
to_dict()
from_dict()
round-trip
Query Methods
has_value()
uses_si_units()
matches_alias()
matches_keyword()
display_name()
is_physical()
is_empirical()
is_user_defined()
is_dimensionless()
Immutability
frozen dataclass
equality
round-trip equality

Target coverage:

≥95% (goal: 100%)
23. Development Roadmap

To stay consistent with the way you've developed Reference, Document, Equation, and Variable, I recommend the following phased implementation:

Phase 0.5.3A
Module header
Imports
Enums
Dataclass
Field definitions
Phase 0.5.3B
__post_init__()
Validation framework
Private validators
Phase 0.5.3C
Serialization
Deserialization
Phase 0.5.3D
Query and analysis methods
Phase 0.5.3E
Comprehensive unit tests

24. Numerical Accuracy Metadata

Scientific software needs to distinguish exact constants from measured constants.

Add:

exact_value : bool

measurement_uncertainty : float | None

relative_uncertainty : float | None

uncertainty_unit : str | None

measurement_reference : Reference | None

Examples:

Speed of light → exact
Gravitational constant → measured
Boltzmann constant → exact (SI 2019)
Avogadro constant → exact

This becomes important for uncertainty propagation.

25. SI Definition Metadata

Many constants are officially defined.

Add:

si_definition_year

codata_version

nist_identifier

iso_reference

Example

CODATA 2022

SI 2019

NIST

This makes the knowledge base auditable.

26. Computational Metadata

Physics engines need more than a value.

Include

preferred_numeric_type

supports_float32

supports_float64

supports_decimal

supports_symbolic

Future optimization engines will use this.

27. Dimension Metadata

Instead of only

dimension = "Pressure"

also store

base_dimensions

kg

m

s

K

mol

A

cd

Example

Pressure

kg¹

m⁻¹

s⁻²

This enables future dimensional analysis.

28. Engineering Applicability

Add

applicable_regimes

temperature_limits

pressure_limits

mach_limits

reynolds_limits

Some constants are only valid within specific engineering regimes.

29. Knowledge Foundation Metadata

Add

knowledge_tags

ontology_category

knowledge_level

related_constants

related_equations

These fields become essential for AI retrieval and knowledge graphs.

30. Version Control Metadata

Every engineering object should be versioned.

created_by

approved_by

reviewed_by

created_timestamp

approved_timestamp

revision_notes

Useful for future collaboration.

31. Deprecation Metadata

Enterprise software never deletes constants.

Instead

deprecated_since

replacement_constant

deprecation_reason

Example

Old NASA value

↓

Updated CODATA 2022 value
32. Search Optimization

Current

aliases

common_names

search_keywords

Expand to

normalized_name

normalized_symbol

abbreviations

legacy_names

This greatly improves search quality.

33. Future AI Integration

Add

embedding_id

semantic_category

llm_description

These can remain optional today but prevent future schema changes.

34. Repository Metadata

Prepare for ConstantRepository.

repository_key

repository_namespace

repository_version

This makes migration to SQLite, PostgreSQL, or a remote knowledge server easier.

35. Validation Status

Instead of only

status

Add

validation_state

verification_level

review_status

These support engineering workflows and audits.

36. Future Symbolic Mathematics

Reserve fields for later integration.

sympy_symbol

canonical_symbol

latex_symbol

unicode_symbol

This allows equations to render consistently in GUIs and documentation.

37. Performance Metadata

Useful later for optimization.

cacheable

immutable_hash

serialization_version
38. Interoperability

Prepare for data exchange.

export_name

export_aliases

external_identifiers

Examples

NASA

NIST

OpenFOAM

RocketCEA

CEA

OpenMDAO
39. Quality Metrics

Track engineering quality.

verification_status

validation_status

confidence_level
40. Testing Requirements

Expand beyond the current tests.

Include:

Enum validation
Unit validation
Provenance validation
Engineering metadata validation
AI metadata validation
Round-trip serialization
Equality
Immutability
Invalid enum values
Invalid nested objects
Optional field defaults
Performance smoke tests
Deterministic serialization
Deterministic equality


One Additional Enterprise Feature

I recommend adding a field that Variable does not currently have:

is_fundamental: bool

Purpose:

True → Fundamental constant (e.g., speed of light c, Planck constant h, universal gas constant R, gravitational constant G).
False → Derived or user-defined constant (e.g., characteristic combustion efficiency, empirical coefficients, calibration constants).

This distinction becomes valuable when integrating with:

symbolic mathematics,
optimization,
dimensional analysis,
automatic equation simplification,
knowledge graphs.

It allows COSMOS to differentiate immutable physical laws from project-specific engineering constants without changing the public API later. I recommend including it in the initial design rather than retrofitting it in a future version.