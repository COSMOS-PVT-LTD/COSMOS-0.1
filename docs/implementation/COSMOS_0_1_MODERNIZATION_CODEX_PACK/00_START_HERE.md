# COSMOS 0.1 — CodeX implementation package

## Purpose
Implement a complete professional scientific UI/UX modernization **and** a Native Geometry Generator (NGG) that can use PicoGK/OpenVDB and an analytic B-rep backend. Preserve the frozen architecture and validated scientific behavior.

## Mandatory execution order
1. Read `01_MASTER_CODEX_PROMPT.md` and `02_EXECUTION_SEQUENCE.md`.
2. Read `03_BASELINE_ARCHITECTURE_AND_SOURCE_LIMITS.md`.
3. Run **AUDIT** prompt first. Record current commit and evidence. Do not infer implementation from the frozen architecture PDF.
4. Implement shared contracts and design system before replacing individual workbench screens.
5. Implement NGG proof of concept before promising CAD export.
6. Execute gated phases with small commits, tests, and concise evidence logs.

## How to give this to Codex
Unzip at repository root under `docs/implementation/COSMOS_0_1_MODERNIZATION_CODEX_PACK/`, or attach the folder to Codex. Give Codex **only** `01_MASTER_CODEX_PROMPT.md` as the first instruction. It instructs Codex to read the remaining documents in order. Use `prompts/P00_REPOSITORY_AUDIT.md` first if Codex cannot follow a long autonomous run.

## Package organization
- `prompts/`: executable phase prompts, small output budgets.
- `specs/`: normative engineering and UI/UX contracts.
- `workbenches/`: individual workbench requirements.
- `diagrams/`: Mermaid diagrams and data-flow maps.
- `acceptance/`: machine-checkable gates and test matrix.
- `videos/`: video storyboard, narration and production plan (not rendered videos).
- `templates/`: reports, decisions, evidence and pull-request templates.

## Execution safety
Do not modify or remove existing validated physics without explicit evidence and approved change record. Do not use the word 'validated' for a simulation result without a validation record. Keep a working rollback path.
