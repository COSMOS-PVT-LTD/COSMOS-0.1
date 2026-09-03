# COSMOS 0.1 — Figma MCP Design System Rules

**Document ID:** `COSMOS-0.1-FIGMA-DS-RULES-001`  
**Purpose:** Authoritative agent rules for integrating Figma designs via the Figma Model Context Protocol with the COSMOS desktop GUI.  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Companion:** `docs/COSMOS_0.1_UI_UX_DESIGN_SYSTEM.md` (product doctrine) · `gui/static/cosmos-tokens.css` (executable tokens)

Use this document whenever:

- translating Figma → COSMOS UI;
- building/updating a Figma variable/component library from code (`figma-generate-library`);
- Code Connect mapping;
- reviewing GUI PRs for design-system conformance.

---

## 0. Executive summary

| Topic | Reality in COSMOS |
|-------|-------------------|
| UI framework | **Vanilla HTML + CSS + JS** (not React/Vue/Svelte) |
| Host | **pywebview** + local HTTP shell (`gui/server.py`) |
| Tokens | CSS custom properties in `gui/static/cosmos-tokens.css` |
| Components | CSS class patterns + JS DOM builders (not a component npm package) |
| Storybook | **None** |
| Bundler | **None** for GUI static — files served directly |
| Theme | Single **Deep Space Engineering** dark theme (no light mode yet) |
| Propulsion UI | Client of Systems/API — **no engineering equations in JS** |

**Visual doctrine:** 80% engineering workstation + 15% mission-control + 5% space atmosphere. Not sci-fi dashboard. Not a clone of ANSYS / NX / COMSOL.

---

## 1. Token definitions

### 1.1 Where tokens live

| Layer | Path |
|-------|------|
| **Executable tokens** | `gui/static/cosmos-tokens.css` |
| **Doctrine / named palette** | `docs/COSMOS_0.1_UI_UX_DESIGN_SYSTEM.md` §4–5 |
| **Shell consumption** | `gui/static/cosmos-shell.css`, `gui/static/cosmos.css` |
| **Feature CSS** | e.g. `gui/static/propulsion-suite.css`, `gui/static/maharshi.css`, `gui/static/login.css` |

Entry import chain:

```css
/* gui/static/cosmos.css */
@import url("cosmos-tokens.css");
@import url("cosmos-background.css");
@import url("cosmos-shell.css");
```

### 1.2 Format / structure

Tokens are **`:root` CSS custom properties** — no Style Dictionary, Tokens Studio export, or JSON token pipeline today.

#### Color primitives

```css
--cosmos-void: #030609;
--cosmos-deep: #060C14;
--cosmos-panel: #0A1220;
--cosmos-raised: #0E192C;
--cosmos-border: #162438;
--cosmos-border-strong: #1F3550;
--cosmos-text: #B0CCE0;
--cosmos-muted: #365570;
--cosmos-dim: #1A3048;
--cosmos-cyan: #00D4FF;      /* primary interactive */
--cosmos-orange: #FF4D00;    /* propulsion / emphasis */
--cosmos-green: #39FF14;     /* verification / ready */
--cosmos-yellow: #FFD000;    /* warning */
--cosmos-violet: #BF5FFF;    /* knowledge */
--cosmos-red: #FF4D4D;       /* error */
```

#### Semantic aliases (legacy shell)

```css
--accent-blue: var(--cosmos-cyan);
--accent-orange: var(--cosmos-orange);
--text-main: #EAF4FF;
--text-muted: var(--cosmos-text);
--success: var(--cosmos-green);
--warning: var(--cosmos-yellow);
--error: var(--cosmos-red);
--info: var(--cosmos-cyan);
```

#### Typography

```css
--font-brand: "Orbitron", "Segoe UI", sans-serif;     /* brand / headings only */
--font-ui: "Exo 2", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
--font-mono: "JetBrains Mono", "SF Mono", "Consolas", monospace;
```

Loaded via Google Fonts `@import` at top of `cosmos-tokens.css`.

#### Spacing scale

```css
--space-1: 4px;  --space-2: 8px;  --space-3: 12px;
--space-4: 16px; --space-5: 20px; --space-6: 24px; --space-8: 32px;
```

#### Radii (engineering-sharp — prefer small)

