"""
Tests unitaires : jumeau du démonstrateur REM (src/rem_bench, EXP-009)

Python pur : ni ROS, ni Gazebo. Les tests qui génèrent les marqueurs demandent OpenCV
(absent de la CI) et sont alors ignorés.
"""

import copy
import math
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.forward_kinematics import rotation_matrix
from src.rem_bench import load_bench_config
from src.rem_bench.geometry import BenchGeometry
from src.rem_bench.scene import (R_C_O, R_G_A, BenchScene, angular_velocity, leg_visual_poses,
                                 matrix_to_quaternion, matrix_to_sdf_rpy, rpy_deg_to_matrix)
from src.rem_bench.sim_config import (aruco_rvec_to_euler_deg, home_sensor_readings,
                                      imu_compute_rpy_deg, make_sim_params, write_clean_runtime_state)
from src.rem_bench.virtual_arduino import PtySerialLink, VirtualArduinoFirmware, _to_float

try:
    import cv2  # noqa: F401
except ImportError:  # pragma: no cover
    cv2 = None

CFG = load_bench_config()


class TestBenchGeometry(unittest.TestCase):

    def setUp(self):
        self.geo = BenchGeometry(CFG)

    def test_matches_bench_parameters(self):
        """Attaches du schéma du banc : M1 à 221,3° (base, r 7,5 cm), P1 à 252,7° (plateforme, r 4 cm)."""
        b, p = self.geo.base_points[:, 0], self.geo.platform_points[:, 0]
        self.assertAlmostEqual(np.degrees(np.arctan2(b[1], b[0])) % 360, 221.3, places=6)
        self.assertAlmostEqual(np.degrees(np.arctan2(p[1], p[0])) % 360, 252.7, places=6)
        self.assertAlmostEqual(np.linalg.norm(b[:2]), 0.075)
        self.assertAlmostEqual(np.linalg.norm(p[:2]), 0.04)

    def test_home_is_below_ik_home_by_l0_offset(self):
        """Défaut D9 : L0 = 18,86 cm < 19,06 cm (IK à home), plateforme 2,06 mm plus bas."""
        home = self.geo.pose_from_encoders(np.zeros(6))
        self.assertTrue(home.converged)
        np.testing.assert_allclose(home.translation[:2], 0, atol=1e-9)
        self.assertAlmostEqual(home.translation[2] * 1000, -2.06, delta=0.01)
        np.testing.assert_allclose(self.geo.ik.solve([0, 0, 0], [0, 0, 0]) * 100, 19.06, atol=0.005)

    def test_encoders_round_trip(self):
        for t, r in [([0, 0, 0.03], [0, 0, 0]), ([0.01, -0.01, 0.05], np.radians([3, -3, 8]))]:
            q = self.geo.encoders_cm(t, r)
            res = self.geo.pose_from_encoders(q)
            np.testing.assert_allclose(res.translation, t, atol=1e-9)
            np.testing.assert_allclose(res.rotation, r, atol=1e-9)

    def test_full_stroke_lifts_about_ten_centimetres(self):
        top = self.geo.pose_from_encoders(np.full(6, 10.0))
        self.assertAlmostEqual(top.translation[2], 0.0999, delta=0.001)


