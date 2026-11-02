"""Negative tests for the independent STL parser and QA; no native dependency."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np
from run_benchmarks import audit_mesh, read_stl


class StlAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cosmos-p02-parser-")
        self.path = Path(self.temp.name) / "fixture.stl"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, triangles=None, header=b"PicoGK UNITS= m", bad_normal=False):
        points = np.array([[0, 0, 0], [.01, 0, 0], [0, .01, 0], [0, 0, .01]])
        faces = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
        triangles = points[faces] if triangles is None else np.array(triangles, float)
        data = bytearray(header.ljust(80, b" ") + struct.pack("<I", len(triangles)))
        for triangle in triangles:
            normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
            length = np.linalg.norm(normal)
            normal = normal / length if length else np.zeros(3)
            if bad_normal:
                normal[0] = math.nan
            data.extend(struct.pack("<12fH", *normal, *triangle.ravel(), 0))
        self.path.write_bytes(data)

    def test_valid_binary_fixture(self):
        self.write()
        tris, normals = read_stl(self.path)
        self.assertEqual(tris.shape, (4, 3, 3))
        self.assertTrue(np.isfinite(normals).all())

    def test_truncated(self):
        self.path.write_bytes(b"short")
        with self.assertRaises(ValueError):
            read_stl(self.path)

    def test_unknown_unit(self):
        self.write(header=b"PicoGK UNITS=mm")
        with self.assertRaises(ValueError):
            read_stl(self.path)

    def test_wrong_count(self):
        self.write()
        data = bytearray(self.path.read_bytes())
        data[80:84] = struct.pack("<I", 500)
        self.path.write_bytes(data)
        with self.assertRaises(ValueError):
            read_stl(self.path)

    def test_trailing_bytes(self):
        self.write()
        self.path.write_bytes(self.path.read_bytes() + b"x")
        with self.assertRaises(ValueError):
            read_stl(self.path)

    def test_nonfinite_coordinates(self):
        self.write()
        data = bytearray(self.path.read_bytes())
        data[96:100] = struct.pack("<f", math.inf)
        self.path.write_bytes(data)
        with self.assertRaises(ValueError):
            read_stl(self.path)

    def test_nonfinite_normals(self):
        self.write(bad_normal=True)
        with self.assertRaises(ValueError):
            read_stl(self.path)

    def test_closed_shape_not_automatically_accepted(self):
        self.write()
        result = audit_mesh(self.path, "sphere", .01, .01, .001)
        self.assertEqual(result["nonmanifoldEdges"], 0)
        self.assertFalse(result["pass"])

    def test_nan_normals_remain_failed_in_diagnostic_mode(self):
        self.write(bad_normal=True)
        result = audit_mesh(self.path, "sphere", .01, .01, .001)
        self.assertEqual(result["nonfiniteNormals"], 4)
        self.assertFalse(result["pass"])

    def test_duplicate_face_remains_failed(self):
        self.write()
        tris, _ = read_stl(self.path)
        self.write(np.concatenate([tris, tris[:1]]))
        result = audit_mesh(self.path, "sphere", .01, .01, .001)
        self.assertEqual(result["duplicateFaces"], 1)
        self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
