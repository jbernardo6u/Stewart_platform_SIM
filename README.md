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
| [docs/experiments/](docs/experiments/README.md) | Fiches d'expérimentation (registre CIR) |

## État du projet

| Niveau | État |
|---|---|
| 1 · Simulation | ✅ PyBullet en boucle fermée **validé : 0,28 mm / 0,044°** (EXP-004) ; Gazebo/ROS2 à créer |
| 2 · Géométrie | ✅ Géométrie réelle identifiée dans le URDF (EXP-001) ; repères à formaliser |
| 3 · Cinématique | 🟡 IK **validée contre le URDF** (EXP-002) ; FK et jacobien à créer |
| 4 · Dynamique | ⬜ À créer |
| 5 · Contrôle | 🟡 Trajectoires géométriques, commande en position basique |
| 6 · Validation | 🟡 28 tests automatisés (16 unitaires, 12 de validation modèle/URDF/simulation) ; aucune mesure réelle |

Phases en cours : **1 (géométrie)**, **2 (cinématique)** et **4 (simulation)**, déjà bien avancées. Détail : [ROADMAP.md](ROADMAP.md).

## Avancement

| Date | Réalisation | Référence |
|---|---|---|
| 2026-09-24 | Analyse complète de l'existant : 3 générations de code, 9 anomalies (A1 à A9), doublons, composants morts | [rapport d'analyse](docs/reports/2026-09-24_analyse_depot.md) |
| 2026-09-24 | Restructuration du dépôt en jumeau numérique (simulation / modèles / contrôle / validation / docs), sans rupture d'API | [rapport de restructuration](docs/reports/2026-09-24_restructuration.md), [ADR-0001](docs/decisions/ADR-0001-conserver-package-src.md) |
| 2026-09-24 | Architecture cible, roadmap en 8 phases, verrous scientifiques, gabarit d'expérimentation CIR | [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [RESEARCH.md](RESEARCH.md) |
| 2026-09-24 | **EXP-002** : l'IK `src` est la bonne (écart de 0,4° avec les vérins du URDF). Correction de l'ordre des actionneurs (`[2, 31, 45, 38, 24, 9]`) : l'ancien ordre envoyait à chaque vérin la consigne d'une autre jambe | [EXP-002](docs/experiments/EXP-002-validation-ik-urdf.md) |
| 2026-09-24 | Dépendances réduites aux 4 paquets réellement utilisés | [CHANGELOG.md](CHANGELOG.md) |
| 2026-09-24 | **EXP-001** : le URDF est un mécanisme 6-UPU exact ; points d'attache réels identifiés (r = 0,19958 m, γ = 12,295°, h = 0,2535 m), écart de 0,8 à 1,6 mm au modèle paramétrique | [EXP-001](docs/experiments/EXP-001-geometrie-urdf.md) |
| 2026-09-24 | **EXP-004** : simulation en boucle fermée débloquée. Deux causes : pose neutre en butée basse des vérins, et limites articulaires [0 ; 2π] parasites de l'export CAO. Suivi de pose : **0,28 mm / 0,044°** avec gravité, **8 µm** sans | [EXP-004](docs/experiments/EXP-004-simulation-boucle-fermee.md) |

**Limites connues** :

- la pose neutre de l'IK correspond aux vérins en butée basse : tout mouvement se fait autour de la hauteur de travail (0,09 m) ;
- avec gravité, la simulation garde ~0,2 à 0,3 mm d'erreur, due à la souplesse des contraintes PyBullet ;
- la démo `ellipse` du générateur de trajectoires demande un lacet de 360°, irréalisable ;
- `PyBulletSimulator` (GUI PyBullet) n'a pas encore la fermeture de boucle.

## Structure

```
.
├── README.md  CLAUDE.md  ARCHITECTURE.md  ROADMAP.md  CHANGELOG.md  RESEARCH.md
├── requirements.txt  requirements-dev.txt  setup.py  run_simulation.py
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
├── scripts/         lanceurs, outils, experiments/ (scripts reproductibles des EXP)
├── examples/        exemples d'API
└── legacy/          code et fichiers historiques (non maintenus)
```

> Le code Python reste dans `src/` pendant la transition ([ADR-0001](docs/decisions/ADR-0001-conserver-package-src.md)). Les README de `models/` et `controllers/` indiquent où se trouve chaque implémentation.

## Installation

