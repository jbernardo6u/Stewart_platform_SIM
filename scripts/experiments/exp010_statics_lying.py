#!/usr/bin/env python3
"""
EXP-010 : efforts statiques des vérins, plateforme du banc couchée ou debout
===========================================================================

Géométrie du démonstrateur REM (configurations/bench_rem.yaml). Efforts ``f = −J⁻ᵀ·w`` dus
au poids de la charge embarquée (src/core/statics.py) :

1. à la pose home, debout et couchée, selon la masse et le centre de gravité ;
   en position couchée, pire cas sur l'angle de montage autour de la normale ;
2. sur tout l'espace de travail (poses tirées uniformément dans la course des codeurs) ;
3. sensibilité aux dimensions (rayon de base, hauteur home), à la pose home.

Masse, centre de gravité, angle de montage et effort disponible ne sont pas mesurés : les
plages viennent de la section ``statics`` de bench_rem.yaml.

Usage (depuis la racine) : python3 scripts/experiments/exp010_statics_lying.py
Sorties : results/dynamics/exp010_*.csv, results/dynamics/figures/exp010_statics.png
"""

import copy
import csv
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from src.core.forward_kinematics import singularity_measures  # noqa: E402
from src.core.statics import STANDARD_GRAVITY, gravity_actuator_forces, gravity_in_base_lying  # noqa: E402
from src.rem_bench import load_bench_config  # noqa: E402
from src.rem_bench.geometry import BenchGeometry  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'results', 'dynamics')
UPRIGHT = np.array([0.0, 0.0, -STANDARD_GRAVITY])


def max_force(ik, t, r, mass, com_offset, gravity):
    return float(np.abs(gravity_actuator_forces(ik, t, r, mass, [0, 0, com_offset], gravity)).max())


def worst_lying(ik, t, r, mass, com_offset, angles):
    """Pire cas sur l'angle de montage : (effort max, angle)."""
    forces = [max_force(ik, t, r, mass, com_offset, gravity_in_base_lying(a)) for a in angles]
    i = int(np.argmax(forces))
    return forces[i], float(angles[i])


def leg_tilt_deg(geo, t, R):
    base, top = geo.legs_world(t, R)
    legs = top - base
    return np.degrees(np.arccos(legs[2] / np.linalg.norm(legs, axis=0)))


