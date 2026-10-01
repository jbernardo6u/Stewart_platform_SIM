"""
Tests unitaires : statique des vérins (src/core/statics.py, EXP-010)
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.forward_kinematics import jacobian, rotation_matrix
from src.core.kinematics import InverseKinematics
from src.core.statics import (STANDARD_GRAVITY, actuator_forces, gravity_actuator_forces,
                              gravity_in_base_lying, gravity_wrench)


def bench_ik():
    ik = InverseKinematics(0.075, 0.04, 11.3, 17.3)
    ik.home_pos = np.array([0.0, 0.0, 0.185])
    return ik


class TestStatics(unittest.TestCase):

    def setUp(self):
        self.ik = bench_ik()

    def test_equilibrium(self):
        rng = np.random.default_rng(0)
        for _ in range(20):
            t = rng.uniform(-0.02, 0.02, 3) + [0, 0, 0.02]
            r = np.radians(rng.uniform(-10, 10, 3))
            w = rng.normal(0, 5, 6)
            f = actuator_forces(self.ik, t, r, w)
            np.testing.assert_allclose(jacobian(self.ik, t, r).T @ f + w, 0, atol=1e-9)

    def test_virtual_work(self):
        """La puissance des vérins compense celle du torseur extérieur, pour toute vitesse."""
        t, r = [0.01, 0, 0.03], np.radians([3, -2, 5])
        w = np.array([1.0, -2.0, -9.81, 0.1, 0.05, -0.2])
        f = actuator_forces(self.ik, t, r, w)
        twist = np.array([0.3, -0.1, 0.2, 0.5, 0.4, -0.7])
        self.assertAlmostEqual(f @ (jacobian(self.ik, t, r) @ twist) + w @ twist, 0.0, places=9)

    def test_upright_centred_load_is_shared_equally(self):
        """Debout, charge centrée : f_i = m·g / (6·cos θ), θ = inclinaison des jambes."""
        f = gravity_actuator_forces(self.ik, [0, 0, 0], [0, 0, 0], 1.0, [0, 0, 0], [0, 0, -STANDARD_GRAVITY])
        P, B = self.ik.calculate_attachment_points()
        legs = self.ik.home_pos[:, None] + P - B
        cos_tilt = legs[2] / np.linalg.norm(legs, axis=0)
        np.testing.assert_allclose(f, STANDARD_GRAVITY / (6 * cos_tilt), rtol=1e-12)
        self.assertTrue(np.all(f > 0))   # les vérins poussent

    def test_lying_is_much_worse_than_upright(self):
        """Banc couché : la gravité est latérale, donc reprise par des jambes presque parallèles."""
        up = np.abs(gravity_actuator_forces(self.ik, [0, 0, 0], [0, 0, 0], 1.0, [0, 0, 0],
                                            [0, 0, -STANDARD_GRAVITY])).max()
        lying = max(np.abs(gravity_actuator_forces(self.ik, [0, 0, 0], [0, 0, 0], 1.0, [0, 0, 0],
                                                   gravity_in_base_lying(a))).max() for a in range(0, 360, 5))
        self.assertGreater(lying / up, 8)

    def test_lying_gravity_is_horizontal_in_base(self):
        for a in (0, 37, 90, 200):
            g = gravity_in_base_lying(a)
            self.assertAlmostEqual(g[2], 0.0)
            self.assertAlmostEqual(np.linalg.norm(g), STANDARD_GRAVITY)
        np.testing.assert_allclose(gravity_in_base_lying(0), [-STANDARD_GRAVITY, 0, 0])

    def test_gravity_wrench_moment(self):
        R = rotation_matrix(np.radians([0, 0, 90]))
        w = gravity_wrench(2.0, [0.05, 0, 0], R, [0, 0, -10.0])
        np.testing.assert_allclose(w[:3], [0, 0, -20.0])
        np.testing.assert_allclose(w[3:], np.cross(R @ [0.05, 0, 0], [0, 0, -20.0]), atol=1e-12)


if __name__ == '__main__':
    unittest.main()
