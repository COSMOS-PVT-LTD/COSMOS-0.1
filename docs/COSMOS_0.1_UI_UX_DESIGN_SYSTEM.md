# COSMOS_0.1_UI_UX_DESIGN_SYSTEM

**Project:** COSMOS --- Cryogenic Optimization and Simulation
Multiphysics Operating System\
**Document:** UI/UX Design System\
**Version:** 0.1\
**Status:** Proposed implementation baseline\
**Audience:** COSMOS frontend engineers, UI/UX engineers, Cursor/Codex
implementation agents, engineering-software architects\
**Scope:** Desktop-first proprietary computational-engineering
application for rocket propulsion design, CAD generation, multiphysics
analysis, AI-assisted engineering, knowledge retrieval, verification,
and controlled release.

------------------------------------------------------------------------

## 0. Executive Design Decision

COSMOS shall retain the strong visual DNA already present in the
developed v0.1 engine interface, but evolve it from a **single engine
calculator UI** into a **desktop computational-engineering workbench**.

The existing implementation already establishes useful visual
foundations:

-   deep dark background;
-   cyan/orange/green/yellow/violet engineering accents;
-   Orbitron for technical headings;
-   JetBrains Mono for numerical and telemetry information;
-   Exo 2 for general UI text;
-   thin technical borders;
-   compact engineering panels;
-   status indicators;
-   charts, tables, validation checks, exports, and history;
-   a restrained starfield/space atmosphere.

The redesign SHALL **not discard this identity**.

Instead, COSMOS 0.1 shall evolve it into:

> **Deep Space Engineering --- a professional aerospace computational
> workbench, not a sci-fi dashboard and not a clone of ANSYS,
> SolidWorks, Siemens NX, COMSOL, or any other external product.**

The target visual balance is:

**80% engineering workstation + 15% aerospace mission-control + 5%
futuristic space aesthetic.**

The software shall feel appropriate for serious company-internal rocket
development.

------------------------------------------------------------------------

# 1. Product UX Doctrine

## 1.1 Core UX proposition

COSMOS is not primarily a calculator, CAD viewer, chatbot, or simulation
launcher.

It is a **traceable computational engineering environment**.

The primary interaction loop is:

``` text
ENGINEERING INTENT
        ↓
DESIGN CONTRACT
        ↓
KNOWLEDGE / EVIDENCE
        ↓
DETERMINISTIC PHYSICS
        ↓
COMPUTATIONAL SYNTHESIS
        ↓
PARAMETRIC CAD
        ↓
MULTIPHYSICS / EXTERNAL SOLVERS
        ↓
OPTIMIZATION
        ↓
COMPARISON / V&V
        ↓
HUMAN REVIEW
        ↓
MANUFACTURING RELEASE
```

The UI must make this digital thread visible.

## 1.2 Primary UX principles

1.  **Engineering workbench first.**
2.  **Evidence before assertion.**
3.  **AI assists; deterministic engineering software owns numerical
    authority.**
4.  **Every important result has provenance.**
5.  **Every design state is versioned.**
6.  **Release readiness is explicit.**
7.  **Dense information is acceptable; visual chaos is not.**
8.  **3D geometry, physics, parameters, solver state, and evidence must
    be able to coexist.**
9.  **The interface must support expert users without becoming
    inaccessible to new engineers.**
10. **The UI must remain useful without decorative animation.**

------------------------------------------------------------------------

# 2. Existing UI Baseline → COSMOS 0.1 Evolution

## 2.1 Preserve

The existing engine UI already has a coherent dark-space visual
language:

``` text
Backgrounds:
#030609
#060C14
#0A1220
#0E192C

Borders:
#162438
#1F3550

Existing accents:
Cyan   #00D4FF
Orange #FF4D00
Green  #39FF14
Yellow #FFD000
Violet #BF5FFF
```

Existing typography:

-   Orbitron --- COSMOS branding, high-level technical headings and key
    numerical values.
-   JetBrains Mono --- telemetry, units, tables, labels, logs and
    machine-readable data.
-   Exo 2 --- general interface text.

These should remain recognizable.

## 2.2 Correct

The existing interface is currently optimized around a 300 px sidebar, a
single main content region, a compact header, and page-level navigation
such as Design, Compare, Charts, Nozzle, Mission Δv, Validate, Export
and History.

That structure is useful for the current engine prototype but does not
scale to the full COSMOS platform.

The new shell SHALL introduce:

``` text
GLOBAL HEADER
      │
      ├── PROJECT / DESIGN CONTEXT
      ├── WORKSPACE NAVIGATION
      ├── SOLVER STATUS
      ├── AI STATUS
      ├── KNOWLEDGE STATUS
      └── USER / SECURITY
      │
LEFT TOOL / WORKSPACE RAIL
      │
CENTRAL WORKBENCH / VIEWPORT
      │
RIGHT CONTEXT / PROPERTIES PANEL
      │
BOTTOM JOB / SOLVER / TELEMETRY BAR
```

------------------------------------------------------------------------

# 3. COSMOS Visual Identity

## 3.1 Theme name

