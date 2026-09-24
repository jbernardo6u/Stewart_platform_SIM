"""
Tests unitaires : InverseKinematics.from_attachment_points (géométrie identifiée)
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.kinematics import InverseKinematics


class TestFromAttachmentPoints(unittest.TestCase):

    def setUp(self):
        self.parametric = InverseKinematics(0.2, 0.2, 12, 12)
        P, B = self.parametric.calculate_attachment_points()
        self.custom = InverseKinematics.from_attachment_points(B, P, self.parametric.home_pos)

    def test_same_points_give_same_lengths(self):
        for t, r in [([0, 0, 0], [0, 0, 0]), ([0.01, -0.02, 0.03], [3, -4, 8])]:
            np.testing.assert_allclose(self.custom.solve(t, r), self.parametric.solve(t, r), atol=1e-12)

    def test_custom_geometry_is_used(self):
        P, B = self.parametric.calculate_attachment_points()
        P_shifted = P + np.array([[0.001], [0.0], [0.0]])
        ik = InverseKinematics.from_attachment_points(B, P_shifted, self.parametric.home_pos)
        np.testing.assert_allclose(ik.solve([0, 0, 0], [0, 0, 0]),
                                   self.parametric.solve([0.001, 0, 0], [0, 0, 0]), atol=1e-12)

    def test_shape_validation(self):
        with self.assertRaises(ValueError):
            InverseKinematics.from_attachment_points(np.zeros((6, 3)), np.zeros((3, 6)), [0, 0, 0.25])

    def test_parametric_behaviour_unchanged(self):
        """Le constructeur historique n'est pas affecté."""
        P, B = self.parametric.calculate_attachment_points()
        self.assertAlmostEqual(np.linalg.norm(P[:2, 0]), 0.2)
        self.assertAlmostEqual(self.parametric.home_pos[2], 0.257547)


if __name__ == '__main__':
    unittest.main()
