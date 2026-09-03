"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.film_cooling
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Film-cooling effectiveness interface without unsourced correlations.
"""

from __future__ import annotations

from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity

__all__ = ("FILM_COOLING", "effectiveness")

FILM_COOLING = ModelIdentity(
    model_id="PHYS-005.film_cooling.interface",
    model_name="Film-cooling effectiveness interface",
    physical_domain="heat_transfer",
    equations=("eta = (T_aw - T_w) / (T_aw - T_c)  (definition)",),
    inputs=("gas and coolant states",),
    outputs=("effectiveness [-]",),
    assumptions=("Definition only until a sourced injector/film correlation is ingested.",),
    validity_range="Not executable without a sourced correlation.",
    source="Definition: Incropera / rocket cooling literature. Correlation: OPEN SCIENTIFIC ISSUE.",
    verification_status="interface_only",
    limitations=("NASA injector-film correlations are not copied here without a sourced dataset.",),
)


def effectiveness(*_args: object, **_kwargs: object) -> float:
    """Film-cooling correlations are not invented in this batch."""

    raise InsufficientDataError(
        "Film-cooling effectiveness requires a sourced correlation "
        "(injector design criteria / NASA film-cooling data). "
        "OPEN SCIENTIFIC ISSUE: ingest an approved film-cooling dataset "
        "before executable evaluation."
    )
