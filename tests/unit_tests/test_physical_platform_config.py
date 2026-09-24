"""
Tests unitaires de PhysicalStewartPlatform (sans matériel : MotorController est un stub).
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.hardware.physical_platform import PhysicalStewartPlatform

MOTOR_CONFIG = {
    'motor_pins': list(range(6)),
    'encoder_pins': list(range(6, 12)),
    'specs': {'gear_ratio': 371, 'rpm_max': 126},
}


class TestPhysicalPlatformDesignVariables(unittest.TestCase):

    def test_design_variables_follow_platform_convention(self):
        """design_variable = [r_P, r_B, γ_P, γ_B], comme StewartPlatform (anomalie A2)."""
        r_P, r_B, gamma_P, gamma_B = 0.15, 0.25, 10, 20
        platform = PhysicalStewartPlatform([r_P, r_B, gamma_P, gamma_B], MOTOR_CONFIG)
        platform.initialize_platform()

        self.assertAlmostEqual(platform.clf.rp, r_P)
        self.assertAlmostEqual(platform.clf.rb, r_B)
        self.assertAlmostEqual(platform.clf.gamma_P, np.deg2rad(gamma_P))
        self.assertAlmostEqual(platform.clf.gamma_B, np.deg2rad(gamma_B))


if __name__ == '__main__':
    unittest.main()
