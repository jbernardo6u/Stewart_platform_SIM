"""
Validation : logique du tableau de bord en simulation (sans interface graphique)
===============================================================================

DashboardController relie consigne, faisabilité et simulation PyBullet (mode DIRECT).
Critères : pose atteinte < 0,5 mm / 0,1° (EXP-004), scénarios exécutés avec un écart
consigne/mesure maximal < 1 mm / 0,25° (retard dynamique compris), saturation signalée.
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


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestDashboardController(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from src.gui.dashboard_controller import DashboardController
        cls.ctrl = DashboardController()
        cls.ctrl.connect(offscreen=False)

    @classmethod
    def tearDownClass(cls):
        cls.ctrl.disconnect()

    def settle(self, seconds=2.0):
        for _ in range(int(seconds * 60)):
            self.ctrl.tick(1 / 60)

    def test_evaluate_without_simulation_fields(self):
        ev = self.ctrl.evaluate([0, 0, 0, 0, 0, 0])
        self.assertTrue(ev['reachable'])
        self.assertEqual(len(ev['usage']), 6)
        self.assertFalse(self.ctrl.evaluate([0, 0, 200, 0, 0, 0])['reachable'])

    def test_command_is_clipped_to_limits(self):
        self.ctrl.set_command([1000, 0, 0, 0, 0, 0])
        self.assertEqual(self.ctrl.command[0], self.ctrl.limits['x'][1])
        self.ctrl.reset()

    def test_pose_tracking(self):
        self.ctrl.reset()
        target = [15, -10, 20, 3, -2, 6]
        self.ctrl.set_command(target)
        self.settle()
        err = np.abs(self.ctrl.measured - target)
        self.assertLess(err[:3].max(), 0.5)
        self.assertLess(err[3:].max(), 0.1)
        self.assertTrue(self.ctrl.history)

    def test_scenarios_run_and_report(self):
        from src.core import scenarios
        for name in scenarios.scenario_names():
            with self.subTest(scenario=name):
                self.ctrl.reset()
                report = self.ctrl.start_scenario(name)
                self.assertTrue(report['feasible'])
                while self.ctrl.run is not None:
                    self.ctrl.tick(1 / 60)
                result = self.ctrl.last_run_report
                self.assertEqual(result['name'], name)
                self.assertTrue(result['simulated'])
                self.assertLess(result['max_mm'], 1.0)
                self.assertLess(result['max_deg'], 0.25)

    def test_emergency_stop_freezes_on_measured_pose(self):
        self.ctrl.reset()
        self.ctrl.start_scenario('square')
        for _ in range(90):
            self.ctrl.tick(1 / 60)
        self.ctrl.emergency_stop()
        self.assertIsNone(self.ctrl.run)
        np.testing.assert_allclose(self.ctrl.command, self.ctrl.measured)
        self.ctrl.reset()


@unittest.skipIf(pybullet is None, "pybullet non installé")
class TestOffscreenRendering(unittest.TestCase):
    def test_render_image(self):
        from src.simulation.pybullet_sim import PyBulletSimulator
        sim = PyBulletSimulator(os.path.join(os.path.dirname(__file__), '..', '..', 'simulation', 'urdf',
                                             'Stewart.urdf'), gui=False, offscreen=False)
        self.assertTrue(sim.connect())
        try:
            sim.style_scene()
            sim.set_camera_view('front')
            sim.orbit_camera(d_yaw=30, d_pitch=-10, zoom=0.8)
            img = sim.render_image(160, 100)       # rendu logiciel : petite image
            self.assertEqual(img.shape, (100, 160, 3))
            self.assertGreater(img.std(), 5)        # l'image n'est pas uniforme
        finally:
            sim.disconnect()


if __name__ == '__main__':
    unittest.main()