```bash
pip install -r requirements.txt       # exécution : numpy, matplotlib, pybullet, pyyaml
pip install -r requirements-dev.txt   # + pytest, jupyterlab (tests, notebook)
pip install -e .                      # optionnel
sudo apt install python3-tk           # GUI Tkinter, si absente
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
from src.core.platform import StewartPlatform, DEFAULT_WORKING_HEIGHT

platform = StewartPlatform.from_urdf("simulation/urdf/Stewart.urdf")  # IK sur la géométrie identifiée
platform.setup_environment(use_gui=True)
platform.initialize_platform()           # base fixe, boucles fermées, limites recentrées
platform.move_to_working_position()      # vérins à mi-course (la pose neutre est en butée basse)

platform.move_to_pose(translation=[0.01, 0, DEFAULT_WORKING_HEIGHT], rotation=[5, 0, 0])
position, rotation = platform.get_current_pose()   # pose mesurée, même repère que la consigne
```

Le constructeur historique reste disponible (modèle paramétrique, précision ~1 mm) :
`StewartPlatform(urdf, DEFAULT_JOINT_INDICES, DEFAULT_ACTUATOR_INDICES, [0.2, 0.2, 12, 12])`.
Options de mouvement : `move_to_pose(..., realtime=False, settle_time=1.0)` pour calculer sans attendre (tests, batch).

```python
from src.core.trajectory import generate_demo_trajectory
translations, rotations = generate_demo_trajectory('mixed', n_points=50)
```

Conventions actuelles : translations en mètres, rotations en **degrés**, `R = Rx·Ry·Rz`. Les longueurs renvoyées par `solve()` sont dans l'ordre des jambes 1 à 6 (Slider_13 à Slider_18 du URDF). N'utilisez jamais l'ancien ordre `[9, 2, 31, 45, 38, 24]` avec cette IK. Voir [ARCHITECTURE.md](ARCHITECTURE.md#niveau-2--géométrie).

## Configuration

`configurations/platform_config.yaml` : géométrie, limites, URDF, indices de joints/actionneurs, paramètres de simulation et de matériel.
Note : ce fichier n'est pas encore lu par le code (Phase 1).

## Tests

```bash
python3 -m pytest tests/unit_tests tests/validation_tests   # 28 tests, ~15 s, sans affichage (PyBullet DIRECT)
```

| Suite | Contenu |
|---|---|
| `unit_tests` (16) | IK paramétrique et à points identifiés, paramètres de `PhysicalStewartPlatform` |
| `validation_tests` (12) | Axes des vérins vs jambes du modèle (EXP-002) ; géométrie URDF (EXP-001) ; suivi de pose en boucle fermée < 0,5 mm / 0,1° (EXP-004) |
| `integration_tests` | Scripts hérités, manuels (PyBullet GUI, anciens imports) |

## Expérimentations

Chaque résultat est tracé par une fiche dans [docs/experiments/](docs/experiments/README.md) (format CIR : contexte, verrou, hypothèse, méthodologie, résultats, analyse, conclusion).

```bash
python3 scripts/experiments/exp001_urdf_geometry.py          # EXP-001 → results/geometry/
python3 scripts/experiments/exp002_ik_vs_urdf.py             # EXP-002 → results/kinematics/
python3 scripts/experiments/exp004_closed_loop_tracking.py   # EXP-004 → results/experiments/
```

Détails et limites connues : [tests/README.md](tests/README.md).

## Dépannage

- **PyBullet GUI plante (segmentation fault / core dump)**, fréquent sous WSL ou sans serveur X : utilisez `python3 -m src.gui.advanced_gui` (Matplotlib) ou le mode DIRECT.
- Guides détaillés : [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md), [docs/guides/GUIDE_UTILISATION.md](docs/guides/GUIDE_UTILISATION.md).

## Contribuer

Suivre [CLAUDE.md](CLAUDE.md) : analyser → planifier → valider les impacts → implémenter → tester → documenter. Ne pas casser l'API existante, toujours ajouter des tests, créer une fiche `docs/experiments/EXP-XXX` pour tout résultat expérimental.

## Crédits

Basé sur [mlayek21/Stewart-Platform](https://github.com/mlayek21/Stewart-Platform) (URDF, IK, simulation PyBullet). Documentation d'origine : [docs/design/README_original.md](docs/design/README_original.md). Licence : [LICENSE](LICENSE).
