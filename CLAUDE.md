# COSMOS 0.1 — Agent notes (GUI / Figma)

## Design system

- Doctrine: `docs/COSMOS_0.1_UI_UX_DESIGN_SYSTEM.md`
- Figma MCP rules: `docs/FIGMA_MCP_DESIGN_SYSTEM_RULES.md`
- Cursor rule: `.cursor/rules/cosmos-figma-design-system.mdc`
- Tokens: `gui/static/cosmos-tokens.css`

## GUI stack

Vanilla HTML/CSS/JS + pywebview. Not React. Prefer CSS variables over new frameworks.

## Propulsion workflow

Orchestration lives in `systems/`. GUI calls `/api/propulsion/*` and `/api/physics/*` only — no equations in JS.
