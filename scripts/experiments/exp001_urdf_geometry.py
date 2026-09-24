#!/usr/bin/env python3
"""
EXP-001 : géométrie réelle du URDF comparée au modèle paramétrique (r, γ, h)
===========================================================================

Identifie les centres des cardans (intersection des axes) et les compare au
modèle paramétrique r_B = r_P = 0,2 m, γ_B = γ_P = 12°, h = 0,257547 m.

Usage (depuis la racine) : python3 scripts/experiments/exp001_urdf_geometry.py
Sortie : results/geometry/exp001_attachment_points.csv
"""

import csv
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from src.core.kinematics import InverseKinematics  # noqa: E402
from src.core.platform import DEFAULT_ACTUATOR_INDICES, DEFAULT_PLATFORM_LINK  # noqa: E402
from src.simulation.urdf_geometry import identify_urdf_geometry  # noqa: E402

URDF = os.path.join(ROOT, 'simulation', 'urdf', 'Stewart.urdf')
OUT = os.path.join(ROOT, 'results', 'geometry', 'exp001_attachment_points.csv')


def main():
    geo = identify_urdf_geometry(URDF, DEFAULT_ACTUATOR_INDICES, DEFAULT_PLATFORM_LINK)
    model = InverseKinematics(0.2, 0.2, 12, 12)
    P_model, B_model = model.calculate_attachment_points()
    B, P = geo['base_points'], geo['platform_points']

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['leg', 'side', 'x_mm', 'y_mm', 'z_mm', 'radius_mm', 'angle_deg',
                    'model_x_mm', 'model_y_mm', 'model_z_mm', 'deviation_mm'])
        for side, X, M in (('base', B, B_model), ('platform', P, P_model)):
            for i in range(6):
                dev = np.linalg.norm(X[:, i] - M[:, i]) * 1000
                w.writerow([i + 1, side, *[f'{v * 1000:.3f}' for v in X[:, i]],
                            f'{np.linalg.norm(X[:2, i]) * 1000:.3f}',
                            f'{np.degrees(np.arctan2(X[1, i], X[0, i])) % 360:.3f}',
                            *[f'{v * 1000:.3f}' for v in M[:, i]], f'{dev:.3f}'])
                print(f'{side:8s} leg{i + 1}: deviation from parametric model {dev:.3f} mm')

    gamma_B = (np.degrees(np.arctan2(B[1, 0], B[0, 0])) - np.degrees(np.arctan2(B[1, 1], B[0, 1]))) / 2
    print(f"max gap between U-joint axes : {geo['max_axis_gap'] * 1000:.4f} mm")
    print(f"mean radius base/platform    : {np.linalg.norm(B[:2], axis=0).mean():.5f} / "
          f"{np.linalg.norm(P[:2], axis=0).mean():.5f} m (model 0.2)")
    print(f"gamma_B                      : {gamma_B:.3f} deg (model 12)")
    print(f"home position                : {np.round(geo['home_position'], 6)} m (model [0 0 0.257547])")
    print(f"platform z spread            : {np.ptp(P[2]) * 1000:.3f} mm")
    print(f"actuator stroke              : {geo['stroke'][0]} m")
    print(f'-> {OUT}')


if __name__ == '__main__':
    main()
