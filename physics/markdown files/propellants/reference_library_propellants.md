# COSMOS PROPELLANT REFERENCE LIBRARY

Document ID: COSMOS-PROP-REF-001

Version: 1.0

Status: Approved Baseline

---

# 1. PURPOSE

This document defines the authoritative scientific references approved for propellant data used by COSMOS.

Only sources listed herein may be used as primary references.

---

# 2. TIER 1 AUTHORITATIVE SOURCES

## NASA RP-1311

Chemical Equilibrium with Applications.

Authority:

Rocket propulsion thermochemistry.

Use for:

* Equilibrium chemistry
* Species properties
* Performance calculations

---

## NASA Glenn Thermodynamic Database

Authority:

Species thermodynamic data.

Use for:

* Cp
* Enthalpy
* Entropy
* NASA polynomial coefficients

---

## NIST Chemistry WebBook

Authority:

Physical property data.

Use for:

* Molecular weight
* Critical properties
* Vapor pressure
* Density references

---

## JANAF Thermochemical Tables

Authority:

Thermodynamic reference data.

Use for:

* Enthalpy
* Entropy
* Heat capacity

---

# 3. TIER 2 APPROVED SOURCES

## CoolProp Documentation

Use for:

* Cryogenic fluid properties
* Verification

---

## Cantera Documentation

Use for:

* Species databases
* Kinetics validation

---

## Burcat Thermodynamic Database

Use for:

* NASA polynomial verification

---

# 4. TIER 3 ENGINEERING REFERENCES

## Rocket Propulsion Elements

George P. Sutton

Use for:

* Propellant characteristics
* Rocket engineering

---

## Liquid Rocket Engine Fluid-Cooled Combustion Chambers

NASA SP-8087

Use for:

* Engine design reference

---

## Turbopump Systems for Liquid Rocket Engines

NASA SP-8107

Use for:

* Feed system design

---

## Rocket Engine Design Manuals

NASA technical publications.

Use for:

* Verification only

---

# 5. INTERNAL COSMOS REFERENCES

Approved internal databases:

* propellants.db
* materials.db

Internal databases supersede external references once validated.

---

# 6. PROHIBITED SOURCES

Not approved:

* Wikipedia
* Reddit
* Quora
* Blogs
* Forum posts
* AI-generated values
* Unsourced tables

These sources may never be used as primary data references.

---

# 7. CITATION REQUIREMENTS

Every propellant value shall include:

* Source
* Edition
* Publication date
* Units
* Reference conditions

---

# 8. TRACEABILITY

All numerical values used by COSMOS shall be traceable to:

* NASA
* NIST
* JANAF
* CoolProp
* Approved textbooks

Traceability is mandatory.

---

# 9. DATA QUALITY LEVELS

Level A

NASA

Level B

NIST

Level C

Peer-reviewed literature

Level D

Engineering handbook

Level E

Unverified source

Level E data prohibited.

---

# 10. LONG-TERM OBJECTIVE

COSMOS shall evolve toward a validated aerospace-grade thermophysical property library whose values are traceable to recognized scientific authorities and suitable for rocket propulsion design, simulation, optimization, and verification.
