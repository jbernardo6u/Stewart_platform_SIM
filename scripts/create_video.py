#!/usr/bin/env python3
"""
Animation d'un scénario (GIF), sans fenêtre
===========================================

Exécute un scénario de ``src.core.scenarios`` dans la simulation PyBullet en boucle
fermée et enregistre la vue 3D rendue hors écran (EGL si disponible) dans un GIF animé,
pour les rapports et présentations. Aucune dépendance vidéo externe (Pillow suffit).

Usage (depuis la racine) :
    python3 scripts/create_video.py                  # scénario « approach »
    python3 scripts/create_video.py sine --fps 20 --size 640 400 --view front
Sortie : output/videos/<scénario>.gif (non versionné)
"""

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from PIL import Image  # noqa: E402

from src.core import scenarios  # noqa: E402
from src.gui.dashboard_controller import DashboardController  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'output', 'videos')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('scenario', nargs='?', default='approach', choices=scenarios.scenario_names())
    parser.add_argument('--fps', type=int, default=20)
    parser.add_argument('--size', type=int, nargs=2, default=[640, 400], metavar=('W', 'H'))
    parser.add_argument('--view', default='isometric', choices=['isometric', 'front', 'side', 'top'])
    parser.add_argument('--output', help='chemin du GIF (défaut : output/videos/<scénario>.gif)')
    args = parser.parse_args()

    ctrl = DashboardController()
    ctrl.connect(offscreen=True)
    sim = ctrl.simulator
    sim.set_camera_view(args.view)
    sim.style_scene()
    report = ctrl.start_scenario(args.scenario)
    if not report['feasible']:
        print(f"Scénario irréalisable : {report['saturated_ratio'] * 100:.0f} % des points hors course")
        return 1

    frames = []
    while ctrl.run is not None:
        ctrl.tick(1.0 / args.fps)
        frames.append(Image.fromarray(sim.render_image(*args.size)))
    result = ctrl.last_run_report
    ctrl.disconnect()

    path = args.output or os.path.join(OUT_DIR, f'{args.scenario}.gif')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / args.fps), loop=0,
                   optimize=True)
    print(f"{len(frames)} images, {result['duration']:.1f} s, écart RMS {result['rms_mm']:.2f} mm "
          f"/ {result['rms_deg']:.3f}° -> {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