**COSMOS --- DEEP SPACE ENGINEERING**

## 3.2 Visual character

The interface should communicate:

-   aerospace;
-   computational science;
-   precision;
-   controlled complexity;
-   engineering authority;
-   high-performance computing;
-   traceability;
-   proprietary technology.

Avoid:

-   cyberpunk excess;
-   excessive neon;
-   giant holographic widgets;
-   decorative spacecraft HUDs;
-   consumer SaaS card layouts;
-   unnecessary gradients;
-   excessive rounded corners;
-   excessive animation.

------------------------------------------------------------------------

# 4. Color System

## 4.1 Base palette

``` text
--cosmos-void       #030609
--cosmos-deep       #060C14
--cosmos-panel      #0A1220
--cosmos-raised     #0E192C
--cosmos-border     #162438
--cosmos-border-2   #1F3550

--cosmos-text      #B0CCE0
--cosmos-muted     #365570
--cosmos-dim       #1A3048
```

## 4.2 Primary interaction color

``` text
COSMOS CYAN
#00D4FF
```

Meaning:

-   active;
-   selected;
-   computational;
-   interactive;
-   information flow.

## 4.3 Secondary system colors

``` text
PROPULSION ORANGE    #FF4D00
VERIFICATION GREEN   #39FF14
WARNING YELLOW       #FFD000
KNOWLEDGE VIOLET     #BF5FFF
```

These existing accents should remain part of the visual identity.

## 4.4 Extended semantic engineering colors

The following are semantic conventions rather than decorative colors:

  System                       Color family
  ---------------------------- --------------------------
  LOX / oxidizer               Cyan / ice blue
  Methane / hydrocarbon fuel   Orange / amber
  Hydrogen                     Pale blue
  Hot gas / combustion         Red-orange
  Cooling circuit              Blue-cyan
  Pressurization               Green
  Electrical                   Yellow
  Controls                     Violet
  Knowledge / evidence         Violet + restrained gold
  Verified                     Green
  Warning                      Yellow
  Critical                     Red
  Informational                Cyan

Color SHALL never be the sole indicator of state; pair color with icon,
text, pattern, or symbol.

------------------------------------------------------------------------

# 5. Typography

## 5.1 Existing family

Retain:

``` text
Orbitron
JetBrains Mono
Exo 2
```

## 5.2 Usage

### Orbitron

Use for:

-   COSMOS logo;
-   major workspace headings;
-   critical numerical readouts;
-   high-level system states;
-   engineering mode labels.

Do not use Orbitron for paragraphs.

### JetBrains Mono

Use for:

-   numerical values;
-   units;
-   IDs;
-   requirement identifiers;
-   solver logs;
-   telemetry;
-   equations;
-   code;
-   tables;
-   timestamps;
-   hashes;
-   version identifiers.

### Exo 2

Use for:

-   explanatory text;
-   form descriptions;
-   tooltips;
-   navigation where readability matters;
-   documentation panels.

------------------------------------------------------------------------

# 6. Layout Grid

## 6.1 Desktop-first

Target baseline:

``` text
1440 × 900
1920 × 1080
2560 × 1440
```

Minimum supported engineering workstation width:

``` text
1280 px
```

## 6.2 Shell

``` text
┌───────────────────────────────────────────────────────────────┐
│ COSMOS │ PROJECT │ WORKSPACE │ SOLVER │ AI │ KB │ USER       │
├────────┬──────────────────────────────────────────┬───────────┤
│        │                                          │           │
│ TOOL   │                                          │ CONTEXT   │
│ RAIL   │            CENTRAL WORKBENCH            │ /         │
│        │                                          │ PROPERTIES │
│        │                                          │           │
├────────┴──────────────────────────────────────────┴───────────┤
│ JOBS │ SOLVER │ CONVERGENCE │ TELEMETRY │ LOG │ EVENTS       │
└───────────────────────────────────────────────────────────────┘
```

## 6.3 Panel widths

Recommended:

``` text
Left rail:
64–280 px

Right contextual panel:
320–420 px

Bottom console:
28–260 px

Header:
56–64 px
```

Panels must be resizable and dockable.

------------------------------------------------------------------------

# 7. Global Application Shell

## 7.1 Header

Left:

``` text
COSMOS
Cryogenic Optimization and Simulation Multiphysics Operating System
```

Center:

``` text
PROJECT
DESIGN
PHYSICS
SIMULATE
OPTIMIZE
MANUFACTURE
V&V
```

Right:

``` text
● SOLVER READY
● AI READY
● KNOWLEDGE ONLINE

USER
SECURITY
SETTINGS
```

The header must always show the current project and design state when a
project is open.

## 7.2 Left rail

Primary workspaces:

``` text
COMMAND
DESIGN CONTRACT
KNOWLEDGE
PROPULSION
CAD / GEOMETRY
PHYSICS
SIMULATION
OPTIMIZATION
COMPARISON
DOCUMENTATION
V&V
RELEASE
```

Secondary utilities:

``` text
PROJECT
FILES
JOBS
LOG
SETTINGS
```

The rail should support:

