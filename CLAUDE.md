# CLAUDE.md

Instructions pour les agents (Claude Code) et les contributeurs travaillant sur ce dépôt.

## Contexte

Projet REM : système autonome d'attelage et de désattelage de remorque.

La plateforme Stewart (hexapode 6-6 à vérins linéaires) est l'actionneur principal. Elle assure l'alignement précis entre le véhicule tracteur et la remorque. Ce dépôt contient son **jumeau numérique** : modèles géométrique, cinématique et dynamique, simulation, contrôle et validation contre le réel.

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
- **Décisions structurantes** : un ADR dans `docs/decisions/`.
- **Changelog** : chaque changement notable est ajouté dans [CHANGELOG.md](CHANGELOG.md) (section `[Non publié]`).
- **Ne rien supprimer sans justification** : archiver dans `legacy/` et le consigner dans le changelog.

## Commandes utiles

```bash
pip install -r requirements-dev.txt                   # dépendances + pytest + jupyterlab
python3 -m pytest tests/unit_tests tests/validation_tests   # tests sans GUI (PyBullet en mode DIRECT)
python3 scripts/experiments/exp002_ik_vs_urdf.py      # rejoue EXP-002 → results/kinematics/
python3 run_simulation.py                             # menu de lancement
python3 scripts/system_check.py                       # diagnostic de l'environnement
```

`tests/integration_tests/test_pybullet_gui.py` ouvre une fenêtre PyBullet et plante (core dump) sans affichage. Ne pas le lancer en CI ni sous WSL sans serveur X.

## Points d'attention connus

Voir `docs/reports/2026-09-24_analyse_depot.md`, section « Dette technique ». En priorité :

- ~~A1~~ **résolu** (EXP-002) : l'IK `src` est validée contre le URDF. Utiliser `DEFAULT_ACTUATOR_INDICES` (`src/core/platform.py`), jamais l'ancien `[9, 2, 31, 45, 38, 24]` (qui n'est valable qu'avec `legacy/inv_kinematics.py`).
- **Simulation bloquée hors de l'axe z** (EXP-002) : les résultats dynamiques PyBullet ne sont pas quantitativement exploitables tant que la Phase 4 n'a pas traité ce point.
- **A3** : `src/core/platform.py` ne crée pas les contraintes de fermeture de boucle.
- **A5** : les fonctions « pose courante » renvoient la pose de la base, pas celle de la plateforme.

Ne pas « corriger » ces points au détour d'une autre tâche : ils relèvent des Phases 2 et 4 de la roadmap et nécessitent une validation.

## Carte du dépôt

| Dossier | Contenu |
|---|---|
| `src/` | Code Python actif (package `src`), API historique |
| `models/` | Modèles géométrie, cinématique, dynamique, calibration, identification (CAO, notebooks, futurs modules) |
| `controllers/` | Contrôle inverse et direct, trajectoires, commande de mouvement, asservissement |
| `simulation/` | URDF, maillages, Gazebo, mondes, launch |
| `ros2_ws/` | Espace de travail ROS2 (à créer) |
| `configurations/` | Fichiers YAML |
| `datasets/` | Mesures brutes (immutables) |
| `results/` | Figures, vidéos et sorties générées, par thème |
| `tests/` | `unit_tests/`, `integration_tests/`, `validation_tests/` |
| `docs/` | `design/`, `experiments/`, `protocols/`, `decisions/`, `validation/`, `reports/`, `guides/` |
| `scripts/` | Lanceurs et outils |
| `examples/` | Exemples d'utilisation de l'API |
| `legacy/` | Code et fichiers historiques, non maintenus |
