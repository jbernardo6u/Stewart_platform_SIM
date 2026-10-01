# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [Non publié]

### Ajouté : jumeau Gazebo du démonstrateur REM (2026-10-01)
- Le banc réel (dépôt `ABMI-software/Demonstrateur_REM`, ROS 2 Jazzy) tourne **sans modification** sur une simulation Gazebo Harmonic ([ADR-0003](docs/decisions/ADR-0003-jumeau-gazebo-demonstrateur.md), proposée).
- `src/rem_bench/` (Python pur) : géométrie physique du banc et FK des codeurs, émulation du firmware `pilotage_feedback_mp.ino` et port série virtuel (pseudo-terminal), caméra embarquée, marqueur et IMU, génération du monde SDF (marqueur ArUco en géométrie, intrinsèques du banc), configuration des nœuds du banc pour la simulation.
- `ros2_ws/src/rem_bench_sim` : nœuds `virtual_hardware`, `sim_aruco` (`aruco_node` du banc sur l'image Gazebo), `sim_imu` (`imu_node` du banc sur un MPU-9250 simulé), `exp009_campaign` ; `bench_sim.launch.py` (modes acquisition, manuel, automatique).
- `configurations/bench_rem.yaml` : mécanisme et capteurs du banc, hypothèses de montage signalées.
- [EXP-009](docs/experiments/EXP-009-jumeau-gazebo-demonstrateur.md) : D1 (IK du banc : x, y et lacet inversés) et D9 reproduits et chiffrés ; nouveaux défauts du banc D13 (lissage puis zone morte dans `aruco_node` : jusqu'à 6,8 mm d'erreur statique) et D14 (OpenCV 4.6 : `DetectorParameters()` provoque une erreur de segmentation) ; mode automatique inopérant avec `reference_position_m: [0, 0, 0]`.
- `bench_rem.yaml` : vitesse des vérins portée de 2 à 7,1 cm/s à PWM 255, estimée d'après l'essai d'endurance du banc (borne basse, non mesurée).
- Guide [docs/guides/GAZEBO_BANC_REM.md](docs/guides/GAZEBO_BANC_REM.md) ; 23 tests unitaires (`tests/unit_tests/test_rem_bench.py`).

### Modifié (2026-10-01)
- `src/__init__.py` : `InverseKinematics`, `StewartPlatform` et `PhysicalStewartPlatform` sont chargés à la demande (PEP 562). L'API est inchangée, mais importer un module NumPy pur n'exige plus PyBullet (côté ROS 2).

### Ajouté : cinématique directe (Phase 2, 2026-10-01)
- `src/core/forward_kinematics.py` (NumPy pur, radians) : `forward_kinematics` (Newton-Raphson, mise à jour de l'orientation sur SO(3)), `pose_from_actuator_positions` (allongements des vérins → pose relative à la position de travail, pour le banc), `jacobian` (`dℓ/dt = J·[v ; ω]`), `singularity_measures` (conditionnement adimensionné, déterminant), `leg_lengths`, `rotation_matrix`, `rotation_to_rpy`. API existante inchangée.
- Configuration : section `kinematics.forward` (tolérance, nombre d'itérations).
- [EXP-008](docs/experiments/EXP-008-cinematique-directe-jacobien.md) : aller-retour IK→FK à 10⁻¹² m (critère de sortie de la Phase 2), 0,8 ms par appel ; FK sur les joints PyBullet à 5 µm sans gravité, 0,15 à 0,5 mm avec gravité (souplesse des liaisons) ; singularité de Fichter à lacet ±90°. Script `scripts/experiments/exp008_forward_kinematics.py`, ajouté à `run_validation.py`.
- Tests : `tests/unit_tests/test_forward_kinematics.py` (20), `tests/validation_tests/test_forward_kinematics_simulation.py` (2).

### Modifié : lisibilité et préparation du banc (2026-09-30, suite)
- Tableau de bord : le graphe « écart consigne/mesure » (deux courbes sur deux axes superposés, difficile à lire) devient deux graphes empilés, **écart de position (mm)** et **écart d'orientation (°)**, chacun avec sa valeur courante, une légende explicative et une ligne pointillée à la précision validée (`gui.dashboard.tracking_criteria`, EXP-004).
- `scripts/create_video.py` porté : GIF d'un scénario par rendu hors écran (l'ancienne version appelait `start_simmulation`, inexistante) ; ancienne version dans `legacy/scripts/`.
- `examples/basic_control.py` réécrit (IK, faisabilité, simulation) ; ancienne version dans `legacy/examples/`.
- `tests/integration_tests/test_physical_platform.py` : import réparé (`src.hardware.physical_platform`), conservé pour le banc.
- Documentation remise à jour : README (état, avancement, API, configuration, tests), RESEARCH (état de chaque verrou), ARCHITECTURE, ROADMAP, CLAUDE.md, README de `docs/`, `results/`, `controllers/`, `models/`, `simulation/`, `tests/`, QUICK_START.

### Ajouté (2026-09-30, suite)
- [ADR-0002](docs/decisions/ADR-0002-interface-commune-simulation-banc.md) (proposée) : contrat commun simulation/banc, pour rejouer les mêmes consignes.
- [PROT-001](docs/protocols/PROT-001-inventaire-banc.md) : grille d'inventaire et de caractérisation du banc, face aux valeurs du modèle.

### Archivé (2026-09-30, suite)
- `tests/integration_tests/test_no_gui.py`, `test_pybullet_gui.py` → `legacy/tests/integration_tests/` (imports obsolètes, fenêtre PyBullet ; couverts par les tests de validation).
- `scripts/migrate_imports.py`, `scripts/setup_project.py` → `legacy/scripts/` (outils ponctuels de la migration de 2025).

### Ajouté : tableau de bord et modes de simulation (2026-09-30)
- **Tableau de bord unique** `src/gui/dashboard.py` (CustomTkinter, thèmes sombre et clair), qui remplace les GUI Simple, Advanced et PyBullet : vue 3D de la simulation rendue hors écran dans la fenêtre (EGL, repli logiciel ; glisser et molette), consigne 6 axes relative à la position de travail, course de chaque vérin avec alerte de saturation (aussi en rouge dans la vue 3D), inclinaison des jambes, écart consigne/mesure en direct, scénarios vérifiés avant exécution avec bilan RMS et maximal, arrêt d'urgence. Logique testable sans affichage dans `src/gui/dashboard_controller.py`.
- `src/core/feasibility.py` : positions des vérins, vérification de la course d'une pose ou d'une trajectoire, inclinaison des jambes.
- `src/core/scenarios.py` : scénarios à lois horaires d'ordre 5 (approche d'attelage, carré, balayage d'orientation, sinusoïdes 6 axes), tous réalisables.
- `src/core/config.py` : chargement de `configurations/platform_config.yaml` (aucun code ne le lisait).
- `PyBulletSimulator` : paramètre optionnel `offscreen`, méthodes `render_image`, `orbit_camera`, `style_scene`, `set_actuator_colors` ; caméras recentrées sur la plateforme.
- `scripts/run_trajectory.py` (rapport de suivi par scénario), `scripts/run_validation.py` (tests + campagnes, bilan).
- EXP-007 (espace de travail limité par la course) : script, résultats `results/kinematics/exp007_*`, fiche.
- Configuration : `platform.actuator_stroke`, `gui.dashboard.limits` et `render_size`.
- CI GitHub : `.github/workflows/tests.yml`.
- Tests : `test_feasibility_scenarios.py` (11), `test_dashboard_controller.py` (6).
- Dépendances : `customtkinter`, `pillow`.

### Modifié (2026-09-30)
- `run_simulation.py` : cinq modes distincts (tableau de bord, rapport de trajectoires, espace de travail, validation, diagnostic) au lieu de neuf entrées redondantes ; accepte le numéro du mode en argument.
- `main()` de `simple_gui`, `advanced_gui` et `pybullet_gui` : ouvrent le tableau de bord (signatures inchangées ; classes conservées, dépréciées).
- `examples/trajectory_demo.py --type spiral` : lacet oscillant ±20° au lieu d'un tour de 360° (60 % des points hors course).
- `setup.py` : `stewart-gui` → tableau de bord ; entrées `stewart-test` et `stewart-demo` retirées (modules inexistants).
- `scripts/system_check.py` : vérifie `pyyaml`, `pybullet`, `customtkinter`, `pillow` et le tableau de bord ; recommande les nouveaux points d'entrée.
- Documentation : `docs/guides/QUICK_START.md` réécrit, README, CLAUDE.md, ARCHITECTURE, ROADMAP (priorités révisées avec le banc réel).

### Corrigé (2026-09-30)
- Longueurs de vérins affichées par les GUI historiques (`BaseStewartGUI.update_kinematics`) : les millimètres étaient passés comme des mètres (vérins de « 30 m ») et les angles convertis en radians alors que l'IK attend des degrés ; la position de travail n'était pas prise en compte.

### Archivé (2026-09-30)
- `scripts/launcher.py`, `gui_launcher.py`, `quick_simulation.py`, `simulation_manager.py` → `legacy/scripts/` : lanceurs redondants (le dernier pointait vers un test supprimé).
- `docs/guides/GUIDE_UTILISATION.md` → `docs/reports/history/` : il décrivait des scripts de 2025 qui n'existent plus à la racine.

### Corrigé : simulateur de la GUI PyBullet (2026-09-30, suite d'EXP-004)
- `PyBulletSimulator` (`src/simulation/pybullet_sim.py`) simule enfin le mécanisme au lieu de téléporter le robot entier : il s'appuie sur `StewartPlatform.from_urdf` (géométrie identifiée, boucles fermées, vérins asservis) et monte à la position de travail à la connexion. API publique inchangée (mêmes méthodes, mêmes clés).
  - `update_platform_pose` : position (mm) et rotation (°) **relatives à la position de travail**, converties en consignes de vérins bornées à leur course ; `leg_lengths` est ignoré.
  - `get_platform_state` : pose mesurée de la plateforme (et non plus de la base) dans la même convention, vitesses du lien plateforme ; clés ajoutées `actuator_positions` et `reachable`.
  - `reset_simulation` : configuration zéro puis retour à la position de travail. `apply_external_force` s'applique à la plateforme (et non plus à la base). `stop_recording` renvoie le vrai nom du fichier.
  - `step_simulation(steps=1)` : paramètre optionnel ; la GUI fait 4 pas par image à 60 Hz (temps réel au lieu de ×1/4).
- Précision vérifiée : ≤ 0,3 mm / 0,05° en mode DIRECT et en mode fenêtre.

### Ajouté (2026-09-30)
- `StewartPlatform.command_pose(translation, rotation)` : consigne non bloquante (la simulation est avancée par l'appelant), bornée à la course, renvoie False en cas de saturation. `StewartPlatform.actuator_limits()` et `StewartPlatform.reset_to_neutral()`.
- `tests/validation_tests/test_pybullet_simulator.py` (6 tests).

### Corrigé : simulation en boucle fermée (2026-09-24, EXP-004)
- `StewartPlatform` simule enfin une plateforme parallèle fidèle : erreur de pose de 0,28 mm / 0,044° (18 mm d'erreur auparavant).
  - `load_robot` : base fixée (`use_fixed_base=True` par défaut).
  - `setup_constraints` (vide jusqu'ici, A3) : fermeture des 5 boucles par contraintes fixes **ancrées** (l'ancienne version collait les centres de masse) ; limites [0 ; 2π] de 11 articulations passives recentrées sur [−π ; π] (sinon butée à 0 et blocage) ; moteurs passifs désactivés.
  - Longueurs initiales des vérins issues de l'IK (A4, au lieu de 0,173205 en dur).
  - `get_current_pose` mesure la pose de la **plateforme** dans le repère des consignes (A5, renvoyait la base).
  - `control_linear_actuators` : la consigne finale est réellement atteinte (l'interpolation s'arrêtait à (n−1)/n), gain de position 0,3 et effort maximal exposés en attributs.
- Docstrings d'unités et de convention de rotation de `InverseKinematics` (A6).

### Ajouté (2026-09-24, EXP-001 / EXP-004)
- `InverseKinematics.from_attachment_points(B, P, home)` : IK sur une géométrie mesurée ou identifiée.
- `src/simulation/urdf_geometry.py::identify_urdf_geometry` : centres des cardans extraits du URDF.
- `StewartPlatform.from_urdf(urdf)`, `move_to_working_position()`, paramètres optionnels `kinematics=`, `realtime=`, `settle_time=`.
- Constantes `DEFAULT_PLATFORM_LINK`, `DEFAULT_WORKING_HEIGHT`, `DEFAULT_PLATFORM_CENTRE_IN_LINK`, fonction `rotation_to_rpy_deg`.
- `configurations/platform_config.yaml` : section `platform.identified` et `working_height`.
- Fiches EXP-001, EXP-004 ; scripts `scripts/experiments/exp001_*.py`, `exp004_*.py` ; résultats `results/geometry/`, `results/experiments/exp004_tracking.csv`.
- 14 tests (4 unitaires, 10 de validation).

### Modifié (2026-09-24)
- `examples/trajectory_demo.py --simulation` : géométrie identifiée et hauteur de travail.

### Corrigé : cinématique et simulation (2026-09-24, EXP-002)
- **Ordre des actionneurs** : `[9, 2, 31, 45, 38, 24]` → `[2, 31, 45, 38, 24, 9]` (Slider_13..18 = jambes 1 à 6). L'ancien ordre était calé sur l'IK historique, qui décrit le mécanisme tourné de −60°. Combiné à l'IK `src`, il envoyait à chaque vérin la consigne d'une autre jambe (écart de 44° entre jambe modèle et vérin URDF, contre 0,4° maintenant). Mis à jour dans `configurations/platform_config.yaml`, `scripts/create_video.py`, `examples/*.py`, `tests/integration_tests/test_no_gui.py`. Les scripts `legacy/` ne sont pas modifiés.
- `PhysicalStewartPlatform` : paramètres de conception passés dans le bon ordre à `InverseKinematics` (anomalie A2 ; sans effet tant que base = plateforme).
- `test_solve_neutral_position` : la longueur attendue au neutre est ‖home + P − B‖, et non ‖home‖.

### Ajouté (2026-09-24, suite)
- `DEFAULT_ACTUATOR_INDICES` et `DEFAULT_JOINT_INDICES` dans `src/core/platform.py`, source unique de la correspondance IK ↔ URDF (ajout, API inchangée).
- `docs/experiments/EXP-002-validation-ik-urdf.md`, `scripts/experiments/exp002_ik_vs_urdf.py`, résultats `results/kinematics/exp002_*.csv`.
- Tests : `tests/validation_tests/test_ik_urdf_consistency.py`, `tests/unit_tests/test_physical_platform_config.py`.
- `requirements-dev.txt` (pytest, jupyterlab).

### Modifié (2026-09-24, suite)
- `requirements.txt` : le gel d'environnement Jupyter/conda de 2023 (87 paquets, dont aucun n'était importé par le code hormis numpy, matplotlib et pybullet) est remplacé par les 4 dépendances réelles avec versions minimales. L'ancien contenu reste dans l'historique git.

### Ajouté (2026-09-24)
- Structure de dépôt « jumeau numérique REM » : `simulation/`, `models/`, `controllers/`, `ros2_ws/`, `configurations/`, `datasets/`, `results/`, `tests/{unit,integration,validation}_tests/`, `docs/{design,experiments,protocols,decisions,validation,reports,guides}/`.
- Documentation : `CLAUDE.md`, `ARCHITECTURE.md` (diagrammes Mermaid d'architecture et de dépendances), `ROADMAP.md` (phases 0 à 8), `RESEARCH.md` (verrous V-1 à V-9), `docs/experiments/TEMPLATE.md` (format CIR), `docs/decisions/ADR-0001`.
- Rapports : `docs/reports/2026-09-24_analyse_depot.md`, `docs/reports/2026-09-24_restructuration.md`.

### Modifié (2026-09-24)
- URDF et maillages déplacés vers `simulation/urdf/` et `simulation/meshes/` ; chemins des maillages dans le URDF mis à jour (`../meshes/`).
- Configuration déplacée vers `configurations/platform_config.yaml`.
- Tous les chemins `assets/…` et `Stewart/Stewart.urdf` du code mis à jour. Aucune modification de logique métier.
- `create_web_viz.py` et `setup_project.py` déplacés dans `scripts/`.
- Tests répartis entre `tests/unit_tests/` et `tests/integration_tests/`.
- `.gitignore` : exceptions pour les médias versionnés dans `docs/` et `results/`.

### Archivé (2026-09-24)
- `Stewart/` → `legacy/Stewart_original/`, `Stewart.zip` → `legacy/archives/` (doublons exacts).
- Anciens rapports 2025 → `docs/reports/history/`.

### Supprimé (2026-09-24)
- Fichiers `.DS_Store` et `__pycache__/` (métadonnées et bytecode, déjà ignorés).

### Problèmes connus
- Voir la section « Dette technique » de `docs/reports/2026-09-24_analyse_depot.md` (anomalies A1 à A9), en particulier A1 : l'IK de `src/core/kinematics.py` diverge de l'IK d'origine.

## [1.0.0] : 2025-07 (non commité)
- Refactorisation en package `src/` (core, gui, hardware, simulation), GUI Tkinter multiples, lanceurs, visualisation web, configuration YAML, tests unitaires de l'IK.

## Upstream : 2023
- Plateforme Stewart d'origine (mlayek21/Stewart-Platform) : URDF Fusion 360, IK 6-6, simulation PyBullet.
