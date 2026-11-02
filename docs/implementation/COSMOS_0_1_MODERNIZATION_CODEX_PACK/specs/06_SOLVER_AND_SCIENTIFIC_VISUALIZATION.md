> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Solver monitoring and scientific visualization

## Required solver status dimensions
`execution_status`, `termination_reason`, `numerical_convergence`, `conservation_checks`, `physical_admissibility`, `solution_verification`, `experimental_validation`. Never collapse to one success flag.

## Solve workspace
Study definition → preflight → immutable run snapshot → queued execution → structured monitor events → result dataset → scientific plots → V&V.

## Required plots
Residuals with declared normalization; conservation balances; CFL/time step and stability indicators where relevant; iteration/time history; field maps with units, legend, clipping, geometry revision and mesh metadata.

## Viewer pipeline
Use an existing viewer when possible. Assess VTK/Qt for large mesh support. Rendering MUST NOT own solver state. Use data adapters and lazy loading for large fields.

## Validation
Plot labels, units and legend ranges have tests. Synthetic reference cases test result navigation, missing data, nonconvergence, corrupt datasets and out-of-memory recovery.
