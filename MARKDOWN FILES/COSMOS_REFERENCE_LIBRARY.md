# COSMOS_REFERENCE_LIBRARY 

Version: 1.1

Status: Approved

Purpose:

Defines the authoritative engineering references used throughout COSMOS.

---

# PRIORITY 1 — AUTHORITATIVE REFERENCES

These references override all lower-priority sources.

## Rocket Propulsion

* NASA CEA
* NASA SP-125 Design of Liquid Propellant Rocket Engines
* Rocket Propulsion Elements (Sutton & Biblarz)
* Huzel & Huang – Modern Engineering for Design of Liquid Propellant Rocket Engines

## Injectors

* NASA SP-8089 Liquid Rocket Engine Injectors

## Turbomachinery

* NASA SP-8107 Turbopump Systems for Liquid Rocket Engines
* NASA SP-8125 Liquid Rocket Engine Axial-Flow Turbopumps

## Cooling

* NASA SP-8080 Fluid-Cooled Combustion Chambers
* Fundamentals of Heat and Mass Transfer (Incropera)

## Gas Dynamics

* Modern Compressible Flow (Anderson)
* Elements of Gas Dynamics (Liepmann & Roshko)

## CFD

* Computational Fluid Dynamics (Anderson)
* The Finite Volume Method (Versteeg & Malalasekera)

## Structures

* Roark's Formulas for Stress and Strain
* Pressure Vessel Design Manual
* ASME Boiler and Pressure Vessel Code Section VIII

## Materials

* ASM Handbooks
* NASA Materials Databases
* MMPDS

## Cryogenics

* NIST Cryogenic Data
* NIST REFPROP

---

# PRIORITY 2 — GOVERNMENT AND INDUSTRY STANDARDS

* NASA Design Criteria Series
* JANNAF Manuals
* ASTM Standards
* ISO Standards
* MIL Standards

---

# PRIORITY 3 — PEER-REVIEWED SOURCES

* AIAA Journal Papers
* Journal of Propulsion and Power
* Aerospace Science and Technology
* Acta Astronautica
* Experimental Rocket Test Data

---

# PRIORITY 4 — SOFTWARE REFERENCES

* OpenFOAM Documentation
* SU2 Documentation
* Cantera Documentation
* CoolProp Documentation

---

# PRIORITY 5 — INTERNAL REFERENCES

* COSMOS Validation Database
* COSMOS Experimental Data
* Company Test Data
* Flight Data
* Internal Reports

---

# CONFLICT RESOLUTION RULE

When two sources disagree:

Priority 1 overrides Priority 2.

Priority 2 overrides Priority 3.

Priority 3 overrides Priority 4.

Priority 4 overrides Priority 5.

Any deviation from Priority 1 references must be documented in validation records.
