#!/usr/bin/env python3
"""
EXP-007 : espace de travail limité par la course des vérins
===========================================================

Géométrie identifiée (from_urdf), autour de la hauteur de travail :
- débattement maximal de chaque degré de liberté pris seul (recherche par dichotomie) ;
- débattement de x et y lorsque le lacet vaut ±10° (cas d'un désalignement d'attelage) ;
- carte (x, y) atteignable pour plusieurs hauteurs ;
- inclinaison maximale des jambes aux extrémités (indicateur du débattement des cardans).

Seule la course des vérins est prise en compte (ni rotules, ni singularités, ni efforts).

Usage (depuis la racine) : python3 scripts/experiments/exp007_workspace_stroke.py
Sorties : results/kinematics/exp007_dof_ranges.csv, results/kinematics/figures/exp007_xy_maps.png
"""

import csv
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from src.core.config import load_config, project_path  # noqa: E402
from src.core.feasibility import actuator_positions, leg_tilt_deg  # noqa: E402
from src.core.platform import StewartPlatform  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'results', 'kinematics')
DOFS = ['x', 'y', 'z', 'roll', 'pitch', 'yaw']
UNITS = ['mm', 'mm', 'mm', 'deg', 'deg', 'deg']
SEARCH_MAX = [0.2, 0.2, 0.2, 45.0, 45.0, 90.0]   # bornes de recherche (m, deg)


def reachable(ik, pose, h, stroke):
    q = actuator_positions(ik, pose[:3], pose[3:], h)
    return bool(np.all((q >= stroke[0]) & (q <= stroke[1])))


def max_along(ik, direction, base, h, stroke, limit, tol=1e-6):
    """Plus grand s tel que base + s·direction reste dans la course (dichotomie)."""
    lo, hi = 0.0, limit
    if not reachable(ik, base, h, stroke):
        return 0.0
    if reachable(ik, base + hi * direction, h, stroke):
        return hi
    while hi - lo > tol * max(1.0, limit):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if reachable(ik, base + mid * direction, h, stroke) else (lo, mid)
    return lo


def dof_ranges(ik, h, stroke, base=np.zeros(6)):
    rows = []
    for i, name in enumerate(DOFS):
        d = np.zeros(6)
        d[i] = 1.0
        plus = max_along(ik, d, base, h, stroke, SEARCH_MAX[i])
        minus = max_along(ik, -d, base, h, stroke, SEARCH_MAX[i])
        scale = 1000.0 if i < 3 else 1.0
        tilt = max(leg_tilt_deg(ik, p[:3], p[3:], h).max() for p in (base + plus * d, base - minus * d))
        capped = plus >= SEARCH_MAX[i] or minus >= SEARCH_MAX[i]
        rows.append((name, -minus * scale, plus * scale, UNITS[i], tilt, capped))
    return rows


def main():
    cfg = load_config()
    h = cfg['platform']['working_height']
    stroke = tuple(cfg['platform']['actuator_stroke'])
    ik = StewartPlatform.from_urdf(project_path(cfg['simulation']['urdf_path'])).kinematics
    os.makedirs(OUT_DIR, exist_ok=True)

    table = [('working', *r) for r in dof_ranges(ik, h, stroke)]
    for yaw in (-10.0, 10.0):
        base = np.array([0, 0, 0, 0, 0, yaw])
        table += [(f'yaw{yaw:+.0f}', *r) for r in dof_ranges(ik, h, stroke, base)[:2]]

    path = os.path.join(OUT_DIR, 'exp007_dof_ranges.csv')
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['case', 'dof', 'min', 'max', 'unit', 'max_leg_tilt_deg', 'search_capped'])
        for case, dof, lo, hi, unit, tilt, capped in table:
            w.writerow([case, dof, f'{lo:.2f}', f'{hi:.2f}', unit, f'{tilt:.1f}', capped])
            note = '  (borne de recherche atteinte : course non limitante)' if capped else ''
            print(f'{case:8s} {dof:5s} [{lo:8.2f} ; {hi:8.2f}] {unit:3s} inclinaison max {tilt:4.1f} deg{note}')
    print(f'inclinaison des jambes à la position de travail : {leg_tilt_deg(ik, [0, 0, 0], [0, 0, 0], h).max():.1f} deg')
    print(f'-> {path}')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    grid = np.linspace(-0.15, 0.15, 121)
    heights = [-0.06, -0.03, 0.0, 0.03, 0.06]
    fig, axes = plt.subplots(1, len(heights), figsize=(4 * len(heights), 4.2), sharey=True)
    for ax, dz in zip(axes, heights):
        ok = np.array([[reachable(ik, np.array([x, y, dz, 0, 0, 0]), h, stroke) for x in grid] for y in grid])
        ax.contourf(grid * 1000, grid * 1000, ok, levels=[-0.5, 0.5, 1.5], colors=['#f2f2f2', '#4c78a8'])
        ax.set_title(f'z = {dz * 1000:+.0f} mm')
        ax.set_xlabel('x (mm)')
        ax.set_aspect('equal')
        ax.grid(alpha=0.3)
    axes[0].set_ylabel('y (mm)')
    fig.suptitle('EXP-007 : positions (x, y) atteignables, orientation nulle, autour de la hauteur de travail')
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    png = os.path.join(OUT_DIR, 'figures', 'exp007_xy_maps.png')
    fig.savefig(png, dpi=110)
    print(f'-> {png}')


if __name__ == '__main__':
    main()
