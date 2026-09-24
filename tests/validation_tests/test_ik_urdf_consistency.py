"""
Validation : cohérence entre InverseKinematics et le modèle URDF (EXP-002)
=========================================================================

Pour chaque jambe, la direction prédite par l'IK en position neutre
(home + P_i − B_i) doit coïncider avec l'axe du joint prismatique
correspondant du URDF. Vérifie à la fois la géométrie (r, γ, home) et
l'ordre de DEFAULT_ACTUATOR_INDICES.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import pybullet as p
except ImportError:  # pragma: no cover
    p = None

from src.core.kinematics import InverseKinematics

URDF_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'simulation', 'urdf', 'Stewart.urdf')
TOLERANCE_DEG = 1.0


def slider_axes_world(actuator_indices):
    """Axes (monde) des joints prismatiques, dans l'ordre donné, configuration zéro."""
    client = p.connect(p.DIRECT)
    try:
        robot = p.loadURDF(URDF_PATH, useFixedBase=1, physicsClientId=client)
        axes = []
        for joint in actuator_indices:
            info = p.getJointInfo(robot, joint, physicsClientId=client)
            assert info[2] == p.JOINT_PRISMATIC, f"joint {joint} n'est pas prismatique"
            state = p.getLinkState(robot, joint, computeForwardKinematics=1, physicsClientId=client)
            rot = np.array(p.getMatrixFromQuaternion(state[5])).reshape(3, 3)
            axes.append(rot @ np.array(info[13]))
        return np.array(axes)
    finally:
        p.disconnect(client)


def leg_axis_errors_deg(actuator_indices):
    ik = InverseKinematics(0.2, 0.2, 12, 12)
    ik.solve([0, 0, 0], [0, 0, 0])
    P, B = ik.get_attachment_points()
    legs = ik.home_pos[:, None] + P - B
    legs = (legs / np.linalg.norm(legs, axis=0)).T
    axes = slider_axes_world(actuator_indices)
    cosines = np.clip(np.abs(np.sum(legs * axes, axis=1)), 0.0, 1.0)
    return np.degrees(np.arccos(cosines))


@unittest.skipIf(p is None, "pybullet non installé")
class TestIKMatchesURDF(unittest.TestCase):

    def test_default_actuator_order_matches_urdf_legs(self):
        from src.core.platform import DEFAULT_ACTUATOR_INDICES
        errors = leg_axis_errors_deg(DEFAULT_ACTUATOR_INDICES)
        self.assertTrue(np.all(errors < TOLERANCE_DEG), f"écarts angulaires (°) : {np.round(errors, 2)}")

    def test_historical_actuator_order_is_rejected(self):
        """L'ordre [9, 2, 31, 45, 38, 24] (calé sur l'ancienne IK) est incompatible avec l'IK actuelle."""
        errors = leg_axis_errors_deg([9, 2, 31, 45, 38, 24])
        self.assertTrue(np.all(errors > 10.0), f"écarts angulaires (°) : {np.round(errors, 2)}")


if __name__ == '__main__':
    unittest.main()
