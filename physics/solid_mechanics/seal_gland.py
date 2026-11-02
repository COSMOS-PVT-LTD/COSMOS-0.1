"""Nominal circular seal / rectangular face-gland geometry, not seal selection."""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import LENGTH
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive
from physics.model import ModelIdentity
from physics.quantities import as_si

FACE_GLAND = ModelIdentity(
    model_id="PHYS-JOINT.nominal_face_gland_geometry",
    model_name="Declared nominal circular-seal face-gland geometry",
    physical_domain="solid_mechanics",
    equations=("squeeze=(d-depth)/d", "seal_volume=2*pi*R*pi*d²/4", "gland_volume=2*pi*R*width*depth", "fill=seal_volume/gland_volume"),
    inputs=("seal section diameter/mean radius [m]", "gland radial width/depth [m]", "explicit sourced squeeze/fill criteria"),
    outputs=("nominal squeeze/fill", "volumes [m3]", "declared nominal geometry checks"),
    assumptions=("Concentric undeformed circular seal volume and rectangular face gland at the same specified reference state.",),
    validity_range="Positive finite dimensions; groove inner radius positive; caller-defined 0<=squeeze_min<squeeze_max<1 and 0<fill_max<1",
    source="Direct geometric volume/squeeze definitions; criteria must come from the selected manufacturer's applicable compound/gland guidance.",
    verification_status="independent torus/annular-gland volumes, scale invariance and domain tests",
    limitations=("No compound selection, oxygen compatibility, cryogenic eligibility, contact pressure, extrusion, thermal contraction, swelling, tolerances or leakage assessment.",
                 "A nominal geometry pass does not qualify an O-ring for cold methane/LOX or a hot chamber joint."),
)


@dataclass(frozen=True, slots=True)
class FaceGlandFit:
    squeeze_fraction: float
    fill_fraction: float
    seal_volume_m3: float
    gland_volume_m3: float
    passed_declared_geometry: bool


def nominal_face_gland(*, section_diameter: Quantity, mean_radius: Quantity, radial_width: Quantity,
                       depth: Quantity, squeeze_min: float, squeeze_max: float, fill_max: float) -> FaceGlandFit:
    dimensions=[]
    for q,name in ((section_diameter,"section diameter"),(mean_radius,"mean radius"),(radial_width,"radial width"),(depth,"depth")):
        if not isinstance(q,Quantity) or isinstance(q.magnitude,bool):raise InvalidInputError("Core non-Boolean dimensions required")
        dimensions.append(validate_positive(as_si(q,LENGTH,name),name))
    d,r,width,height=dimensions
    if any(type(v) not in {int,float} or not math.isfinite(v) for v in (squeeze_min,squeeze_max,fill_max)):
        raise InvalidInputError("Explicit finite real squeeze/fill criteria required")
    if not 0<=squeeze_min<squeeze_max<1 or not 0<fill_max<1 or r<=max(width,d)/2:
        raise InvalidInputError("Invalid nominal gland/ring dimensions or declared criteria")
    squeeze=(d-height)/d
    seal=math.pi**2*r*d*d/2; gland=2*math.pi*r*width*height
    fill=seal/gland
    if not all(math.isfinite(v) and v>0 for v in (seal,gland,fill)):raise InvalidInputError("Gland volume exceeds finite positive bounds")
    return FaceGlandFit(squeeze,fill,seal,gland,squeeze_min<=squeeze<=squeeze_max and fill<=fill_max)