-   icon-only collapsed mode;
-   expanded mode;
-   tooltips;
-   keyboard navigation;
-   role-based visibility.

------------------------------------------------------------------------

# 8. Workbench Model

COSMOS SHALL use workspaces rather than independent application pages.

## 8.1 Command Workspace

Purpose:

-   project overview;
-   design health;
-   active jobs;
-   warnings;
-   open issues;
-   release readiness;
-   latest design changes.

Example:

``` text
COSMOS ENGINEERING CONTROL

PROJECT: C-5K-FFSC-001
DESIGN: REV 0.4

DESIGN STATUS        82%
PHYSICS STATUS       74%
CAD STATUS           91%
V&V STATUS           63%
RELEASE READINESS    BLOCKED

ACTIVE JOBS           3
OPEN ISSUES           7
FAILED CHECKS         2
```

## 8.2 Design Contract Workspace

Inputs shall be unit-aware and validation-aware.

Example:

``` text
TARGET THRUST        [ 5.000 ] [kN]
CHAMBER PRESSURE     [ 20.00  ] [bar]
PROPELLANT           [ LOX / LCH4 ]
BURN TIME            [ ... ]
COOLING              [ REGEN ]
MATERIAL SYSTEM      [ CuCrZr ]
MANUFACTURING        [ LPBF ]
```

Every input should expose:

-   source;
-   unit;
-   valid range;
-   requirement ID;
-   assumption status;
-   provenance.

## 8.3 Knowledge / Evidence Workspace

Show:

-   source documents;
-   equations;
-   variables;
-   constants;
-   correlations;
-   material data;
-   propellant data;
-   manufacturing rules;
-   validity ranges;
-   citations;
-   evidence packets.

No RAG answer should visually appear as an authoritative numerical
result without evidence binding.

## 8.4 Propulsion Workspace

A specialized engineering workbench for:

``` text
Cycle
Injector
Combustion Chamber
Nozzle
Turbopump
Turbine
Valves
Feed System
Cooling
Ignition
Manifolds
Instrumentation
```

## 8.5 CAD / Geometry Studio

Layout:

``` text
┌─────────────┬────────────────────────────┬──────────────┐
│ DESIGN TREE │                            │ PARAMETERS   │
│             │                            │              │
│ Components  │       3D VIEWPORT          │ Feature      │
│ Features    │                            │ Material     │
│ Evidence    │                            │ Constraints   │
│             │                            │              │
└─────────────┴────────────────────────────┴──────────────┘
```

The 3D viewport is the hero surface.

## 8.6 Physics Workspace

Provide synchronized views:

``` text
3D RESULT
+
PLOT
+
NUMERICAL TABLE
+
SOLVER STATE
+
BOUNDARY CONDITIONS
+
EVIDENCE
```

Do not force engineers to switch between unrelated pages to understand
one result.

## 8.7 Simulation Hub

Track:

-   solver;
-   solver version;
-   case ID;
-   mesh;
-   boundary conditions;
-   convergence;
-   run status;
-   imported result;
-   provenance;
-   comparison status.

External tools may include adapters for CFD/FEA/FEM systems.

## 8.8 Comparison Cockpit

The COSMOS-specific comparison interface SHALL be a first-class
workspace.

``` text
                 COSMOS       EXTERNAL SOLVER
Pressure          20.01 bar       19.88 bar
Thrust             5.02 kN         5.00 kN
Heat flux          ...             ...
Stress             ...             ...

DELTA
PASS / WARN / FAIL
```

Include:

-   side-by-side plots;
-   field overlays;
-   numerical deltas;
-   convergence information;
-   mesh metadata;
-   reviewer comments.

## 8.9 Optimization Workspace

Show the design space rather than only a final answer.

``` text
                PERFORMANCE
                     ↑
                     │     ● C
                 ●   │  ●
              ●      │
          ●          │
─────────────────────┼────────→ MASS
                     │
```

Provide:

-   candidate count;
-   feasible candidates;
-   Pareto front;
-   objective functions;
-   constraints;
-   sensitivity;
-   selected candidate;
-   reason for selection.

## 8.10 Documentation Center

Generated outputs:

-   Design Basis;
-   Calculation Package;
-   CAD Report;
-   Analysis Report;
-   Comparison Report;
-   Change Report;
-   Manufacturing Release Passport.

Documents are generated from the design state and evidence graph.

## 8.11 Release Gate

Release must be an explicit engineering state.

Example:

``` text
MANUFACTURING RELEASE

[✓] Requirements complete
[✓] Geometry regenerated
[✓] Mesh validated
[✓] Thermal analysis
[✓] Structural analysis
[✓] CFD review
[✓] External comparison
[ ] Human signoff
[ ] Open issues closed

RELEASE STATUS: BLOCKED
```

------------------------------------------------------------------------

# 9. 3D Viewport Design

The viewport is the visual centerpiece.

## 9.1 Default

Use:

-   dark neutral background;
-   subtle engineering grid;
-   restrained starfield only in non-analysis contexts;
-   physically meaningful lighting;
-   clean selection outlines;
-   axis triad;
-   scale indicator;
-   section/cutaway tools;
-   exploded-view tools;
-   measurement tools.

