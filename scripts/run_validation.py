#!/usr/bin/env python3
"""
Campagnes de validation
=======================

Relance les tests automatisés (unitaires et de validation, critères chiffrés compris)
puis les scripts d'expérimentation, qui régénèrent leurs résultats dans ``results/``.
Un résultat versionné qui change apparaît ensuite dans ``git status``.

Usage (depuis la racine) : python3 scripts/run_validation.py [--tests-only]
"""

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STEPS = [
    ("Tests unitaires et de validation", [sys.executable, '-m', 'pytest', '-q',
                                          'tests/unit_tests', 'tests/validation_tests']),
    ("EXP-001 géométrie du URDF", [sys.executable, 'scripts/experiments/exp001_urdf_geometry.py']),
    ("EXP-002 IK contre URDF", [sys.executable, 'scripts/experiments/exp002_ik_vs_urdf.py']),
    ("EXP-004 suivi en boucle fermée", [sys.executable, 'scripts/experiments/exp004_closed_loop_tracking.py']),
    ("EXP-007 espace de travail (course)", [sys.executable, 'scripts/experiments/exp007_workspace_stroke.py']),
    ("EXP-008 cinématique directe", [sys.executable, 'scripts/experiments/exp008_forward_kinematics.py']),
    ("EXP-010 statique, banc couché", [sys.executable, 'scripts/experiments/exp010_statics_lying.py']),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--tests-only', action='store_true', help='uniquement les tests automatisés')
    args = parser.parse_args()
    steps = STEPS[:1] if args.tests_only else STEPS

    results = []
    for label, cmd in steps:
        print(f"\n=== {label}")
        start = time.time()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        lines = [l for l in proc.stdout.splitlines() if l.strip() and 'pybullet build time' not in l]
        print("\n".join(lines[-12:]))
        if proc.returncode != 0:
            print(proc.stderr[-2000:])
        results.append((label, proc.returncode == 0, time.time() - start))

    print("\n=== Bilan")
    for label, ok, duration in results:
        print(f"  {'OK   ' if ok else 'ÉCHEC'}  {label:40s} {duration:6.1f} s")
    changed = subprocess.run(['git', 'status', '--porcelain', 'results'], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
    print("\nRésultats versionnés : " + ("inchangés (reproductibles)" if not changed else f"modifiés\n{changed}"))
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == '__main__':
    sys.exit(main())
