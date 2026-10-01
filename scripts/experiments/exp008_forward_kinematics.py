#!/usr/bin/env python3
"""
EXP-008 : cinématique directe, jacobien et singularités
=======================================================

1. Aller-retour IK→FK sur des poses aléatoires de l'espace de travail exploré par le
   tableau de bord (géométrie identifiée) : erreur, itérations, temps de calcul.
2. Jacobien analytique contre différences finies.
3. FK appliquée aux positions **mesurées** des joints prismatiques dans PyBullet
   (comme le ferait le banc avec ses codeurs), comparée à la pose mesurée du corps
   de la plateforme.
4. Conditionnement du jacobien : en fonction du lacet (singularité attendue à ±90°),
   puis carte (roll, pitch) à plusieurs lacets.

Usage (depuis la racine) : python3 scripts/experiments/exp008_forward_kinematics.py
Sorties : results/kinematics/exp008_*.csv, results/kinematics/figures/exp008_conditioning.png
"""

import csv
import os
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from src.core.config import load_config, project_path  # noqa: E402
from src.core.forward_kinematics import (forward_kinematics, jacobian, leg_lengths,  # noqa: E402
                                         pose_from_actuator_positions, singularity_measures,
                                         solver_settings, _exp_so3, rotation_matrix)
from src.core.platform import StewartPlatform  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'results', 'kinematics')
SIM_POSES = [
    ("travail", [0, 0, 0], [0, 0, 0]),
    ("x+20mm", [0.02, 0, 0], [0, 0, 0]),
    ("y-20mm", [0, -0.02, 0], [0, 0, 0]),
    ("z+30mm", [0, 0, 0.03], [0, 0, 0]),
    ("roll+8", [0, 0, 0], [8, 0, 0]),
    ("pitch-8", [0, 0, 0], [0, -8, 0]),
    ("yaw+20", [0, 0, 0], [0, 0, 20]),
    ("combinee", [0.03, -0.02, 0.02], [5, -4, 12]),
]


