# Steady spherical conduction benchmark

Isolated software verification case. No changes to existing engine physics.

SI: centered solid sphere R=0.01 m; constant isotropic k=10 W/(m K); uniform volumetric generation q=1e6 W/m³; fixed exterior T=300 K; regular zero-flux center. These are declared synthetic benchmark values, not sourced flight material properties.

Equation: `-k/r² d/dr(r² dT/dr) = q`. Integrate with regular center: `dT/dr = -qr/(3k)`. Apply exterior temperature: `T(r) = Ts + q(R²-r²)/(6k)`. The center reference is 301.6666666666667 K. Total generation and exterior outward power equal `q 4πR³/3 = 4.188790204786391 W`. Analytic radial outward flux is `qr/3 W/m²`.

Spherical control volumes use exact shell volume and face area, uniform radial spacing, center symmetry and exterior Dirichlet boundary. This is a **1D symmetry-reduced volume mesh**, not a STEP triangulation, arbitrary 3D mesher or the P08 coarse display mesh. The exact semantic `outer-surface` maps to its `radial-outer-shell`; this is a fixture-specific analytic mapping, not persisted native face-ID remapping. Mesh metadata binds source/export hashes, geometry revision, frame, selection, material region and original independent geometry QA hash.

Gauss-Seidel explicitly solves `A(T-Ts)=qV`. Numerical termination uses `||qV-A(T-Ts)||2/||qV||2`, not update norm. Report signed `outward_power-generated_power` in W and relative absolute imbalance separately. Conservation tolerance is `2 sqrt(N) relative_residual` (Cauchy-Schwarz residual bound with conservative RHS norm bound), not relaxed silently. Positive finite temperature is the scoped physical-admissibility check. No CFL or time-step stability applies to this steady elliptic model.

Solution verification compares cell-center values to the independent analytic expression. The declared max error acceptance is `qR²/(6kN²)`, tested with mesh refinement at 8/16/32/64 cells and an adequately tighter numerical residual. If the analytic error or conservation check fails, execution completion is not verification success. Experimental validation is always `not-performed`; engineering review is `pending`.

Acceptance basis: on this uniform radial mesh, exact integrated generation gives face power `q 4πr³/3`. Interior midpoint diffusion differences reproduce differences of the quadratic analytic profile. The exterior half-cell Dirichlet discretization adds the uniform cell-center error `q Δr²/(24k)` at exact algebraic convergence. The predeclared ceiling `q Δr²/(6k)` is four times that analytic discretization error, leaving room for the separately controlled iterative residual. The measured refinement ratio must remain approximately 4; this is a scoped code/solution check, not an engineering uncertainty budget.