```css
--radius-sm: 2px; --radius-md: 4px; --radius-lg: 8px;
--radius-glass: 18px; --radius-pill: 999px;
```

#### Motion / elevation / layout

```css
--shadow: 0 18px 50px rgba(0, 0, 0, 0.55);
--shadow-sm: 0 8px 24px rgba(0, 0, 0, 0.4);
--transition-fast: 140ms ease;
--transition-med: 280ms ease;
--frame-pad: 14px;
--nav-width: 84px;
--nav-width-expanded: 196px;
--console-height: 32px;
```

### 1.3 Token transformation

**None.** Figma variables should mirror CSS names 1:1 with code syntax like:

```text
CODE_SYNTAX_WEB → var(--cosmos-cyan)
```

Do not invent a second token naming scheme (e.g. `color.primary.500`) unless explicitly migrating both CSS and Figma together.

### 1.4 Figma variable mapping (recommended collections)

| Figma collection | Mode | Contents |
|------------------|------|----------|
| `COSMOS / Primitives` | Default (dark) | Raw hex → cosmos-void…cosmos-red |
| `COSMOS / Semantic` | Default | Aliases → accent, success, text-main |
| `COSMOS / Spacing` | Default | space-1…space-8, frame-pad, nav-width |
| `COSMOS / Radius` | Default | radius-sm…radius-pill |

**No light mode** in code — do not add a Light mode in Figma unless product explicitly requests it.

---

## 2. Component library

### 2.1 Where UI “components” live

There is **no** React component tree. Patterns are:

| Pattern | Definition |
|---------|------------|
| Shell layout | HTML structure in `gui/static/*.html` + `cosmos-shell.css` |
| Sidebar / hub | Built in JS: `gui/static/app.js` (`renderSidebar`, workbench cards) |
| Propulsion suite | `gui/static/propulsion-suite.js` + `.css` |
| Knowledge / Maharshi | `maharshi.js`, `maharshi.css`, `maharshi-popup.js` |
| Login | `login.html`, `login.css`, `login.js` |

### 2.2 Architecture

```text
HTML page shell
  └── .app-frame.page-shell
        ├── .app-header (avatar, context, user-badge)
        ├── .app-body
        │     ├── .sidebar (JS-rendered)
        │     └── .content-area (page-specific)
        ├── .maharshi-module (FAB)
        └── .status-bar
```

JS global: `window.COSMOS` — shell, RBAC helpers, suite inits.

### 2.3 Documentation / Storybook

- Design doctrine: `docs/COSMOS_0.1_UI_UX_DESIGN_SYSTEM.md`
- **No Storybook / Ladle / Styleguidist**
- Propulsion suite catalog: `gui/workbenches/propulsion_suite.py` + live HTML

### 2.4 Key CSS component classes (Figma component candidates)

| Class | Role |
|-------|------|
| `.zone-pill` / `.header-pill` | Compact header chips |
| `.sidebar-btn` | Nav rail button (+ `.active`, `.disabled`) |
| `.workbench-card` | Hub launcher card |
| `.module-btn` | Workbench module tile |
| `.suite-card` / `.suite-nav` | Propulsion suite forms + stage nav |
| `.status` / `.pill.live\|partial\|planned` | Capability honesty badges |
| `.maharshi-module` | Knowledge FAB |
| `.status-bar` / `.status-indicator` | Bottom engineering status |
| `.cosmos-btn` / `.primary` | Actions |

### 2.5 Workflow / engineering result UI contract

Every calculation stage UI should expose (doctrine + Systems Phase 2+):

```text
INPUTS · MODEL · ASSUMPTIONS · CALCULATE · RESULTS · WARNINGS · VALIDITY · V&V
```

Statuses: `CURRENT | STALE | FAILED | NOT_CALCULATED | NOT_IMPLEMENTED | OUT_OF_RANGE`

Never present STALE as current. Never put Physics equations in Figma-exported JS.

---

## 3. Frameworks & libraries

| Concern | Choice |
|---------|--------|
| UI framework | None (vanilla) |
| Desktop bridge | `pywebview` (`gui/native_window.py`) |
| Server | Python `ThreadingHTTPServer` (`gui/server.py`) |
| CSS | Plain CSS + custom properties; some `color-mix()` |
| Charts | Not a shared charting library in shell (feature-specific if any) |
| Build | Static files; `STATIC_ASSETS` whitelist in `gui/server.py` |
| Package managers for GUI | N/A for shell (Python repo for backend) |

