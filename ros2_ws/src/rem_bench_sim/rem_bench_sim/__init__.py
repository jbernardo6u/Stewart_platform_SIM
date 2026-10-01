"""
Jumeau Gazebo du démonstrateur REM (ROS 2 Jazzy, Gazebo Harmonic)
================================================================

Remplace le matériel du banc **à ses interfaces**, pour que les nœuds de
``stewart_control`` (dépôt ABMI-software/Demonstrateur_REM) tournent sans modification :

- ``virtual_hardware`` : Arduino virtuel sur pseudo-terminal (protocole série du
  firmware), FK des codeurs simulés, poses des corps Gazebo ;
- ``sim_aruco`` : ``aruco_node`` du banc, alimenté par la caméra rendue par Gazebo ;
- ``sim_imu`` : ``imu_node`` du banc, alimenté par un MPU-9250 simulé.

Aucune logique métier ici : modèles et émulation sont dans ``src.rem_bench`` du dépôt
Stewart-Platform, ajouté au chemin Python par :func:`ensure_stewart_platform_on_path`.
"""

import os
import sys


def stewart_platform_root() -> str:
    """Racine du dépôt Stewart-Platform (``STEWART_PLATFORM_ROOT``, sinon déduite des sources)."""
    env = os.environ.get('STEWART_PLATFORM_ROOT')
    if env:
        return os.path.abspath(env)
    # ros2_ws/src/rem_bench_sim/rem_bench_sim/__init__.py (installation --symlink-install)
    here = os.path.realpath(__file__)
    return os.path.abspath(os.path.join(os.path.dirname(here), '..', '..', '..', '..'))


def ensure_stewart_platform_on_path() -> str:
    root = stewart_platform_root()
    if not os.path.isfile(os.path.join(root, 'src', 'rem_bench', '__init__.py')):
        raise RuntimeError(
            f"Dépôt Stewart-Platform introuvable ({root}). Construire avec --symlink-install "
            "ou définir STEWART_PLATFORM_ROOT.")
    if root not in sys.path:
        sys.path.insert(0, root)
    return root
