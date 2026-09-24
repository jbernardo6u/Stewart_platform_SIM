# Rapport d'analyse du dépôt : Étape 1 (état initial)

- **Date** : 2026-09-24
- **Périmètre** : dépôt `Stewart_platform_SIM` (fork de `mlayek21/Stewart-Platform`), branche `master`, commit `7d14aaf` + modifications non commitées
- **Méthode** : lecture intégrale du code Python, de la configuration et de la documentation ; comparaison des doublons avec `diff` ; exécution de la suite de tests ; chargement du URDF dans PyBullet (mode DIRECT) ; comparaison numérique de l'ancienne et de la nouvelle cinématique inverse.
- **Règle** : ce rapport décrit l'état **avant** restructuration. Il n'a entraîné aucune modification de code.

---

## 1. Architecture actuelle

Le dépôt superpose **trois générations** de code :

| Génération | Emplacement | État |
|---|---|---|
| G0 : upstream (mlayek21, 2023) | fichiers racine commités : `StewartPlatform.py`, `inv_kinematics.py`, `main.py`, `Stewart/` | Supprimés de la racine dans l'arbre de travail, copiés dans `legacy/` |
| G1 : prototypes GUI (juillet 2025) | `legacy/stewart_gui_*.py`, `legacy/main_*.py`, `legacy/physical_stewart.py` | Non commités, conservés comme archive |
| G2 : package `src/` (juillet 2025) | `src/{core,gui,hardware,simulation,utils}` | Non commité ; c'est le code « actif » |

Architecture G2 (package Python `src`) :

```
src/core        cinématique inverse, plateforme PyBullet, trajectoires
src/simulation  PyBulletSimulator, MatplotlibVisualizer
src/gui         4 GUI Tkinter (base, simple, avancée, PyBullet)
src/hardware    MotorController (stub), PhysicalStewartPlatform, config
src/utils       vide
```

Points d'entrée : `run_simulation.py` (menu texte), `scripts/launcher.py` (lanceur Tk), `scripts/gui_launcher.py`, `scripts/quick_simulation.py`, `scripts/simulation_manager.py`, soit 5 lanceurs qui se recouvrent.

**Il n'y a ni ROS2, ni Gazebo, ni modèle dynamique** : la simulation repose entièrement sur PyBullet.

## 2. Arborescence initiale (hors `.git`, 228 fichiers, 48 Mo)

```
./
├── README.md (modifié)  README_original.md  GUIDE_UTILISATION.md  QUICK_START.md
├── PROJECT_STRUCTURE.md  RESTRUCTURING_COMPLETION.md  SIMULATION_ENHANCEMENT.md  SIMULATION_IMPROVEMENTS.md
├── LICENSE  requirements.txt (modifié)  setup.py  setup_project.py  .gitignore  .gitattributes
├── __init__.py (vide)  run_simulation.py  create_web_viz.py  stewart_visualization.html
├── Link_graph.txt  Stewart.zip (3,3 Mo)  Stewart_CAD.f3d (14 Mo)  .DS_Store
├── __pycache__/ (bytecode, en partie commité)
├── assets/
│   ├── config/platform_config.yaml
│   └── models/{Stewart.urdf, hello_bullet.py, meshes/*.stl (51)}
├── Stewart/{Stewart.urdf, hello_bullet.py, meshes/*.stl (51)}   ← doublon exact de assets/models
├── Files/{analysis.ipynb, output*.png (7), StewartPlatformDocument.pdf, URDF_LINK.png, Stewart1 v2.png, *.svg}
├── Simulation/{Full_simulation.mp4, simulation{1,2,3}.mp4}
├── docs/ (vide)   output/ (vide)
├── src/{core,gui,gui/widgets,hardware,simulation,utils}/
├── legacy/ (16 scripts)
├── examples/{basic_control,trajectory_demo,hardware_integration}.py
├── scripts/{launcher,gui_launcher,quick_simulation,simulation_manager,system_check,create_video,migrate_imports}.py
└── tests/{test_kinematics,test_no_gui,test_physical_platform,test_pybullet_gui}.py
```