### Figma → code implication

`figma-design-to-code` output must be **adapted** to:

1. HTML fragment / page under `gui/static/`
2. Classes using `--cosmos-*` tokens
3. Optional page CSS file registered in `STATIC_ASSETS` if new
4. Behavior in JS without React hooks

Do **not** scaffold a Next.js/Vite React app inside this repo for shell screens unless product direction changes.

---

## 4. Asset management

### 4.1 Storage

| Asset type | Location | URL |
|------------|----------|-----|
| Workbench art | `gui/assets/workbenches/*.svg` (+ optional `.png`) | `/assets/workbenches/{id}.svg` |
| Brand / portrait | `gui/assets/cosmos_logo.png`, `maharshi_bharadwaj.png` | `/assets/...` |
| Profile photos | `gui/assets/profiles/` (runtime) | `/assets/profiles/...` |
| Static CSS/JS | `gui/static/` | `/assets/{filename}` via whitelist |

### 4.2 Serving rules (`gui/server.py`)

- `/assets/{name}` → if name in `STATIC_ASSETS`, serve from `gui/static/`; else from `gui/assets/`
- Path traversal blocked (`_safe_asset_path`)

### 4.3 Optimization / CDN

- No CDN for desktop app assets
- No automated image pipeline (no ImageMagick/webpack image loader)
- Prefer SVG for workbench illustrations; PNG for photographic Maharshi portrait
- FAB portrait: avoid `mix-blend-mode: screen` (made icon disappear) — use normal blend + fixed positioning

### 4.4 Figma asset rule

Export SVG/PNG into `gui/assets/` with kebab-case names matching workbench IDs where applicable (`rocket-engine.svg`).

---

## 5. Icon system

### 5.1 Navigation icons

**Inline SVG strings** in `gui/static/app.js` → `COSMOS.NAV_ICONS`.

```javascript
NAV_ICONS: {
  command: '<svg viewBox="0 0 24 24">...</svg>',
  knowledge: '<svg viewBox="0 0 24 24">...</svg>',
  // ...
}
```

Rendered via:

```javascript
navIcon(name) {
  return `<span class="nav-icon" aria-hidden="true">${this.NAV_ICONS[name] || ...}</span>`;
}
```

### 5.2 Conventions

- ViewBox: **24×24**
- Stroke-based (CSS fills stroke on `.nav-icon svg`)
- Naming: **kebab-case** keys matching nav ids (`design-contract`, `vv`)
- No Lucide/Heroicons package — do not add icon font dependencies without decision

### 5.3 Workbench / domain icons

Separate from nav: illustration SVGs in `gui/assets/workbenches/`.

### 5.4 Figma icon library

Create a Figma icon component set `Icon / 24` with variants matching `NAV_ICONS` keys. Export as SVG path content for paste into `NAV_ICONS` or as files under assets.

---

## 6. Styling approach

### 6.1 Methodology

- **Global CSS** + BEM-like / utility-ish class names
- **No** CSS Modules, Styled Components, Emotion, Tailwind
- Feature CSS files scoped by class prefix (`.suite-*`, `.mh-*`, `.login-*`)

### 6.2 Global styles

- Reset-ish: `box-sizing: border-box` on `*`
- `body.cosmos-app { overflow: hidden; }` — desktop frame
- Background atmosphere: `cosmos-background.css` (starfield / space — keep restrained)

### 6.3 Responsive design

Desktop-first breakpoints in `cosmos.css`:

```css
@media (max-width: 1100px) { /* denser header / 2-col workbench grid */ }
@media (max-width: 720px)  { /* hide sidebar; single column */ }
```

Propulsion suite: `@media (max-width: 980px)` stacks suite nav.

Figma frames should prioritize **desktop 1440 / 1280** widths; mobile is secondary collapse, not mobile-first product.

### 6.4 Visual anti-patterns (reject in Figma reviews)

- Inter / Roboto / system as primary UI fonts
- Purple-on-white SaaS gradients
- Warm cream + terracotta editorial look
- Over-rounded consumer cards in hero/workbench
- Glow as primary brand signal
- Fake “complete” calculators without `NOT_IMPLEMENTED` honesty

---

## 7. Project structure (GUI-relevant)