class TestVirtualArduino(unittest.TestCase):

    def setUp(self):
        self.fw = VirtualArduinoFirmware(CFG['actuators'])

    def run_until_still(self, max_loops=2000):
        for _ in range(max_loops):
            self.fw.step()
            if not self.fw.active.any():
                return
        self.fail("les vérins ne se sont pas arrêtés")

    def test_protocol_line_and_feedback_format(self):
        applied = self.fw.receive("1.50,2,3.25,0,0,4\r\n")
        self.assertEqual(applied, [[1.5, 2.0, 3.25, 0.0, 0.0, 4.0]])
        self.assertEqual(self.fw.feedback_line(), "0.00,0.00,0.00,0.00,0.00,0.00")
        self.assertEqual(self.fw.ready_message, "Arduino connecte via USB - Pret")

    def test_partial_lines_are_buffered(self):
        self.assertEqual(self.fw.receive("1.0,1.0,"), [])
        self.assertEqual(len(self.fw.receive("1.0,1.0,1.0,1.0\n")), 1)

    def test_reaches_target_within_stop_tolerance(self):
        self.fw.receive("3.12,3.12,3.12,3.12,3.12,3.12\n")
        self.run_until_still()
        self.assertTrue(np.all(np.abs(self.fw.position - 3.12) <= CFG['actuators']['stop_tolerance_cm'] + 0.02))

    def test_hysteresis_small_changes_are_ignored(self):
        self.fw.receive("2,2,2,2,2,2\n")
        self.run_until_still()
        before = self.fw.position.copy()
        self.fw.receive(','.join(f'{v + 0.05:.2f}' for v in before) + "\n")   # < 0,10 cm : pas de redémarrage
        self.fw.step()
        np.testing.assert_allclose(self.fw.position, before)

    def test_end_stops(self):
        self.fw.receive("15,15,15,15,15,15\n")
        for _ in range(3000):
            self.fw.step()
        np.testing.assert_allclose(self.fw.position, 10.0)

    def test_arduino_tofloat(self):
        self.assertEqual(_to_float("2.5abc"), 2.5)
        self.assertEqual(_to_float(""), 0.0)
        self.assertEqual(_to_float(" -1.25 "), -1.25)

    def test_pty_link_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            link = PtySerialLink(os.path.join(d, 'ttyVIRT'))
            try:
                fd = os.open(link.link_path, os.O_RDWR | os.O_NOCTTY)
                os.write(fd, b"1,2,3,4,5,6\n")
                import time
                time.sleep(0.05)
                self.assertEqual(link.read_text(), "1,2,3,4,5,6\n")
                link.write_line("0.00,0.00,0.00,0.00,0.00,0.00")
                time.sleep(0.05)
                self.assertEqual(os.read(fd, 100), b"0.00,0.00,0.00,0.00,0.00,0.00\r\n")
                os.close(fd)
            finally:
                link.close()
            self.assertFalse(os.path.lexists(os.path.join(d, 'ttyVIRT')))


class TestScene(unittest.TestCase):

    def setUp(self):
        self.scene = BenchScene(CFG)

    def test_fixed_frames_are_rotations(self):
        for R in (R_C_O, R_G_A):
            np.testing.assert_allclose(R @ R.T, np.eye(3), atol=1e-15)
            self.assertAlmostEqual(np.linalg.det(R), 1.0)

    def test_marker_seen_straight_ahead_at_home(self):
        """Hypothèse de montage : marqueur 30 cm devant, 2,06 mm plus haut que la caméra (D9)."""
        r = home_sensor_readings(CFG)
        np.testing.assert_allclose(r['marker_tvec'], [0, -0.00206, 0.300], atol=1e-5)
        np.testing.assert_allclose(r['marker_euler_deg'], [-180, 0, 0], atol=1e-9)

    def test_camera_moves_with_platform(self):
        geo = BenchGeometry(CFG)
        res = geo.pose_from_encoders(geo.encoders_cm([0, 0, 0.03], [0, 0, 0]))
        tvec, _ = self.scene.marker_in_optical_frame(geo.platform_position_world(res.translation),
                                                     res.rotation_matrix)
        # Plateforme 3 cm au-dessus de la pose home de l'IK : marqueur 3 cm plus bas (y optique vers le bas)
        self.assertAlmostEqual(tvec[1], 0.03, delta=1e-6)
        self.assertAlmostEqual(tvec[2], 0.30, delta=1e-6)

    def test_imu_formula_recovers_zyx_angles(self):
        for rpy in ([0, 0, 0], [5, -3, 20], [-10, 8, -45]):
            R = rpy_deg_to_matrix(rpy)
            accel, mag, _ = self.scene.imu_readings(R, np.zeros(3))
            got = imu_compute_rpy_deg(accel, mag)
            np.testing.assert_allclose(got[:2], rpy[:2], atol=1e-9)
            if rpy[0] == 0:   # cap exact à roulis nul ; formule du banc approchée sinon
                self.assertAlmostEqual(got[2], rpy[2], places=9)

    def test_angular_velocity(self):
        R0 = rotation_matrix([0, 0, 0])
        R1 = rotation_matrix([0, 0, 0.01])
        np.testing.assert_allclose(angular_velocity(R0, R1, 0.02), [0, 0, 0.5], atol=1e-6)

    def test_conversions(self):
        R = rpy_deg_to_matrix([10, -20, 30])
        np.testing.assert_allclose(np.degrees(matrix_to_sdf_rpy(R)), [10, -20, 30], atol=1e-9)
        w, x, y, z = matrix_to_quaternion(R)
        Rq = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                       [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                       [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])
        np.testing.assert_allclose(Rq, R, atol=1e-12)

    def test_leg_visuals_end_at_anchors(self):
        geo = BenchGeometry(CFG)
        base, top = geo.legs_world([0, 0, 0.02], np.eye(3))
        for (pb, Rb, pr, Rr), b, t in zip(leg_visual_poses(base, top, 0.13, 0.16), base.T, top.T):
            np.testing.assert_allclose(pb - Rb[:, 2] * 0.065, b, atol=1e-12)
            np.testing.assert_allclose(pr + Rr[:, 2] * 0.08, t, atol=1e-12)