## 3. Composants existants

| Composant | Fichier | Rôle |
|---|---|---|
| `InverseKinematics` | `src/core/kinematics.py` | IK 6-6 : points d'attache, matrices de rotation, longueurs des vérins |
| `StewartPlatform` | `src/core/platform.py` | Connexion PyBullet, chargement URDF, commande des vérins prismatiques |
| Générateurs de trajectoires | `src/core/trajectory.py` | Ellipse, spirale, sinus, huit, séquence de test, `TrajectoryGenerator` |
| `PyBulletSimulator` | `src/simulation/pybullet_sim.py` | Simulateur PyBullet orienté GUI (caméra, enregistrement, forces externes) |
| `MatplotlibVisualizer` | `src/simulation/matplotlib_viz.py` | Tracés temps réel et analyse de trajectoire |
| GUI Tk | `src/gui/*.py` | `BaseStewartGUI` (abstraite), Simple, Avancée, PyBullet |
| `MotorController` | `src/hardware/motor_controller.py` | **Stub** : écrit sur stdout, aucune E/S réelle |
| `PhysicalStewartPlatform` | `src/hardware/physical_platform.py` | IK + `MotorController` |
| Modèle URDF | `assets/models/Stewart.urdf` | 51 liens, 50 joints (29 révolutes, 6 prismatiques, 14 fixes, 1 continu) |
| CAO | `Stewart_CAD.f3d` | Source Fusion 360 du URDF |
| Notebook | `Files/analysis.ipynb` | Dérivation de l'IK 6-6 (17 cellules) |

## 4. Fonctions implémentées

