#!/usr/bin/env python3
"""
EXP-002 : validation de la cinématique inverse contre le modèle URDF
====================================================================

Compare trois configurations (IK + ordre des actionneurs) :
  A. IK historique (legacy/inv_kinematics.py) + ordre historique [9, 2, 31, 45, 38, 24]
  B. IK src + ordre historique (état avant correction)
  C. IK src + ordre jambes 1..6 [2, 31, 45, 38, 24, 9] (DEFAULT_ACTUATOR_INDICES)

Essai 1 (cinématique) : angle entre la direction de jambe prédite au neutre
et l'axe du joint prismatique URDF correspondant.
Essai 2 (dynamique, PyBullet) : pose mesurée du centre de la plateforme
(lien indicator1) après commande de petits déplacements élémentaires.

Usage (depuis la racine) : python3 scripts/experiments/exp002_ik_vs_urdf.py
Sorties : results/kinematics/exp002_leg_axes.csv, results/kinematics/exp002_dynamic.csv
"""

import csv
import os
import sys

import numpy as np
import pybullet as p

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'legacy'))

from inv_kinematics import inv_kinematics as LegacyIK  # noqa: E402
from src.core.kinematics import InverseKinematics  # noqa: E402
from src.core.platform import DEFAULT_ACTUATOR_INDICES, DEFAULT_JOINT_INDICES  # noqa: E402

URDF = os.path.join(ROOT, 'simulation', 'urdf', 'Stewart.urdf')
OUT_DIR = os.path.join(ROOT, 'results', 'kinematics')
PLATFORM_CENTRE_LINK = 21  # indicator1
HISTORICAL_ORDER = [9, 2, 31, 45, 38, 24]
GEOMETRY = (0.2, 0.2, 12, 12)

CONFIGS = {
    'A_legacyIK_historical': (lambda: LegacyIK(*GEOMETRY), HISTORICAL_ORDER),
    'B_srcIK_historical': (lambda: InverseKinematics(*GEOMETRY), HISTORICAL_ORDER),
    'C_srcIK_legs1to6': (lambda: InverseKinematics(*GEOMETRY), DEFAULT_ACTUATOR_INDICES),
}
POSES = [('x+10mm', [0.01, 0, 0], [0, 0, 0]), ('y+10mm', [0, 0.01, 0], [0, 0, 0]),
         ('z+10mm', [0, 0, 0.01], [0, 0, 0]), ('roll+5deg', [0, 0, 0], [5, 0, 0]),
         ('pitch+5deg', [0, 0, 0], [0, 5, 0]), ('yaw+5deg', [0, 0, 0], [0, 0, 5])]


def leg_directions(ik):
    """Directions unitaires des jambes au neutre, indépendamment de la convention B/P interne."""
    ik.solve(np.zeros(3), np.zeros(3))
    legs = ik.L - ik.B  # L = position des jambes dans le repère global (L = l + B)
    return (legs / np.linalg.norm(legs, axis=0)).T


def slider_axes(robot, order):
    axes = []
    for j in order:
        info = p.getJointInfo(robot, j)
        state = p.getLinkState(robot, j, computeForwardKinematics=1)
        axes.append(np.array(p.getMatrixFromQuaternion(state[5])).reshape(3, 3) @ np.array(info[13]))
    return np.array(axes)


def build_closed_loop():
    p.resetSimulation()
    p.setGravity(0, 0, -9.81)
    robot = p.loadURDF(URDF, useFixedBase=1, flags=p.URDF_USE_INERTIA_FROM_FILE)
    for a, b in DEFAULT_JOINT_INDICES:
        c = p.createConstraint(robot, a, robot, b, p.JOINT_FIXED, [0, 0, 0.1], [0, 0, 0], [0, 0, 0])
        p.changeConstraint(c, maxForce=1e20)
    for i in range(p.getNumJoints(robot)):
        p.setJointMotorControl2(robot, i, p.VELOCITY_CONTROL, force=0)
    return robot


def platform_pose(robot):
    s = p.getLinkState(robot, PLATFORM_CENTRE_LINK, computeForwardKinematics=1)
    return np.array(s[4]), np.array(p.getMatrixFromQuaternion(s[5])).reshape(3, 3)


def rpy_deg(R):
    """Inverse de R = Rx(a)·Ry(b)·Rz(c), convention des deux IK."""
    return np.degrees([np.arctan2(-R[1, 2], R[2, 2]), np.arcsin(R[0, 2]), np.arctan2(-R[0, 1], R[0, 0])])


def dynamic_trial(ik, order, t, rot, settle=300, steps=1500, force=250):
    robot = build_closed_loop()
    for _ in range(settle):
        p.setJointMotorControlArray(robot, order, p.POSITION_CONTROL, targetPositions=[0] * 6, forces=[force] * 6)
        p.stepSimulation()
    p0, R0 = platform_pose(robot)
    delta = ik.solve(np.array(t, float), np.array(rot, float)) - ik.solve(np.zeros(3), np.zeros(3))
    for _ in range(steps):
        p.setJointMotorControlArray(robot, order, p.POSITION_CONTROL, targetPositions=list(delta), forces=[force] * 6)
        p.stepSimulation()
    p1, R1 = platform_pose(robot)
    slider_err = max(abs(p.getJointState(robot, j)[0] - d) for j, d in zip(order, delta))
    return (p1 - p0) * 1000, rpy_deg(R1 @ R0.T), slider_err * 1000


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    p.connect(p.DIRECT)

    robot = p.loadURDF(URDF, useFixedBase=1)
    with open(os.path.join(OUT_DIR, 'exp002_leg_axes.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['config'] + [f'leg_slot{i}_deg' for i in range(6)] + ['max_deg'])
        for name, (make_ik, order) in CONFIGS.items():
            err = np.degrees(np.arccos(np.clip(np.abs(np.sum(leg_directions(make_ik()) * slider_axes(robot, order), axis=1)), 0, 1)))
            w.writerow([name] + [f'{e:.2f}' for e in err] + [f'{err.max():.2f}'])
            print(f'[axes] {name:24s} max {err.max():5.2f}°  {np.round(err, 2)}')

    with open(os.path.join(OUT_DIR, 'exp002_dynamic.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['config', 'pose', 'dx_mm', 'dy_mm', 'dz_mm', 'droll_deg', 'dpitch_deg', 'dyaw_deg', 'max_slider_err_mm'])
        for name, (make_ik, order) in CONFIGS.items():
            for label, t, rot in POSES:
                dp, de, se = dynamic_trial(make_ik(), order, t, rot)
                w.writerow([name, label] + [f'{v:.2f}' for v in (*dp, *de, se)])
                print(f'[dyn]  {name:24s} {label:10s} dpos(mm)={np.round(dp, 2)} drot(°)={np.round(de, 2)} slider_err={se:.2f} mm')
    p.disconnect()


if __name__ == '__main__':
    main()
