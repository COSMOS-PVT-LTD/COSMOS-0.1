"""Test conditioning refusal paths and geometry preservation independently."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from export_adapter import ExportRejected, condition

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_benchmarks import audit_mesh, read_stl

HERE = Path(__file__).resolve().parent


class ExportAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cosmos-p02-conditioning-")
        self.target = Path(self.temp.name) / "result.stl"
        self.source = HERE.parent / "artifacts/source-difference-0.001000m.stl"

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_zero_area_only_preserves_every_retained_vertex(self):
        original, _ = read_stl(self.source, False)
        profile = condition(self.source, self.target)
        output, normals = read_stl(self.target)
        keep = np.linalg.norm(np.cross(original[:, 1]-original[:, 0], original[:, 2]-original[:, 0]), axis=1) != 0
        np.testing.assert_array_equal(output, original[keep])
        self.assertEqual(profile["exactZeroAreaFacesRemoved"], 22)
        self.assertEqual(profile["maximumVertexDisplacementM"], 0)
        self.assertTrue(np.isfinite(normals).all())
        self.assertTrue(audit_mesh(self.target, "difference", .01, .01, .001)["pass"])

    def test_cannot_overwrite(self):
        self.target.write_bytes(b"existing")
        with self.assertRaises(ExportRejected) as error:
            condition(self.source, self.target)
        self.assertEqual(error.exception.code, "ARTIFACT_EXISTS")
        self.assertEqual(self.target.read_bytes(), b"existing")

    def test_excess_degeneracy_is_rejected_without_output(self):
        import struct
        bad = Path(self.temp.name) / "collapsed.stl"
        bad.write_bytes(b"UNITS= m".ljust(80, b" ") + struct.pack("<I", 1) + bytes(50))
        with self.assertRaises(ExportRejected) as error:
            condition(bad, self.target)
        self.assertEqual(error.exception.code, "EXCESS_DEGENERACY")
        self.assertFalse(self.target.exists())

    def test_missing_source_has_structured_diagnostic(self):
        with self.assertRaises(ExportRejected) as error:
            condition(Path(self.temp.name) / "missing.stl", self.target)
        self.assertEqual(error.exception.code, "STL_INPUT")
        self.assertFalse(self.target.exists())

    def test_nonfinite_nonzero_face_is_not_silently_repaired(self):
        bad = Path(self.temp.name) / "bad.stl"
        content = bytearray(self.source.read_bytes())
        # First nonzero-area face receives a nonfinite normal.
        original, _ = read_stl(self.source, False)
        index = int(np.flatnonzero(np.linalg.norm(np.cross(original[:, 1]-original[:, 0], original[:, 2]-original[:, 0]), axis=1) != 0)[0])
        import struct
        content[84+index*50:88+index*50] = struct.pack("<f", float("nan"))
        bad.write_bytes(content)
        with self.assertRaises(ExportRejected) as error:
            condition(bad, self.target)
        self.assertEqual(error.exception.code, "NONFINITE_NORMAL")
        self.assertFalse(self.target.exists())

    def test_completed_candidate_keeps_failed_coarse_attempt(self):
        data = json.loads((HERE / "accepted_benchmarks.json").read_text())
        self.assertEqual(len(data["cases"]), 21)
        self.assertTrue(data["allPass"])
        refined = [case for case in data["cases"] if case["refined"]]
        self.assertEqual(len(refined), 1)
        self.assertFalse(refined[0]["attempts"][0]["qa"]["pass"])
        self.assertTrue(refined[0]["attempts"][1]["qa"]["pass"])
        self.assertEqual(refined[0]["request"]["voxelM"], .001)
        self.assertEqual(refined[0]["attempts"][1]["actualVoxelM"], .0005)
        self.assertFalse(data["tolerancesChanged"])


if __name__ == "__main__":
    unittest.main()
