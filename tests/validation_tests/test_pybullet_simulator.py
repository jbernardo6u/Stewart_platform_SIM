"""
Validation : PyBulletSimulator (simulateur des GUI) en boucle fermée
====================================================================

PyBulletSimulator délègue le mécanisme à StewartPlatform.from_urdf (EXP-004). Les poses
de update_platform_pose / get_platform_state sont en mm et degrés, relatives à la
position de travail. Mêmes critères que test_closed_loop_simulation : < 0,5 mm et < 0,1°.
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
TOL_MM = 0.5
TOL_DEG = 0.1
SETTLE_STEPS = 480  # 2 s à 240 Hz
POSES = [
    ("x+10mm", [10, 0, 0], [0, 0, 0]),
    ("z-20mm", [0, 0, -20], [0, 0, 0]),
    ("roll+5", [0, 0, 0], [5, 0, 0]),
    ("yaw-8", [0, 0, 0], [0, 0, -8]),
    ("combined", [20, -15, 20], [4, -3, 8]),
]


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestPyBulletSimulator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from src.simulation.pybullet_sim import PyBulletSimulator
        cls.sim = PyBulletSimulator(URDF_PATH, gui=False)
        assert cls.sim.connect()

    @classmethod
    def tearDownClass(cls):
        cls.sim.disconnect()

    def command(self, position, rotation):
        self.sim.update_platform_pose({'position': position, 'rotation': rotation})
        self.sim.step_simulation(steps=SETTLE_STEPS)
        return self.sim.get_platform_state()

    def assert_state_matches(self, state, position, rotation):
        err_mm = np.abs(np.array(state['position']) - position).max()
        err_deg = np.abs(np.array(state['rotation']) - rotation).max()
        self.assertLess(err_mm, TOL_MM, f"erreur de position {err_mm:.3f} mm")
        self.assertLess(err_deg, TOL_DEG, f"erreur d'orientation {err_deg:.4f}°")

    def test_connect_reaches_working_position(self):
        self.sim.reset_simulation()
        state = self.sim.get_platform_state()
        self.assert_state_matches(state, [0, 0, 0], [0, 0, 0])
        # Vérins à mi-course environ, et non en butée basse
        self.assertTrue(all(q > 0.05 for q in state['actuator_positions']))

    def test_pose_tracking(self):
        for label, position, rotation in POSES:
            with self.subTest(pose=label):
                state = self.command(position, rotation)
                self.assertTrue(state['reachable'])
                self.assert_state_matches(state, position, rotation)

    def test_unreachable_pose_is_flagged_and_bounded(self):
        state = self.command([0, 0, 200], [0, 0, 0])   # au-delà de la course des vérins
        self.assertFalse(state['reachable'])
        limits = self.sim.platform.actuator_limits()
        q = np.array(state['actuator_positions'])
        self.assertTrue(np.all(q <= limits[:, 1] + 1e-3))
        self.command([0, 0, 0], [0, 0, 0])

    def test_state_keys_and_units(self):
        state = self.command([0, 0, 0], [0, 0, 0])
        for key in ('position', 'rotation', 'linear_velocity', 'angular_velocity',
                    'actuator_positions', 'reachable'):
            self.assertIn(key, state)
        self.assertEqual(len(state['actuator_positions']), 6)
        self.assertLess(np.linalg.norm(state['linear_velocity']), 1e-3)  # immobile

    def test_reset_returns_to_working_position(self):
        self.command([20, 0, 10], [0, 5, 0])
        self.sim.reset_simulation()
        self.assert_state_matches(self.sim.get_platform_state(), [0, 0, 0], [0, 0, 0])

    def test_external_force_moves_platform(self):
        self.command([0, 0, 0], [0, 0, 0])
        before = np.array(self.sim.get_platform_state()['position'])
        link = self.sim.platform.platform_link
        centre = pybullet.getLinkState(self.sim.robot_id, link)[0]
        for _ in range(60):
            self.sim.apply_external_force([0, 0, -2000.0], centre)
            self.sim.step_simulation()
        after = np.array(self.sim.get_platform_state()['position'])
        self.assertLess(after[2], before[2] - 0.01)   # la plateforme s'enfonce
        self.sim.reset_simulation()


if __name__ == '__main__':
    unittest.main()