def round_trip(ik, h, limits, settings, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    lo = np.array([limits[k][0] for k in ('x', 'y', 'z', 'roll', 'pitch', 'yaw')], float)
    hi = np.array([limits[k][1] for k in ('x', 'y', 'z', 'roll', 'pitch', 'yaw')], float)
    lo[:3] /= 1000
    hi[:3] /= 1000
    errs_t, errs_r, its, failures = [], [], [], 0
    start = time.perf_counter()
    for _ in range(n):
        pose = rng.uniform(lo, hi)
        t, r = pose[:3] + [0, 0, h], np.radians(pose[3:])
        res = forward_kinematics(ik, leg_lengths(ik, t, r), [0, 0, h], **settings)
        failures += not res.converged
        errs_t.append(np.abs(res.translation - t).max())
        errs_r.append(np.abs(res.rotation - r).max())
        its.append(res.iterations)
    per_call_ms = (time.perf_counter() - start) / n * 1000
    return dict(n=n, failures=failures, max_err_um=max(errs_t) * 1e6,
                max_err_urad=max(errs_r) * 1e6, max_iterations=max(its),
                mean_iterations=float(np.mean(its)), ms_per_call=per_call_ms)


def jacobian_check(ik, h, h_fd=1e-7):
    t, r = np.array([0.02, -0.01, h]), np.radians([5, -3, 10])
    J, R = jacobian(ik, t, r), rotation_matrix(r)
    from src.core.forward_kinematics import _legs
    Jfd = np.zeros((6, 6))
    for k in range(6):
        d = np.zeros(6)
        d[k] = h_fd
        lp = np.linalg.norm(_legs(ik, t + d[:3], _exp_so3(d[3:]) @ R)[0], axis=0)
        lm = np.linalg.norm(_legs(ik, t - d[:3], _exp_so3(-d[3:]) @ R)[0], axis=0)
        Jfd[:, k] = (lp - lm) / (2 * h_fd)
    return float(np.abs(J - Jfd).max())


def fk_on_simulation(urdf, h, settings, gravity=True):
    import pybullet as p
    platform = StewartPlatform.from_urdf(urdf)
    platform.setup_environment(use_gui=False)
    if not gravity:
        p.setGravity(0, 0, 0)
    platform.initialize_platform(verbose=False)
    platform.move_to_working_position(height=h, duration=1.0, realtime=False, settle_time=1.0)
    rows = []
    for label, t, rot in SIM_POSES:
        target = np.array(t, float) + [0, 0, h]
        platform.move_to_pose(target, rot, duration=1.0, realtime=False, settle_time=1.0)
        q = np.array([p.getJointState(platform.robot_id, j)[0] for j in platform.actuator_indices])
        pos, rpy = platform.get_current_pose()
        fk = pose_from_actuator_positions(platform.kinematics, q, h, **settings)
        rows.append(dict(pose=label, gravity=gravity,
                         fk_vs_measured_mm=float(np.abs(fk.translation + [0, 0, h] - pos).max() * 1000),
                         fk_vs_measured_deg=float(np.abs(fk.rotation_deg - rpy).max()),
                         measured_vs_target_mm=float(np.abs(np.array(pos) - target).max() * 1000),
                         converged=fk.converged, condition=fk.condition))
    platform.disconnect()
    return rows


def main():
    cfg = load_config()
    h = cfg['platform']['working_height']
    settings = solver_settings(cfg)
    urdf = project_path(cfg['simulation']['urdf_path'])
    ik = StewartPlatform.from_urdf(urdf).kinematics
    os.makedirs(os.path.join(OUT_DIR, 'figures'), exist_ok=True)

    rt = round_trip(ik, h, cfg['gui']['dashboard']['limits'], settings)
    print("Aller-retour IK→FK :", {k: round(v, 4) if isinstance(v, float) else v for k, v in rt.items()})
    fd = jacobian_check(ik, h)
    print(f"Jacobien vs différences finies : {fd:.2e}")
    with open(os.path.join(OUT_DIR, 'exp008_round_trip.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rt) + ['jacobian_fd_error'])
        w.writeheader()
        w.writerow({**rt, 'jacobian_fd_error': fd})

    sim_rows = fk_on_simulation(urdf, h, settings, True) + fk_on_simulation(urdf, h, settings, False)
    for r in sim_rows:
        print(f"  {r['pose']:9s} g={'oui' if r['gravity'] else 'non'}  FK/mesure "
              f"{r['fk_vs_measured_mm']:.4f} mm {r['fk_vs_measured_deg']:.4f}°  cond {r['condition']:.2f}")
    with open(os.path.join(OUT_DIR, 'exp008_fk_vs_pybullet.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(sim_rows[0]))
        w.writeheader()
        w.writerows(sim_rows)

    yaws = np.arange(-180, 181, 1.0)
    cond = [singularity_measures(ik, [0, 0, h], np.radians([0, 0, y])) for y in yaws]
    with open(os.path.join(OUT_DIR, 'exp008_conditioning_yaw.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['yaw_deg', 'condition', 'determinant'])
        for y, c in zip(yaws, cond):
            w.writerow([y, c['condition'], c['determinant']])
    lim = cfg['gui']['dashboard']['limits']
    in_range = [c['condition'] for y, c in zip(yaws, cond) if lim['yaw'][0] <= y <= lim['yaw'][1]]
    print(f"Conditionnement sur le lacet du tableau de bord {lim['yaw']} : max {max(in_range):.2f}")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(17, 4))
    axes[0].semilogy(yaws, [c['condition'] for c in cond])
    axes[0].axvspan(*lim['yaw'], color='tab:green', alpha=0.15, label='tableau de bord')
    axes[0].set(xlabel='lacet (°)', ylabel='conditionnement de J (adim.)',
                title='Position de travail, roll = pitch = 0')
    axes[0].legend()
    rr = np.linspace(lim['roll'][0], lim['roll'][1], 51)
    pp = np.linspace(lim['pitch'][0], lim['pitch'][1], 51)
    for ax, yaw in zip(axes[1:], (0, 45, 75)):
        grid = np.array([[singularity_measures(ik, [0, 0, h], np.radians([a, b, yaw]))['condition']
                          for a in rr] for b in pp])
        im = ax.pcolormesh(rr, pp, np.log10(grid), shading='auto', vmin=0.5, vmax=2.0)
        ax.set(xlabel='roll (°)', ylabel='pitch (°)', title=f'log10(cond), lacet = {yaw}°')
    fig.subplots_adjust(wspace=0.35)
    fig.colorbar(im, ax=axes[1:], shrink=0.9)
    out = os.path.join(OUT_DIR, 'figures', 'exp008_conditioning.png')
    fig.savefig(out, dpi=120, bbox_inches='tight')
    print("Figure :", os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
