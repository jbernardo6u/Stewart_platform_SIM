#!/usr/bin/env python3
"""
Exemple minimal de l'API : cinématique, faisabilité, simulation
===============================================================

1. Longueurs de vérins pour une pose (IK sur la géométrie identifiée dans le URDF).
2. Vérification de la course des vérins avant d'envoyer une consigne.
3. Mouvement simulé en boucle fermée et mesure de la pose atteinte.

Usage (depuis la racine) : python3 examples/basic_control.py
L'ancienne version (API ``start_simmulation`` de 2023) est dans ``legacy/examples/``.
"""

import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from src.core.config import load_config, project_path  # noqa: E402
from src.core.feasibility import actuator_positions, check_trajectory  # noqa: E402
from src.core.platform import StewartPlatform  # noqa: E402


def main():
    cfg = load_config()
    h = cfg['platform']['working_height']
    stroke = tuple(cfg['platform']['actuator_stroke'])
    platform = StewartPlatform.from_urdf(project_path(cfg['simulation']['urdf_path']))

    # 1. Pose relative à la position de travail : 20 mm en x, 10° de lacet
    translation, rotation = np.array([0.02, 0.0, 0.0]), np.array([0.0, 0.0, 10.0])
    q = actuator_positions(platform.kinematics, translation, rotation, h)
    print("Positions des vérins (mm) :", np.round(q * 1000, 1))

    # 2. Faisabilité : une pose atteignable et une qui ne l'est pas
    for label, t, r in [("x+20 mm, lacet 10°", translation, rotation), ("z+150 mm", [0, 0, 0.15], [0, 0, 0])]:
        report = check_trajectory(platform.kinematics, [t], [r], h, stroke)
        print(f"{label:20s} atteignable : {report['feasible']}  (marge {report['margin'] * 1000:+.1f} mm)")

    # 3. Simulation (PyBullet DIRECT, boucle fermée)
    platform.setup_environment(use_gui=False)
    platform.initialize_platform(verbose=False)
    platform.move_to_working_position(realtime=False, settle_time=0.5)
    target = translation + [0, 0, h]              # move_to_pose : repère de la pose neutre
    platform.move_to_pose(target, rotation, duration=1.0, realtime=False, settle_time=1.0)
    position, measured_rotation = platform.get_current_pose()
    error_mm = np.abs(np.array(position) - target).max() * 1000
    error_deg = np.abs(np.array(measured_rotation) - rotation).max()
    print(f"Pose mesurée : écart {error_mm:.2f} mm / {error_deg:.3f}°")
    platform.disconnect()


if __name__ == '__main__':
    main()
