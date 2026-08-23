"""Engineering-domain feature encoding for local neural embeddings."""

from __future__ import annotations

import hashlib
import math
import re

__all__ = (
    "ENGINEERING_SYNONYMS",
    "FeatureEncoder",
)

ENGINEERING_SYNONYMS: dict[str, tuple[str, ...]] = {
    "lox": ("liquid", "oxygen", "oxidizer"),
    "lh2": ("liquid", "hydrogen", "fuel"),
    "rp1": ("rocket", "propellant", "kerosene"),
    "isp": ("specific", "impulse", "performance"),
    "thrust": ("force", "propulsion", "motor"),
    "chamber": ("combustion", "pressure", "nozzle"),
    "turbopump": ("pump", "feed", "propellant"),
    "combustion": ("reaction", "flame", "oxidizer"),
    "thermodynamics": ("entropy", "enthalpy", "energy"),
    "conduction": ("heat", "transfer", "thermal"),
    "convection": ("heat", "transfer", "fluid"),
    "radiation": ("heat", "transfer", "thermal"),
    "reynolds": ("fluid", "flow", "turbulence"),
    "mach": ("compressible", "flow", "aerodynamics"),
    "stress": ("structure", "load", "material"),
    "strain": ("deformation", "material", "elastic"),
    "composite": ("material", "laminate", "structure"),
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class FeatureEncoder:
    """Bag-of-features encoder with engineering synonym expansion."""

    def __init__(self, *, feature_dimension: int = 512) -> None:
        self._feature_dimension = feature_dimension

    @property
    def feature_dimension(self) -> int:
        return self._feature_dimension

    def encode(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        expanded: list[str] = []

        for token in tokens:
            expanded.append(token)
            synonyms = ENGINEERING_SYNONYMS.get(token)

            if synonyms is not None:
                expanded.extend(synonyms)

        features = [0.0] * self._feature_dimension

        for token in expanded:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._feature_dimension
            features[index] += 1.0

        norm = math.sqrt(sum(value * value for value in features))

        if norm == 0.0:
            return features

        return [value / norm for value in features]
