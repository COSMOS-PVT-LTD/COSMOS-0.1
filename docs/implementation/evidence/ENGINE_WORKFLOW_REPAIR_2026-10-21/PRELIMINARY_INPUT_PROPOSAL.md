# Methalox numerical-study input proposal — preliminary study approved

## Approval record — 2026-10-21

The user explicitly replied **“Approve these preliminary study assumptions”** to
the approval request referencing this proposal. Approved scope: 5 s duration,
8 bar absolute regulated source feeds, 1 bar drop per propellant injector,
assumed Cd 0.70, 8 ports per propellant, GRCop-42 liner / INCONEL 718 jacket as
material **candidates**. This authorizes preliminary numerical/geometry study,
not hardware operation, fabrication or validation. No hot material allowables,
heated-fluid validity windows, feed losses or cooling design were approved.

The draft and raw `proposal.json` below are retained as originally prepared;
their historical NOT_APPROVED labels are superseded only by this approval record.
Installation and qualification are tracked separately. R08 remains on hold.

## Original proposal

Prepared2026-10-21 at the user's request. Approval below would authorize only
preliminary numerical/geometry work, not fabrication, pressurization or firing.
The original1500 N,5 bar **absolute**, sea-level static, methane111.15 K /
LOX90.15 K requirements remain unchanged. O/F2.633 remains the preceding finite-grid
ideal-CEA study selection, not a physically optimal or validated mixture ratio.

## Proposed exploratory assumptions for approval

| Input | Proposal | Basis / limit |
|---|---:|---|
| Nominal duration | 5 s | Explicit study assumption; no transient/startup or thermal-life evidence |
| Regulated propellant source pressures | 8 bar absolute each | Exploratory boundary, not an established safe or closed feed design |
| Injector pressure drop | 1 bar each propellant | Explicit hydraulic study assumption, not a measured requirement |
| Injector discharge coefficient | 0.70 each | Unmeasured assumption; sensitivity and cold-flow evidence required |
| Injector port counts | 8 fuel + 8 oxidizer | Initial doublet concept; not atomization/stability qualification |
| Liner candidate | GRCop-42 | Candidate requiring exact process/condition/material data, not an accepted allowable |
| Jacket candidate | INCONEL718 | Candidate requiring product-form/heat-treatment data; no automatic material substitution |

No arbitrary wall temperature, temperature-independent hot allowable, accepted
coolant pressure loss or tank/line resistance is proposed as a known fact.
Those must be sourced and/or solved consistently. The8 bar source is not a
pressure-vessel specification or permission to operate hardware.

## Sourced cold inlet properties (single state, not a validity window)

Actual public NIST WebBook requests were retrieved with **normal TLS validation**
using system curl. The local Python CA store rejected its HTTPS request; certificate
checking was not disabled. Raw TSV responses and URL/SHA256 provenance are retained
in the local proposal folder listed below.

| State at8 bar absolute | Methane | Oxygen |
|---|---:|---:|
| Temperature [K] | 111.15 | 90.15 |
| NIST phase label | liquid | liquid |
| Density [kg/m³] | 423.763 | 1142.91 |
| Dynamic viscosity [Pa·s] | 0.000119226 | 0.000196253 |
| Specific heat, raw NIST units [J/(g·K)] | 3.46931 | 1.69568 |
| Conductivity [W/(m·K)] | 0.185203 | 0.151430 |

These are reference-fluid property calculations, **not measured engine evidence**.
They do not establish saturation margins along heated cooling passages, pressure-
temperature property bounds or acceptable uncertainty. A full sourced property
domain is still required before using the constant-property/phase-window engine
operating solver. Do not stretch a one-point source into a broad validity range.

Using the existing `physics/injectors/orifice.py` model with the declared draft
Cd, pressure drops/counts and prior ideal core flows gives preliminary geometric
diameters **2.266 mm fuel** and **2.869 mm oxidizer**. These are conditional model
outputs, not drill/fabrication instructions or final injector dimensions.

This reveals a real CAD integration gap: the existing equal-hole-radius doublet
does not represent these distinct propellant areas or identities. Retain the old
illustrative CAD as historical; implement/verify source-bound distinct ports and
feed routing before claiming a hydraulically designed injector model.

## Material and structural qualification still required

[NASA's GRCop thrust-chamber work](https://www.nasa.gov/organizations/otps/2024-invention-of-the-year-winner/)
supports researching GRCop-42 as a liner candidate; it does not validate this engine.
[NASA GRCop-42 development report](https://ntrs.nasa.gov/citations/20190030433) and
[Special Metals' INCONEL718 bulletin](https://www.specialmetals.com/documents/technical-bulletins/inconel/inconel-alloy-718.pdf)
are candidate data authorities. No numerical hot strength/thermal-conductivity
curve from either has yet been ingested or accepted. Existing room-temperature
catalog entries cannot be relabelled as those datasets.

The current concept's chamber bore radius51.429 mm / radial wall6 mm is about8.57,
outside the existing tensile thin-wall model's required radius/thickness≥10.
An appropriate thick-wall model plus local channel-ligament/thermal-stress treatment
is required; reducing thickness just to make the old model pass is not a fix.

## Retained artifacts and replay

`/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/output/methalox-input-proposal-2026-10-21-v1/`

- `proposal.json`: all actual NIST rows/URLs/hashes, conditional orifice results,
  proposed assumptions, material candidates and remaining non-executable gaps.
- `fuel-nist-8bar.tsv`, `oxidizer-nist-8bar.tsv`: original public responses.
- Reproduction script: `scripts/prepare_methalox_input_proposal.py`.

Approval requested: accept these as **exploratory study assumptions/candidates**,
or revise them. Approval must not be construed as acceptance of missing property
windows, material allowables, a completed cooling model, build-ready engine CAD,
physical readiness, or permission to advance R08.
