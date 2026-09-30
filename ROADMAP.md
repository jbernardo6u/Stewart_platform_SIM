# Roadmap : jumeau numérique de la plateforme Stewart (REM)

Chaque phase se termine par un **critère de sortie** vérifiable et au moins une fiche d'expérimentation dans `docs/experiments/`.
Légende : ✅ fait · 🟡 partiel · ⬜ à faire.

## Priorités pour finaliser (révisées le 2026-09-30, banc physique disponible)

Le banc existe : les phases matérielles (6 et 7) ne sont plus un horizon lointain. Ordre proposé :

1. **Préparer le banc tôt** (en parallèle des étapes 2 à 4)
   - Inventaire du banc réel contre le modèle : dimensions (r, γ, hauteur), course et longueurs réelles des vérins, type de cardans. `hardware.actuators` (0,15–0,25 m, 0,173 m initial) ne correspond pas au URDF (course 0–0,19 m, jambe ≈ 0,286 m au neutre) : à arbitrer.
   - Interface matériel réelle à la place du stub `MotorController` : lecture des codeurs, consigne de position, arrêt d'urgence, **même API que `PyBulletSimulator`**, pour que le tableau de bord pilote indifféremment la simulation ou le banc.
   - Protocole de mesure de pose (`docs/protocols/`) : moyen disponible (vision/ArUco, comparateurs, laser tracker ?) et incertitude.
2. **Cinématique complète** (Phase 2, V-2, V-3) : FK Newton-Raphson, jacobien, singularités, espace de travail avec le débattement des cardans mesuré.
3. **Statique, dynamique, énergie** (Phase 3, V-4 à V-6) : efforts vérins `J⁻ᵀw` sous la charge du timon ; c'est la question de faisabilité de fond pour REM.
4. **Commande temps réel** (Phase 5) : limites de vitesse et d'accélération, asservissement, puis ROS2 si imposé.
5. **Calibration et validation simulation/réel** (Phases 6 et 7), dès que 1 est prêt.
6. **Scénarios REM complets** (Phase 8) : repère outil, estimation de pose du timon, boucle d'alignement.

Gazebo (Phase 4, EXP-005) n'est utile que si l'intégration ROS2/Gazebo est une exigence : PyBullet est validé à 0,28 mm.

## Phase 0 : Assainissement du dépôt 🟡

- ✅ Analyse complète de l'existant (`docs/reports/2026-09-24_analyse_depot.md`)
- ✅ Arborescence cible, documentation d'architecture, CLAUDE.md, roadmap
- ✅ Commit de l'état restructuré
- ✅ `requirements.txt` réduit aux dépendances réelles (`numpy`, `matplotlib`, `pybullet`, `pyyaml`) avec versions minimales ; `requirements-dev.txt` (pytest, jupyterlab)
- ✅ Attente erronée de `test_solve_neutral_position` corrigée : `pytest tests/unit_tests tests/validation_tests` → 14/14
- ✅ Intégration continue : `.github/workflows/tests.yml` (tests unitaires et de validation, PyBullet DIRECT) sur chaque push
- ✅ Entrées `stewart-test` / `stewart-demo` de `setup.py` retirées (cibles inexistantes) ; `stewart-gui` ouvre le tableau de bord
- ✅ Points d'entrée ramenés à `run_simulation.py` (5 modes) ; 4 lanceurs redondants archivés dans `legacy/scripts/`
- ⬜ Réparer ou retirer : `examples/basic_control.py`, tests d'intégration hérités

**Sortie** : `pytest tests/unit_tests` au vert en CI.

## Phase 1 : Caractérisation géométrique 🟡

- Formaliser les repères `{W}`, `{B}`, `{P}`, `{T}` et les conventions d'angles (document `docs/design/`)
- Module `models/geometry` : `PlatformGeometry` chargé depuis le YAML ; suppression de la hauteur neutre en dur
- ✅ Extraire du URDF les coordonnées réelles des attaches et les comparer au modèle paramétrique ([EXP-001](docs/experiments/EXP-001-geometrie-urdf.md) : écart de 0,8 à 1,6 mm ; géométrie identifiée utilisable via `StewartPlatform.from_urdf`)
- ✅ Documenter le lien entre `joint_indices`/`actuator_indices` et les jambes 1 à 6 (EXP-002, `src/core/platform.py`)
- ⬜ Comparer à la CAO : décentrage de 1,2 mm et non-planéité de 1 mm de la plateforme, voulus ou défauts ?

**Sortie** : écart géométrie modèle/URDF documenté, et modèle de référence < 0,5 mm (✅ géométrie identifiée : 0,008 mm en simulation sans gravité).

## Phase 2 : Caractérisation cinématique 🟡

- ✅ **Anomalie A1 arbitrée** ([EXP-002](docs/experiments/EXP-002-validation-ik-urdf.md)) : l'IK `src` est correcte ; l'ordre des actionneurs est corrigé en `[2, 31, 45, 38, 24, 9]`
- ✅ Ordre des arguments de `PhysicalStewartPlatform` corrigé (A2)
- ✅ Docstrings d'unités et de convention de rotation (A6)
- Cinématique directe (Newton-Raphson), jacobien, détection des singularités
- 🟡 Espace de travail atteignable : course des vérins faite ([EXP-007](docs/experiments/EXP-007-espace-travail-course.md) : non limitante en x/y, lacet ±72°) ; débattement des cardans à mesurer sur le banc
- Tests : aller-retour IK→FK, valeurs de référence, propriétés de symétrie

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
- ⬜ Porter ou archiver `scripts/create_video.py` et `examples/basic_control.py` (API `start_simmulation` de legacy)
- Conversion URDF→SDF (corriger les limites [0 ; 2π] dans le modèle), monde Gazebo, fermeture de boucle sous Gazebo
- Scénarios REM : approche du timon, désalignements, charge verticale
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
