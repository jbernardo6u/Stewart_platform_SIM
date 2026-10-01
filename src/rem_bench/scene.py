"""
Scène du démonstrateur REM : caméra embarquée, marqueur, IMU, poses Gazebo
==========================================================================

Repères (monde = repère de la base, origine au centre de la base, z vers le haut) :

- ``{P}`` plateforme : centre ``home_position + t``, orientation ``R`` (convention de l'IK) ;
- corps caméra ``{C}`` (Gazebo) : x = axe optique, y à gauche, z en haut ; monté dans ``{P}`` ;
- optique OpenCV ``{O}`` : z = axe optique, x à droite, y en bas (``R_C←O`` fixe) ;
- modèle marqueur ``{G}`` (Gazebo) : face visible dans le plan y-z, normale sortante −x_G ;
- marqueur ArUco ``{A}`` (convention OpenCV) : x à droite, y en haut, z sortant de la face.

:func:`marker_in_optical_frame` donne la pose vraie que doit estimer
``estimatePoseSingleMarkers`` : c'est la référence des tests de la caméra simulée.
"""

from typing import Sequence, Tuple

import numpy as np

from ..core.forward_kinematics import rotation_matrix

# Optique OpenCV {O} exprimée dans le corps caméra Gazebo {C}
R_C_O = np.array([[0.0, 0.0, 1.0],
                  [-1.0, 0.0, 0.0],
                  [0.0, -1.0, 0.0]])
# Marqueur ArUco {A} exprimé dans le modèle Gazebo du marqueur {G}
R_G_A = np.array([[0.0, 0.0, -1.0],
                  [-1.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0]])


def rpy_deg_to_matrix(rpy_deg: Sequence[float]) -> np.ndarray:
    """Rotation fixe des fichiers de configuration et de SDF : ``Rz(y)·Ry(p)·Rx(r)``."""
    r, p, y = np.radians(rpy_deg)
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return (np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
            @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
            @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]]))


def matrix_to_sdf_rpy(R: np.ndarray) -> np.ndarray:
    """Inverse de :func:`rpy_deg_to_matrix`, en radians (convention SDF ``<pose>``)."""
    pitch = np.arcsin(np.clip(-R[2, 0], -1.0, 1.0))
    return np.array([np.arctan2(R[2, 1], R[2, 2]), pitch, np.arctan2(R[1, 0], R[0, 0])])


def matrix_to_quaternion(R: np.ndarray) -> np.ndarray:
    """Quaternion ``[w, x, y, z]`` d'une matrice de rotation (méthode de Shepperd)."""
    m = R
    trace = np.trace(m)
    if trace > 0:
        s = 2.0 * np.sqrt(trace + 1.0)
        q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
        q = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
    elif m[1, 1] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
        q = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
    else:
        s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
        q = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q) * (1 if q[0] >= 0 else -1)


def align_z(direction: np.ndarray) -> np.ndarray:
    """Rotation qui amène l'axe z sur ``direction`` (pour orienter un cylindre)."""
    z = np.asarray(direction, dtype=float)
    z = z / np.linalg.norm(z)
    helper = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(helper, z)
    x /= np.linalg.norm(x)
    return np.column_stack([x, np.cross(z, x), z])


class BenchScene:
    """Transformations fixes de la scène, lues dans bench_rem.yaml."""

    def __init__(self, config: dict):
        cam, mk, imu = config['camera'], config['markers']['target'], config['imu']
        self.camera_position_P = np.asarray(cam['mount_position_in_platform'], dtype=float)
        self.R_P_C = rpy_deg_to_matrix(cam['mount_rpy_in_platform_deg'])
        self.marker_position_W = np.asarray(mk['position'], dtype=float)
        self.R_W_G = rpy_deg_to_matrix(mk['rpy_deg'])
        self.R_P_I = rpy_deg_to_matrix(imu['mount_rpy_in_platform_deg'])
        self.gravity = float(imu['gravity_m_s2'])
        self.magnetic_field_W = np.asarray(imu['magnetic_field_world'], dtype=float)
        self.camera = cam

    # --- caméra ---
    def camera_pose_world(self, platform_position_W, R_W_P) -> Tuple[np.ndarray, np.ndarray]:
        """Pose du corps caméra {C} dans le monde."""
        return platform_position_W + R_W_P @ self.camera_position_P, R_W_P @ self.R_P_C

    def marker_in_optical_frame(self, platform_position_W, R_W_P) -> Tuple[np.ndarray, np.ndarray]:
        """Pose vraie du marqueur {A} dans l'optique {O} : ``(tvec (m), R_O←A)``."""
        p_C, R_W_C = self.camera_pose_world(platform_position_W, R_W_P)
        R_W_O = R_W_C @ R_C_O
        R_W_A = self.R_W_G @ R_G_A
        return R_W_O.T @ (self.marker_position_W - p_C), R_W_O.T @ R_W_A

    def horizontal_fov(self) -> float:
        """Champ horizontal (rad) correspondant à ``fx`` et à la largeur d'image."""
        return 2.0 * np.arctan(self.camera['width'] / (2.0 * self.camera['fx']))

    # --- IMU (lectures brutes d'un MPU-9250 monté sur la plateforme) ---
    def imu_readings(self, R_W_P: np.ndarray, omega_W: np.ndarray):
        """
        ``(accel, mag, gyro)`` dans le repère capteur : force spécifique au repos (m/s²,
        +g vers le haut quand le capteur est à plat), champ magnétique (gauss), vitesse
        angulaire (rad/s). Accélérations de la plateforme négligées (mouvements lents).
        """
        R_W_I = R_W_P @ self.R_P_I
        accel = R_W_I.T @ np.array([0.0, 0.0, self.gravity])
        return accel, R_W_I.T @ self.magnetic_field_W, R_W_I.T @ np.asarray(omega_W, dtype=float)


def angular_velocity(R_prev: np.ndarray, R_now: np.ndarray, dt: float) -> np.ndarray:
    """Vitesse angulaire (rad/s, repère monde) entre deux orientations séparées de ``dt``."""
    dR = R_now @ R_prev.T
    angle = np.arccos(np.clip((np.trace(dR) - 1.0) / 2.0, -1.0, 1.0))
    if angle < 1e-12 or dt <= 0:
        return np.zeros(3)
    axis = np.array([dR[2, 1] - dR[1, 2], dR[0, 2] - dR[2, 0], dR[1, 0] - dR[0, 1]]) / (2 * np.sin(angle))
    return axis * angle / dt


def leg_visual_poses(base_W: np.ndarray, top_W: np.ndarray, body_length: float, rod_length: float):
    """
    Poses (centre, R) du corps fixe et de la tige de chaque vérin.

    Le corps part de l'attache base, la tige finit à l'attache plateforme : leurs
    longueurs sont fixes et ils se recouvrent, comme un vérin télescopique.
    """
    poses = []
    for b, t in zip(base_W.T, top_W.T):
        axis = (t - b) / np.linalg.norm(t - b)
        R = align_z(axis)
        poses.append(((b + axis * body_length / 2), R, (t - axis * rod_length / 2), R))
    return poses


__all__ = ['BenchScene', 'R_C_O', 'R_G_A', 'align_z', 'angular_velocity', 'leg_visual_poses',
           'matrix_to_quaternion', 'matrix_to_sdf_rpy', 'rpy_deg_to_matrix', 'rotation_matrix']
