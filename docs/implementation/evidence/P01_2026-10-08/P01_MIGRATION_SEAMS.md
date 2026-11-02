# P01 — Additive migration seams and approval boundaries

P01 changes only its evidence/prototype directory. This is a design contract, not an implemented migration.

Repository root: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

## Current source → future integration seam

| Current source and symbol | Reuse | Additive integration / phase |
|---|---|---|
| `gui/workbenches/registry.py:WorkbenchDefinition` | Stable IDs/routes/maturity catalog | P04 capability-driven primary nav plus complete legacy catalog; no removed routes |
| `gui/workbenches/propulsion_suite.py`; `api/catalogs.py:list_workflow_catalog` | Stage names/order/implementation status | P05 task groups render the existing 17-stage graph; not a new solver ordering |
| `gui/static/propulsion-suite.js:field/selectField/makeCard/renderStructuredPhase/appendCeaVisual` | Units, structured result/errors, CEA/station views | P03 semantic components, P05 task-local preflight/compact result inspection; retain raw data |
| `gui/static/propulsion-suite.js:renderNav/setWorkspaceUrl` | Current step/tool and query context | Preserve stage/module deep links, focus and history before new route transitions |
| `gui/static/engineering-ux.js:getProjectContext/setProjectContext` | Existing local UI preference | P04 separate preference from durable project/design identity; no silent store migration |
| `systems/projects/models.py:PropulsionDesign` | Working aggregate/change log | P04/P06 expected-base CAS and distinct immutable published snapshots; no overwrite of historical input |
| `api/propulsion_workflow.py:save_design`; `systems/persistence/design_store.py:DesignStore` | Current validated edit guard/atomic file write | Storage-level transaction/CAS; race regression fixtures before worker updates. Keep existing edit validation. |
| `systems/workflow/graph.py`, `invalidation.py`, `orchestrator.py` | Dependencies, stale cones, scoped chain execution | UI dependency-impact preview from authority; no independently editable stale Boolean |
| `systems/contracts/results.py` | Status, validity, verification, validation, provenance | Presentation adapters preserve dimensions; new published result identity is P06, not a frontend flag |
| `physics/thermochemistry/cea_interface.py`; `plugins/nasa_cea/engine.py` | Qualified request/result/native adapter | UI requests existing services; no duplicated equations or changed temperatures/defaults |
| `knowledge/workspace/`, `storage/local_store.py`, vault/RAG policies | Governed ingestion/evidence/index/provenance | P11 source inspection/report panels; scientific artifact ownership remains separately approved |
| `gui/native_window.py`; `gui/server.py`; API client | Working launcher/local service/auth | P04 flagged shell and P12 packaging/security; no framework replacement approved here |

## Flags and rollout contract

Proposed flags: `COSMOS_NEW_SHELL`, `COSMOS_NGG`, `COSMOS_NEW_SIM_UI`, `COSMOS_NEW_VV_UI`. None are added to production in P01. P04 defines typed evaluation and defaults-off behavior before integration. A UI flag cannot activate an unsupported scientific backend.

First vertical slice: shared context and navigation against existing API, preserving legacy routes and flag-off shell. Next: compact Rocket input/preflight/result view with full scientific parity. Introduce new geometry/worker/publication contracts only after their own architecture/license gates. Do not combine native kernel upgrades with a UI migration.

## Data safety and rollback

- Prototype synthetic snapshot/CAS tests demonstrate intended behavior only; they do not fix the P00 persistence race.
- Recoverable backups and schema/read compatibility tests precede any approved production migration. Never use destructive Git resets as a data rollback plan.
- Flag-off returns existing navigation/views without downgrading, rewriting or relabeling scientific records.
- Layout/density preferences are namespaced UI data. They must never be included in numerical model hashes or chosen as solver defaults.
- Keep user draft edits on conflict; show newer persisted revision and require deliberate reconciliation. Do not silently replace them.

## Decisions not approved by P01

Engineering/Systems ownership amendment; authoritative Project/Geometry/Simulation storage ownership; native worker protocol/resource isolation; kernel/transitive license acceptance; framework/viewer selection; network exposure; credential-vault/signing policy; destructive migration; scientific/model/tolerance changes. Use reviewed ADRs and the relevant phase gates for these choices.

## Compatibility acceptance before merge

Every audited workbench ID remains discoverable; Rocket and Knowledge remain usable with existing data; legacy physics redirects and stage/module links work; browser history and unsaved drafts behave predictably; flag-off rollback is tested; numerical/CEA negative and reference cases remain unchanged. P01's route-map test is not a production integration or rollback test.
