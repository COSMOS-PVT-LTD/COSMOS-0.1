import math
from dataclasses import replace

import numpy as np
import pytest

from plugins.geometry.nozzle_protocol import validate
from systems.geometry.nozzle_qa import NozzleQALimits
from systems.geometry.nozzle_reference import NozzleReference
from tests.fixtures.nozzle_geometry import case, qa_spec


def test_independent_frustum_annulus_volume_centroid_and_surfaces():
    s, g, r = case()
    ref = NozzleReference(validate(r, s, g))
    t, length, a, b = .002, .04, .01, .02
    expected = math.pi * length / 3 * ((a+t)**2 + (a+t)*(b+t) + (b+t)**2 - a*a - a*b - b*b)
    assert ref.volume_m3 == pytest.approx(expected, rel=1e-14)
    # Independent numerical quadrature of the ring-area first moment.
    xs = np.linspace(0, length, 10001)
    area = math.pi * (2*t*(a + (b-a)*xs/length) + t*t)
    moment = xs * area
    assert ref.centroid_m[0] == pytest.approx(np.sum((moment[1:] + moment[:-1]) * np.diff(xs) / 2) / np.sum((area[1:] + area[:-1]) * np.diff(xs) / 2), rel=1e-8)
    assert np.abs(ref.sdf(ref.surface_samples())).max() < 1e-17
    assert ref.sdf([[.02, .016, 0]])[0] < 0 and ref.sdf([[.02, 0, 0]])[0] > 0
    assert np.array_equal(ref.bounds_m, [0, -.022, -.022, .04, .022, .022])
    assert NozzleQALimits.from_spec(qa_spec()).relative_volume == .005


@pytest.mark.parametrize("defect", ["fixture", "frame", "graph", "tol", "version"])
def test_source_graph_frame_and_tolerance_refused_before_worker(defect):
    s, g, r = case()
    if defect == "fixture": s = replace(s, project_id="p07-software-fixtures")
    if defect == "graph": g = replace(g, output_feature_ids=("inner-profile",))
    if defect == "tol": r = replace(r, export_tolerance_m=.00002)
    if defect == "version": r = replace(r, backend_version="fixture-worker")
    with pytest.raises(ValueError):
        if defect == "frame": s = replace(s, frame_id="unsupported")
        validate(r, s, g)
