"""
Configuration des nœuds du banc pour la simulation
==================================================

Les nœuds de ``stewart_control`` lisent ``stewart_params.yaml`` (variable
``STEWART_CONFIG``). Pour la simulation, on part du fichier **du banc** et on ne
change que ce qui dépend du matériel remplacé :

- ``serial.port`` : lien vers le pseudo-terminal de l'Arduino virtuel ;
- ``aruco.reference_orientation_deg`` et ``imu.reference_orientation_deg`` : ce sont des
  constantes d'étalonnage qui dépendent du montage. On refait l'étalonnage du banc
  (lecture brute à la pose home, ``test_imu_home_reference.py``) sur le montage simulé,
  pour que l'orientation publiée soit nulle à home, comme sur le banc étalonné ;
- ``aruco.reference_position_m`` est **conservée** (``[0, 0, 0]`` sur le banc : la
  position publiée est le vecteur caméra → marqueur brut).

Les formules de :func:`aruco_rvec_to_euler_deg` et :func:`imu_compute_rpy_deg` sont
recopiées de ``aruco_node.rvec_to_euler`` et ``imu_node.compute_rpy`` (Demonstrateur_REM
@36fd541), pour calculer les références sans importer ROS.

Le fichier d'état d'exécution (``motor_runtime_state.json``) est réécrit « home
confirmé » : l'Arduino virtuel démarre codeurs à zéro, plateforme à home.
"""

import copy
import json
import math
import os
import time

import numpy as np

from .geometry import BenchGeometry
from .scene import BenchScene


def aruco_rvec_to_euler_deg(R: np.ndarray):
    """``ArucoRelativePose.rvec_to_euler`` (angles ZYX de ``R_O←A``), en degrés."""
    sy = math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
    if sy >= 1e-6:
        roll, pitch, yaw = math.atan2(R[2, 1], R[2, 2]), math.atan2(-R[2, 0], sy), math.atan2(R[1, 0], R[0, 0])
    else:
        roll, pitch, yaw = math.atan2(-R[1, 2], R[1, 1]), math.atan2(-R[2, 0], sy), 0.0
    return [math.degrees(roll), math.degrees(pitch), math.degrees(yaw)]


def imu_compute_rpy_deg(accel, mag):
    """``imu_node.compute_rpy`` : roulis et tangage par l'accéléromètre, cap compensé."""
    ax, ay, az = accel
    mx, my, mz = mag
    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay ** 2 + az ** 2))
    xh = mx * math.cos(pitch) + mz * math.sin(pitch)
    yh = mx * math.sin(roll) * math.sin(pitch) + my * math.cos(roll) - mz * math.sin(roll) * math.cos(pitch)
    return math.degrees(roll), math.degrees(pitch), math.degrees(math.atan2(-yh, xh))


def _wrap(values):
    return [((v + 180.0) % 360.0) - 180.0 for v in values]


def _remap(values, order, sign):
    w = _wrap(values)
    return _wrap([w[i] * s for i, s in zip(order, sign)])


def home_sensor_readings(bench_cfg: dict):
    """Lectures brutes (caméra ArUco, IMU) à la pose home du banc simulé."""
    geo, scene = BenchGeometry(bench_cfg), BenchScene(bench_cfg)
    home = geo.pose_from_encoders(np.zeros(6))
    centre = geo.platform_position_world(home.translation)
    tvec, R_O_A = scene.marker_in_optical_frame(centre, home.rotation_matrix)
    accel, mag, _ = scene.imu_readings(home.rotation_matrix, np.zeros(3))
    return dict(marker_tvec=tvec, marker_euler_deg=aruco_rvec_to_euler_deg(R_O_A),
                imu_rpy_deg=list(imu_compute_rpy_deg(accel, mag)))


def make_sim_params(bench_params: dict, bench_cfg: dict, serial_link: str) -> dict:
    """``stewart_params.yaml`` du banc adapté à la simulation (copie modifiée)."""
    params = copy.deepcopy(bench_params)
    home = home_sensor_readings(bench_cfg)
    params['serial']['port'] = serial_link
    ar = params['aruco']
    ar['reference_orientation_deg'] = [round(v, 3) for v in _remap(
        home['marker_euler_deg'], ar.get('orientation_axis_order', [0, 1, 2]),
        ar.get('orientation_axis_sign', [1, 1, 1]))]
    imu = params['imu']
    imu['reference_orientation_deg'] = [round(v, 3) for v in _remap(
        home['imu_rpy_deg'], imu.get('orientation_axis_order', [0, 1, 2]),
        imu.get('orientation_axis_sign', [1, 1, 1]))]
    params['simulation'] = {
        'generated_by': 'Stewart-Platform/src/rem_bench/sim_config.py',
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'note': 'Copie de stewart_params.yaml du banc ; seuls serial.port et les références '
                'd\'orientation (étalonnage du montage simulé) sont modifiés.',
    }
    return params


def write_clean_runtime_state(runtime_dir: str) -> str:
    """État d'exécution « position home confirmée », au format de ``RuntimeStateManager``."""
    os.makedirs(runtime_dir, exist_ok=True)
    path = os.path.join(runtime_dir, 'motor_runtime_state.json')
    state = {
        'version': 1, 'position_known': True, 'home_confirmed': True, 'recovery_required': False,
        'clean_shutdown': True, 'shutdown_in_progress': False, 'session_dirty': False,
        'owner_pid': None, 'last_feedback_cm': [0.0] * 6, 'last_command_cm': [0.0] * 6,
        'last_update': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'last_status_message': 'Simulation : Arduino virtuel démarré à home.',
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    return path