- **Cinématique inverse** : complète (translation + roulis/tangage/lacet, convention `Rx·Ry·Rz`).
- **Cinématique directe** : **absente**.
- **Jacobien, singularités, espace de travail** : absents (`plot_workspace_analysis` ne fait qu'afficher des données fournies).
- **Dynamique** : absente (seules les masses/inerties du URDF sont exploitées implicitement par PyBullet).
- **Trajectoires** : génération géométrique (pas de profil temporel vitesse/accélération, pas de contrôle de limites).
- **Commande** : interpolation linéaire des consignes de vérins + `POSITION_CONTROL` PyBullet ; P simple côté matériel (stub).
- **Visualisation** : PyBullet GUI, Matplotlib, export HTML/Three.js (`create_web_viz.py`), enregistrement MP4.

## 5. Technologies

Python 3.8–3.11 (testé en 3.10.12), NumPy, Matplotlib, PyBullet, Tkinter, PyYAML (config), Jupyter (notebook), Fusion 360 (CAO), URDF.

## 6. Dépendances

`requirements.txt` est un **gel d'environnement Jupyter/conda** (87 lignes : jupyterlab, twine, keyring, tornado…), sans rapport avec le besoin réel. Les dépendances réellement importées sont `numpy`, `matplotlib`, `pybullet` (non épinglées) et `pyyaml` (**absente** du fichier). La modification locale a retiré les chemins `file:///…conda-bld` (installables nulle part), ce qui est une bonne correction.

## 7. Scripts de lancement

`run_simulation.py`, `scripts/launcher.py`, `scripts/gui_launcher.py`, `scripts/quick_simulation.py`, `scripts/simulation_manager.py`, `scripts/create_video.py`, `scripts/system_check.py`, `create_web_viz.py`, `setup_project.py`, et `setup.py` (entrées console `stewart-gui`, `stewart-test`, `stewart-demo`).

## 8. Modèles physiques

- URDF exporté de Fusion 360 : base de 13,76 kg, masses et inerties par lien, limites articulaires ±0,785 rad, maillages STL à l'échelle 0,001.
- Chaîne ouverte (arbre URDF) + **fermeture de boucle par 5 contraintes `JOINT_FIXED`** créées à l'exécution (`joint_indices`), et une 6e jambe fermée par l'arbre lui-même (`Link_graph.txt`).
- Paramètres géométriques : `r_B = r_P = 0,2 m`, `γ_B = γ_P = 12°`, hauteur neutre `0,257547 m`.

## 9. Modèles dynamiques

**Aucun modèle dynamique analytique** (Newton-Euler, Lagrange, efforts dans les jambes). La dynamique n'existe qu'à travers le moteur physique PyBullet.

## 10–13. ROS2 : nodes, services, actions, topics

**Aucun.** Aucun `package.xml`, `CMakeLists.txt`, `rclpy`, fichier launch ROS, `.msg/.srv/.action` ni monde Gazebo.

## 14. Configuration de simulation

`assets/config/platform_config.yaml` : géométrie, limites, chemins URDF, indices de joints/actionneurs, gravité, pas de temps 1/240 s, paramètres matériels, GUI, logging, trajectoires.
**Ce fichier n'est lu par aucun code** : toutes les valeurs sont recopiées en dur dans les scripts.

## 15. Jeux de données

Aucun jeu de données de mesure. Seules sorties existantes : 7 figures PNG, 4 vidéos MP4 et une page HTML générée.

## 16. Tests existants

| Fichier | Résultat |
|---|---|
| `tests/test_kinematics.py` (unittest, 11 tests) | 10 réussis, **1 échec** : `test_solve_neutral_position` attend ‖home_pos‖ = 0,2575 alors que la jambe vaut 0,2857 (l'attente ignore le décalage horizontal base/plateforme) |
| `tests/test_no_gui.py` | **Erreur d'import** (`from StewartPlatform import …`, module supprimé de la racine) |
| `tests/test_physical_platform.py` | **Erreur d'import** (`physical_stewart`) |
| `tests/test_pybullet_gui.py` | Ouvre une fenêtre PyBullet GUI : **core dump** en environnement sans écran (WSL) |

Aucune intégration continue.

## 17. Documentation existante

`README.md` (réécrit, français), `README_original.md` (théorie upstream, anglais), `GUIDE_UTILISATION.md`, `QUICK_START.md`, `PROJECT_STRUCTURE.md`, `RESTRUCTURING_COMPLETION.md`, `SIMULATION_ENHANCEMENT.md`, `SIMULATION_IMPROVEMENTS.md`, `Files/StewartPlatformDocument.pdf`, notebook. Les docstrings sont bonnes dans `src/core`.

---

## Dette technique et anomalies

### A. Anomalies fonctionnelles (bloquantes pour un jumeau numérique)

| # | Constat | Emplacement | Impact |
|---|---|---|---|
| A1 | **L'IK de `src` n'est pas équivalente à l'IK d'origine.** L'ancienne `solve()` inverse `B`/`P` (`self.B, self.P = self.frame()` alors que `frame()` renvoie `(P, B)`), ce qui compensait l'ordre des arguments de l'appelant. La réécriture a supprimé l'inversion. Mesuré : mêmes longueurs au neutre, mais écart jusqu'à **42 mm** et ordre des jambes permuté pour un lacet de 15° | `legacy/inv_kinematics.py:94` vs `src/core/kinematics.py` | Les indices d'actionneurs `[9, 2, 31, 45, 38, 24]` ont été calés sur l'ancienne IK : la simulation G2 commande probablement les mauvais vérins |
| A2 | `PhysicalStewartPlatform` appelle `InverseKinematics(r_P, r_B, γ_P, γ_B)` alors que la signature est `(r_B, r_P, γ_B, γ_P)` | `src/hardware/physical_platform.py:37` | Rayons et angles inversés (invisible tant que base = plateforme) |
| A3 | `StewartPlatform.setup_constraints()` est vide (`pass`) et `loadURDF` n'utilise pas `useFixedBase` : **les boucles fermées ne sont pas créées**, contrairement à l'original | `src/core/platform.py:134,143-148` | Le mécanisme simulé n'est pas une plateforme parallèle |
| A4 | Longueur initiale en dur `0.173205` alors que l'IK donne 0,2857 au neutre : le premier `move_to_pose` produit un saut de ~112 mm | `src/core/platform.py:64` | Commande incohérente |
| A5 | `get_current_pose()` / `get_platform_state()` renvoient la pose de la **base**, pas celle de la plateforme mobile | `src/core/platform.py:269`, `src/simulation/pybullet_sim.py:285` | Aucune mesure de pose exploitable pour la validation |
| A6 | Commentaire `R = Rz·Ry·Rx` alors que le code calcule `Rx·Ry·Rz` ; docstring de `calculate()` en « mm et radians » alors que `solve()` attend m et degrés | `src/core/kinematics.py:182,229` | Risque d'erreur d'unités et de convention |
| A7 | `TrajectoryGenerator.generate_spiral()` passe ses arguments dans le mauvais ordre : `TypeError` à l'appel | `src/core/trajectory.py:317` | Méthode inutilisable |
| A8 | Limites de `TrajectoryGenerator` en mm (±50) alors que la config est en m (±0,02) | `src/core/trajectory.py:301` | Incohérence d'unités |
| A9 | `MotorController.move_to_position()` suppose que la cible est atteinte instantanément, sans lecture codeur | `src/hardware/motor_controller.py:79` | La boucle matérielle n'est pas réelle |

### B. Doublons

- `Stewart/` et `assets/models/` : **identiques octet pour octet** (seul le `.DS_Store` diffère) ; `Stewart.zip` en contient une 3e copie (+ `__MACOSX`).
- `legacy/motor_controller.py` = `src/hardware/motor_controller.py` ; `legacy/hardware_config.py` = `src/hardware/config.py` (identiques) ; `legacy/physical_stewart.py` ≈ `src/hardware/physical_platform.py` (imports seulement).
- 6 variantes de GUI dans `legacy/` + 4 dans `src/gui`.
- 5 lanceurs avec des menus qui se recouvrent.
- 2 wrappers PyBullet concurrents : `src/core/platform.py::StewartPlatform` et `src/simulation/pybullet_sim.py::PyBulletSimulator`.
- 4 documents de « restructuration/amélioration » qui décrivent la même opération.

### C. Fichiers obsolètes

`legacy/*` (remplacés par `src/`), `__pycache__/` commités, `.DS_Store`, `stewart_visualization.html` (généré), `scripts/migrate_imports.py` (migration one-shot déjà faite), `setup_project.py::update_paths()` (crée des liens symboliques vers l'ancienne arborescence), `__init__.py` racine vide.

### D. Composants non utilisés ou cassés

- `platform_config.yaml` : jamais chargé.
- `src/utils`, `src/gui/widgets` : vides.
- `setup.py` : entrée `stewart-test=scripts.run_tests:main` vers un module inexistant ; `package_data` sous un package `stewart_platform` inexistant.
- `examples/basic_control.py` : `ImportError` (`draw_3d_spiral`, `generate_elliptical_points` n'existent pas dans `src.core.trajectory`).
- `PyBulletSimulator.apply_external_force`, `get_contact_info` : jamais appelés.

### E. Documentation manquante

Pas de description des repères (base, plateforme, monde), des conventions d'angles ni des unités ; pas de justification des indices de joints ; pas de protocole expérimental ; pas de contexte REM (attelage de remorque) ; pas de traçabilité CIR ; pas de changelog.

### F. Incohérences architecturales

- La logique métier (`src/core/platform.py`) dépend directement de PyBullet : impossible de tester la cinématique sans moteur physique et impossible de brancher un autre simulateur (Gazebo/ROS2).
- La couche GUI importe la couche simulation, et la simulation connaît la GUI (paramètres `use_gui`) : pas de séparation modèle, contrôle et vue.
- Pas de source unique de vérité pour les paramètres géométriques (YAML, `home_pos` en dur, valeurs répétées dans chaque script).
- Mélange d'unités (m/mm, degrés/radians) selon les modules.
- Code de production, prototypes et sorties générées mélangés à la racine.
