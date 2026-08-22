# COSMOS Propellant Property Verification Report

Version: 1.0

Document ID: COSMOS-PROP-VERIFY-V1

Status: Verification Baseline

Date: 2026-06-24

Project: Cryogenic Optimization and Simulation Multiphysics Operating System (COSMOS)

---

# 1. PURPOSE

This document establishes the verification matrix for the initial COSMOS propellant database.

The objective is to ensure that all thermophysical properties stored within:

databases/propellants_master_verified_v1.json

are traceable to approved reference sources.

This document shall be used as the engineering audit trail for database population and future updates.

---

# 2. APPROVED REFERENCE SOURCES

Priority 1

* NIST Chemistry WebBook
* NIST REFPROP Documentation

Priority 2

* NASA Glenn Research Center Publications
* NASA CEA Documentation

Priority 3

* Rocket Propulsion Elements (Sutton)
* Huzel & Huang
* Cryogenic Engineering References

When conflicts exist, higher-priority sources take precedence.

---

# 3. PROPERTY DEFINITIONS

All properties shall use SI units.

| Property             | Unit    |
| -------------------- | ------- |
| Molecular Weight     | kg/kmol |
| Density              | kg/m³   |
| Density Temperature  | K       |
| Density Pressure     | Pa      |
| Storage Temperature  | K       |
| Storage Pressure     | Pa      |
| Boiling Point        | K       |
| Freezing Point       | K       |
| Critical Temperature | K       |
| Critical Pressure    | Pa      |

---

# 4. LOX VERIFICATION MATRIX

Name:
Liquid Oxygen

Short Name:
LOX

Formula:
O₂

CEA Species:
O2(L)

Elements:

O = 2

Reference Source:

NIST Chemistry WebBook

Properties Requiring Verification:

* Molecular Weight
* Density
* Density Temperature
* Density Pressure
* Storage Temperature
* Storage Pressure
* Boiling Point
* Freezing Point
* Critical Temperature
* Critical Pressure

Verification Status:

Pending Final Verification

Data Quality Level:

A

---

# 5. LCH4 VERIFICATION MATRIX

Name:
Liquid Methane

Short Name:
LCH4

Formula:
CH₄

CEA Species:
CH4(L)

Elements:

C = 1
H = 4

Reference Source:

NIST Chemistry WebBook

Properties Requiring Verification:

* Molecular Weight
* Density
* Density Temperature
* Density Pressure
* Storage Temperature
* Storage Pressure
* Boiling Point
* Freezing Point
* Critical Temperature
* Critical Pressure

Verification Status:

Pending Final Verification

Data Quality Level:

A

---

# 6. RP-1 VERIFICATION MATRIX

Name:
RP-1

Short Name:
RP1

Representative Formula:

C12H26

Reference Source:

Rocket Propulsion Elements

Special Note:

RP-1 is not a pure chemical species.

Thermophysical properties must originate from accepted aerospace references and shall not be treated as pure-component NIST data.

Properties Requiring Verification:

* Density
* Storage Conditions
* Freezing Point
* Boiling Range
* Representative Molecular Weight

Verification Status:

Pending Final Verification

Data Quality Level:

B

---

# 7. LH2 VERIFICATION MATRIX

Name:
Liquid Hydrogen

Short Name:
LH2

Formula:
H₂

CEA Species:
H2(L)

Elements:

H = 2

Reference Source:

NIST Chemistry WebBook

Properties Requiring Verification:

* Molecular Weight
* Density
* Density Temperature
* Density Pressure
* Storage Temperature
* Storage Pressure
* Boiling Point
* Freezing Point
* Critical Temperature
* Critical Pressure

Verification Status:

Pending Final Verification

Data Quality Level:

A

---

# 8. HELIUM VERIFICATION MATRIX

Name:
Helium

Short Name:
HE

Formula:
He

CEA Species:
HE

Elements:

He = 1

Reference Source:

NIST Chemistry WebBook

Properties Requiring Verification:

* Molecular Weight
* Density
* Storage Temperature
* Storage Pressure
* Boiling Point
* Critical Temperature
* Critical Pressure

Verification Status:

Pending Final Verification

Data Quality Level:

A

---

# 9. NITROGEN VERIFICATION MATRIX

Name:
Nitrogen

Short Name:
N2

Formula:
N₂

CEA Species:
N2

Elements:

N = 2

Reference Source:

NIST Chemistry WebBook

Properties Requiring Verification:

* Molecular Weight
* Density
* Density Temperature
* Density Pressure
* Storage Temperature
* Storage Pressure
* Boiling Point
* Freezing Point
* Critical Temperature
* Critical Pressure

Verification Status:

Pending Final Verification

Data Quality Level:

A

---

# 10. VERIFICATION PROCEDURE

For every property:

1. Retrieve value from approved source.
2. Record exact source document.
3. Record publication version.
4. Record retrieval date.
5. Record verification engineer.
6. Record uncertainty if available.
7. Store value in propellants_master_verified_v1.json.
8. Update last_verified field.

---

# 11. DATABASE RELEASE CRITERIA

The verified database may be released only when:

* Every required property has a verified value.
* Every value has traceability.
* Every value has source documentation.
* Verification review is complete.
* COSMOS QA review is complete.

---

# 12. NEXT DELIVERABLE

Upon completion of property verification:

databases/propellants_master_verified_v1.json

shall be generated and frozen as the official COSMOS propellant baseline database.

END OF DOCUMENT
