# COSMOS PROPELLANTS SPECIFICATION

Document ID: COSMOS-PROP-001

Version: 1.0

Status: Approved Baseline

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md
* COSMOS_CODING_STANDARD.md

---

# 1. PURPOSE

This document defines the official requirements for:

physics/thermochemistry/propellants.py

This module shall serve as the canonical source of propellant definitions throughout COSMOS.

All thermochemistry, fluid property, injector, cooling, tank, performance, and optimization modules shall obtain propellant information from this module.

No duplicate propellant definitions shall exist elsewhere in the software.

---

# 2. RESPONSIBILITIES

The module shall:

* Define propellant data structures
* Store approved propellant records
* Validate propellant data
* Provide lookup services
* Provide serialization support
* Provide API access to other modules
* Support future database expansion

The module shall NOT:

* Perform equilibrium calculations
* Call NASA CEA
* Calculate performance
* Compute transport properties
* Execute external API calls

---

# 3. INITIAL SUPPORTED PROPELLANTS

Required baseline propellants:

* Liquid Oxygen (LOX)
* Liquid Methane (LCH4)
* RP-1
* Liquid Hydrogen (LH2)
* Helium (He)
* Nitrogen (N2)

Future additions shall not require modification of existing interfaces.

---

# 4. DATA MODEL

Canonical class:

Propellant

Required fields:

* name
* short_name
* formula
* molecular_weight
* phase
* propellant_type
* cea_species_name
* aliases
* density
* density_temperature
* density_pressure
* storage_temperature
* storage_pressure
* boiling_point
* freezing_point
* critical_temperature
* critical_pressure
* elements

---

# 5. ENUMERATIONS

Phase:

* SOLID
* LIQUID
* GAS
* SUPERCRITICAL

PropellantType:

* OXIDIZER
* FUEL
* INERT
* PRESSURANT

---

# 6. UNIT SYSTEM

Mandatory SI units.

Density:
kg/m³

Pressure:
Pa

Temperature:
K

Molecular Weight:
kg/kmol

No imperial units permitted internally.

---

# 7. VALIDATION REQUIREMENTS

The module shall validate:

* Non-empty names
* Unique names
* Unique aliases
* Positive density
* Positive molecular weight
* Positive pressure
* Positive temperatures
* Valid enum values
* Valid elemental composition

Invalid data shall raise:

PropellantValidationError

---

# 8. LOOKUP REQUIREMENTS

Required interfaces:

get_propellant(name)

get_propellant_by_alias(alias)

list_propellants()

list_fuels()

list_oxidizers()

list_pressurants()

exists(name)

All lookups shall be case-insensitive.

---

# 9. DATABASE REQUIREMENTS

Initial implementation:

Internal Python registry.

Future support:

* JSON
* YAML
* SQLite

Migration shall not break public interfaces.

---

# 10. IMMUTABILITY

Propellant objects shall be immutable.

Runtime modification prohibited.

---

# 11. SERIALIZATION

Required:

to_dict()

from_dict()

JSON serialization support.

---

# 12. ERROR HANDLING

Required exceptions:

PropellantError

PropellantNotFoundError

PropellantValidationError

DuplicatePropellantError

---

# 13. TESTING REQUIREMENTS

Minimum coverage:

95%

Required tests:

* Construction tests
* Validation tests
* Alias lookup tests
* Serialization tests
* Database integrity tests
* Duplicate detection tests

---

# 14. PERFORMANCE REQUIREMENTS

Lookup time:

O(1)

Initialization:

<100 ms

Memory footprint:

<10 MB

---

# 15. FUTURE COMPATIBILITY

The module shall support future integration with:

* RocketCEA
* NASA CEA
* CoolProp
* Cantera
* Thermodynamic databases

without API redesign.
