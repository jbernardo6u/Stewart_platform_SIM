"""
Tests unitaires : cinématique directe, jacobien et singularités (Phase 2, EXP-008)
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.config import load_config
from src.core.feasibility import actuator_positions
from src.core.forward_kinematics import (_exp_so3, _legs, forward_kinematics, jacobian,
                                         leg_lengths, pose_from_actuator_positions,
                                         rotation_matrix, rotation_to_rpy,
                                         singularity_measures, solver_settings)
from src.core.kinematics import InverseKinematics

WORKING_HEIGHT = 0.09
# Espace exploré par le tableau de bord, autour de la hauteur de travail (m, deg)
LOW = np.array([-0.1, -0.1, -0.085, -25, -25, -60])
HIGH = np.array([0.1, 0.1, 0.105, 25, 25, 60])


def random_poses(n, seed=0):
    rng = np.random.default_rng(seed)
    for pose in rng.uniform(LOW, HIGH, size=(n, 6)):
        yield pose[:3] + [0, 0, WORKING_HEIGHT], np.radians(pose[3:])


def asymmetric_ik():
    """Géométrie non symétrique (attaches perturbées de ±2 mm), comme la géométrie identifiée."""
    ref = InverseKinematics(0.2, 0.2, 12, 12)
    P, B = ref.calculate_attachment_points()
    rng = np.random.default_rng(42)
    return InverseKinematics.from_attachment_points(B + rng.uniform(-2e-3, 2e-3, B.shape),
                                                    P + rng.uniform(-2e-3, 2e-3, P.shape),
                                                    [-0.0012, 0.0004, 0.2535])


class TestRotations(unittest.TestCase):

    def test_matches_solve_convention(self):
        ik = InverseKinematics(0.2, 0.2, 12, 12)
        rpy = [10, -20, 35]
        np.testing.assert_allclose(rotation_matrix(np.radians(rpy)), ik.calculate_rotation_matrix(rpy),
                                   atol=1e-15)

    def test_rpy_round_trip(self):
        for rpy in ([0, 0, 0], [0.3, -0.5, 1.2], [-1.0, 1.4, -3.0]):
            np.testing.assert_allclose(rotation_to_rpy(rotation_matrix(rpy)), rpy, atol=1e-12)


class TestForwardKinematics(unittest.TestCase):

    def setUp(self):
        self.geometries = {'paramétrique': InverseKinematics(0.2, 0.2, 12, 12),
                           'asymétrique': asymmetric_ik()}

    def test_leg_lengths_match_solve(self):
        for name, ik in self.geometries.items():
            with self.subTest(geometry=name):
                t, r = [0.01, -0.02, 0.1], np.radians([3, -4, 8])
                np.testing.assert_allclose(leg_lengths(ik, t, r), ik.solve(t, np.degrees(r)), atol=1e-15)

    def test_round_trip_below_one_micrometre(self):
        """Critère de sortie de la Phase 2 : aller-retour IK→FK < 1 µm."""
        for name, ik in self.geometries.items():
            for t, r in random_poses(200):
                res = forward_kinematics(ik, ik.solve(t, np.degrees(r)), [0, 0, WORKING_HEIGHT])
                with self.subTest(geometry=name, t=t, r=r):
                    self.assertTrue(res.converged)
                    self.assertLess(np.abs(res.translation - t).max(), 1e-9)
                    self.assertLess(np.abs(res.rotation - r).max(), 1e-9)
                    self.assertLessEqual(res.iterations, 10)

    def test_already_at_solution(self):
        ik = self.geometries['paramétrique']
        res = forward_kinematics(ik, ik.solve([0, 0, 0], [0, 0, 0]))
        self.assertTrue(res.converged)
        self.assertEqual(res.iterations, 0)
        np.testing.assert_allclose(res.translation, 0, atol=1e-15)

    def test_degrees_property(self):
        ik = self.geometries['paramétrique']
        res = forward_kinematics(ik, ik.solve([0, 0, 0.09], [2, -3, 5]), [0, 0, 0.09])
        np.testing.assert_allclose(res.rotation_deg, [2, -3, 5], atol=1e-9)

    def test_unreachable_lengths_do_not_converge(self):
        ik = self.geometries['paramétrique']
        lengths = np.array([0.1, 0.5, 0.1, 0.5, 0.1, 0.5])   # incompatibles avec un corps rigide
        res = forward_kinematics(ik, lengths, max_iterations=30)
        self.assertFalse(res.converged)
        self.assertGreater(res.residual, 1e-6)

    def test_rejects_wrong_size(self):
        with self.assertRaises(ValueError):
            forward_kinematics(self.geometries['paramétrique'], [0.2] * 5)

    def test_orientation_stays_orthonormal(self):
        ik = self.geometries['asymétrique']
        for t, r in random_poses(20, seed=3):
            R = forward_kinematics(ik, ik.solve(t, np.degrees(r)), [0, 0, WORKING_HEIGHT]).rotation_matrix
            np.testing.assert_allclose(R @ R.T, np.eye(3), atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(R), 1.0, places=12)


class TestActuatorPositions(unittest.TestCase):
    """Convention du banc et du tableau de bord : allongements depuis la pose neutre."""

    def test_inverse_of_feasibility(self):
        ik = asymmetric_ik()
        for t_rel, rot_deg in [([0, 0, 0], [0, 0, 0]), ([0.02, -0.03, 0.04], [5, -6, 20])]:
            q = actuator_positions(ik, t_rel, rot_deg, WORKING_HEIGHT)
            res = pose_from_actuator_positions(ik, q, WORKING_HEIGHT)
            self.assertTrue(res.converged)
            np.testing.assert_allclose(res.translation, t_rel, atol=1e-10)
            np.testing.assert_allclose(res.rotation_deg, rot_deg, atol=1e-8)

    def test_initial_guess_is_relative_to_working_position(self):
        ik = InverseKinematics(0.2, 0.2, 12, 12)
        q = actuator_positions(ik, [0.05, 0, 0], [0, 0, 30], WORKING_HEIGHT)
        res = pose_from_actuator_positions(ik, q, WORKING_HEIGHT, initial_translation=[0.05, 0, 0],
                                           initial_rotation_rad=np.radians([0, 0, 30]))
        self.assertLessEqual(res.iterations, 1)
        np.testing.assert_allclose(res.translation, [0.05, 0, 0], atol=1e-10)


class TestJacobian(unittest.TestCase):

    def test_matches_finite_differences(self):
        ik = asymmetric_ik()
        h = 1e-7
        for t, r in random_poses(10, seed=1):
            R = rotation_matrix(r)
            J_fd = np.zeros((6, 6))
            for k in range(6):
                d = np.zeros(6)
                d[k] = h
                lp = np.linalg.norm(_legs(ik, t + d[:3], _exp_so3(d[3:]) @ R)[0], axis=0)
                lm = np.linalg.norm(_legs(ik, t - d[:3], _exp_so3(-d[3:]) @ R)[0], axis=0)
                J_fd[:, k] = (lp - lm) / (2 * h)
            np.testing.assert_allclose(jacobian(ik, t, r), J_fd, atol=1e-8)

    def test_pure_vertical_motion_at_neutral(self):
        """Plateforme horizontale centrée : dℓ_i/dz = cos(inclinaison de la jambe), identique pour les 6."""
        ik = InverseKinematics(0.2, 0.2, 12, 12)
        J = jacobian(ik, [0, 0, WORKING_HEIGHT], [0, 0, 0])
        np.testing.assert_allclose(J[:, 2], J[0, 2], atol=1e-12)
        self.assertTrue(np.all(J[:, 2] > 0))


class TestSingularities(unittest.TestCase):

    def setUp(self):
        self.ik = InverseKinematics(0.2, 0.2, 12, 12)

    def test_well_conditioned_at_working_position(self):
        m = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], [0, 0, 0])
        self.assertLess(m['condition'], 10)
        self.assertGreater(m['determinant'], 0)

    def test_classical_yaw_singularity(self):
        """Hexapode symétrique : singularité parallèle connue à lacet ±90° (Fichter, 1986)."""
        for yaw in (90, -90):
            m = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, yaw]))
            self.assertLess(m['inverse_condition'], 1e-10)
        near = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, 85]))
        self.assertGreater(near['condition'], 30)

    def test_determinant_changes_sign_across_singularity(self):
        before = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, 89]))
        after = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, 91]))
        self.assertGreater(before['determinant'], 0)
        self.assertLess(after['determinant'], 0)

    def test_symmetric_in_yaw(self):
        for yaw in (20, 50, 80):
            plus = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, yaw]))
            minus = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, -yaw]))
            self.assertAlmostEqual(plus['condition'], minus['condition'], places=8)

    def test_dashboard_yaw_range_is_far_from_singularity(self):
        for yaw in np.linspace(-60, 60, 25):
            m = singularity_measures(self.ik, [0, 0, WORKING_HEIGHT], np.radians([0, 0, yaw]))
            self.assertLess(m['condition'], 10)


class TestSolverSettings(unittest.TestCase):

    def test_read_from_repository_config(self):
        s = solver_settings(load_config())
        self.assertEqual(s, dict(tolerance=1e-12, max_iterations=50))

    def test_defaults_when_section_missing(self):
        self.assertEqual(solver_settings({}), dict(tolerance=1e-12, max_iterations=50))


if __name__ == '__main__':
    unittest.main()