## 9.2 View modes

``` text
SOLID
WIREFRAME
X-RAY
SECTION
EXPLODED
THERMAL
PRESSURE
VELOCITY
MACH
STRESS
STRAIN
MESH
MANUFACTURING
EVIDENCE
```

## 9.3 Engineering overlays

The viewport may display:

``` text
Feature IDs
Requirement IDs
Boundary conditions
Loads
Sensors
Flow paths
Cooling channels
Material zones
Thermal limits
Manufacturing constraints
Evidence links
```

## 9.4 Evidence-bound geometry

Selecting a geometry feature should expose:

``` text
FEATURE
THROAT-R-042

GENERATED FROM
Requirement: REQ-THR-017

PHYSICS
Equation: EQ-GAS-014

MATERIAL
CuCrZr / MAT-004

VALIDATED BY
RUN-0247

STATUS
✓ VERIFIED
```

This is a signature COSMOS capability.

------------------------------------------------------------------------

# 10. Maharshi Bharadwaj Knowledge Infrastructure

## 10.1 Identity

**MAHARSHI BHARADWAJ** is the name of the COSMOS knowledge
infrastructure.

It SHALL NOT be implemented as a generic chatbot.

It is the user-facing identity of the:

> **Knowledge + evidence + engineering intelligence layer.**

## 10.2 Floating knowledge entry point

A persistent but unobtrusive floating Maharshi Bharadwaj visual may
exist within appropriate workspaces.

Interaction:

``` text
Hover
  ↓
Knowledge availability indicator
  ↓
Click
  ↓
Contextual Knowledge Workspace
```

The current design/viewport state must remain preserved.

## 10.3 Knowledge pop-up

``` text
┌──────────────────────────────────────────────────────────┐
│ MAHARSHI BHARADWAJ                                      │
│ KNOWLEDGE INFRASTRUCTURE                                │
├─────────────────────┬────────────────────────────────────┤
│ KNOWLEDGE GRAPH     │ ENGINEERING CONTEXT                │
│                     │                                    │
│ Physical Laws       │ Current component: Injector       │
│ Equations           │ Current material: CuCrZr          │
│ Materials           │ Current run: RUN-0247             │
│ Components          │                                    │
│ Experiments         │ Ask:                              │
│ Simulations         │ "Why was this geometry selected?" │
│ Design Rules        │                                    │
│ References          │ [SEARCH] [TRACE] [COMPARE]        │
└─────────────────────┴────────────────────────────────────┘
```

## 10.4 Context preservation

When opened from a component:

-   component context;
-   selected feature;
-   active solver;
-   active result;
-   current project;
-   current design revision

must be passed to Maharshi Bharadwaj.

The user should not need to re-explain the engineering context.

------------------------------------------------------------------------

# 11. AI Interaction Model

AI SHALL behave as an engineering copilot.

## 11.1 Do not use

A generic:

``` text
Ask COSMOS anything...
```

chat interface as the primary AI interaction.

## 11.2 Use contextual actions

Examples:

``` text
GENERATE VARIANT
EXPLAIN RESULT
TRACE EVIDENCE
COMPARE DESIGNS
FIND CONSTRAINT
IDENTIFY FAILURE
PROPOSE NEXT RUN
GENERATE REPORT
EXPLAIN EQUATION
```

## 11.3 AI activity trace

Whenever AI performs meaningful work:

``` text
AI ENGINE

✓ Requirements interpreted
✓ Evidence retrieved
✓ Design rules loaded
✓ Physics model selected
✓ Candidate generated
● Thermal optimization
○ Structural verification
○ Manufacturing analysis
```

The user must be able to inspect what happened.

## 11.4 AI authority boundary

The UI must distinguish:

``` text
AI SUGGESTION
AI EXPLANATION
AI RETRIEVAL
AI PLAN

from:

DETERMINISTIC SOLVER RESULT
VERIFIED EVIDENCE
ENGINEERING RELEASE DECISION
```

AI SHALL NOT visually impersonate a solver or release authority.

------------------------------------------------------------------------

# 12. Solver UX

## 12.1 Solver job model

Every job needs:

``` text
JOB ID
DESIGN REVISION
SOLVER
SOLVER VERSION
INPUT HASH
MESH / MODEL VERSION
START TIME
STATUS
CONVERGENCE
OUTPUT HASH
```

## 12.2 Live solver view

``` text
THERMAL SOLVER

ITERATION       042
RESIDUAL        2.1e-7
ENERGY ERROR    0.03%
MAX TEMP        812 K

CONVERGENCE
━━━━━━━━━━━━━━━━━━━╸ 91%

STATUS: CONVERGING
```

## 12.3 Solver states

``` text
QUEUED
PREPARING
RUNNING
CONVERGING
CONVERGED
COMPLETED
WARNING
FAILED
CANCELLED
STALE
SUPERSEDED
```

------------------------------------------------------------------------

# 13. Bottom Engineering Console

Persistent bottom bar:

``` text
┌───────────────────────────────────────────────────────────────┐
│ JOBS 3 │ SOLVER RUN-0247 │ CONVERGENCE 91% │ LOG │ EVENTS   │
└───────────────────────────────────────────────────────────────┘
```

