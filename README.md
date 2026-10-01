# REM : jumeau numérique de la plateforme Stewart

Jumeau numérique d'une plateforme Stewart (hexapode 6-6 à vérins linéaires), actionneur principal du **projet REM** : système autonome d'attelage et de désattelage de remorque. La plateforme aligne précisément le véhicule tracteur sur la remorque.

Le dépôt couvre la modélisation géométrique, cinématique et dynamique, la simulation (PyBullet, et un jumeau Gazebo / ROS 2 Jazzy du démonstrateur réel), le contrôle, la visualisation et la validation simulation/réel.

![Stewart Platform](https://user-images.githubusercontent.com/110429424/236367485-5a0f2e46-17ea-44dc-a7d6-048d4344a79d.gif)

| Document | Rôle |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture cible en 6 niveaux, diagrammes Mermaid, état de chaque composant |
| [ROADMAP.md](ROADMAP.md) | Phases 0 à 8 et critères de sortie |
| [RESEARCH.md](RESEARCH.md) | Verrous scientifiques (traçabilité CIR) |
| [CLAUDE.md](CLAUDE.md) | Règles d'ingénierie pour les contributeurs et les agents |
| [CHANGELOG.md](CHANGELOG.md) | Historique des changements |
| [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md) | Prise en main : les 5 modes, le tableau de bord, les scénarios |
| [docs/experiments/](docs/experiments/README.md) | Fiches d'expérimentation (registre CIR) |
| [docs/decisions/](docs/decisions/) | Décisions d'architecture (ADR) |
| [docs/protocols/](docs/protocols/) | Protocoles de mesure (PROT-001 : inventaire du banc) |
| [docs/reports/2026-09-24_analyse_depot.md](docs/reports/2026-09-24_analyse_depot.md) | Diagnostic initial de l'existant (daté) |

## État du projet

| Niveau | État |
|---|---|
| 1 · Simulation | ✅ PyBullet en boucle fermée **validé : 0,28 mm / 0,044°** (EXP-004) ; ✅ **jumeau Gazebo du démonstrateur** : logiciel ROS 2 du banc exécuté sans modification, caméra embarquée rendue (EXP-009, [guide](docs/guides/GAZEBO_BANC_REM.md)) |
| 2 · Géométrie | ✅ Géométrie réelle identifiée dans le URDF (EXP-001) ; repères à formaliser |
| 3 · Cinématique | 🟡 IK **validée contre le URDF** (EXP-002) ; espace de travail limité par la course (EXP-007) ; **FK, jacobien et singularités** (EXP-008) |
| 4 · Dynamique | ⬜ À créer |
| 5 · Contrôle | 🟡 Scénarios à lois horaires d'ordre 5, vérification de la course, tableau de bord de pilotage ; limites vitesse/accélération à faire |
| 6 · Validation | 🟡 51 tests automatisés (27 unitaires, 24 de validation), CI GitHub ; banc physique disponible, aucune mesure réelle encore |

Prochaine étape : **inventaire du banc** ([PROT-001](docs/protocols/PROT-001-inventaire-banc.md)) et interface commune simulation/banc ([ADR-0002](docs/decisions/ADR-0002-interface-commune-simulation-banc.md)), en parallèle de la cinématique directe (Phase 2). Détail et priorités : [ROADMAP.md](ROADMAP.md#priorités-pour-finaliser-révisées-le-2026-09-30-banc-physique-disponible).

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
| 2026-09-30 | Simulateur des interfaces (`PyBulletSimulator`) passé sur le modèle en boucle fermée validé | [CHANGELOG.md](CHANGELOG.md) |
| 2026-09-30 | **Tableau de bord unique** (CustomTkinter, vue 3D intégrée, vérins, précision en direct, scénarios) ; lanceur ramené à 5 modes ; correction des longueurs affichées par les anciennes GUI (unités) ; CI GitHub | [QUICK_START](docs/guides/QUICK_START.md) |
| 2026-09-30 | **EXP-007** : la course des vérins limite z (−90/+111 mm), roulis, tangage (±26 à 36°) et lacet (±72°), mais pas x/y : la limite latérale viendra des cardans | [EXP-007](docs/experiments/EXP-007-espace-travail-course.md) |
| 2026-09-30 | Préparation du banc : protocole d'inventaire, interface commune simulation/banc proposée | [PROT-001](docs/protocols/PROT-001-inventaire-banc.md), [ADR-0002](docs/decisions/ADR-0002-interface-commune-simulation-banc.md) |

**Limites connues** :

- la pose neutre de l'IK correspond aux vérins en butée basse : tout mouvement se fait autour de la hauteur de travail (0,09 m) ;
- avec gravité, la simulation garde ~0,2 à 0,3 mm d'erreur, due à la souplesse des contraintes PyBullet ;
- la démo `ellipse` de `generate_demo_trajectory` (API historique) demande un lacet de 360°, irréalisable ; les scénarios de `src/core/scenarios.py` sont tous vérifiés ;
- la limite latérale réelle (débattement des cardans) est inconnue : les bornes du tableau de bord sont des bornes d'exploration (EXP-007) ;
- sous WSLg, la fermeture d'une fenêtre PyBullet se termine par un segfault (sans effet sur les résultats) ; le tableau de bord l'évite par un rendu hors écran.

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
├── scripts/         run_trajectory · run_validation · create_video · system_check · experiments/ (EXP)
├── examples/        exemples d'API
├── legacy/          code et fichiers historiques (non maintenus)
└── .github/         CI (tests à chaque push)
```

> Le code Python reste dans `src/` pendant la transition ([ADR-0001](docs/decisions/ADR-0001-conserver-package-src.md)). Les README de `models/` et `controllers/` indiquent où se trouve chaque implémentation.

## Installation

```bash
pip install -r requirements.txt       # exécution : numpy, matplotlib, pybullet, pyyaml, customtkinter, pillow
pip install -r requirements-dev.txt   # + pytest, jupyterlab (tests, notebook)
pip install -e .                      # optionnel
sudo apt install python3-tk           # GUI Tkinter, si absente
python3 scripts/system_check.py   # diagnostic de l'environnement
```

## Utilisation

Toutes les commandes se lancent depuis la racine du dépôt.

```bash
python3 run_simulation.py                  # menu : 5 modes (ou run_simulation.py 1 à 5)
python3 -m src.gui.dashboard               # 1. tableau de bord 3D (CustomTkinter)
python3 scripts/run_trajectory.py --save   # 2. scénarios en simulation, erreurs chiffrées
python3 scripts/experiments/exp007_workspace_stroke.py   # 3. espace de travail
python3 scripts/run_validation.py          # 4. tests + campagnes EXP-001/002/004/007
python3 scripts/system_check.py            # 5. diagnostic

python3 scripts/create_video.py approach   # GIF d'un scénario → output/videos/
python3 examples/basic_control.py          # exemple d'API : IK, faisabilité, simulation
python3 examples/trajectory_demo.py --type sine --simulation   # démo dans une fenêtre PyBullet
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
from src.core.config import load_config
from src.core.feasibility import check_trajectory
from src.core import scenarios

cfg = load_config()
t, translations, rotations = scenarios.get_scenario('approach')      # m et degrés, relatifs à la position de travail
report = check_trajectory(platform.kinematics, translations, rotations,
                          cfg['platform']['working_height'], cfg['platform']['actuator_stroke'])
report['feasible'], report['margin']                                 # dans la course ? marge aux butées (m)
```

Pilotage sans affichage (même logique que le tableau de bord) : `src.gui.dashboard_controller.DashboardController` (`connect`, `set_command`, `start_scenario`, `tick`).

Conventions actuelles : translations en mètres, rotations en **degrés**, `R = Rx·Ry·Rz`. Les longueurs renvoyées par `solve()` sont dans l'ordre des jambes 1 à 6 (Slider_13 à Slider_18 du URDF). N'utilisez jamais l'ancien ordre `[9, 2, 31, 45, 38, 24]` avec cette IK. Voir [ARCHITECTURE.md](ARCHITECTURE.md#niveau-2--géométrie).

## Configuration

`configurations/platform_config.yaml` : géométrie, limites, URDF, indices de joints/actionneurs, paramètres de simulation, de matériel et du tableau de bord. Lu par `src.core.config.load_config()` : hauteur de travail, course des vérins, chemin du URDF, bornes et critères du tableau de bord. Les constantes de `src/core/platform.py` restent la source pour l'API historique (migration en Phase 1).

## Tests

```bash
python3 -m pytest tests/unit_tests tests/validation_tests   # 51 tests, ~25 s, sans affichage (PyBullet DIRECT)
python3 scripts/run_validation.py                           # tests + toutes les campagnes, avec bilan
```

| Suite | Contenu |
|---|---|
| `unit_tests` (27) | IK paramétrique et à points identifiés, paramètres de `PhysicalStewartPlatform`, configuration, faisabilité, scénarios |
| `validation_tests` (24) | Axes des vérins (EXP-002) ; géométrie URDF (EXP-001) ; suivi de pose < 0,5 mm / 0,1° (EXP-004) ; `PyBulletSimulator` ; logique du tableau de bord et rendu hors écran |
| `integration_tests` | `test_physical_platform.py` : script manuel pour le banc (matériel requis) |

La CI GitHub (`.github/workflows/tests.yml`) lance `unit_tests` et `validation_tests` à chaque push.

## Expérimentations

Chaque résultat est tracé par une fiche dans [docs/experiments/](docs/experiments/README.md) (format CIR : contexte, verrou, hypothèse, méthodologie, résultats, analyse, conclusion).

```bash
python3 scripts/experiments/exp001_urdf_geometry.py          # EXP-001 → results/geometry/
python3 scripts/experiments/exp002_ik_vs_urdf.py             # EXP-002 → results/kinematics/
python3 scripts/experiments/exp004_closed_loop_tracking.py   # EXP-004 → results/experiments/
python3 scripts/experiments/exp007_workspace_stroke.py       # EXP-007 → results/kinematics/
```

Détails et limites connues : [tests/README.md](tests/README.md).

## Dépannage

- **Fenêtre PyBullet : segmentation fault à la fermeture** (WSLg, bogue PyBullet/OpenGL, même sans modèle chargé). Le tableau de bord n'ouvre pas de fenêtre PyBullet (rendu hors écran), il n'est donc pas concerné.
- Rendu 3D lent dans le tableau de bord : le greffon EGL n'a pas pu être chargé (statut « rendu logiciel ») ; réduire `gui.dashboard.render_size` dans la configuration.
- Guide détaillé : [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md).

## Contribuer

Suivre [CLAUDE.md](CLAUDE.md) : analyser → planifier → valider les impacts → implémenter → tester → documenter. Ne pas casser l'API existante, toujours ajouter des tests, créer une fiche `docs/experiments/EXP-XXX` pour tout résultat expérimental.

## Crédits

Basé sur [mlayek21/Stewart-Platform](https://github.com/mlayek21/Stewart-Platform) (URDF, IK, simulation PyBullet). Documentation d'origine : [docs/design/README_original.md](docs/design/README_original.md). Licence : [LICENSE](LICENSE).
