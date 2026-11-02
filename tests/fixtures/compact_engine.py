"""Millimetre-scale manufactured CSG software fixture, never engine evidence."""

from dataclasses import replace

from systems.geometry.component_model import Part
from systems.geometry.engine_redesign import Candidate, Group
from tests.fixtures.component_geometry import plan


def joined_rings(*, gap=0.0, overlap=0.0):
    source = plan("profile.wall")
    left = Part("left", "body", "world", ((0.0, 0.005, 0.008), (0.002, 0.005, 0.008)))
    right = Part(
        "right",
        "body",
        "world",
        ((0.002 + gap - overlap, 0.005, 0.008), (0.004, 0.005, 0.008)),
    )
    channel = Part(
        "variable-channel",
        "body",
        "world",
        ((0.0, 0.0058, 0.0068), (0.002, 0.006, 0.0072), (0.004, 0.0058, 0.0068)),
        role="coolant",
        sector=(0.2, 0.5),
    )
    source = replace(source, parts=(left, right))
    return Candidate(
        source, {}, (Group("joined-rings", (left, right), (channel,)),), (channel,)
    )
