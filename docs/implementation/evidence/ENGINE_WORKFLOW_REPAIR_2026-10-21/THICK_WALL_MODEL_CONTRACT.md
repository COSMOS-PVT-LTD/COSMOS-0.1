# Bounded thick-wall structural model contract

2026-10-21. Additive extension to Physics → Systems → API → existing GUI;
the frozen dependency direction and original thin-wall model are preserved.

`LAME_CLOSED_ENDS` is explicitly selected, never an automatic thin-wall fallback.
It represents a long, homogeneous, isotropic, unperforated elastic cylinder,
away from end discontinuities, with uniform absolute internal/external pressures
and pressure-loaded closed ends. Tensile stress is positive. With inner radius a,
outer radius b, and d=(b-a)(b+a):

- A=(Pi*a²-Po*b²)/d; B=(Pi-Po)*a²*b²/d.
- radial(r)=A-B/r²; hoop(r)=A+B/r²; axial=A by closed-end force balance.
- von Mises(r)=sqrt(3)*abs(B)/r², maximal at the bore for this load case.

Reference: [NPTEL Solid Mechanics, annular-cylinder boundary-value solution,
equations 7.66–7.69](https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch7.html).
That example fixes axial length; its axial stress is **not** reused. This model's
axial stress follows the separate end-force balance above. External pressure is
not simply subtracted from all three absolute stress components. Equal pressures
must give hydrostatic compression and zero equivalent stress.

The elementary Physics stress field may describe Pi<Po, but the Systems tensile
screen rejects that case until shell stability/buckling is supported. No numerical
PASS implies small strain, elastic admissibility or safety has been established.
The stage uses explicitly temperature-valid catalog typical yield only; no new
GRCop-42 or INCONEL 718 allowables are inferred from candidate selection.

Verification: traction at both radii, radial equilibrium, closed-end force,
hydrostatic invariance, pressure scaling, thin-wall limit, SI dimensions,
invalid/nonfinite inputs, and exact-revision persisted model selection. Keep
`hoop_over_yield` for compatibility, but use `stress_over_yield` (von Mises for
Lamé, hoop for legacy thin-wall) as the governing preliminary yield screen.

Explicit exclusions: channel ligaments/holes, bonded bimetallic liner/jacket,
thermal gradients/stress, creep, fatigue, plasticity, welds, end plates, nozzle
contour loads, mounts, buckling and pressure-vessel-code certification. The
current cooled engine CAD cannot be qualified by this smooth-cylinder model.