Expandable into:

``` text
SOLVER
TELEMETRY
LOG
ERRORS
WARNINGS
AI ACTIVITY
SYSTEM EVENTS
```

This replaces hidden background activity with visible engineering state.

------------------------------------------------------------------------

# 14. Component Design

## 14.1 Panels

Existing sharp rectangular panels should remain.

Recommended:

``` text
border-radius: 2–4 px
```

Avoid large rounded cards.

## 14.2 Buttons

Primary:

``` text
Cyan border
dark translucent fill
technical typography
subtle hover glow
```

Secondary:

``` text
transparent
thin border
muted text
```

Danger:

``` text
red border
explicit destructive label
confirmation for irreversible actions
```

## 14.3 Inputs

All numerical engineering inputs SHALL show:

``` text
VALUE
UNIT
VALID RANGE
SOURCE / DEFAULT
VALIDATION STATE
```

Example:

``` text
CHAMBER PRESSURE
┌────────────────┬──────┐
│ 20.00          │ bar  │
└────────────────┴──────┘
Range: 5–100 bar
Source: Design Contract
✓ VALID
```

## 14.4 Tables

Tables should:

-   use JetBrains Mono;
-   support sorting;
-   support filtering;
-   preserve units;
-   distinguish calculated vs imported values;
-   support evidence links;
-   support copy/export;
-   expose status without relying only on color.

------------------------------------------------------------------------

# 15. Engineering Status Language

Use explicit states.

Good:

``` text
VERIFIED
VALIDATED
CONVERGED
BLOCKED
WARNING
STALE
SUPERSEDED
REQUIRES REVIEW
EXTERNAL RESULT
AI SUGGESTION
```

Avoid vague states such as:

``` text
Looks good
Done
Smart
Optimized
AI approved
```

------------------------------------------------------------------------

# 16. Animation System

Animation must communicate computation or state.

Allowed:

-   subtle hover transitions;
-   solver progress;
-   object selection;
-   viewport transitions;
-   panel docking;
-   job state changes;
-   knowledge graph expansion.

Avoid:

-   continuous decorative pulsing;
-   constant star movement;
-   excessive scanlines;
-   animated borders everywhere;
-   unnecessary 3D UI transitions.

The existing scanline effect should be disabled by default in
engineering-critical workspaces and retained only as a restrained
optional visual effect for Command/Launcher contexts.

------------------------------------------------------------------------

# 17. Starfield Rules

The existing starfield is useful for identity.

Use it primarily in:

-   launcher;
-   command dashboard;
-   project overview;
-   idle background areas.

Reduce or remove it in:

-   CAD;
-   CFD;
-   FEA;
-   thermal;
-   mesh editing;
-   engineering drawings;
-   dense tables.

Engineering clarity takes priority.

------------------------------------------------------------------------

# 18. Charts and Scientific Visualization

Charts must prioritize readability.

Use:

-   dark background;
-   thin grid;
-   semantic colors;
-   high contrast;
-   unit labels;
-   legends;
-   cursor readouts;
-   engineering notation.

Avoid:

-   decorative gradients;
-   3D charts;
-   excessive glow;
-   rainbow heatmaps unless scientifically meaningful.

Heatmaps must use documented scales and legends.

------------------------------------------------------------------------

# 19. Engineering Information Density

COSMOS should be information-dense without being visually noisy.

Use three information levels:

### L0 --- Mission level

Simple:

``` text
READY
RUNNING
BLOCKED
REVIEW REQUIRED
```

### L1 --- Engineering level

``` text
Pc 20.0 bar
Thrust 5.0 kN
Isp 326 s
Margin 1.42
```

### L2 --- Evidence level

``` text
Equation
Source
Validity range
Solver
Run ID
Mesh
Boundary condition
Reviewer
```

Users should be able to drill from L0 → L1 → L2.

------------------------------------------------------------------------

# 20. Traceability UX

Every important output shall have a visible trace icon or action.

Example:

``` text
5.02 kN  [TRACE]
```

Click:

``` text
RESULT TRACE

Requirement
REQ-THR-001

Equation
EQ-PERF-014

Inputs
...

Solver
COSMOS-PERF v0.1.3

Run
RUN-0247

CAD
ENGINE-REV-04

External comparison
EXT-CASE-091

Review
PENDING
```

------------------------------------------------------------------------

# 21. Design Lineage

Every design must support:

``` text
REV 0.1
   ↓
REV 0.2
   ↓
REV 0.3
   ↓
REV 0.4
```

The UI should allow:

-   compare revisions;
-   restore;
-   branch;
-   replay;
-   inspect changed features;
-   inspect changed equations;
-   inspect changed solver versions;
-   inspect changed requirements.

------------------------------------------------------------------------

# 22. Role-Based UX

The UI SHALL respect role-based access.

Example roles:

``` text
PROGRAM OWNER
ENGINE DESIGN ENGINEER
ANALYSIS ENGINEER
CAD ENGINEER
TEST ENGINEER
DATA / KNOWLEDGE ENGINEER
QUALITY / CONFIGURATION
REVIEWER
ADMINISTRATOR
```

