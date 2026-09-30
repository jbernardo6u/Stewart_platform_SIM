#!/usr/bin/env python3
"""
Rapport de trajectoires (sans affichage)
========================================

Pour chaque scénario de ``src.core.scenarios`` : vérification de la course des vérins,
puis exécution dans la simulation PyBullet en boucle fermée (mode DIRECT, plus rapide
que le temps réel) et mesure de l'écart consigne/mesure.

Usage (depuis la racine) :
    python3 scripts/run_trajectory.py                  # tous les scénarios
    python3 scripts/run_trajectory.py approach sine    # scénarios choisis
    python3 scripts/run_trajectory.py --list
    python3 scripts/run_trajectory.py --save           # CSV et figures dans output/trajectories/
"""

import argparse
import csv
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from src.core import scenarios  # noqa: E402
from src.gui.dashboard_controller import AXES, DashboardController  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'output', 'trajectories')   # sorties de démonstration, non versionnées
DT = 1 / 60


def run(ctrl: DashboardController, name: str):
    """Exécute un scénario ; renvoie (rapport de faisabilité, journal (N, 13), bilan)."""
    report = ctrl.start_scenario(name)
    if not report['feasible']:
        return report, None, None
    log = []
    while ctrl.run is not None:
        ctrl.tick(DT)
        log.append([ctrl.sim_time, *ctrl.command, *ctrl.measured])
    return report, np.array(log), ctrl.last_run_report


def save(name, log):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f'{name}.csv')
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t_s'] + [f'cmd_{a}' for a in AXES] + [f'meas_{a}' for a in AXES])
        w.writerows(np.round(log, 4).tolist())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 6), sharex=True)
    for i, (ax, axis) in enumerate(zip(axes.flat, AXES)):
        ax.plot(log[:, 0], log[:, 1 + i], label='consigne', lw=2, alpha=0.6)
        ax.plot(log[:, 0], log[:, 7 + i], label='mesure', lw=1, ls='--')
        ax.set_title(f"{axis} ({'mm' if i < 3 else '°'})")
        ax.grid(alpha=0.3)
    axes[0, 0].legend()
    for ax in axes[1]:
        ax.set_xlabel('temps (s)')
    fig.suptitle(f'{scenarios.SCENARIOS[name][0]} : consigne et pose mesurée (simulation PyBullet)')
    fig.tight_layout()
    png = os.path.join(OUT_DIR, f'{name}.png')
    fig.savefig(png, dpi=100)
    plt.close(fig)
    return path, png


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('names', nargs='*', help='scénarios (défaut : tous)')
    parser.add_argument('--list', action='store_true', help='lister les scénarios')
    parser.add_argument('--save', action='store_true', help='écrire CSV et figures dans output/trajectories/')
    parser.add_argument('--no-gravity', action='store_true')
    args = parser.parse_args()

    if args.list:
        for key, (label, _) in scenarios.SCENARIOS.items():
            print(f'{key:12s} {label}')
        return 0
    names = args.names or scenarios.scenario_names()
    unknown = [n for n in names if n not in scenarios.SCENARIOS]
    if unknown:
        parser.error(f"scénario(s) inconnu(s) : {', '.join(unknown)}")

    ctrl = DashboardController()
    ctrl.connect(offscreen=False)
    ctrl.set_gravity(not args.no_gravity)
    print(f"\n{'scénario':12s} {'durée':>6s} {'course':>11s} {'RMS mm':>7s} {'max mm':>7s} {'RMS °':>7s} {'max °':>7s}")
    status = 0
    for name in names:
        ctrl.reset()
        report, log, result = run(ctrl, name)
        span = ctrl.stroke[1] - ctrl.stroke[0]
        usage = (f"{(report['min'].min() - ctrl.stroke[0]) / span * 100:3.0f}-"
                 f"{(report['max'].max() - ctrl.stroke[0]) / span * 100:3.0f} %")
        if log is None:
            print(f"{name:12s} {'':>6s} {usage:>11s}  IRRÉALISABLE ({report['saturated_ratio'] * 100:.0f} % hors course)")
            status = 1
            continue
        print(f"{name:12s} {result['duration']:5.1f}s {usage:>11s} {result['rms_mm']:7.2f} {result['max_mm']:7.2f} "
              f"{result['rms_deg']:7.3f} {result['max_deg']:7.3f}")
        if args.save:
            for path in save(name, log):
                print(f'  -> {os.path.relpath(path, ROOT)}')
    ctrl.disconnect()
    return status


if __name__ == '__main__':
    sys.exit(main())
