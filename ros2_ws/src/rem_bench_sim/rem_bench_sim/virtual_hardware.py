"""
Nœud ``virtual_hardware`` : Arduino virtuel + mécanisme du banc + poses Gazebo
=============================================================================

Boucle à la période du firmware (20 ms) :

1. lit les consignes écrites par les nœuds du banc sur le pseudo-terminal ;
2. avance l'émulation des 6 vérins (:class:`VirtualArduinoFirmware`) ;
3. renvoie la ligne de retour ``p1,...,p6`` ;
4. calcule la pose de la plateforme par FK des codeurs (géométrie physique du banc) ;
5. publie la vérité terrain et transmet les poses des corps à Gazebo.

Topics publiés (vérité de simulation, absents du banc, préfixe ``/sim``) :

- ``/sim/encoders_cm`` (``Float32MultiArray``) : positions des vérins (cm) ;
- ``/sim/platform_pose`` (``PoseStamped``, repère ``base``) : pose physique de la plateforme ;
- ``/sim/marker_in_camera`` (``Float32MultiArray``) : ``[tx, ty, tz (m), roll, pitch, yaw (deg)]``,
  pose vraie du marqueur dans l'optique caméra, convention ``aruco_node`` (avant référence).

Paramètres ROS : ``bench_config`` (chemin de bench_rem.yaml), ``serial_link`` (lien du
pseudo-terminal), ``world`` (nom du monde Gazebo, par défaut celui de bench_rem.yaml).
"""

import threading

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

from . import ensure_stewart_platform_on_path

ensure_stewart_platform_on_path()

from src.rem_bench import load_bench_config  # noqa: E402
from src.rem_bench.geometry import BenchGeometry  # noqa: E402
from src.rem_bench.scene import BenchScene, matrix_to_quaternion  # noqa: E402
from src.rem_bench.sdf import body_poses  # noqa: E402
from src.rem_bench.sim_config import aruco_rvec_to_euler_deg  # noqa: E402
from src.rem_bench.virtual_arduino import PtySerialLink, VirtualArduinoFirmware  # noqa: E402


class GazeboPoseWriter:
    """Envoie les poses des corps à Gazebo (``set_pose_vector``) dans un fil dédié."""

    def __init__(self, world: str, logger):
        from gz.msgs10.boolean_pb2 import Boolean
        from gz.msgs10.pose_v_pb2 import Pose_V
        from gz.transport13 import Node as GzNode
        self._Pose_V, self._Boolean = Pose_V, Boolean
        self._node = GzNode()
        self._service = f'/world/{world}/set_pose_vector'
        self._logger = logger
        self._latest = None
        self._event = threading.Event()
        self._stop = False
        self._warned = False
        self._thread = threading.Thread(target=self._run, name='gz-pose-writer', daemon=True)
        self._thread.start()

    def submit(self, poses: dict) -> None:
        self._latest = poses
        self._event.set()

    def _run(self):
        while not self._stop:
            self._event.wait(0.5)
            self._event.clear()
            poses, self._latest = self._latest, None
            if poses is None:
                continue
            req = self._Pose_V()
            for name, (p, R) in poses.items():
                pose = req.pose.add()
                pose.name = name
                pose.position.x, pose.position.y, pose.position.z = (float(v) for v in p)
                w, x, y, z = matrix_to_quaternion(R)
                pose.orientation.w, pose.orientation.x = float(w), float(x)
                pose.orientation.y, pose.orientation.z = float(y), float(z)
            ok, _ = self._node.request(self._service, req, self._Pose_V, self._Boolean, 200)
            if not ok and not self._warned:
                self._logger.warn(f"Gazebo ne répond pas sur {self._service} (monde lancé ?)")
                self._warned = True
            elif ok:
                self._warned = False

    def close(self):
        self._stop = True
        self._event.set()


class VirtualHardware(Node):

    def __init__(self):
        super().__init__('virtual_hardware')
        self.declare_parameter('bench_config', '')
        self.declare_parameter('serial_link', '~/.rem_bench_sim/ttyVIRT')
        self.declare_parameter('world', '')
        self.declare_parameter('gazebo', True)
        cfg_path = self.get_parameter('bench_config').value or None
        self.cfg = load_bench_config(cfg_path)
        self.geo = BenchGeometry(self.cfg)
        self.scene = BenchScene(self.cfg)
        self.firmware = VirtualArduinoFirmware(self.cfg['actuators'])
        self.link = PtySerialLink(self.get_parameter('serial_link').value)
        self.link.write_line(self.firmware.ready_message)
        world = self.get_parameter('world').value or self.cfg['gazebo']['world_name']
        self.gz = GazeboPoseWriter(world, self.get_logger()) if self.get_parameter('gazebo').value else None

        self.pub_enc = self.create_publisher(Float32MultiArray, '/sim/encoders_cm', 10)
        self.pub_pose = self.create_publisher(PoseStamped, '/sim/platform_pose', 10)
        self.pub_marker = self.create_publisher(Float32MultiArray, '/sim/marker_in_camera', 10)
        self.period = float(self.cfg['actuators']['loop_period_s'])
        self.pose_period = float(self.cfg['gazebo']['pose_update_period_s'])
        self._since_pose = self.pose_period
        self.timer = self.create_timer(self.period, self.loop)
        self.get_logger().info(
            f"Arduino virtuel prêt : {self.link.link_path} -> {self.link.slave_name} ; "
            f"Gazebo : {'monde ' + world if self.gz else 'désactivé'}")

    def loop(self):
        for line in self.firmware.receive(self.link.read_text()):
            self.get_logger().debug(f"Consigne reçue : {line}")
        self.firmware.step(self.period)
        self.link.write_line(self.firmware.feedback_line())

        encoders = self.firmware.position.copy()
        self.pub_enc.publish(Float32MultiArray(data=[float(v) for v in encoders]))
        fk = self.geo.pose_from_encoders(encoders)
        if not fk.converged:
            self.get_logger().error(f"FK non convergée (résidu {fk.residual:.2e} m)", throttle_duration_sec=2.0)
            return
        R = fk.rotation_matrix
        centre = self.geo.platform_position_world(fk.translation)

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base'
        msg.pose.position.x, msg.pose.position.y, msg.pose.position.z = (float(v) for v in centre)
        w, x, y, z = matrix_to_quaternion(R)
        msg.pose.orientation.w, msg.pose.orientation.x = float(w), float(x)
        msg.pose.orientation.y, msg.pose.orientation.z = float(y), float(z)
        self.pub_pose.publish(msg)

        tvec, R_O_A = self.scene.marker_in_optical_frame(centre, R)
        self.pub_marker.publish(Float32MultiArray(
            data=[float(v) for v in tvec] + [float(v) for v in aruco_rvec_to_euler_deg(R_O_A)]))

        self._since_pose += self.period
        if self.gz is not None and self._since_pose >= self.pose_period - 1e-9:
            self._since_pose = 0.0
            self.gz.submit(body_poses(self.cfg, self.geo, fk.translation, R))

    def destroy_node(self):
        if self.gz is not None:
            self.gz.close()
        self.link.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VirtualHardware()
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
