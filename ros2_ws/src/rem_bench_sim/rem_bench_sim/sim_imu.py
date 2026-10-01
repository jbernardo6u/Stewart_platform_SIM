"""
Nœud ``sim_imu`` : ``imu_node`` du banc sur un MPU-9250 simulé
==============================================================

On exécute **le code du banc** (``stewart_control.imu_node.IMUPublisher`` : calcul de
l'orientation, remappage d'axes, référence, gyroscope, publication de ``/imu_error`` et
``/imu_gyro``). Seul le pilote matériel est remplacé : les modules ``smbus`` et
``imusensor.MPU9250`` sont substitués avant l'import par des doublures qui lisent la pose
vraie de la plateforme (``/sim/platform_pose``).

Le MPU simulé fournit, dans son repère : la force spécifique (gravité, accélérations
négligées), le champ magnétique terrestre et la vitesse angulaire (différences finies
d'orientation), avec les unités attendues par ``imu.gyro_units``. Bruits : section
``imu`` de bench_rem.yaml (nuls par défaut, à calibrer sur les enregistrements du banc).
"""

import sys
import types

import numpy as np

from . import ensure_stewart_platform_on_path

ensure_stewart_platform_on_path()

from src.rem_bench import load_bench_config  # noqa: E402
from src.rem_bench.scene import BenchScene, angular_velocity  # noqa: E402


class _SimState:
    """Dernière orientation reçue, partagée avec le MPU simulé."""
    R = np.eye(3)
    R_prev = np.eye(3)
    stamp = None
    stamp_prev = None


class SimMPU9250:
    """Doublure de ``imusensor.MPU9250.MPU9250`` (interface utilisée par imu_node)."""
    scene: BenchScene = None
    gyro_deg_s = True
    rng = np.random.default_rng()
    noise_deg = 0.0
    noise_gyro = 0.0

    def __init__(self, bus=None, address=None):
        self.AccelVals = np.array([0.0, 0.0, 9.81])
        self.MagVals = np.array([0.22, 0.0, -0.42])
        self.GyroVals = np.zeros(3)

    def begin(self):
        return True

    def loadCalibDataFromFile(self, path):
        return True

    def readSensor(self):
        s = _SimState
        dt = 0.0 if s.stamp is None or s.stamp_prev is None else s.stamp - s.stamp_prev
        omega = angular_velocity(s.R_prev, s.R, dt) if dt > 0 else np.zeros(3)
        R = s.R
        if self.noise_deg > 0:
            from src.rem_bench.scene import rpy_deg_to_matrix
            R = R @ rpy_deg_to_matrix(self.rng.normal(0, self.noise_deg, 3))
        accel, mag, gyro = self.scene.imu_readings(R, omega)
        gyro = np.degrees(gyro) if self.gyro_deg_s else gyro
        if self.noise_gyro > 0:
            gyro = gyro + self.rng.normal(0, self.noise_gyro, 3)
        self.AccelVals, self.MagVals, self.GyroVals = accel, mag, gyro


def install_hardware_doubles():
    """Substitue ``smbus`` et ``imusensor.MPU9250`` dans ``sys.modules``."""
    # imu_node fait « import smbus », « from imusensor.MPU9250 import MPU9250 », puis
    # « MPU9250.MPU9250(bus, adresse) » : paquet imusensor.MPU9250, module MPU9250, classe MPU9250.
    smbus = types.ModuleType('smbus')
    smbus.SMBus = lambda bus=1: None
    package = types.ModuleType('imusensor.MPU9250')
    module = types.ModuleType('imusensor.MPU9250.MPU9250')
    module.MPU9250 = SimMPU9250
    package.MPU9250 = module
    root = types.ModuleType('imusensor')
    root.MPU9250 = package
    sys.modules.update({'smbus': smbus, 'imusensor': root, 'imusensor.MPU9250': package,
                        'imusensor.MPU9250.MPU9250': module})


def main(args=None):
    import rclpy
    from geometry_msgs.msg import PoseStamped

    cfg = load_bench_config()
    SimMPU9250.scene = BenchScene(cfg)
    SimMPU9250.noise_deg = float(cfg['imu'].get('noise_orientation_deg', 0.0))
    SimMPU9250.noise_gyro = float(cfg['imu'].get('noise_gyro_deg_s', 0.0))
    install_hardware_doubles()
    from stewart_control import imu_node
    from stewart_control.config_loader import get_config
    SimMPU9250.gyro_deg_s = str(get_config()['imu'].get('gyro_units', 'deg_s')).lower() == 'deg_s'

    rclpy.init(args=args)
    node = imu_node.IMUPublisher()

    def on_pose(msg):
        q = msg.pose.orientation
        w, x, y, z = q.w, q.x, q.y, q.z
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                      [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                      [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])
        _SimState.R_prev, _SimState.stamp_prev = _SimState.R, _SimState.stamp
        _SimState.R = R
        _SimState.stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

    node.create_subscription(PoseStamped, '/sim/platform_pose', on_pose, 10)
    node.get_logger().info("IMU simulée : imu_node du banc alimenté par /sim/platform_pose")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
