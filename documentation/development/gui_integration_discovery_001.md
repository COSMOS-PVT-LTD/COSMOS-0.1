# COSMOS 0.1 — GUI Integration Discovery 001

**Document ID:** `GUI-INTEGRATION-DISCOVERY-001`  
**Date:** 2026-09-03  
**Phase:** B (GUI discovery) — read-only  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Code modified:** none  

Prerequisite for Phase C: Core + Physics freeze gate (human PHYS-004 waiver approval).

---

## 1. Framework and location

| Item | Finding |
|------|---------|
| Package | `gui/` |
| Shell | **pywebview** + localhost HTTP (`gui/server.py`) |
| Frontend | Vanilla HTML/CSS/JS under `gui/static/` |
| Entry | `main.py` → `gui.application.launch_desktop_application` |
| Not used | PyQt / Qt / Tk (older docs are obsolete relative to implemented shell) |

---

## 2. Navigation / views

- Auth: `/login`
- Workbench hub: `/app/workbenches`
- Workbench detail: `/app/workbench/{id}`
- Knowledge: `/app/workbench/knowledge` (+ proxy)
- Admin / audit: role-gated
- Sidebar includes **Physics** as disabled / “coming soon”
- Active workbenches: `rocket-engine`, `knowledge` (`gui/workbenches/registry.py`)

---

## 3. State management

Cookie session (`cosmos_session`) + `localStorage` / `sessionStorage` + server `CosmosApplication`. No SPA state framework.

---

## 4. Calculation pathways today

| Path | Status |
|------|--------|
| GUI → Physics | **None** |
| GUI → Core | **None** |
| GUI → Knowledge | Proxied via `gui/knowledge_proxy.py` |
| GUI → `api/` | Auth / profile / RBAC only |
| `engineering/`, `systems/`, `services/` | **Absent** |

Workbench module buttons are stubs (`alert` / coming soon). No Physics equations in JS.

---

## 5. Architecture compliance (presentation)

```text
gui/  ──X──►  physics   (no imports found — correct for now)
gui/  ──X──►  core
```

Clean slate for a service boundary. Do **not** import Physics into GUI JS or into `gui/` presentation modules.

---

## 6. UI/UX system to preserve

- `docs/COSMOS_0.1_UI_UX_DESIGN_SYSTEM.md`
- `gui/static/cosmos-tokens.css`, `cosmos.css`, `cosmos-shell.css`
- `gui/static/engineering-ux.js` (properties, console, toasts)

Do not rebuild the shell.

---

## 7. Recommended Phase C vertical slice

```text
GUI form (Rocket Engine workbench or enabled Physics page)
   ↓  POST /api/physics/compressible/isentropic  (auth cookie)
Application adapter (NEW: api/physics_compressible.py — not gui/)
   ↓
physics.compressible_flow.isentropic / area_mach
   ↓
core.Quantity / validation
   ↓
Structured JSON result
   ├── values + units
   ├── model_id / version / equations
   ├── verification status
   ├── validation: NOT CLAIMED
   └── warnings / errors (typed)
   ↓
GUI view (properties panel / result card)
```

### First operations

1. Stagnation ratios from Mach + γ  
2. Area–Mach forward and inverse  

### Explicitly out of Phase C

Full CFD GUI, CAD, digital twin, AI optimization, canonical Numerics, full engine workflow.

---

## 8. Key files for implementation (after freeze)

- `gui/server.py` — add route  
- `api/physics_compressible.py` — **new** request/result adapter  
- `gui/static/workbench/` — thin form UI  
- `gui/workbenches/registry.py` — enable module entry  
- Tests under `tests/unit_tests/api/` and `tests/unit_tests/gui/`

---

## 9. Phase B status

```text
GUI DISCOVERY COMPLETE — AWAITING HUMAN FREEZE GATE
```