class TestSimConfig(unittest.TestCase):

    BENCH_PARAMS = {
        'serial': {'port': '/dev/ttyACM0', 'baudrate': 115200},
        'aruco': {'reference_position_m': [0, 0, 0], 'reference_orientation_deg': [-180.2, -5.9, 89.6],
                  'orientation_axis_order': [0, 1, 2], 'orientation_axis_sign': [-1, -1, 1]},
        'imu': {'reference_orientation_deg': [-0.92, -3.62, -42.3],
                'orientation_axis_order': [0, 1, 2], 'orientation_axis_sign': [1, 1, 1]},
        'actuators': {'logical_max_cm': 10.0},
    }

    def test_only_hardware_dependent_keys_change(self):
        sim = make_sim_params(self.BENCH_PARAMS, CFG, '/tmp/ttyVIRT')
        self.assertEqual(sim['serial']['port'], '/tmp/ttyVIRT')
        self.assertEqual(sim['serial']['baudrate'], 115200)
        self.assertEqual(sim['actuators'], self.BENCH_PARAMS['actuators'])
        self.assertEqual(sim['aruco']['reference_position_m'], [0, 0, 0])
        self.assertEqual(self.BENCH_PARAMS['serial']['port'], '/dev/ttyACM0')   # source intacte

    def test_references_null_orientation_at_home(self):
        """Le remappage puis la soustraction de la référence (code du banc) donnent 0 à home."""
        sim = make_sim_params(copy.deepcopy(self.BENCH_PARAMS), CFG, '/tmp/ttyVIRT')
        raw = home_sensor_readings(CFG)
        ar = sim['aruco']
        remapped = [((v * s + 180) % 360) - 180 for v, s in
                    zip(raw['marker_euler_deg'], ar['orientation_axis_sign'])]
        corrected = [((a - b + 180) % 360) - 180 for a, b in zip(remapped, ar['reference_orientation_deg'])]
        np.testing.assert_allclose(corrected, 0, atol=1e-3)
        np.testing.assert_allclose(sim['imu']['reference_orientation_deg'], 0, atol=1e-3)

    def test_aruco_euler_matches_bench_formula(self):
        R = rpy_deg_to_matrix([10, 20, 30])   # Rz·Ry·Rx : rvec_to_euler du banc rend (roll, pitch, yaw)
        np.testing.assert_allclose(aruco_rvec_to_euler_deg(R), [10, 20, 30], atol=1e-9)

    def test_clean_runtime_state(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            state = json.load(open(write_clean_runtime_state(d)))
        self.assertFalse(state['recovery_required'])
        self.assertTrue(state['home_confirmed'] and state['position_known'] and state['clean_shutdown'])


@unittest.skipIf(cv2 is None, "OpenCV non installé")
class TestWorldGeneration(unittest.TestCase):

    def test_world_is_valid_sdf_with_bench_camera(self):
        from src.rem_bench.sdf import GZ_PIXEL_OFFSET, generate_world, marker_bits
        with tempfile.TemporaryDirectory() as d:
            path = generate_world(CFG, d)
            root = ET.parse(path).getroot()
            names = {m.get('name') for m in root.iter('model')}
            self.assertTrue({'platform', 'base', 'target_marker', 'leg1_body', 'leg6_rod'} <= names)
            intr = root.find('.//sensor/camera/lens/intrinsics')
            self.assertAlmostEqual(float(intr.find('fx').text), CFG['camera']['fx'])
            self.assertAlmostEqual(float(intr.find('cx').text), CFG['camera']['cx'] + GZ_PIXEL_OFFSET, places=3)
            hfov = float(root.find('.//sensor/camera/horizontal_fov').text)
            self.assertAlmostEqual(hfov, 2 * math.atan(320 / CFG['camera']['fx']), places=5)
            obj = open(os.path.join(d, 'markers', 'aruco_26.obj')).read()
            black_quads = obj.split('usemtl aruco_26_black')[1].count('\nf ') // 2
            self.assertEqual(black_quads, int(marker_bits(26, 'DICT_4X4_1000').sum()))


if __name__ == '__main__':
    unittest.main()
