"""
Validation : suivi de pose de la simulation PyBullet en boucle fermée (EXP-004)
=============================================================================

Pour chaque consigne (autour de la hauteur de travail), la pose mesurée par
StewartPlatform.get_current_pose() doit coïncider avec la consigne.

- Géométrie identifiée (StewartPlatform.from_urdf), avec gravité : < 0,5 mm et < 0,1°
  (critère de sortie de la Phase 4) ;
- même chose sans gravité : < 0,05 mm, ce qui vérifie que la simulation et le modèle
  cinématique décrivent exactement le même mécanisme ;
- modèle paramétrique historique (r = 0,2 m, γ = 12°) : < 1 mm, écart dû à la géométrie (EXP-001).
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
POSES = [
    ("x+10mm", [0.01, 0, 0], [0, 0, 0]),
    ("y+10mm", [0, 0.01, 0], [0, 0, 0]),
    ("z+10mm", [0, 0, 0.01], [0, 0, 0]),
    ("roll+5", [0, 0, 0], [5, 0, 0]),
    ("pitch+5", [0, 0, 0], [0, 5, 0]),
    ("yaw+5", [0, 0, 0], [0, 0, 5]),
    ("combined", [0.02, -0.015, 0.02], [4, -3, 8]),
]


class _TrackingCase(unittest.TestCase):
    """Base : une plateforme simulée par classe de test, amenée à la hauteur de travail."""
    TOL_MM = TOL_MM
    TOL_DEG = TOL_DEG
    GRAVITY = True

    @classmethod
    def make_platform(cls):
        raise NotImplementedError

    @classmethod
    def setUpClass(cls):
        import pybullet as p
        from src.core.platform import DEFAULT_WORKING_HEIGHT
        cls.height = DEFAULT_WORKING_HEIGHT
        cls.platform = cls.make_platform()
        assert cls.platform.setup_environment(use_gui=False)
        if not cls.GRAVITY:
            p.setGravity(0, 0, 0)
        assert cls.platform.initialize_platform(verbose=False)
        cls.platform.move_to_working_position(duration=1.0, realtime=False, settle_time=1.0)

    @classmethod
    def tearDownClass(cls):
        cls.platform.disconnect()

    def assert_tracks(self, translation, rotation):
        target_t = np.array(translation, float) + [0, 0, self.height]
        self.platform.move_to_pose(target_t, rotation, duration=1.0, realtime=False, settle_time=1.0)
        pos, rpy = self.platform.get_current_pose()
        err_mm = np.abs(np.array(pos) - target_t).max() * 1000
        err_deg = np.abs(np.array(rpy) - np.array(rotation, float)).max()
        self.assertLess(err_mm, self.TOL_MM, f"erreur de position {err_mm:.3f} mm")
        self.assertLess(err_deg, self.TOL_DEG, f"erreur d'orientation {err_deg:.4f}°")

    def test_working_position(self):
        self.assert_tracks([0, 0, 0], [0, 0, 0])

    def test_elementary_and_combined_moves(self):
        for label, t, rot in POSES:
            with self.subTest(pose=label):
                self.assert_tracks(t, rot)
                self.assert_tracks([0, 0, 0], [0, 0, 0])   # retour à la position de travail


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestIdentifiedGeometryTracking(_TrackingCase):
    @classmethod
    def make_platform(cls):
        from src.core.platform import StewartPlatform
        return StewartPlatform.from_urdf(URDF_PATH)


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestIdentifiedGeometryTrackingNoGravity(TestIdentifiedGeometryTracking):
    GRAVITY = False
    TOL_MM = 0.05
    TOL_DEG = 0.005


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestParametricModelTracking(_TrackingCase):
    TOL_MM = 1.0

    @classmethod
    def make_platform(cls):
        from src.core.platform import StewartPlatform, DEFAULT_ACTUATOR_INDICES, DEFAULT_JOINT_INDICES
        return StewartPlatform(URDF_PATH, DEFAULT_JOINT_INDICES, DEFAULT_ACTUATOR_INDICES, [0.2, 0.2, 12, 12])


del _TrackingCase  # classe de base abstraite : ne pas la collecter


if __name__ == '__main__':
    unittest.main()