```text
COSMOS_0.1/
├── docs/
│   ├── COSMOS_0.1_UI_UX_DESIGN_SYSTEM.md    # doctrine
│   └── FIGMA_MCP_DESIGN_SYSTEM_RULES.md     # this file
├── gui/
│   ├── application.py / native_window.py / server.py
│   ├── assets/          # images, workbench SVGs
│   ├── static/          # HTML/CSS/JS served as /assets
│   │   ├── cosmos-tokens.css
│   │   ├── cosmos-shell.css
│   │   ├── cosmos.css
│   │   ├── app.js
│   │   ├── propulsion-suite.*
│   │   └── workbench/*.html
│   └── workbenches/     # Python registry + suite catalog
├── systems/             # propulsion workflow (not UI)
├── api/                 # HTTP adapters
├── physics/ / core/     # FROZEN — no GUI imports
└── .cursor/rules/
    └── cosmos-figma-design-system.mdc
```

### Feature organization pattern

1. Add/extend HTML under `gui/static/` or `gui/static/workbench/`
2. Add CSS tokens/classes; register new static filenames in `STATIC_ASSETS` if needed
3. Wire JS init (`COSMOS.init…`)
4. Server route in `gui/server.py` if new page
5. Backend via `api/` → `systems/` — never Physics in GUI

---

## 8. Figma MCP workflow (agent checklist)

### Skills to load

1. `figma-use` — Plugin API calls  
2. `figma-generate-library` — variables/components order  
3. `figma-design-to-code` — before `get_design_context`  
4. `figma-generate-design` — code → Figma screen capture  
5. `figma-code-connect` — when mapping components (map to **CSS class / HTML pattern**, not React)

### Phase 0 discovery (before mutating Figma)

- [ ] Tokens extracted from `cosmos-tokens.css`
- [ ] Shell components listed (§2.4)
- [ ] Confirm no React — adapt codegen
- [ ] Gap analysis: Figma vs code
- [ ] Lock v1 scope (shell + workbench card + suite stage chrome)

### Implementation acceptance

A Figma-integrated screen is done when:

1. Uses `--cosmos-*` tokens (or documented new tokens added to `cosmos-tokens.css`)
2. Fits `.app-frame` shell
3. Typography uses Orbitron / Exo 2 / JetBrains Mono correctly
4. Engineering numbers use mono
5. Status honesty preserved for workflow modules
6. No Physics equations in client JS
7. Assets under `gui/assets` or inline SVG icons

---

## 9. Propulsion workflow UI notes (Systems phases)

When designing workflow stages in Figma (Requirements → … → Design Review):

- Live inside **Rocket Engine** workbench — not a top-level “Propulsion” sidebar item
- Share one **design context** (server `PropulsionDesign`), not isolated calculator frames
- Show model id / verification / validation (`NOT_CLAIMED`) on results
- Mark unavailable stages `NOT_IMPLEMENTED` visually (planned/partial/live pills already exist)

Backend authority: `systems/` + `api/propulsion_workflow.py`. GUI is a client.

---

## 10. Quick reference — copy into Figma variables

| Name | Value |
|------|-------|
| cosmos/void | `#030609` |
| cosmos/deep | `#060C14` |
| cosmos/panel | `#0A1220` |
| cosmos/raised | `#0E192C` |
| cosmos/border | `#162438` |
| cosmos/cyan | `#00D4FF` |
| cosmos/orange | `#FF4D00` |
| cosmos/green | `#39FF14` |
| cosmos/yellow | `#FFD000` |
| cosmos/violet | `#BF5FFF` |
| cosmos/red | `#FF4D4D` |
| cosmos/text | `#B0CCE0` |
| cosmos/muted | `#365570` |
| text/main | `#EAF4FF` |
| space/1…8 | 4, 8, 12, 16, 20, 24, 32 px |
| radius/sm | 2 px |
| font/brand | Orbitron |
| font/ui | Exo 2 |
| font/mono | JetBrains Mono |

---

## 11. Related frozen engineering rules (do not violate for UI beauty)

```text
physics → core
core ─X→ physics
gui ─X→ physics   (use api/)
gui ─X→ systems internals (HTTP only)
```

UI must not invent CEA results, cycle power balance, or injector math to fill empty Figma frames.

---

**End of FIGMA_MCP_DESIGN_SYSTEM_RULES_001**
