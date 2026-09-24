# Roadmap : jumeau numérique de la plateforme Stewart (REM)

Chaque phase se termine par un **critère de sortie** vérifiable et au moins une fiche d'expérimentation dans `docs/experiments/`.
Légende : ✅ fait · 🟡 partiel · ⬜ à faire.

## Phase 0 : Assainissement du dépôt 🟡

- ✅ Analyse complète de l'existant (`docs/reports/2026-09-24_analyse_depot.md`)
- ✅ Arborescence cible, documentation d'architecture, CLAUDE.md, roadmap
- ✅ Commit de l'état restructuré
- ✅ `requirements.txt` réduit aux dépendances réelles (`numpy`, `matplotlib`, `pybullet`, `pyyaml`) avec versions minimales ; `requirements-dev.txt` (pytest, jupyterlab)
- ✅ Attente erronée de `test_solve_neutral_position` corrigée : `pytest tests/unit_tests tests/validation_tests` → 14/14
- ⬜ Intégration continue : `pytest tests/unit_tests` sur chaque push
- ⬜ Réparer ou retirer : entrée `stewart-test` de `setup.py`, `examples/basic_control.py`, tests d'intégration hérités

**Sortie** : `pytest tests/unit_tests` au vert en CI.

## Phase 1 : Caractérisation géométrique ⬜

- Formaliser les repères `{W}`, `{B}`, `{P}`, `{T}` et les conventions d'angles (document `docs/design/`)
- Module `models/geometry` : `PlatformGeometry` chargé depuis le YAML ; suppression de la hauteur neutre en dur
- Extraire du URDF et de la CAO les coordonnées réelles des attaches ; comparer au modèle paramétrique (`r`, `γ`)
- Documenter le lien entre `joint_indices`/`actuator_indices` et les jambes 1 à 6

**Sortie** : écart entre attaches paramétriques et URDF < 0,5 mm, documenté (EXP-001).

## Phase 2 : Caractérisation cinématique 🟡

- ✅ **Anomalie A1 arbitrée** ([EXP-002](docs/experiments/EXP-002-validation-ik-urdf.md)) : l'IK `src` est correcte ; l'ordre des actionneurs est corrigé en `[2, 31, 45, 38, 24, 9]`
- ✅ Ordre des arguments de `PhysicalStewartPlatform` corrigé (A2)
- ⬜ Docstrings d'unités et de convention de rotation (A6)
- Cinématique directe (Newton-Raphson), jacobien, détection des singularités
- Espace de travail atteignable sous contraintes de course des vérins et de débattement des rotules
- Tests : aller-retour IK→FK, valeurs de référence, propriétés de symétrie

**Sortie** : erreur aller-retour IK→FK < 1 µm ; IK validée contre PyBullet < 0,1 mm (EXP-002).

## Phase 3 : Caractérisation dynamique ⬜

- Modèle de masse et d'inertie (plateforme + charge d'attelage) depuis le URDF et la CAO
- Statique : efforts dans les vérins `f = J⁻ᵀ w` sur l'espace de travail
- Dynamique inverse (Newton-Euler) ; comparaison avec PyBullet
- Première étude énergétique : puissance et énergie par trajectoire type

**Sortie** : efforts statiques simulés/analytiques à < 2 % près (EXP-003).

## Phase 4 : Simulation Stewart complète ⬜

- Adaptateur de simulation unique (fusion de `StewartPlatform` et `PyBulletSimulator`) avec fermeture de boucle (A3) et mesure de la pose réelle de la plateforme (A5)
- **Lever le blocage cinématique** de la boucle fermée observé dans EXP-002 : hors de l'axe z, les vérins n'atteignent pas leur consigne (jusqu'à 18 mm d'écart). Piste : contraintes `JOINT_POINT2POINT` aux centres des cardans
- Conversion URDF→SDF, monde Gazebo, fermeture de boucle sous Gazebo
- Scénarios REM : approche du timon, désalignements, charge verticale
- Enregistrement systématique dans `results/`

**Sortie** : même trajectoire rejouée sous PyBullet et Gazebo, écart de pose documenté (EXP-004).

## Phase 5 : Contrôle temps réel ⬜

- Générateur de trajectoires avec lois horaires (trapèze, polynôme d'ordre 5), limites de vitesse et d'accélération
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
