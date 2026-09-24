#!/usr/bin/env python3
"""
EXP-004 : précision de suivi de la simulation PyBullet en boucle fermée
======================================================================

Pour le modèle paramétrique et pour la géométrie identifiée (from_urdf), avec et
sans gravité : consigne de pose autour de la hauteur de travail, puis mesure de la
pose de la plateforme par get_current_pose().

Usage (depuis la racine) : python3 scripts/experiments/exp004_closed_loop_tracking.py
Sortie : results/experiments/exp004_tracking.csv
"""

import csv
import os
import sys

import numpy as np
import pybullet as p

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from src.core.platform import (StewartPlatform, DEFAULT_ACTUATOR_INDICES,  # noqa: E402
                               DEFAULT_JOINT_INDICES, DEFAULT_WORKING_HEIGHT)

URDF = os.path.join(ROOT, 'simulation', 'urdf', 'Stewart.urdf')
OUT = os.path.join(ROOT, 'results', 'experiments', 'exp004_tracking.csv')
POSES = [('working', [0, 0, 0], [0, 0, 0]), ('x+10mm', [0.01, 0, 0], [0, 0, 0]),
         ('y+10mm', [0, 0.01, 0], [0, 0, 0]), ('z+10mm', [0, 0, 0.01], [0, 0, 0]),
         ('roll+5', [0, 0, 0], [5, 0, 0]), ('pitch+5', [0, 0, 0], [0, 5, 0]),
         ('yaw+5', [0, 0, 0], [0, 0, 5]), ('combined', [0.02, -0.015, 0.02], [4, -3, 8]),
         ('roll+10', [0, 0, 0], [10, 0, 0]), ('yaw+20', [0, 0, 0], [0, 0, 20])]
MODELS = {
    'parametric': lambda: StewartPlatform(URDF, DEFAULT_JOINT_INDICES, DEFAULT_ACTUATOR_INDICES, [0.2, 0.2, 12, 12]),
    'identified': lambda: StewartPlatform.from_urdf(URDF),
}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['model', 'gravity', 'pose', 'err_x_mm', 'err_y_mm', 'err_z_mm',
                    'err_roll_deg', 'err_pitch_deg', 'err_yaw_deg', 'max_pos_err_mm', 'max_rot_err_deg'])
        for name, make in MODELS.items():
            for gravity in (True, False):
                platform = make()
                platform.setup_environment(use_gui=False)
                if not gravity:
                    p.setGravity(0, 0, 0)
                platform.initialize_platform(verbose=False)
                platform.move_to_working_position(duration=1.0, realtime=False, settle_time=1.0)
                worst = [0.0, 0.0]
                for label, t, rot in POSES:
                    target = np.array(t, float) + [0, 0, DEFAULT_WORKING_HEIGHT]
                    platform.move_to_pose(target, rot, duration=1.0, realtime=False, settle_time=1.0)
                    pos, rpy = platform.get_current_pose()
                    e_t = (np.array(pos) - target) * 1000
                    e_r = np.array(rpy) - np.array(rot, float)
                    worst = [max(worst[0], np.abs(e_t).max()), max(worst[1], np.abs(e_r).max())]
                    w.writerow([name, gravity, label, *[f'{v:.4f}' for v in e_t], *[f'{v:.5f}' for v in e_r],
                                f'{np.abs(e_t).max():.4f}', f'{np.abs(e_r).max():.5f}'])
                platform.disconnect()
                print(f'{name:10s} gravity={gravity!s:5s} worst error: {worst[0]:.3f} mm / {worst[1]:.4f} deg')
    print(f'-> {OUT}')


if __name__ == '__main__':
    main()
