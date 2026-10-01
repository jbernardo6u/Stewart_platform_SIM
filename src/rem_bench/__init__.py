"""
Jumeau du démonstrateur REM (banc ROS 2 Jazzy, dépôt ABMI-software/Demonstrateur_REM)
====================================================================================

Python pur (NumPy, PyYAML) : aucune dépendance à ROS, Gazebo ni PyBullet, pour être
testé dans la CI de ce dépôt et importé par le paquet ROS 2 ``ros2_ws/src/rem_bench_sim``.

- :mod:`.geometry` : mécanisme physique du banc (attaches, longueurs, codeurs → pose) ;
- :mod:`.virtual_arduino` : émulation du firmware ``pilotage_feedback_mp.ino`` et liaison
  série virtuelle (pseudo-terminal) ;
- :mod:`.scene` : caméra embarquée, marqueur, IMU synthétique, poses des corps Gazebo ;
- :mod:`.sdf` : génération du monde Gazebo et des textures de marqueurs.

Paramètres : ``configurations/bench_rem.yaml``.
"""

import os

from ..core.config import PROJECT_ROOT, load_config

DEFAULT_BENCH_CONFIG = os.path.join(PROJECT_ROOT, 'configurations', 'bench_rem.yaml')


def load_bench_config(path=None):
    """Configuration du jumeau du banc (par défaut ``configurations/bench_rem.yaml``)."""
    return load_config(path or DEFAULT_BENCH_CONFIG)
