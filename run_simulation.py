#!/usr/bin/env python3
"""
Lanceur des simulations de la plateforme Stewart (jumeau numérique REM)
======================================================================

Cinq modes, chacun avec un but distinct :

1. Tableau de bord 3D   : pilotage interactif, vérins, écart de suivi, scénarios
2. Rapport trajectoires : scénarios exécutés sans affichage, écart consigne/mesure chiffré
3. Espace de travail    : débattements atteignables selon la course des vérins (EXP-007)
4. Validation           : tests automatisés et campagnes EXP-001/002/004/007
5. Diagnostic           : vérification de l'environnement

Usage :
    python3 run_simulation.py        # menu
    python3 run_simulation.py 1      # lance directement un mode
"""

import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

PY = sys.executable
MODES = [
    ("1", "Tableau de bord 3D", "pilotage interactif, vérins, suivi en direct, scénarios",
     [PY, "-m", "src.gui.dashboard"]),
    ("2", "Rapport trajectoires", "scénarios en simulation sans affichage, erreurs chiffrées",
     [PY, "scripts/run_trajectory.py", "--save"]),
    ("3", "Espace de travail", "débattements selon la course des vérins (EXP-007)",
     [PY, "scripts/experiments/exp007_workspace_stroke.py"]),
    ("4", "Validation", "tests automatisés et campagnes EXP-001/002/004/007",
     [PY, "scripts/run_validation.py"]),
    ("5", "Diagnostic", "vérification de l'environnement et des dépendances",
     [PY, "scripts/system_check.py"]),
]


def print_menu():
    print()
    print("=" * 72)
    print("  REM · Plateforme Stewart — jumeau numérique")
    print("=" * 72)
    for key, title, description, _ in MODES:
        print(f"  {key}. {title:22s} {description}")
    print("  q. Quitter")
    print("-" * 72)


def run_mode(key: str) -> int:
    for k, title, _, cmd in MODES:
        if k == key:
            print(f"\n>>> {title}\n", flush=True)
            return subprocess.run(cmd, cwd=project_root).returncode
    print(f"Choix inconnu : {key}")
    return 2


def main():
    if len(sys.argv) > 1:
        return run_mode(sys.argv[1])
    while True:
        print_menu()
        try:
            choice = input("Votre choix : ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 0
        if choice in ("q", "quit", ""):
            return 0
        run_mode(choice)


if __name__ == "__main__":
    sys.exit(main())