Roles may control:

-   project access;
-   knowledge sources;
-   solver execution;
-   geometry generation;
-   export;
-   release;
-   administrative settings.

UI hiding is not sufficient authorization; backend authorization remains
authoritative.

------------------------------------------------------------------------

# 23. Security / Proprietary Software UX

Because COSMOS is company proprietary software:

Display security context where appropriate:

``` text
PROJECT: CONFIDENTIAL
DESIGN: INTERNAL
EXPORT: CONTROLLED
```

Do not expose sensitive data through casual UI surfaces.

Export actions must communicate:

``` text
EXPORT CONTROL
DESIGN RELEASE STATUS
CHECKSUM
VERSION
USER
TIMESTAMP
```

------------------------------------------------------------------------

# 24. Accessibility

Even though COSMOS is an expert desktop application:

-   keyboard navigation is mandatory;
-   focus states must be visible;
-   color must not be the only status signal;
-   text must remain readable against dark backgrounds;
-   tooltips must have keyboard equivalents;
-   numerical values must not depend on color alone;
-   reduced-motion preference should disable nonessential animation.

------------------------------------------------------------------------

# 25. Responsive / Window Behavior

COSMOS is desktop-first.

Priority:

``` text
1920×1080
2560×1440
1440×900
1280×800
```

At reduced widths:

1.  collapse left rail;
2.  collapse right properties panel into a drawer;
3.  keep central viewport usable;
4.  move bottom console to a tabbed drawer.

Do not simply stack the entire engineering application into a
mobile-style card layout.

------------------------------------------------------------------------

# 26. Iconography

Create a proprietary COSMOS engineering icon set.

Core icons:

``` text
PROJECT
REQUIREMENT
KNOWLEDGE
EQUATION
MATERIAL
PROPELLANT
ENGINE
INJECTOR
CHAMBER
NOZZLE
TURBOPUMP
TURBINE
VALVE
MANIFOLD
COOLING
THERMAL
CFD
FEA
MESH
SOLVER
OPTIMIZATION
CAD
MANUFACTURING
V&V
RELEASE
TRACE
AI
EVIDENCE
EXPERIMENT
```

Use thin technical line icons.

Avoid generic emoji icons in production UI.

The current prototype's emoji navigation icons should be replaced
progressively with the COSMOS icon system.

------------------------------------------------------------------------

# 27. Navigation Migration

Current prototype:

``` text
Design
Compare
Charts
Nozzle
Mission Δv
Validate
Export
History
```

Evolve to:

``` text
COMMAND
DESIGN
PROPULSION
CAD / GEOMETRY
PHYSICS
SIMULATION
OPTIMIZATION
COMPARISON
KNOWLEDGE
DOCUMENTATION
V&V
RELEASE
```

Existing functions should be retained and relocated rather than removed.

Mapping:

``` text
Design       → Design Contract / Propulsion
Compare      → Comparison Cockpit
Charts       → Physics / Analysis
Nozzle       → Propulsion / Geometry
Mission Δv   → Mission / System Analysis
Validate     → V&V
Export       → Documentation / Release
History      → Design Lineage
```

------------------------------------------------------------------------

# 28. Launcher

The application launcher should visually introduce COSMOS without
becoming a marketing page.

``` text
                     COSMOS

       DEEP SPACE ENGINEERING ENVIRONMENT

      [ NEW PROJECT ]    [ OPEN PROJECT ]

RECENT DESIGNS
────────────────────────────────────────
C-5K-FFSC-001
C-1K-METHALOX-003
NOZZLE-OPT-021

SYSTEM STATUS
● PHYSICS ENGINE
● CAD ENGINE
● KNOWLEDGE
● SOLVER
● AI
```

The Maharshi Bharadwaj visual may appear here as a subtle
knowledge-system entry point.

------------------------------------------------------------------------

# 29. Design System Tokens

Implement all visual values as centralized tokens.

Example:

``` css
:root {
  --cosmos-void: #030609;
  --cosmos-deep: #060C14;
  --cosmos-panel: #0A1220;
  --cosmos-raised: #0E192C;

  --cosmos-border: #162438;
  --cosmos-border-strong: #1F3550;

  --cosmos-cyan: #00D4FF;
  --cosmos-orange: #FF4D00;
  --cosmos-green: #39FF14;
  --cosmos-yellow: #FFD000;
  --cosmos-violet: #BF5FFF;

  --cosmos-text: #B0CCE0;
  --cosmos-muted: #365570;
  --cosmos-dim: #1A3048;

  --radius-sm: 2px;
  --radius-md: 4px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
}
```

The exact token values may evolve only through the design-system
baseline.

------------------------------------------------------------------------

# 30. Component Library

Create reusable components before implementing individual workspaces.

Required foundation:

