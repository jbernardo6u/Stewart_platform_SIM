# REM : jumeau numérique de la plateforme Stewart

Jumeau numérique d'une plateforme Stewart (hexapode 6-6 à vérins linéaires), actionneur principal du **projet REM** : système autonome d'attelage et de désattelage de remorque. La plateforme aligne précisément le véhicule tracteur sur la remorque.

Le dépôt couvre la modélisation géométrique, cinématique et dynamique, la simulation (PyBullet aujourd'hui, Gazebo/ROS2 prévus), le contrôle, la visualisation et la validation simulation/réel.

![Stewart Platform](https://user-images.githubusercontent.com/110429424/236367485-5a0f2e46-17ea-44dc-a7d6-048d4344a79d.gif)

| Document | Rôle |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture cible en 6 niveaux, diagrammes Mermaid, état de chaque composant |
| [ROADMAP.md](ROADMAP.md) | Phases 0 à 8 et critères de sortie |
| [RESEARCH.md](RESEARCH.md) | Verrous scientifiques (traçabilité CIR) |
| [CLAUDE.md](CLAUDE.md) | Règles d'ingénierie pour les contributeurs et les agents |
| [CHANGELOG.md](CHANGELOG.md) | Historique des changements |
| [docs/reports/2026-09-24_analyse_depot.md](docs/reports/2026-09-24_analyse_depot.md) | Diagnostic de l'existant et dette technique |

## État du projet

| Niveau | État |
|---|---|
| 1 · Simulation | 🟡 PyBullet + URDF opérationnels ; Gazebo/ROS2 à créer |
| 2 · Géométrie | 🟡 Modèle paramétrique ; repères à formaliser |
| 3 · Cinématique | 🟡 IK implémentée (⚠️ anomalie A1 à arbitrer) ; FK et jacobien à créer |
| 4 · Dynamique | ⬜ À créer |
| 5 · Contrôle | 🟡 Trajectoires géométriques, commande en position basique |
| 6 · Validation | ⬜ Gabarits prêts, aucune donnée |

## Structure

```
.
├── README.md  CLAUDE.md  ARCHITECTURE.md  ROADMAP.md  CHANGELOG.md  RESEARCH.md
├── docs/            design · experiments (CIR) · protocols · decisions (ADR) · validation · reports · guides
├── simulation/      urdf (Stewart.urdf) · meshes (51 STL) · gazebo · worlds · launch
├── models/          geometry (CAO) · kinematics (notebook) · dynamics · calibration · identification
├── controllers/     inverse_kinematics · forward_kinematics · trajectory_generation · motion_control · servo_control
├── ros2_ws/         src · launch
├── src/             code Python actif (package `src` : core, gui, hardware, simulation)
├── configurations/  platform_config.yaml
├── datasets/        mesures brutes
├── results/         geometry · kinematics · dynamics · experiments
├── tests/           unit_tests · integration_tests · validation_tests
├── scripts/         lanceurs et outils
├── examples/        exemples d'API
└── legacy/          code et fichiers historiques (non maintenus)
```

> Le code Python reste dans `src/` pendant la transition ([ADR-0001](docs/decisions/ADR-0001-conserver-package-src.md)). Les README de `models/` et `controllers/` indiquent où se trouve chaque implémentation.

## Installation

```bash
pip install -r requirements.txt   # numpy, matplotlib, pybullet (+ pyyaml pour la configuration)
pip install -e .                  # optionnel
python3 scripts/system_check.py   # diagnostic de l'environnement
```

## Utilisation

Toutes les commandes se lancent depuis la racine du dépôt.

```bash
python3 run_simulation.py                  # menu principal
python3 scripts/launcher.py                # lanceur graphique (Tk)

python3 -m src.gui.advanced_gui            # GUI avancée (Matplotlib), recommandée
python3 -m src.gui.simple_gui              # GUI simple (calculs seulement)
python3 -m src.gui.pybullet_gui            # GUI + simulation PyBullet
python3 scripts/create_web_viz.py          # génère stewart_visualization.html

python3 examples/trajectory_demo.py --type ellipse
python3 examples/trajectory_demo.py --type spiral --simulation
python3 examples/hardware_integration.py --test
```

Test de chargement du URDF seul : `cd simulation/urdf && python3 hello_bullet.py`.

## API

```python
from src.core.kinematics import InverseKinematics

ik = InverseKinematics(radius_base=0.2, radius_platform=0.2, gamma_base=12, gamma_platform=12)
leg_lengths = ik.solve(translation=[0.01, 0, 0], rotation=[0, 0, 15])  # m, degrés → longueurs (m)
```

```python
from src.core.platform import StewartPlatform

platform = StewartPlatform("simulation/urdf/Stewart.urdf",
                           joint_indices=[(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)],
                           actuator_indices=[9, 2, 31, 45, 38, 24],
                           design_variables=[0.2, 0.2, 12, 12])
platform.setup_environment(use_gui=True)
platform.initialize_platform()
platform.move_to_pose(translation=[0, 0, 0.01], rotation=[5, 0, 0])
```

```python
from src.core.trajectory import generate_demo_trajectory
translations, rotations = generate_demo_trajectory('mixed', n_points=50)
```

Conventions actuelles : translations en mètres, rotations en **degrés**, `R = Rx·Ry·Rz`. Voir [ARCHITECTURE.md](ARCHITECTURE.md#niveau-2--géométrie).

## Configuration

`configurations/platform_config.yaml` : géométrie, limites, URDF, indices de joints/actionneurs, paramètres de simulation et de matériel.
Note : ce fichier n'est pas encore lu par le code (Phase 1).

## Tests

```bash
python3 -m pytest tests/unit_tests
```

Détails et limites connues : [tests/README.md](tests/README.md).

## Dépannage

- **PyBullet GUI plante (segmentation fault / core dump)**, fréquent sous WSL ou sans serveur X : utilisez `python3 -m src.gui.advanced_gui` (Matplotlib) ou le mode DIRECT.
- Guides détaillés : [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md), [docs/guides/GUIDE_UTILISATION.md](docs/guides/GUIDE_UTILISATION.md).

## Contribuer

Suivre [CLAUDE.md](CLAUDE.md) : analyser → planifier → valider les impacts → implémenter → tester → documenter. Ne pas casser l'API existante, toujours ajouter des tests, créer une fiche `docs/experiments/EXP-XXX` pour tout résultat expérimental.

## Crédits

Basé sur [mlayek21/Stewart-Platform](https://github.com/mlayek21/Stewart-Platform) (URDF, IK, simulation PyBullet). Documentation d'origine : [docs/design/README_original.md](docs/design/README_original.md). Licence : [LICENSE](LICENSE).
