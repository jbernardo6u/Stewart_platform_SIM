# Roadmap : jumeau numérique de la plateforme Stewart (REM)

Chaque phase se termine par un **critère de sortie** vérifiable et au moins une fiche d'expérimentation dans `docs/experiments/`.
Légende : ✅ fait · 🟡 partiel · ⬜ à faire.

## Périmètre et priorités (révisés le 2026-10-01)

Ce dépôt traite de la **plateforme de Stewart seule** ; le banc d'attelage complet est développé dans [Demonstrateur_REM](https://github.com/ABMI-software/Demonstrateur_REM) ([ADR-0004](docs/decisions/ADR-0004-perimetre-des-depots.md)). Détail : [rapport du 2026-10-01](docs/reports/2026-10-01_perimetre_et_suite.md).

1. ✅ Cinématique complète (FK, jacobien, singularités, EXP-008).
2. ⬜ **Inventaire de la plateforme imprimée en 3D** (PROT-001) et essais réels si son électronique le permet (ADR-0002 à réviser).
3. ⬜ **Gazebo de la plateforme seule**, en réutilisant l'approche du prototype EXP-009 (FK, rendu), paramétré par sa géométrie.
4. ⬜ **Statique en position couchée** (Phase 3, V-4) : efforts `f = J⁻ᵀ·w` sur l'espace de travail, masse et centre de gravité en paramètres. C'est la réponse au verrou de couple du banc.
5. ⬜ Fusion et migration du prototype de jumeau du banc vers Demonstrateur_REM, où se poursuivent : scène corrigée (caméra fixe, marqueur sur la plaque, plateforme couchée), rail d'approche, vérins limités en effort, corrections D1–D3, D13, D14.

## Priorités pour finaliser (révisées le 2026-09-30, banc physique disponible ; remplacées par la section ci-dessus)

Le banc existe : les phases matérielles (6 et 7) ne sont plus un horizon lointain. Ordre proposé :