``` text
CosmosShell
CosmosHeader
CosmosRail
CosmosPanel
CosmosSectionHeader
CosmosButton
CosmosIconButton
CosmosInput
CosmosUnitInput
CosmosSelect
CosmosChip
CosmosStatus
CosmosBadge
CosmosMetric
CosmosTable
CosmosPlot
CosmosJob
CosmosSolverStatus
CosmosEvidenceLink
CosmosTracePanel
CosmosPropertyPanel
CosmosViewport
CosmosDesignTree
CosmosCommandPalette
CosmosModal
CosmosDrawer
CosmosToast
CosmosTooltip
CosmosKnowledgeEntry
MaharshiKnowledgePanel
CosmosReleaseGate
CosmosAuditTimeline
```

------------------------------------------------------------------------

# 31. Command Palette

Provide a global keyboard-driven command palette.

Example:

``` text
⌘ / CTRL + K

Search COSMOS commands...

> Generate injector variant
> Open thermal solver
> Find requirement
> Trace selected feature
> Open Maharshi Bharadwaj
> Compare revisions
> Run validation
> Open design lineage
> Export engineering report
```

This is especially important for expert users.

------------------------------------------------------------------------

# 32. Contextual Right Panel

The right panel is context-sensitive.

For a selected geometry feature:

``` text
FEATURE
THROAT

PARAMETERS
Radius
Length
Wall thickness

PHYSICS
Heat flux
Pressure
Mach

CONSTRAINTS
Thermal
Structural
Manufacturing

EVIDENCE
REQ-...
EQ-...
RUN-...

AI ACTIONS
Explain
Optimize
Compare
Trace
```

The same panel should adapt to:

-   components;
-   solver results;
-   plots;
-   requirements;
-   evidence;
-   materials;
-   manufacturing features.

------------------------------------------------------------------------

# 33. Error and Warning UX

Never show only:

``` text
ERROR
```

Use:

``` text
THERMAL SOLVER FAILED

Cause:
Non-convergent throat heat-flux solution.

Detected:
Iteration 42

Suggested actions:
[VIEW RESIDUAL]
[INSPECT COOLING]
[COMPARE PREVIOUS RUN]

Trace:
RUN-0247
```

Warnings should be actionable.

------------------------------------------------------------------------

# 34. Empty States

Empty states should teach the workflow.

Bad:

``` text
Nothing here.
```

Good:

``` text
NO DESIGN CONTRACT

Create a Design Contract before running
engineering synthesis.

[CREATE DESIGN CONTRACT]
```

------------------------------------------------------------------------

# 35. Loading States

Never use only a spinner for long engineering operations.

Show:

``` text
GENERATING ENGINE

Requirements ........ COMPLETE
Evidence ............ COMPLETE
Physics ............. RUNNING
Geometry ............ QUEUED
Validation .......... QUEUED
```

------------------------------------------------------------------------

# 36. Engineering Confidence

Confidence must be evidence-based.

Display:

``` text
EVIDENCE COVERAGE
████████████████░░ 87%

MODEL VALIDATION
██████████████░░░░ 78%

MANUFACTURABILITY
█████████████████░ 94%

RELEASE READINESS
████████░░░░░░░░░░ BLOCKED
```

Never represent AI confidence as engineering certification.

------------------------------------------------------------------------

# 37. Design Passport UX

Every engine/component should have a design passport.

``` text
DESIGN PASSPORT

Identity
Requirements
Assumptions
Materials
Physics
Geometry
Simulation
Optimization
External Validation
V&V
Manufacturing
Review
Release
Checksums
```

This should be accessible from the Command workspace and Release
workspace.

------------------------------------------------------------------------

# 38. Implementation Rules for Cursor

Cursor implementation SHALL follow this sequence.

## Phase 1 --- Design-system foundation

1.  Create centralized design tokens.
2.  Replace scattered hard-coded colors with tokens.
3.  Establish typography tokens.
4.  Create icon system.
5.  Establish spacing/grid system.
6.  Establish component primitives.

## Phase 2 --- Application shell

1.  Implement global header.
2.  Implement workspace rail.
3.  Implement central workbench.
4.  Implement contextual right panel.
5.  Implement bottom job/solver console.
6.  Implement command palette.

## Phase 3 --- Existing functionality migration

Do not remove existing engine capabilities.

Map current prototype functions into the new workspaces.

## Phase 4 --- Knowledge integration

Implement Maharshi Bharadwaj as a contextual knowledge infrastructure
interface.

## Phase 5 --- Physics / CAD

Implement synchronized:

``` text
3D
plots
tables
solver status
properties
evidence
```

## Phase 6 --- V&V / Release

Implement:

``` text
comparison cockpit
design lineage
release gate
manufacturing passport
audit trail
```

------------------------------------------------------------------------

# 39. What Cursor Must NOT Do

Cursor SHALL NOT:

-   replace the entire UI with a generic dashboard;
-   remove existing working physics functionality;
-   replace the dark-space identity with a light theme;
-   turn COSMOS into a chatbot;
-   introduce excessive rounded cards;
-   use emoji as the final iconography;
-   add decorative neon everywhere;
-   hide solver state;
-   hide validation state;
-   imply that AI output is verified engineering truth;
-   bypass backend authorization;
-   bypass evidence requirements;
-   make STL/3MF appear release-ready without the required release
    state;
