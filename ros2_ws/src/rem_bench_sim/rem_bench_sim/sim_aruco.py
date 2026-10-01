"""
Nœud ``sim_aruco`` : ``aruco_node`` du banc sur la caméra rendue par Gazebo
==========================================================================

On exécute **le code du banc** (``stewart_control.aruco_node.ArucoRelativePose`` :
détection, estimation de pose, référence, remappage, lissage, zone morte, aperçu,
publication de ``/aruco_position``, ``/aruco_orientation`` et ``/camera/image_raw``).
Seule l'acquisition change : ``_open_camera`` renvoie une « capture » alimentée par le
topic ROS de la caméra Gazebo, au lieu d'un périphérique V4L2 (absent sous WSL).

La caméra Gazebo est un sténopé idéal aux intrinsèques du banc (``calib_int.npz``) : les
coefficients de distorsion sont donc mis à zéro après l'initialisation du nœud.

Paramètre ROS : ``image_topic`` (par défaut ``/rem_bench/camera/image``).
"""

import threading
import time

import numpy as np

from . import ensure_stewart_platform_on_path

ensure_stewart_platform_on_path()


class _ArucoWithoutBrokenConstructor:
    """
    Proxy de ``cv2.aruco`` sans ``DetectorParameters`` si ce constructeur est défectueux.

    Avec l'OpenCV 4.6 d'Ubuntu 24.04 (apt), ``cv2.aruco.DetectorParameters()`` renvoie un
    objet qui provoque une erreur de segmentation dès qu'on modifie un attribut.
    ``aruco_node.create_detector_parameters`` l'essaie en premier ; sans lui, elle prend
    son repli ``DetectorParameters_create()``, avec les mêmes réglages. Défaut du dépôt
    du banc, signalé dans EXP-009 ; le code du banc n'est pas modifié.
    """

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        if name == 'DetectorParameters':
            raise AttributeError(name)
        return getattr(self._module, name)


def detector_parameters_constructor_is_broken() -> bool:
    """Teste le constructeur dans un sous-processus (le défaut est une erreur de segmentation)."""
    import subprocess
    import sys
    code = ("import cv2\n"
            "p = cv2.aruco.DetectorParameters()\n"
            "p.cornerRefinementMethod = 1\n")
    return subprocess.run([sys.executable, '-c', code], capture_output=True).returncode != 0


class TopicCapture:
    """Interface minimale de ``cv2.VideoCapture`` utilisée par aruco_node."""

    def __init__(self, timeout_s: float = 1.0):
        self._frame = None
        self._lock = threading.Lock()
        self._new = threading.Condition(self._lock)
        self._timeout = timeout_s
        self.frames = 0

    def push(self, frame_bgr):
        with self._new:
            self._frame = frame_bgr
            self.frames += 1
            self._new.notify_all()

    def isOpened(self):
        return True

    def read(self):
        with self._new:
            if self._frame is None:
                self._new.wait(self._timeout)
            frame, self._frame = self._frame, None
        if frame is None:
            return False, None
        return True, frame

    def set(self, prop, value):
        return False

    def get(self, prop):
        return 0.0

    def release(self):
        pass


def main(args=None):
    import rclpy
    from cv_bridge import CvBridge
    from rclpy.executors import MultiThreadedExecutor
    from sensor_msgs.msg import Image
    from stewart_control import aruco_node

    if hasattr(aruco_node.aruco, 'DetectorParameters_create') and detector_parameters_constructor_is_broken():
        aruco_node.aruco = _ArucoWithoutBrokenConstructor(aruco_node.aruco)

    class SimArucoRelativePose(aruco_node.ArucoRelativePose):
        def _open_camera(self):
            if getattr(self, '_sim_capture', None) is None:
                self._sim_capture = TopicCapture()
                self._sim_bridge = CvBridge()
                self.declare_parameter('image_topic', '/rem_bench/camera/image')
                topic = self.get_parameter('image_topic').value

                def on_image(msg):
                    self._sim_capture.push(self._sim_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8'))

                # Groupe réentrant : les images arrivent pendant que loop() attend dans read()
                from rclpy.callback_groups import ReentrantCallbackGroup
                self.create_subscription(Image, topic, on_image, 2,
                                         callback_group=ReentrantCallbackGroup())
                self.get_logger().info(f"Caméra simulée : images de {topic}")
            return self._sim_capture

    rclpy.init(args=args)
    node = SimArucoRelativePose()
    node.dist = np.zeros_like(node.dist)   # sténopé idéal (voir docstring)
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    time.sleep(0.1)


if __name__ == '__main__':
    main()
