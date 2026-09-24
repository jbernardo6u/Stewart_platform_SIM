"""
Validation : géométrie identifiée depuis le URDF (EXP-001)
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import pybullet  # noqa: F401
except ImportError:  # pragma: no cover
    pybullet = None

URDF_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'simulation', 'urdf', 'Stewart.urdf')


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestURDFGeometry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from src.core.platform import DEFAULT_ACTUATOR_INDICES, DEFAULT_PLATFORM_LINK, DEFAULT_PLATFORM_CENTRE_IN_LINK
        from src.simulation.urdf_geometry import identify_urdf_geometry
        cls.geo = identify_urdf_geometry(URDF_PATH, DEFAULT_ACTUATOR_INDICES, DEFAULT_PLATFORM_LINK)
        cls.centre_constant = np.array(DEFAULT_PLATFORM_CENTRE_IN_LINK)

    def test_universal_joints_are_ideal(self):
        """Les deux axes de chaque cardan se coupent (mécanisme 6-UPU exact)."""
        self.assertLess(self.geo['max_axis_gap'], 1e-5)

    def test_parametric_values(self):
        B, P = self.geo['base_points'], self.geo['platform_points']
        np.testing.assert_allclose(np.linalg.norm(B[:2], axis=0), 0.19958, atol=2e-5)
        np.testing.assert_allclose(np.linalg.norm(P[:2], axis=0), 0.19958, atol=2e-5)
        base_angles = np.degrees(np.arctan2(B[1], B[0])) % 360
        # jambes 1-2 autour de 210°, écartées de ±γ_B = ±12,295°
        self.assertAlmostEqual((base_angles[0] - base_angles[1]) / 2, 12.295, places=2)
        self.assertAlmostEqual(self.geo['home_position'][2], 0.253489, places=5)

    def test_platform_centre_constant_matches_urdf(self):
        np.testing.assert_allclose(self.geo['platform_centre_in_link'], self.centre_constant, atol=1e-6)

    def test_stroke(self):
        for lo, hi in self.geo['stroke']:
            self.assertEqual((lo, hi), (0.0, 0.19))


if __name__ == '__main__':
    unittest.main()
