# COSMOS

## Cryogenic Optimization and Simulation Multiphysics Operating System

**Publicly visible proprietary company software**

Copyright © 2026 COSMOS PVT LTD. All Rights Reserved.

---

## Overview

COSMOS is the proprietary computational engineering and artificial intelligence
platform developed and owned by **COSMOS PVT LTD**. It is intended to accelerate,
assist, and support the company's engineering activities across rocket propulsion,
aerospace systems, multiphysics simulation, optimization, knowledge management,
and AI-assisted engineering.

COSMOS is an internal company technology platform and forms part of the
company's proprietary intellectual-property portfolio. It is **not** open-source
software.

## Strategic Purpose

COSMOS is intended to become a core engineering software platform supporting
COSMOS PVT LTD's research and development, engineering design, analysis,
simulation, optimization, knowledge management, and future operational
activities.

## Engineering Scope

COSMOS is designed to support domains including:

- computational engineering
- physics-based modelling
- thermochemistry
- thermodynamics
- fluid mechanics
- cryogenics
- combustion
- heat transfer
- propulsion
- rocket engine engineering
- numerical methods
- optimization
- multiphysics simulation
- engineering knowledge systems
- AI-assisted engineering

### Implementation status (COSMOS 0.1)

Capabilities are classified against the current repository. Architectural
documents describe intent; they are not evidence that a capability is live.

| Area | Status |
|------|--------|
| Core infrastructure (`core/`) | **IMPLEMENTED** (units, quantities, validation) |
| Numerics foundation (`numerics/`) | **DEVELOPMENT-QUALIFIED CANDIDATE** (generic math; explicit advanced deferrals; not production CFD/FEA) |
| Physics foundation (`physics/`) | **PARTIAL** (frozen compressible / heat-transfer / materials / propellant registry; CEA unbound) |
| Systems propulsion workflow (`systems/`) | **PARTIAL** (Phases 3–6; injector / cooling / cycle / MOC **NOT_IMPLEMENTED**) |
| Application API (`api/`) | **PARTIAL** (auth, physics adapters, propulsion design lifecycle) |
| Desktop GUI (`gui/`) | **PARTIAL** (login, hub, Rocket Engine, Maharshi Bharadwaj) |
| Knowledge workspace | **PARTIAL** (authenticated in the desktop app; standalone `:8765` is development-only) |
| Remaining workbenches (turbopumps, CAD, CFD, PLM, …) | **PLANNED** |

Numerics candidate scope, test evidence and limitations:
[V&V report](documentation/development/COSMOS_NUMERICS_FOUNDATION_VV_001.md),
[freeze candidate](documentation/development/COSMOS_NUMERICS_FOUNDATION_FREEZE_001.md).
Owner acceptance and protected-main merge are separate from numerical qualification.

## Quick start (native desktop — default)

COSMOS 0.1 is a **local installed desktop application** (native window via pywebview),
not a website. The UI is served on `127.0.0.1` inside your own app window — the same
pattern used by many modern engineering tools that embed a local shell.

```bash
cd /path/to/COSMOS_0.1
pip install -r requirements-desktop.txt
python main.py
```

On macOS you can also double-click `scripts/launch_cosmos.command` after installing
dependencies once.

Developer browser mode (automation / debugging only — **not** the product experience):

```bash
python main.py --browser
```

Headless HTTP only (CI / API testing):

```bash
python main.py --headless --port 8780
```

If pywebview is missing, `python main.py` prints install instructions and temporarily
opens the default browser so you are not blocked — install desktop dependencies and
relaunch for the native window.

### Bootstrap administrator (local development)

| Field | Value |
|-------|-------|
| Login ID | `cosmos-admin` |
| Password | `COSMOS-Dev-2026!` |
| Login profile | **Administrator** |

The default login screen profile is Engineer. The bootstrap user is an
Administrator — select Administrator or the login is rejected as a profile
mismatch, not a bad password.

Open **Rocket Engine** for the propulsion workspace. Ten other hub cards are
roadmap pages, not solvers.

**Knowledge** is available only after desktop login. `python -m knowledge.workspace`
on port 8765 is an unauthenticated development server.

## Architecture

The authoritative COSMOS 0.1 architecture is defined in:

- `documentation/COSMOS_0.1_FREEZED.md`
- `documentation/COSMOS_0.1_FREEZED_ARCHITECTURE_export.pdf`

COSMOS 0.1 is organized into six architectural layers (Foundation, Scientific
Computing, Engineering Workflows, Integration, Presentation, and Governance) as
documented in the frozen architecture specification. This repository
initialization does not redesign that architecture.

## Development Status

COSMOS 0.1 is in **early development**. The desktop application, Rocket Engine
workflow, and knowledge workspace are usable for local engineering analysis.
Most other workbenches remain planned. Results are **not** flight-certified.

## Intellectual Property

COSMOS and its original source code, software architecture, algorithms,
engineering models, computational methods, documentation, and associated
proprietary technical material are proprietary intellectual property of
**COSMOS PVT LTD**, subject to applicable third-party rights and licenses.

## Public Repository

This repository is publicly visible for development and collaboration purposes.
Public visibility does **not** constitute an open-source license and does **not**
grant unrestricted rights to use, reproduce, modify, distribute, sublicense,
commercialize, or create derivative works from COSMOS.

See also `documentation/PUBLIC_REPOSITORY_IP_POLICY.md`.

## Licensing

Use of COSMOS is governed by the proprietary license in [LICENSE](LICENSE).
See [NOTICE](NOTICE) for copyright and third-party notice information.

## Security

Report security concerns according to [SECURITY.md](SECURITY.md).

## Contribution

Contribution rules for authorized personnel are described in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Governance

- `documentation/IP_GOVERNANCE.md`
- `documentation/PUBLIC_REPOSITORY_IP_POLICY.md`

## Copyright

Copyright © 2026 COSMOS PVT LTD. All Rights Reserved.
