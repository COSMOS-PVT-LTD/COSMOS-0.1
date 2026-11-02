# R06.3 and R06.4 — approved selected-cycle implementation

Entry HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`. Existing dirty work is preserved. User explicitly requests gas-generator contracts/implementation, subsystem coupling and integrated qualification. No release, push, live-data migration or hardware operation is authorized.

## Acceptance contract fixed before implementation

1. Add a dimensional Physics model for a steady single-shaft open GG cycle. Liquids are incompressible. Turbine gas is calorically perfect with explicitly supplied total state, cp, gamma and total-to-total efficiency. Pump efficiencies and pressure rises are explicit design-point assumptions, not component maps. GG O/F is separate from core O/F. Both pumps also feed their GG fractions; solve this feedback, not just core pump demand.
2. Use the existing immutable downstream assessment boundary. Do not create a back-edge from performance/cooling into the frozen upstream cycle stage. Do not modify existing equations or original results. Implement selected-cycle assessment completion separately from workflow/physical readiness.
3. Consume actual retained CURRENT injector results; check their flow, pressure and property context against the retained core. Optional regenerative cooling must be explicitly disabled or consume its CURRENT result as a full-core-fuel series path, with flow/density/pressure/energy consistency checks. No arbitrary partial-flow routing is invented. Film is explicitly disabled or drawn from the CURRENT cooling film estimate as an additional fuel withdrawal with an imposed externally conditioned boundary; no liquid-to-gas conditioner model is claimed. Include its feed pressure requirement, source and external conditioning boundary in the record. Other external withdrawals are explicit nonnegative streams. They reduce core-only thrust per total propellant flow; no invented GG/film/external exhaust thrust.
4. Accept exact saved assumed-state and CEA core performance results through their explicit adapters; never rerun/relabel CEA as assumed-state. Preserve the core nozzle result. Report total-withdrawal effective core-only Isp and a mass/pressure/power/energy ledger, with limits explaining that frozen core thermochemistry is not a coupled combustion/heat-loss recalculation.
5. Preserve R05 capture-before-evaluate, CAS, actor-scoped idempotency/restart, membership, original source export and selective baseline/method invalidation. Reuse configurable existing pressure-fed authority/routes, keeping their existing defaults and tests unchanged.
6. Add Projects controls, source inspection, residual CSV and source-bound plots. Require explicit SI specification input; no operating values defaulted from fixtures. Keep unsupported cycles explicit.
7. Independently verify hand-derived values, feedback infeasibility, energy mismatch, stale/wrong source, unit/Boolean/nonfinite rejection, no mutation, exact storage/restart/exports, cross-project/reader denial and UI contracts. Run focused and full regression/static checks. Record actual evidence and exclusions without rewriting earlier receipts.

## Primary equation sources inspected

- NASA Glenn, [Power Turbine Thermodynamics](https://www.grc.nasa.gov/WWW/K-12/airplane/powtrbth.html), equations for total pressure ratio, isentropic temperature ratio and efficiency-adjusted specific turbine work. Use total-to-total isentropic efficiency only; separate shaft mechanical efficiency. No source-supplied numerical efficiencies or gas properties.
- DOE-HDBK-1012/3-92 [Fluid Flow](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL3.pdf), HT-03 pp9–11 continuity, p25 extended Bernoulli including pump head, pp47–49 pump pressure/efficiency and map/NPSH limitations. Coherent SI gives hydraulic work `dp/rho`; shaft work divides by pump efficiency. No pump-speed, cavitation or map acceptance is inferred.
- NASA-SP-8081 [Liquid propellant gas generators](https://ntrs.nasa.gov/citations/19730018978), topology/temperature limitations only. Not used as a component map or thermochemical-property source.

## Equations and termination

`w_p,i=(p_out,i-p_in,i)/(rho_i*eta_p,i)` [J/kg]. `w_t=eta_t*cp*Tt_in*(1-(Pt_out/Pt_in)^((gamma-1)/gamma))`. `Tt_out=Tt_in-w_t/cp`.

Let `b_i` be core + film + explicitly external demand, and `a_ox=r_GG/(1+r_GG)`, `a_f=1/(1+r_GG)`. `m_p,i=b_i+a_i*m_GG`. Solve exactly `m_GG=(sum(b_i*w_p,i)+P_aux)/(eta_shaft*w_t-sum(a_i*w_p,i))`. Nonpositive denominator or flow exceeding explicitly supplied GG limit is infeasible, not clipped. This is an affine, closed-form solution: zero iterations, DIRECT_AFFINE termination. Independently evaluate shaft residual afterward; finite arithmetic and all declared residual tolerances must pass. No iterative-convergence claim.

GG energy uses user-sourced common-reference specific inlet enthalpy and net released chemical energy: `m_GG*(h_in+q_release-cp*Tt_in)-Q_loss`. This checks supplied thermal state; it does not solve combustion chemistry. Turbine energy residual is `m_GG*cp*(Tin-Tout)-P_turbine`. Regenerative residual is retained `Q-m_core_f*cp_c*(Tout-Tin)`; regenerative flow is not counted twice. Pressure residuals are independent per core/GG/film/external branch. A declared branch control drop is required to consume surplus; no automatic throttle loss is inserted.

## Independent fixtures declared before code

Synthetic Physics case: core oxidizer/fuel 2/1 kg/s; each pump dp1MPa, rho1000, eta.5 gives2000 J/kg. Turbine Tin1000K, cp1000J/kg/K, gamma2, pressure ratio1/4, eta.8 gives400000J/kg, Tout600K; shaft eta.9. GG O/F1 gives denominator358000J/kg, mGG=6000/358000=3/179kg/s; total pump mass3+3/179 and shaft power `6000+2000*(3/179)`. Auxiliary100W gives6100/358000kg/s. Fuel-film.1kg/s increases numerator to6200W. GG common-reference energy input1MJ/kg and zero heat loss closes independently. A1J/kg thermal inconsistency must produce a nonzero residual. If available turbine work <= feedback pump work, refuse. A GG mass cap below3/179 refuses. Equal inlet/outlet turbine pressure and efficiency outside(0,1] refuse.

Software qualification is not experimental validation, hardware feasibility, production/flight acceptance, full network operating-point solution, pressurant sizing or transient startup. SC/expander/electric remain unsupported. Human/native macOS accessibility and hardware evidence are not substituted with automated tests.
