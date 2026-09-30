"""
Tests unitaires : configuration, faisabilité (course des vérins) et scénarios de mouvement.
Aucun appel à PyBullet : modèle paramétrique de la configuration (r = 0,2 m, γ = 12°).
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.config import load_config, project_path  # noqa: E402
from src.core.feasibility import (actuator_positions, check_trajectory, leg_tilt_deg,  # noqa: E402
                                  stroke_usage)
from src.core.kinematics import InverseKinematics  # noqa: E402
from src.core import scenarios  # noqa: E402

CFG = load_config()
H = CFG['platform']['working_height']
STROKE = tuple(CFG['platform']['actuator_stroke'])


def parametric_ik():
    p = CFG['platform']
    return InverseKinematics(p['radius_base'], p['radius_platform'], p['gamma_base'], p['gamma_platform'])


class TestConfig(unittest.TestCase):
    def test_required_keys(self):
        self.assertEqual(STROKE, (0.0, 0.19))
        self.assertAlmostEqual(H, 0.09)
        limits = CFG['gui']['dashboard']['limits']
        for axis in ('x', 'y', 'z', 'roll', 'pitch', 'yaw'):
            lo, hi = limits[axis]
            self.assertLess(lo, 0)
            self.assertGreater(hi, 0)

    def test_urdf_path_resolves(self):
        self.assertTrue(os.path.exists(project_path(CFG['simulation']['urdf_path'])))


class TestFeasibility(unittest.TestCase):
    def setUp(self):
        self.ik = parametric_ik()

    def test_working_position_is_mid_stroke_and_symmetric(self):
        q = actuator_positions(self.ik, [0, 0, 0], [0, 0, 0], H)
        self.assertEqual(q.shape, (6,))
        np.testing.assert_allclose(q, q[0], atol=1e-9)
        usage = stroke_usage(q, STROKE)
        self.assertTrue(np.all((usage > 0.3) & (usage < 0.6)))

    def test_neutral_pose_is_bottom_stop(self):
        q = actuator_positions(self.ik, [0, 0, -H], [0, 0, 0], H)
        np.testing.assert_allclose(q, 0.0, atol=1e-12)

    def test_trajectory_shape_and_flags(self):
        t = np.zeros((3, 3))
        r = np.array([[0, 0, 0], [0, 0, 20], [0, 0, 90]], dtype=float)
        report = check_trajectory(self.ik, t, r, H, STROKE)
        self.assertEqual(report['positions'].shape, (3, 6))
        self.assertFalse(report['feasible'])
        np.testing.assert_array_equal(report['saturated'], [False, False, True])

    def test_unreachable_pose_detected(self):
        report = check_trajectory(self.ik, [[0, 0, 0.2]], [[0, 0, 0]], H, STROKE)
        self.assertFalse(report['feasible'])
        self.assertLess(report['margin'], 0)
        self.assertEqual(report['saturated_ratio'], 1.0)

    def test_full_yaw_turn_is_infeasible(self):
        # Démo « spirale » historique : lacet de 0 à 360° (60 % de points saturés)
        yaw = np.linspace(0, 360, 30)
        report = check_trajectory(self.ik, np.zeros((30, 3)), np.column_stack([0 * yaw, 0 * yaw, yaw]), H, STROKE)
        self.assertFalse(report['feasible'])

    def test_leg_tilt_at_working_position(self):
        tilt = leg_tilt_deg(self.ik, [0, 0, 0], [0, 0, 0], H)
        self.assertEqual(tilt.shape, (6,))
        self.assertTrue(np.all((tilt > 10) & (tilt < 30)))
        # un déplacement latéral incline davantage certaines jambes
        self.assertGreater(leg_tilt_deg(self.ik, [0.1, 0, 0], [0, 0, 0], H).max(), tilt.max())


class TestScenarios(unittest.TestCase):
    def test_all_scenarios_are_feasible_and_well_formed(self):
        ik = parametric_ik()
        for name in scenarios.scenario_names():
            with self.subTest(scenario=name):
                t, trans, rot = scenarios.get_scenario(name)
                self.assertEqual(trans.shape, (len(t), 3))
                self.assertEqual(rot.shape, (len(t), 3))
                self.assertTrue(np.all(np.diff(t) > 0))
                np.testing.assert_allclose(trans[0], 0, atol=1e-12)   # départ et arrivée à la
                np.testing.assert_allclose(trans[-1], 0, atol=1e-9)   # position de travail
                np.testing.assert_allclose(rot[-1], 0, atol=1e-9)
                self.assertTrue(check_trajectory(ik, trans, rot, H, STROKE)['feasible'])

    def test_waypoints_are_reached_smoothly(self):
        t, trans, rot = scenarios.waypoints_trajectory([(0, [0] * 6), (1.0, [10, 0, 0, 0, 0, 5])])
        self.assertAlmostEqual(t[-1], 1.0)
        np.testing.assert_allclose(trans[-1], [0.01, 0, 0])
        np.testing.assert_allclose(rot[-1], [0, 0, 5])
        v = np.diff(trans[:, 0])
        self.assertLess(v[0], v[len(v) // 2] / 10)   # démarrage en douceur (loi d'ordre 5)

    def test_sample_interpolates_and_clamps(self):
        traj = scenarios.waypoints_trajectory([(0, [0] * 6), (1.0, [10, 0, 0, 0, 0, 0])])
        mid, _ = scenarios.sample(traj, 0.5)
        self.assertAlmostEqual(mid[0], 0.005, places=4)
        end, _ = scenarios.sample(traj, 5.0)
        self.assertAlmostEqual(end[0], 0.01)


if __name__ == '__main__':
    unittest.main()
