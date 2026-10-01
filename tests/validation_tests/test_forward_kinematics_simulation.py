"""
Validation : cinématique directe sur les positions de joints mesurées dans PyBullet (EXP-008)
===========================================================================================

Comme le banc avec ses codeurs : on lit la position des 6 joints prismatiques, on en
déduit la pose par la FK (géométrie identifiée), et on la compare à la pose mesurée
du corps de la plateforme.

- sans gravité : < 0,01 mm et < 0,005°, le modèle et la simulation décrivent le même mécanisme ;
- avec gravité : < 0,6 mm et < 0,05°. L'écart (0,15 à 0,5 mm) vient de la souplesse des
  contraintes de fermeture sous charge, que les codeurs ne voient pas.
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
POSES = [
    ("travail", [0, 0, 0], [0, 0, 0]),
    ("z+30mm", [0, 0, 0.03], [0, 0, 0]),
    ("pitch-8", [0, 0, 0], [0, -8, 0]),
    ("combinee", [0.03, -0.02, 0.02], [5, -4, 12]),
]


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestFKOnJointStatesNoGravity(unittest.TestCase):
    GRAVITY = False
    TOL_MM = 0.01
    TOL_DEG = 0.005

    @classmethod
    def setUpClass(cls):
        import pybullet as p
        from src.core.platform import DEFAULT_WORKING_HEIGHT, StewartPlatform
        cls.p = p
        cls.height = DEFAULT_WORKING_HEIGHT
        cls.platform = StewartPlatform.from_urdf(URDF_PATH)
        assert cls.platform.setup_environment(use_gui=False)
        if not cls.GRAVITY:
            p.setGravity(0, 0, 0)
        assert cls.platform.initialize_platform(verbose=False)
        cls.platform.move_to_working_position(duration=1.0, realtime=False, settle_time=1.0)

    @classmethod
    def tearDownClass(cls):
        cls.platform.disconnect()

    def test_fk_matches_measured_pose(self):
        from src.core.forward_kinematics import pose_from_actuator_positions
        for label, t, rot in POSES:
            with self.subTest(pose=label):
                self.platform.move_to_pose(np.array(t, float) + [0, 0, self.height], rot,
                                           duration=1.0, realtime=False, settle_time=1.0)
                q = [self.p.getJointState(self.platform.robot_id, j)[0] for j in self.platform.actuator_indices]
                pos, rpy = self.platform.get_current_pose()
                fk = pose_from_actuator_positions(self.platform.kinematics, q, self.height)
                self.assertTrue(fk.converged)
                err_mm = np.abs(fk.translation + [0, 0, self.height] - pos).max() * 1000
                err_deg = np.abs(fk.rotation_deg - rpy).max()
                self.assertLess(err_mm, self.TOL_MM, f"{err_mm:.4f} mm")
                self.assertLess(err_deg, self.TOL_DEG, f"{err_deg:.4f}°")


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestFKOnJointStatesWithGravity(TestFKOnJointStatesNoGravity):
    GRAVITY = True
    TOL_MM = 0.6
    TOL_DEG = 0.05


if __name__ == '__main__':
    unittest.main()
