import numpy as np
import pytest

from plugins.geometry.workers.stl_encoding import RECORD, encode_si_stl
from systems.contracts.geometry import GeometryContractError
from systems.geometry.qa import read_stl


def native(path, count=101, *, bad=False):
    records = np.zeros(count, dtype=RECORD)
    records["vertices"][:-1] = [[0, 0, 0], [10, 0, 0], [0, 10, 0]]
    if bad:
        records["vertices"][0, 0, 0] = float("nan")
    path.write_bytes(b"native mm".ljust(80, b" ") + count.to_bytes(4, "little") + records.tobytes())


def test_si_encoder_excludes_only_exact_zero_and_preserves_scaled_vertices(tmp_path):
    source, target = tmp_path / "native.stl", tmp_path / "export.stl"
    native(source)
    original = source.read_bytes()
    report = encode_si_stl(source, target)
    assert report["excluded_exact_zero_area_triangles"] == 1
    assert report["positive_area_epsilon"] is None and not report["vertex_welding"]
    assert source.read_bytes() == original
    assert np.array_equal(read_stl(target)[1][0], np.array([[0, 0, 0], [.01, 0, 0], [0, .01, 0]], dtype=np.float32))
    with pytest.raises(GeometryContractError):
        encode_si_stl(source, target)


@pytest.mark.parametrize("defect", ["excess", "nonfinite", "length", "symlink"])
def test_encoder_refuses_bad_native_tessellation_before_output(tmp_path, defect):
    source, target = tmp_path / "native.stl", tmp_path / "export.stl"
    native(source, count=2 if defect == "excess" else 101, bad=defect == "nonfinite")
    if defect == "length":
        source.write_bytes(source.read_bytes()[:-1])
    if defect == "symlink":
        link = tmp_path / "link.stl"; link.symlink_to(source); source = link
    with pytest.raises(GeometryContractError):
        encode_si_stl(source, target)
    assert not target.exists()
