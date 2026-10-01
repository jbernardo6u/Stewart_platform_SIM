"""
Campagne EXP-009 : jumeau Gazebo du démonstrateur, en mode manuel
================================================================

À lancer pendant ``bench_sim.launch.py mode:=manual``. Pour chaque consigne, envoyée comme
le fait l'interface du banc (``/manual_position`` en cm, ``/manual_orientation`` en °),
attend la stabilisation puis enregistre :

- la consigne, la pose physique atteinte (FK des codeurs simulés, convention de l'IK du
  banc : translation depuis ``home_position``, ``R = Rx·Ry·Rz``) ;
- les consignes des vérins (``/stewart/longueurs``) et les codeurs simulés ;
- la position marqueur publiée par ``aruco_node`` et la vérité (``/sim/marker_in_camera``).

Sortie : ``<output_dir>/exp009_manual.csv`` (paramètre ``output_dir``).
"""

import csv
import os
import time

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

from . import ensure_stewart_platform_on_path

ensure_stewart_platform_on_path()

from src.core.forward_kinematics import rotation_to_rpy  # noqa: E402
from src.rem_bench import load_bench_config  # noqa: E402

# (libellé, position cm, orientation deg), comme l'interface du banc
COMMANDS = [
    ('home', [0, 0, 0], [0, 0, 0]),
    ('z+3', [0, 0, 3], [0, 0, 0]),
    ('z+3 x+1', [1, 0, 3], [0, 0, 0]),
    ('z+3 y+1', [0, 1, 3], [0, 0, 0]),
    ('z+3 roll+5', [0, 0, 3], [5, 0, 0]),
    ('z+3 pitch+5', [0, 0, 3], [0, 5, 0]),
    ('z+3 yaw+10', [0, 0, 3], [0, 0, 10]),
    ('z+5 combinee', [1, -1, 5], [3, -3, 8]),
    ('retour z+0.5', [0, 0, 0.5], [0, 0, 0]),
]


def quaternion_to_matrix(q):
    w, x, y, z = q.w, q.x, q.y, q.z
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


class Campaign(Node):

    def __init__(self):
        super().__init__('exp009_campaign')
        self.declare_parameter('output_dir', os.path.expanduser('~/.rem_bench_sim/results'))
        self.declare_parameter('settle_s', 12.0)
        self.home = np.asarray(load_bench_config()['geometry']['home_position'], dtype=float)
        self.pub_pos = self.create_publisher(Float32MultiArray, 'manual_position', 1)
        self.pub_ori = self.create_publisher(Float32MultiArray, 'manual_orientation', 1)
        self.latest = {}
        for topic, key in [('/sim/encoders_cm', 'encoders'), ('/stewart/longueurs', 'targets'),
                           ('/aruco_position', 'aruco'), ('/sim/marker_in_camera', 'truth')]:
            self.create_subscription(Float32MultiArray, topic,
                                     lambda m, k=key: self.latest.__setitem__(k, list(m.data)), 10)
        self.create_subscription(PoseStamped, '/sim/platform_pose', self.on_pose, 10)

    def on_pose(self, msg):
        p = msg.pose.position
        R = quaternion_to_matrix(msg.pose.orientation)
        self.latest['pose'] = (np.array([p.x, p.y, p.z]) - self.home, np.degrees(rotation_to_rpy(R)))

    def spin_for(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def run(self):
        self.spin_for(3.0)
        rows = []
        for label, pos_cm, rot_deg in COMMANDS:
            self.pub_ori.publish(Float32MultiArray(data=[float(v) for v in rot_deg]))
            self.spin_for(0.2)
            self.pub_pos.publish(Float32MultiArray(data=[float(v) for v in pos_cm]))
            self.spin_for(float(self.get_parameter('settle_s').value))
            t, r = self.latest['pose']
            aruco = np.array(self.latest.get('aruco', [np.nan] * 3)) * 100
            truth = np.array(self.latest['truth'][:3]) * 100
            row = dict(label=label)
            row.update({f'cmd_{k}_cm': v for k, v in zip('xyz', pos_cm)})
            row.update({f'cmd_{k}_deg': v for k, v in zip(('roll', 'pitch', 'yaw'), rot_deg)})
            row.update({f'real_{k}_cm': round(float(v * 100), 3) for k, v in zip('xyz', t)})
            row.update({f'real_{k}_deg': round(float(v), 3) for k, v in zip(('roll', 'pitch', 'yaw'), r)})
            row.update({f'target_M{i + 1}_cm': round(v, 3) for i, v in enumerate(self.latest.get('targets', [np.nan] * 6))})
            row.update({f'encoder_M{i + 1}_cm': round(v, 3) for i, v in enumerate(self.latest['encoders'])})
            row.update({f'aruco_{k}_cm': round(float(v), 3) for k, v in zip('xyz', aruco)})
            row.update({f'truth_{k}_cm': round(float(v), 3) for k, v in zip('xyz', truth)})
            row['aruco_error_mm'] = round(float(np.linalg.norm(aruco - truth) * 10), 2)
            rows.append(row)
            self.get_logger().info(
                f"{label:14s} consigne {pos_cm} cm {rot_deg}° -> atteint {np.round(t * 100, 2).tolist()} cm "
                f"{np.round(r, 2).tolist()}° ; écart ArUco/vérité {row['aruco_error_mm']} mm")
        out_dir = os.path.expanduser(self.get_parameter('output_dir').value)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, 'exp009_manual.csv')
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        self.get_logger().info(f"Résultats : {path}")


def main(args=None):
    rclpy.init(args=args)
    node = Campaign()
    try:
        node.run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