1. **Préparer le banc tôt** (en parallèle des étapes 2 à 4)
   - Inventaire du banc réel contre le modèle : dimensions (r, γ, hauteur), course et longueurs réelles des vérins, type de cardans. `hardware.actuators` (0,15–0,25 m, 0,173 m initial) ne correspond pas au URDF (course 0–0,19 m, jambe ≈ 0,281 m au neutre) : à arbitrer.
   - Interface matériel réelle à la place du stub `MotorController` : lecture des codeurs, consigne de position, arrêt d'urgence, **même API que `PyBulletSimulator`**, pour que le tableau de bord pilote indifféremment la simulation ou le banc.
   - Protocole de mesure de pose (`docs/protocols/`) : moyen disponible (vision/ArUco, comparateurs, laser tracker ?) et incertitude.
   - ✅ Préparé : [PROT-001](docs/protocols/PROT-001-inventaire-banc.md) (grille d'inventaire à remplir) et [ADR-0002](docs/decisions/ADR-0002-interface-commune-simulation-banc.md) (contrat `PlatformBackend`, à valider).
2. **Cinématique complète** (Phase 2, V-2, V-3) : ✅ FK, jacobien, singularités (EXP-008) ; reste l'espace de travail avec le débattement des cardans mesuré.
3. **Statique, dynamique, énergie** (Phase 3, V-4 à V-6) : efforts vérins `J⁻ᵀw` sous la charge du timon ; c'est la question de faisabilité de fond pour REM.
4. **Commande temps réel** (Phase 5) : limites de vitesse et d'accélération, asservissement, puis ROS2 si imposé.
5. **Calibration et validation simulation/réel** (Phases 6 et 7), dès que 1 est prêt.
6. **Scénarios REM complets** (Phase 8) : repère outil, estimation de pose du timon, boucle d'alignement.

**Mise à jour du 2026-10-01** : le banc réel est sous **ROS 2 Jazzy** (dépôt `ABMI-software/Demonstrateur_REM`), et ses mouvements sont gelés (la mécanique ne tient pas). Un **jumeau Gazebo du démonstrateur** exécute désormais son logiciel sans modification ([ADR-0003](docs/decisions/ADR-0003-jumeau-gazebo-demonstrateur.md), [EXP-009](docs/experiments/EXP-009-jumeau-gazebo-demonstrateur.md)). Le URDF/PyBullet (20 cm) décrit une autre plateforme que le banc (7,5 cm).

## Phase 0 : Assainissement du dépôt 🟡

- ✅ Analyse complète de l'existant (`docs/reports/2026-09-24_analyse_depot.md`)
- ✅ Arborescence cible, documentation d'architecture, CLAUDE.md, roadmap
- ✅ Commit de l'état restructuré
- ✅ `requirements.txt` réduit aux dépendances réelles (`numpy`, `matplotlib`, `pybullet`, `pyyaml`) avec versions minimales ; `requirements-dev.txt` (pytest, jupyterlab)
- ✅ Attente erronée de `test_solve_neutral_position` corrigée (aujourd'hui : 51 tests, voir `tests/README.md`)
- ✅ Intégration continue : `.github/workflows/tests.yml` (tests unitaires et de validation, PyBullet DIRECT) sur chaque push
- ✅ Entrées `stewart-test` / `stewart-demo` de `setup.py` retirées (cibles inexistantes) ; `stewart-gui` ouvre le tableau de bord
- ✅ Points d'entrée ramenés à `run_simulation.py` (5 modes) ; 4 lanceurs redondants archivés dans `legacy/scripts/`
- ✅ `examples/basic_control.py` réécrit sur l'API actuelle ; tests d'intégration hérités archivés (`test_physical_platform.py` conservé, import réparé, pour le banc)

**Sortie** : `pytest tests/unit_tests` au vert en CI (workflow en place ; premier passage à vérifier sur GitHub).

## Phase 1 : Caractérisation géométrique 🟡

- Formaliser les repères `{W}`, `{B}`, `{P}`, `{T}` et les conventions d'angles (document `docs/design/`)
- Module `models/geometry` : `PlatformGeometry` chargé depuis le YAML ; suppression de la hauteur neutre en dur
- ✅ Extraire du URDF les coordonnées réelles des attaches et les comparer au modèle paramétrique ([EXP-001](docs/experiments/EXP-001-geometrie-urdf.md) : écart de 0,8 à 1,6 mm ; géométrie identifiée utilisable via `StewartPlatform.from_urdf`)
- ✅ Documenter le lien entre `joint_indices`/`actuator_indices` et les jambes 1 à 6 (EXP-002, `src/core/platform.py`)
- ⬜ Comparer à la CAO : décentrage de 1,2 mm et non-planéité de 1 mm de la plateforme, voulus ou défauts ?

**Sortie** : écart géométrie modèle/URDF documenté, et modèle de référence < 0,5 mm (✅ géométrie identifiée : 0,008 mm en simulation sans gravité).

## Phase 2 : Caractérisation cinématique 🟡 (critère de sortie atteint)

- ✅ **Anomalie A1 arbitrée** ([EXP-002](docs/experiments/EXP-002-validation-ik-urdf.md)) : l'IK `src` est correcte ; l'ordre des actionneurs est corrigé en `[2, 31, 45, 38, 24, 9]`
- ✅ Ordre des arguments de `PhysicalStewartPlatform` corrigé (A2)
- ✅ Docstrings d'unités et de convention de rotation (A6)
- ✅ Cinématique directe (Newton-Raphson sur SO(3)), jacobien, indicateurs de singularité : `src/core/forward_kinematics.py` ([EXP-008](docs/experiments/EXP-008-cinematique-directe-jacobien.md) : aller-retour 10⁻¹² m, 0,8 ms, 7 itérations au plus ; singularité de Fichter à lacet ±90°, conditionnement ≤ 7 sur le lacet ±60°)
- ⬜ Recherche de singularités sur tout l'espace 6D ; seuil de conditionnement dans `check_trajectory` (après la Phase 3)
- 🟡 Espace de travail atteignable : course des vérins faite ([EXP-007](docs/experiments/EXP-007-espace-travail-course.md) : non limitante en x/y, lacet ±72°) ; débattement des cardans à mesurer sur le banc
- ✅ Tests : aller-retour IK→FK, différences finies, singularité de référence, symétrie, FK sur les joints PyBullet (`test_forward_kinematics*.py`)

**Sortie** : erreur aller-retour IK→FK < 1 µm ; IK validée contre PyBullet < 0,1 mm (EXP-002).

## Phase 3 : Caractérisation dynamique ⬜

- Modèle de masse et d'inertie (plateforme + charge d'attelage) depuis le URDF et la CAO
- Statique : efforts dans les vérins `f = J⁻ᵀ w` sur l'espace de travail
- Dynamique inverse (Newton-Euler) ; comparaison avec PyBullet
- Première étude énergétique : puissance et énergie par trajectoire type

**Sortie** : efforts statiques simulés/analytiques à < 2 % près (EXP-003).

## Phase 4 : Simulation Stewart complète 🟡

- ✅ Fermeture de boucle (A3), longueurs initiales (A4) et pose mesurée de la plateforme (A5) dans `StewartPlatform` ([EXP-004](docs/experiments/EXP-004-simulation-boucle-fermee.md))
- ✅ **Blocage cinématique levé** : butée basse des vérins à la pose neutre (d'où une hauteur de travail de 0,09 m) et limites [0 ; 2π] parasites. Suivi PyBullet de **0,28 mm / 0,044°** (critère < 0,5 mm / 0,1° atteint)
- ✅ `PyBulletSimulator` (GUI PyBullet) délègue à `StewartPlatform` : mêmes corrections, suivi < 0,5 mm / 0,1° vérifié par `tests/validation_tests/test_pybullet_simulator.py`
- ✅ `scripts/create_video.py` porté : GIF d'un scénario par rendu hors écran (`output/videos/`) ; `examples/basic_control.py` réécrit
- ✅ **Jumeau Gazebo du démonstrateur** (`src/rem_bench`, `ros2_ws/src/rem_bench_sim`) : Arduino virtuel (protocole et firmware), caméra rendue aux intrinsèques du banc (montée à tort sur la plateforme dans le prototype), IMU simulée ; `aruco_node`, `imu_node`, `fusion_node`, `manual_stewart_node`, `stewart_node` inchangés. ArUco à 0,7 % en profondeur, 0,06 mm latéral ([EXP-009](docs/experiments/EXP-009-jumeau-gazebo-demonstrateur.md))
- ⬜ Jumeau du banc (**suite dans Demonstrateur_REM**, ADR-0004) : scène d'après photos (caméra fixe sur col de cygne **confirmée**, marqueur sur la plaque, plateforme couchée, environ 20 cm), rail, vérins limités en effort, cadence de 8–10 Hz et latence de 200 ms, distorsion et bruit calibrés, `launch_testing` et CI Jazzy
- ⬜ **Gazebo de la plateforme seule** (ce dépôt)
- ⬜ Mécanisme dynamique fermé sous Gazebo (si les efforts sont nécessaires) ; conversion du URDF 20 cm
- 🟡 Scénarios REM : approche d'attelage illustrative (`scenarios.hitch_approach`) ; désalignements réels et charge verticale à spécifier
- Enregistrement systématique dans `results/`

**Sortie** : même trajectoire rejouée sous PyBullet et Gazebo, écart de pose documenté (EXP-005).

## Phase 5 : Contrôle temps réel ⬜

- 🟡 Scénarios à lois horaires d'ordre 5 (`src/core/scenarios.py`) et **vérification de la course des vérins** (`src/core/feasibility.py`) ; restent les limites de vitesse et d'accélération, et la démo `ellipse` de `generate_demo_trajectory` (lacet de 360°)
- ✅ Tableau de bord unique (`src/gui/dashboard.py`) : consigne, vérins, écart de suivi en direct, scénarios
- Contrôle en position, vitesse et accélération ; anticipation dynamique
- Workspace ROS2 : nodes IK/FK/trajectoire, `ros2_control`, topics, services et actions (voir ARCHITECTURE.md)
- Couche d'asservissement matériel réelle (remplacement du stub `MotorController`)

**Sortie** : suivi de trajectoire en simulation temps réel à 100 Hz minimum, erreur de suivi bornée et mesurée.

## Phase 6 : Calibration ⬜

- Protocole de mesure (`docs/protocols/`) : laser tracker, bras de mesure ou vision
- Identification des paramètres géométriques réels (attaches, offsets de longueur)
- Mise à jour de `configurations/` avec les paramètres identifiés

**Sortie** : précision de pose après calibration mesurée et documentée (EXP-006).

## Phase 7 : Validation simulation/réel ⬜

- Campagnes de mesure → `datasets/`
- Tests de validation automatisés (`tests/validation_tests/`) comparant simulation et mesures
- Analyse d'erreur (biais, dispersion, sensibilité)

**Sortie** : rapport de validation dans `docs/validation/`.

## Phase 8 : Intégration REM ⬜

- Interface d'attelage (repère outil `{T}`), boucle d'alignement pilotée par capteurs
- Scénarios complets d'attelage et de désattelage en simulation, puis sur banc
- Dossier de synthèse CIR (`docs/reports/`)

**Sortie** : démonstration d'attelage autonome en simulation, puis sur banc.
