"""Kernel-independent exact polygon-of-revolution reference, not physical validation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

import numpy as np

from plugins.geometry.nozzle_protocol import NozzleProfile


@dataclass(frozen=True)
class NozzleReference:
    profile: NozzleProfile
    operation: str = "divergent-nozzle-radial-wall-v1"

    @property
    def radius_m(self) -> float:
        return self.profile.points[0][1]

    def integrals(self) -> tuple[float, float]:
        t = self.profile.radial_thickness_m
        volumes, moments = [], []
        for (x0, r0), (x1, r1) in pairwise(self.profile.points):
            dx, slope = x1 - x0, (r1 - r0) / (x1 - x0)
            a, b = 2 * t * r0 + t * t, 2 * t * slope
            volume = math.pi * (a * dx + b * dx * dx / 2)
            volumes.append(volume)
            moments.append(x0 * volume + math.pi * (a * dx * dx / 2 + b * dx ** 3 / 3))
        return math.fsum(volumes), math.fsum(moments)

    @property
    def volume_m3(self) -> float:
        return self.integrals()[0]

    @property
    def centroid_m(self):
        volume, moment = self.integrals()
        return np.array([moment / volume, 0., 0.])

    @property
    def bounds_m(self):
        outer = self.profile.points[-1][1] + self.profile.radial_thickness_m
        return np.array([0., -outer, -outer, self.profile.points[-1][0], outer, outer])

    def sdf(self, points):
        data = np.asarray(points, dtype=float).reshape(-1, 3)
        radial = np.hypot(data[:, 1], data[:, 2])
        planar = np.column_stack((data[:, 0], radial))
        inner = np.array(self.profile.points)
        outer = inner.copy(); outer[:, 1] += self.profile.radial_thickness_m
        polygon = np.vstack((inner, outer[::-1], inner[:1]))
        distances = np.full(len(data), np.inf)
        for a, b in pairwise(polygon):
            delta = b - a
            alpha = np.clip(((planar - a) * delta).sum(axis=1) / np.dot(delta, delta), 0, 1)
            distances = np.minimum(distances, np.linalg.norm(planar - a - alpha[:, None] * delta, axis=1))
        surface_radius = np.interp(data[:, 0], inner[:, 0], inner[:, 1])
        inside = (data[:, 0] >= inner[0, 0]) & (data[:, 0] <= inner[-1, 0]) & (radial >= surface_radius) & (radial <= surface_radius + self.profile.radial_thickness_m)
        return np.where(inside, -distances, distances)

    def surface_samples(self):
        points = self.profile.points
        xs = sorted({x for x, _ in points} | {(a[0] + b[0]) / 2 for a, b in pairwise(points)})
        angle = np.arange(8) * (math.pi / 4)
        source = np.array(points)
        rows = []
        for x in xs:
            radius = float(np.interp(x, source[:, 0], source[:, 1]))
            for r in (radius, radius + self.profile.radial_thickness_m):
                rows.extend((x, r * math.cos(a), r * math.sin(a)) for a in angle)
        for x, r in (points[0], points[-1]):
            rows.extend((x, radius * math.cos(a), radius * math.sin(a)) for radius in np.linspace(r, r + self.profile.radial_thickness_m, 3) for a in angle)
        return np.array(rows)