def main():
    cfg = load_bench_config()
    st = cfg['statics']
    geo = BenchGeometry(cfg)
    ik = geo.ik
    angles = np.arange(0, 360, st['mount_angle_step_deg'])
    limit = st['actuator_force_limit_n']
    os.makedirs(os.path.join(OUT_DIR, 'figures'), exist_ok=True)

    # Pose « home » physique (codeurs à 0) et mi-course (codeurs à 5 cm)
    poses = {name: geo.pose_from_encoders(np.full(6, q)) for name, q in (('home', 0.0), ('mi-course', 5.0))}
    rows = []
    for pose_name, fk in poses.items():
        tilt = float(leg_tilt_deg(geo, fk.translation, fk.rotation_matrix).mean())
        for mass in st['payload_mass_kg']:
            for c in st['centre_of_mass_offsets_m']:
                up = max_force(ik, fk.translation, fk.rotation, mass, c, UPRIGHT)
                lying, angle = worst_lying(ik, fk.translation, fk.rotation, mass, c, angles)
                rows.append(dict(pose=pose_name, leg_tilt_deg=round(tilt, 2), mass_kg=mass, com_offset_m=c,
                                 upright_max_n=round(up, 3), lying_worst_max_n=round(lying, 3),
                                 lying_worst_mount_deg=angle, ratio=round(lying / up, 2),
                                 lying_over_limit=lying > limit))
    with open(os.path.join(OUT_DIR, 'exp010_home.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("Pose | masse | CdG | debout max | couché pire cas (angle) | rapport")
    for r in rows:
        print(f"{r['pose']:9s} {r['mass_kg']:.1f} kg  {r['com_offset_m'] * 100:3.0f} cm  "
              f"{r['upright_max_n']:6.2f} N  {r['lying_worst_max_n']:6.2f} N ({r['lying_worst_mount_deg']:.0f}°)  ×{r['ratio']}")

    # Espace de travail de compensation : poses tirées autour de la mi-course, gardées si les
    # 6 codeurs restent dans la course ; masse max, pire montage, pour chaque CdG
    rng = np.random.default_rng(0)
    mass = max(st['payload_mass_kg'])
    c = st['centre_of_mass_offsets_m'][0]
    rg = st['workspace_ranges']
    lo = np.array([rg['x_m'][0], rg['y_m'][0], rg['z_m'][0], rg['roll_deg'][0], rg['pitch_deg'][0], rg['yaw_deg'][0]])
    hi = np.array([rg['x_m'][1], rg['y_m'][1], rg['z_m'][1], rg['roll_deg'][1], rg['pitch_deg'][1], rg['yaw_deg'][1]])
    centre = poses['mi-course'].translation
    ws, rejected = [], 0
    for p in rng.uniform(lo, hi, size=(st['workspace_samples'], 6)):
        t, r = centre + p[:3], np.radians(p[3:])
        q = geo.encoders_cm(t, r)
        if np.any(q < geo.stroke[0] * 100) or np.any(q > geo.stroke[1] * 100):
            rejected += 1
            continue
        lying, angle = worst_lying(ik, t, r, mass, c, angles[::3])
        ws.append(dict(x_m=p[0], y_m=p[1], z_m=p[2], roll_deg=p[3], pitch_deg=p[4], yaw_deg=p[5],
                       lying_worst_max_n=lying, upright_max_n=max_force(ik, t, r, mass, c, UPRIGHT),
                       condition=singularity_measures(ik, t, r)['condition']))
    print(f"Espace de compensation : {len(ws)} poses dans la course, {rejected} hors course")
    lying_ws = np.array([w['lying_worst_max_n'] for w in ws])
    upright_ws = np.array([w['upright_max_n'] for w in ws])
    with open(os.path.join(OUT_DIR, 'exp010_workspace.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(ws[0]))
        w.writeheader()
        w.writerows(ws)
    print(f"Espace de compensation ({len(ws)} poses, {mass} kg, CdG {c * 100:.0f} cm) : couché pire cas médiane "
          f"{np.median(lying_ws):.1f} N, 95 % {np.percentile(lying_ws, 95):.1f} N, max {lying_ws.max():.1f} N ; "
          f"debout médiane {np.median(upright_ws):.1f} N, max {upright_ws.max():.1f} N ; "
          f"poses au-delà de {limit:.0f} N : {np.mean(lying_ws > limit) * 100:.1f} % ; "
          f"conditionnement max {max(w['condition'] for w in ws):.1f}")
    print(f"Masse admissible (couché, pire montage) pour {limit:.0f} N : home {limit / rows[4]['lying_worst_max_n']:.2f} kg, "
          f"mi-course {limit / rows[12]['lying_worst_max_n']:.2f} kg, 95 % de l'espace {limit / np.percentile(lying_ws, 95) * mass:.2f} kg")

    # Sensibilité aux dimensions, à la pose home de l'IK, 1 kg, pire CdG, pire montage
    sweep = []
    for rb in st['design_sweep']['radius_base_m']:
        for h in st['design_sweep']['home_height_m']:
            c2 = copy.deepcopy(cfg)
            c2['geometry']['radius_base'] = rb
            c2['geometry']['home_position'] = [0.0, 0.0, h]
            g2 = BenchGeometry(c2)
            lying, _ = worst_lying(g2.ik, [0, 0, 0], [0, 0, 0], mass, c, angles)
            sweep.append(dict(radius_base_m=rb, home_height_m=h, lying_worst_max_n=round(lying, 2),
                              leg_tilt_deg=round(float(leg_tilt_deg(g2, [0, 0, 0], np.eye(3)).mean()), 1)))
    with open(os.path.join(OUT_DIR, 'exp010_design_sweep.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(sweep[0]))
        w.writeheader()
        w.writerows(sweep)
    print("Sensibilité (couché, pire cas, home) : rayon base × hauteur -> effort max (inclinaison des jambes)")
    for s in sweep:
        print(f"  rb {s['radius_base_m'] * 100:4.1f} cm  h {s['home_height_m'] * 100:4.1f} cm  "
              f"{s['lying_worst_max_n']:6.2f} N  ({s['leg_tilt_deg']:.0f}°)")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
    ax = axes[0]
    home = [r for r in rows if r['pose'] == 'home']
    for mass, color in zip(st['payload_mass_kg'], ('tab:blue', 'tab:red')):
        sel = [r for r in home if r['mass_kg'] == mass]
        x = [r['com_offset_m'] * 100 for r in sel]
        ax.plot(x, [r['lying_worst_max_n'] for r in sel], 'o-', color=color, label=f'couchée, {mass} kg (pire montage)')
        ax.plot(x, [r['upright_max_n'] for r in sel], 's--', color=color, alpha=0.6, label=f'debout, {mass} kg')
    ax.axhline(limit, color='k', ls=':', label=f'{limit:.0f} N (hypothèse de conception)')
    ax.set(xlabel='centre de gravité devant la plaque (cm)', ylabel='effort max dans un vérin (N)',
           title='Pose home du banc')
    ax.legend(fontsize=8)
    ax = axes[1]
    ax.hist(lying_ws, bins=40, color='tab:red', alpha=0.8, label='couchée (pire montage)')
    ax.hist(upright_ws, bins=40, color='tab:blue', alpha=0.8, label='debout')
    ax.axvline(limit, color='k', ls=':')
    ax.set(xlabel='effort max dans un vérin (N)', ylabel='nombre de poses',
           title=f'Espace de compensation, {mass} kg, CdG à {c * 100:.0f} cm')
    ax.legend(fontsize=8)
    ax = axes[2]
    rbs, hs = st['design_sweep']['radius_base_m'], st['design_sweep']['home_height_m']
    grid = np.array([[next(s['lying_worst_max_n'] for s in sweep if s['radius_base_m'] == rb and s['home_height_m'] == h)
                      for rb in rbs] for h in hs])
    im = ax.pcolormesh(np.array(rbs) * 100, np.array(hs) * 100, grid, shading='nearest', cmap='viridis')
    for i, h in enumerate(hs):
        for j, rb in enumerate(rbs):
            ax.text(rb * 100, h * 100, f'{grid[i, j]:.0f}', ha='center', va='center', color='w', fontsize=8)
    ax.plot(cfg['geometry']['radius_base'] * 100, cfg['geometry']['home_position'][2] * 100, 'r*', ms=14, label='banc actuel')
    ax.set(xlabel='rayon de la base (cm)', ylabel='hauteur home (cm)',
           title=f'Couchée, home : effort max (N), {mass} kg, CdG {c * 100:.0f} cm')
    ax.legend(fontsize=8, loc='upper right')
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    out = os.path.join(OUT_DIR, 'figures', 'exp010_statics.png')
    fig.savefig(out, dpi=120)
    print("Figure :", os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
