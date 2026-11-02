# Guided cold-reference property package v1

The two original TSV responses are retained byte-for-byte from the existing
2026-10-21 NIST study. Checksums and complete request identities are pinned in
plugins/guided_engine/sources.py. Only the exact liquid rows at 6 bar absolute,
methane 111.15 K and oxygen 90.15 K are consumed. The additional 6.1 bar response
rows do not authorize interpolation, extrapolation, saturation or heated cooling.

Source: https://webbook.nist.gov/chemistry/fluid/ (NIST SRD 69, DEF reference state).
No historical study approval is transferred; a new guided profile review is
required per accepted brief. Reference properties are not engine measurements
or certified material data. No user credentials or private documents are bundled.
