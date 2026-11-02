# COSMOS target architecture — conceptual

```mermaid
flowchart TB
 UI[COSMOS Shell] --> RE[Rocket Engine Workbench]
 UI --> NG[NGG Workbench]
 UI --> SI[Simulation Workbench]
 UI --> VV[Comparison and V&V]
 UI --> KB[Maharshi Bharadwaj]
 RE --> D[Versioned Engineering Design Model]
 NG --> D
 D --> A[NGG Application Service]
 A --> P[PicoGK Sidecar]
 A --> C[OCCT B-rep Backend]
 P --> S[Immutable Artifact Store]
 C --> S
 S --> Q[Geometry QA]
 Q --> SI
 SI --> VV
 KB -. Evidence .-> D
 VV -. Feedback .-> D
```

**Diagram type:** logical target architecture, not current repo evidence. **Review:** validate arrows and service ownership against frozen architecture before implementation.
