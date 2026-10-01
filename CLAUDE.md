# CLAUDE.md

Instructions pour les agents (Claude Code) et les contributeurs travaillant sur ce dépôt.

## Contexte

Projet REM : système autonome d'attelage et de désattelage de remorque.

La plateforme Stewart (hexapode 6-6 à vérins linéaires) est l'actionneur principal. Elle assure l'alignement précis entre le véhicule tracteur et la remorque. Ce dépôt contient son **jumeau numérique** : modèles géométrique, cinématique et dynamique, simulation, contrôle et validation contre le réel.

## Périmètre (ADR-0004)

- **Ce dépôt** : la plateforme de Stewart **seule** (modèles, PyBullet, Gazebo de la MP seule, essais sur la MP imprimée en 3D).
- **Banc d'attelage complet** (Stewart + rail d'approche, caméra, IMU) : dépôt de référence [ABMI-software/Demonstrateur_REM](https://github.com/ABMI-software/Demonstrateur_REM). Les développements du banc et de son jumeau Gazebo s'y font. Ici, `src/rem_bench` et `ros2_ws/src/rem_bench_sim` sont un **prototype** figé, conservé pour la migration, sauf correction.
- État et suite : `docs/reports/2026-10-01_perimetre_et_suite.md`.

## Objectifs scientifiques

- caractérisation géométrique
- caractérisation dynamique
- étude de stabilité
- étude de précision
- étude énergétique
- génération de trajectoires
- validation expérimentale

Le détail des verrous et des hypothèses se trouve dans [RESEARCH.md](RESEARCH.md), le plan de travail dans [ROADMAP.md](ROADMAP.md) et l'architecture dans [ARCHITECTURE.md](ARCHITECTURE.md).

## Règles d'ingénierie

Avant toute modification :

1. analyser l'existant
2. proposer un plan
3. valider les impacts
4. implémenter
5. tester
6. documenter

Ne jamais casser les API existantes.

Toujours ajouter des tests.

Toujours documenter les nouvelles fonctionnalités.

### Règles complémentaires

- **API publique à préserver** : `src.InverseKinematics`, `src.StewartPlatform`, `src.PhysicalStewartPlatform`, `src.core.kinematics.inv_kinematics` (alias), les signatures de `InverseKinematics.solve(translation, rotation)` et les `main()` des modules `src/gui/*`. Pour déplacer du code, laisser un réexport dans `src/` (voir `docs/decisions/ADR-0001-conserver-package-src.md`).
- **Unités** : SI en interne (m, rad, kg, N, s). L'API historique `solve()` prend des **degrés** : ne pas la modifier, ajouter plutôt une nouvelle fonction en radians.
- **Paramètres** : les valeurs géométriques et de simulation viennent de `configurations/platform_config.yaml`. Ne pas en ajouter de nouvelles en dur.
- **Dépendances de couches** : `models` → rien ; `controllers` → `models` ; `simulation`/`ros2_ws`/GUI → `controllers`, `models`. Jamais l'inverse.
- **Expérimentations** : toute campagne produisant un résultat reçoit une fiche `docs/experiments/EXP-XXX-*.md` (gabarit : `docs/experiments/TEMPLATE.md`) pour la traçabilité CIR.
- **Décisions structurantes** : un ADR dans `docs/decisions/` (ADR-0002, interface commune simulation/banc, est **proposée** : la valider avant de coder `BenchPlatform`).
- **Banc physique** : toute mesure suit un protocole de `docs/protocols/` (PROT-001 : inventaire) ; données brutes dans `datasets/`, immuables. Aucune consigne n'est envoyée au banc sans passer par `check_trajectory`.
- **Changelog** : chaque changement notable est ajouté dans [CHANGELOG.md](CHANGELOG.md) (section `[Non publié]`).
- **Ne rien supprimer sans justification** : archiver dans `legacy/` et le consigner dans le changelog.

## Commandes utiles

```bash
pip install -r requirements-dev.txt                   # dépendances + pytest + jupyterlab
python3 -m pytest tests/unit_tests tests/validation_tests   # tests sans GUI (PyBullet en mode DIRECT)
python3 scripts/experiments/exp001_urdf_geometry.py   # EXP-001 → results/geometry/
python3 scripts/experiments/exp002_ik_vs_urdf.py      # EXP-002 → results/kinematics/
python3 scripts/experiments/exp004_closed_loop_tracking.py  # EXP-004 → results/experiments/
python3 scripts/experiments/exp007_workspace_stroke.py      # EXP-007 → results/kinematics/
python3 scripts/experiments/exp008_forward_kinematics.py    # EXP-008 → results/kinematics/
python3 scripts/experiments/exp010_statics_lying.py         # EXP-010 → results/dynamics/
python3 scripts/run_validation.py                     # tests + toutes les campagnes, bilan
python3 scripts/run_trajectory.py                     # scénarios en simulation DIRECT, erreurs de suivi
python3 -m src.gui.dashboard                          # tableau de bord (CustomTkinter)
python3 run_simulation.py                             # menu de lancement (5 modes)
python3 scripts/system_check.py                       # diagnostic de l'environnement
# Jumeau Gazebo du démonstrateur (Ubuntu 24.04, ROS 2 Jazzy) : docs/guides/GAZEBO_BANC_REM.md
ros2 launch rem_bench_sim bench_sim.launch.py mode:=manual
```

`tests/integration_tests/test_physical_platform.py` pilote le banc réel : ne jamais le lancer sans matériel ni en CI. La CI (`.github/workflows/tests.yml`) ne lance que `unit_tests` et `validation_tests`.

## Points d'attention connus

Diagnostic initial : `docs/reports/2026-09-24_analyse_depot.md` (daté, ne pas le réécrire). État courant et priorités : [ROADMAP.md](ROADMAP.md). En priorité :

- ~~A1~~ **résolu** (EXP-002) : l'IK `src` est validée contre le URDF. Utiliser `DEFAULT_ACTUATOR_INDICES` (`src/core/platform.py`), jamais l'ancien `[9, 2, 31, 45, 38, 24]` (qui n'est valable qu'avec `legacy/inv_kinematics.py`).
- **Simulation** : utiliser `StewartPlatform.from_urdf(...)` (géométrie identifiée, EXP-001), puis `move_to_working_position()` avant tout mouvement. La pose neutre de l'IK est en **butée basse des vérins**, donc toute consigne doit être exprimée autour de `DEFAULT_WORKING_HEIGHT`. Précision validée : 0,28 mm / 0,044° (EXP-004).
- Ne pas retirer le recentrage des limites [0 ; 2π] dans `setup_constraints()` : sans lui, le mécanisme se bloque.
- `PyBulletSimulator` (`src/simulation/pybullet_sim.py`, utilisé par la GUI PyBullet) délègue à `StewartPlatform.from_urdf` : ses poses sont en **mm / degrés relatifs à la position de travail**, et `update_platform_pose` ne fait que fixer les consignes (la simulation avance par `step_simulation`).
- En mode GUI sous WSLg, `p.disconnect()` provoque un segfault (bogue PyBullet/OpenGL, reproduit sans modèle). Le tableau de bord utilise donc DIRECT + rendu hors écran (`PyBulletSimulator(offscreen=True)`, greffon EGL chargé **avant** les modèles) : ne pas le repasser en `p.GUI`.
- Interfaces : `src/gui/dashboard.py` (vue) + `dashboard_controller.py` (logique testable sans affichage). Les classes `SimpleStewartGUI`, `AdvancedStewartGUI`, `PyBulletStewartGUI` sont dépréciées ; leurs `main()` ouvrent le tableau de bord.
- Cinématique directe : `src.core.forward_kinematics` (**radians**, SI) ; `pose_from_actuator_positions` donne la pose relative à la position de travail à partir des allongements des vérins (codeurs du banc).
- **Deux plateformes** : le URDF/PyBullet (r = 20 cm) n'est **pas** le banc réel. Le banc (r = 7,5/4 cm, vérins de 10 cm, ROS 2 Jazzy, dépôt `ABMI-software/Demonstrateur_REM`) a son jumeau dans `src/rem_bench` + `ros2_ws/src/rem_bench_sim` (Gazebo), paramétré par `configurations/bench_rem.yaml`. Ne jamais modifier le code du banc depuis ce dépôt ; le jumeau le remplace à ses interfaces (ADR-0003).
- Jumeau Gazebo (prototype) : les attaches du mécanisme sont les vraies (sans l'inversion D1 de l'IK du banc) ; les valeurs marquées HYPOTHÈSE dans `bench_rem.yaml` ne sont pas mesurées, et **la scène (caméra embarquée, marqueur fixe, plateforme debout) est fausse** : sur le banc, la caméra est fixe sur le col de cygne (confirmé le 2026-10-01), le marqueur sur la plaque, la plateforme couchée : ne pas la présenter comme fidèle.
- Faisabilité : toute trajectoire nouvelle passe par `src.core.feasibility.check_trajectory` (course des vérins) ; les scénarios de démonstration sont dans `src/core/scenarios.py`.

Ne pas « corriger » ces points au détour d'une autre tâche : ils relèvent des Phases 2 et 4 de la roadmap et nécessitent une validation.

## Carte du dépôt

| Dossier | Contenu |
|---|---|
| `src/` | Code Python actif (package `src`), API historique |
| `models/` | Modèles géométrie, cinématique, dynamique, calibration, identification (CAO, notebooks, futurs modules) |
| `controllers/` | Contrôle inverse et direct, trajectoires, commande de mouvement, asservissement |
| `simulation/` | URDF, maillages, Gazebo, mondes, launch |
| `ros2_ws/` | Espace de travail ROS 2 Jazzy : `rem_bench_sim` (jumeau Gazebo du démonstrateur) |
| `configurations/` | Fichiers YAML |
| `datasets/` | Mesures brutes (immutables) |
| `results/` | Figures, vidéos et sorties générées, par thème |
| `tests/` | `unit_tests/`, `integration_tests/`, `validation_tests/` |
| `docs/` | `design/`, `experiments/`, `protocols/`, `decisions/`, `validation/`, `reports/`, `guides/` |
| `scripts/` | `run_trajectory`, `run_validation`, `create_video`, `system_check`, `experiments/` (un script par EXP) |
| `examples/` | Exemples d'utilisation de l'API |
| `legacy/` | Code et fichiers historiques, non maintenus |
