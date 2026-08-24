"""Rights metadata. UNKNOWN is never treated as cleared."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "INGESTIBLE_RIGHTS",
    "RightsRecord",
    "RightsStatus",
    "rights_allow_ingestion",
)


class RightsStatus(Enum):
    RIGHTS_CLEARED = "RIGHTS_CLEARED"
    LICENSED = "LICENSED"
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


INGESTIBLE_RIGHTS = frozenset(
    {
        RightsStatus.RIGHTS_CLEARED,
        RightsStatus.LICENSED,
        RightsStatus.PUBLIC_DOMAIN,
        RightsStatus.INTERNAL,
    },
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RightsRecord:
    status: RightsStatus
    license: str | None = None
    usage_constraints: str | None = None
    organization: str | None = None
    publication_year: int | None = None
    notes: str | None = None


def rights_allow_ingestion(status: RightsStatus) -> bool:
    return status in INGESTIBLE_RIGHTS
