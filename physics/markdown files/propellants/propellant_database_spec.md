# COSMOS PROPELLANT DATABASE SPECIFICATION

Document ID: COSMOS-PROP-DB-001

Version: 1.0

Status: Approved Baseline

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md
* COSMOS_CODING_STANDARD.md
* COSMOS_DATABASE_SPEC.md
* propellants.md
* propellants_api.md
* reference_library_propellants.md

---

# 1. PURPOSE

This document defines the authoritative structure, content, validation requirements, traceability requirements, versioning policy, and quality assurance requirements for all propellant records stored within COSMOS.

This specification governs:

* propellants_master.json
* future YAML databases
* future SQLite databases
* imported scientific databases
* internal propellant registries

The database defined herein shall be considered the single source of truth for all propellant data used throughout COSMOS.

---

# 2. DESIGN PHILOSOPHY

The COSMOS propellant database shall satisfy the following requirements:

* Aerospace-grade traceability
* Offline operation
* Deterministic calculations
* Reproducibility
* Version control compatibility
* Scientific auditability
* Future scalability

No engineering calculation shall depend on live internet access.

No runtime process shall modify validated database values.

---

# 3. DATABASE OWNERSHIP

The following module owns propellant definitions:

physics/thermochemistry/propellants.py

The following database owns propellant records:

databases/propellants_master.json

All other modules shall consume data from this database.

No duplicate propellant definitions shall exist elsewhere.

---

# 4. SUPPORTED STORAGE FORMATS

Primary Format:

JSON

Future Formats:

* YAML
* SQLite
* PostgreSQL
* Enterprise Database Connectors

Public interfaces shall remain unchanged regardless of backend.

---

# 5. REQUIRED PROPULSION FLUIDS (VERSION 1.0)

Mandatory baseline records:

1. Liquid Oxygen (LOX)
2. Liquid Methane (LCH4)
3. RP-1
4. Liquid Hydrogen (LH2)
5. Helium (He)
6. Nitrogen (N2)

Future additions shall not require schema changes.

---

# 6. REQUIRED DATABASE SCHEMA

Every propellant record shall contain:

name

short_name

formula

molecular_weight

phase

propellant_type

cea_species_name

aliases

density

density_temperature

density_pressure

storage_temperature

storage_pressure

boiling_point

freezing_point

critical_temperature

critical_pressure

elements

source

reference

reference_date

data_quality_level

version

last_verified

notes

All fields are mandatory unless explicitly marked optional in future revisions.

---

# 7. FIELD DEFINITIONS

## name

Human-readable official name.

Example:

"Liquid Oxygen"

---

## short_name

Engineering shorthand.

Example:

"LOX"

---

## formula

Chemical formula.

Example:

"O2"

---

## molecular_weight

Units:

kg/kmol

Must be positive.

---

## phase

Allowed values:

SOLID
LIQUID
GAS
SUPERCRITICAL

---

## propellant_type

Allowed values:

FUEL
OXIDIZER
PRESSURANT
INERT

---

## cea_species_name

NASA CEA compatible species name.

Examples:

O2(L)
CH4(L)
H2(L)

---

## aliases

Array of strings.

All aliases shall be unique globally.

---

## density

Reference density.

Units:

kg/m³

---

## density_temperature

Temperature corresponding to density.

Units:

K

---

## density_pressure

Pressure corresponding to density.

Units:

Pa

---

## storage_temperature

Nominal storage temperature.

Units:

K

---

## storage_pressure

Nominal storage pressure.

Units:

Pa

---

## boiling_point

Units:

K

---

## freezing_point

Units:

K

---

## critical_temperature

Units:

K

---

## critical_pressure

Units:

Pa

---

## elements

Elemental composition map.

Example:

{
"O": 2
}

or

{
"C": 1,
"H": 4
}

---

## source

Primary data source.

Examples:

NASA Glenn
NIST Chemistry WebBook

---

## reference

Specific publication.

---

## reference_date

Publication date.

ISO-8601 format preferred.

---

## data_quality_level

Allowed values:

A
B
C
D

Definitions:

A = NASA
B = NIST
C = Peer-reviewed literature
D = Engineering handbook

Level E prohibited.

---

## version

Database version.

Example:

1.0.0

---

## last_verified

Date of latest verification.

---

## notes

Optional engineering notes.

---

# 8. UNIT POLICY

Mandatory SI Units.

Temperature:
K

Pressure:
Pa

Density:
kg/m³

Molecular Weight:
kg/kmol

No imperial units permitted.

---

# 9. TRACEABILITY REQUIREMENTS

Every numerical value shall be traceable to:

* NASA
* NIST
* JANAF
* CoolProp verification
* Approved engineering references

Traceability metadata is mandatory.

Anonymous values prohibited.

---

# 10. VALIDATION REQUIREMENTS

The database loader shall validate:

* Unique names
* Unique aliases
* Positive density
* Positive molecular weight
* Positive temperatures
* Positive pressures
* Valid enum values
* Valid elemental composition
* Valid source metadata

Validation failure shall prevent database loading.

---

# 11. QUALITY ASSURANCE PROCESS

New records shall follow:

Step 1:
Source identification

Step 2:
Unit normalization

Step 3:
Independent verification

Step 4:
Database insertion

Step 5:
Automated validation

Step 6:
Peer review

Step 7:
Approval

---

# 12. VERSION CONTROL POLICY

The database shall be maintained under Git.

Every modification shall include:

* Commit message
* Author
* Verification source
* Change description

---

# 13. BACKWARD COMPATIBILITY

Future schema revisions shall:

* Preserve existing fields
* Preserve existing APIs
* Avoid breaking serialization

Deprecation process required before removal.

---

# 14. SECURITY REQUIREMENTS

Runtime code shall not:

* Modify validated database values
* Download replacement databases
* Overwrite local databases

Database updates shall be explicit user actions.

---

# 15. AUDIT REQUIREMENTS

Every record shall support complete scientific audit.

Required metadata:

* Source
* Reference
* Verification date
* Quality level
* Version

Missing audit information shall fail validation.

---

# 16. FUTURE EXTENSIONS

Future versions may add:

* Transport properties
* Thermal conductivity
* Dynamic viscosity
* Specific heat
* Vapor pressure curves
* Surface tension
* Compressibility factors
* NASA polynomial coefficients
* CoolProp mappings
* Cantera mappings

These additions shall not break Version 1.0 records.

---

# 17. LONG-TERM OBJECTIVE

The COSMOS propellant database shall evolve into an aerospace-grade thermophysical property repository suitable for:

* Rocket engine design
* Feed system analysis
* Injector design
* Cryogenic system modeling
* Thermal analysis
* Multiphysics simulation
* Optimization
* Verification and validation

while maintaining full scientific traceability and reproducibility.