-   break existing design-state persistence;
-   discard existing navigation functionality without mapping it into
    the new information architecture.

------------------------------------------------------------------------

# 40. Acceptance Criteria

The implementation is acceptable only when:

### Visual

-   [ ] Deep Space Engineering theme is consistent.
-   [ ] Existing COSMOS cyan/orange/green/yellow/violet identity remains
    recognizable.
-   [ ] UI does not look like a clone of another engineering product.
-   [ ] No excessive neon/cyberpunk styling.
-   [ ] Panels remain dense but readable.
-   [ ] Typography is consistent.

### Navigation

-   [ ] All major workspaces are discoverable.
-   [ ] Existing prototype functionality is preserved.
-   [ ] Workspace state is preserved when switching context.
-   [ ] Command palette works.

### Engineering

-   [ ] Units are visible.
-   [ ] Solver status is visible.
-   [ ] Validation state is visible.
-   [ ] Design revision is visible.
-   [ ] Evidence is traceable.
-   [ ] External results are distinguishable from COSMOS results.
-   [ ] Release readiness is explicit.

### AI

-   [ ] AI is contextual.
-   [ ] AI activity is inspectable.
-   [ ] AI suggestions are visually distinct from deterministic solver
    results.
-   [ ] AI cannot imply release authority.

### Knowledge

-   [ ] Maharshi Bharadwaj is integrated as the knowledge
    infrastructure.
-   [ ] Context is preserved when opening it.
-   [ ] Evidence and source binding are accessible.
-   [ ] Knowledge graph and engineering context can be inspected.

### Security

-   [ ] RBAC is enforced by backend.
-   [ ] UI respects role permissions.
-   [ ] Export/release actions are controlled.
-   [ ] Audit information is available.

------------------------------------------------------------------------

# 41. Final COSMOS UI Identity

The final product should feel like:

``` text
                  COSMOS

        DEEP SPACE ENGINEERING

   ┌─────────────────────────────────┐
   │ REQUIREMENT                     │
   │       ↓                         │
   │ KNOWLEDGE                       │
   │       ↓                         │
   │ PHYSICS                         │
   │       ↓                         │
   │ COMPUTATIONAL DESIGN            │
   │       ↓                         │
   │ CAD                             │
   │       ↓                         │
   │ MULTIPHYSICS                    │
   │       ↓                         │
   │ OPTIMIZATION                    │
   │       ↓                         │
   │ VALIDATION                      │
   │       ↓                         │
   │ HUMAN REVIEW                    │
   │       ↓                         │
   │ RELEASE                         │
   └─────────────────────────────────┘
```

The visual language should communicate that COSMOS is a **computational
engineering compiler for rocket development**, not simply another CAD
package with AI attached.

The most important design principle is:

> **The UI must expose the engineering chain of custody of a design.**

A generated geometry feature should be able to lead the engineer
backward to its requirement, evidence, equation, solver, analysis,
optimization history, and review decision.

That traceability is the visual expression of the COSMOS **TRACE-GEN**
architecture.

------------------------------------------------------------------------

# 42. Baseline Relationship to COSMOS Architecture

This UI system is subordinate to the existing COSMOS engineering
architecture.

It must preserve:

``` text
UI
 ↓
Backend APIs
 ↓
Systems
 ↓
Physics
 ↓
Core
```

Knowledge remains an evidence/traceability layer rather than an
unchecked numerical authority.

Deterministic engineering solvers remain responsible for calculations.

Parametric CAD remains the engineering geometry authority.

External solver results remain independently identifiable.

Human review remains required for controlled release.

The UI must expose these boundaries rather than blur them.

------------------------------------------------------------------------

# 43. Recommended Initial Implementation Order

``` text
01  Design tokens
02  Icon system
03  Global shell
04  Workspace rail
05  Context panel
06  Bottom solver console
07  Command palette
08  Command workspace
09  Design Contract
10  Propulsion workbench
11  CAD / Geometry Studio
12  Physics workspace
13  Simulation Hub
14  Comparison Cockpit
15  Maharshi Bharadwaj
16  Optimization workspace
17  Documentation Center
18  V&V
19  Release Gate
20  Design Passport / Lineage
```

This order deliberately prioritizes UI/UX first, then workbenches, then
deeper backend integration.

------------------------------------------------------------------------

# 44. Design-System Status

**Baseline:** COSMOS 0.1 UI/UX proposed baseline\
**Theme:** Deep Space Engineering\
**Architecture:** Desktop-first, local-first, professional engineering
workbench\
**Knowledge Identity:** Maharshi Bharadwaj\
**Engineering Pattern:** TRACE-GEN\
**Primary interaction:** Contextual computational engineering\
**AI role:** Engineering copilot / retrieval / planning / explanation /
comparison\
**Numerical authority:** Deterministic, validated engineering software\
**Release authority:** Human review + evidence gate\
**Implementation posture:** Preserve existing UI capabilities; evolve
the shell and information architecture rather than rewrite functionality
blindly.

------------------------------------------------------------------------

## END OF COSMOS_0.1_UI_UX_DESIGN_SYSTEM
