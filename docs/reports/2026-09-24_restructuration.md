# Rapport de restructuration : Étapes 3 et 8

- **Date** : 2026-09-24
- **Prérequis** : [rapport d'analyse](2026-09-24_analyse_depot.md)
- **Décision cadre** : [ADR-0001](../decisions/ADR-0001-conserver-package-src.md) (le code de `src/` n'est pas déplacé)
- **Sauvegarde** : instantané complet de l'arbre de travail (hors `.git`), pris avant toute opération, hors du dépôt.

## Principes appliqués

1. Aucun code métier modifié (IK, trajectoires, contrôle, simulation) ; les anomalies A1 à A9 sont **documentées, pas corrigées**.
2. Seules des **chaînes de chemin** et des `sys.path` ont été modifiés, uniquement là où un déplacement l'imposait.
3. Aucune suppression de contenu utile. Les doublons exacts sont archivés dans `legacy/`, pas supprimés.
4. Déplacements faits avec `mv` (pas `git mv`) : l'index git n'est pas modifié. `git add -A` détectera les renommages par similarité.

## Déplacements

| Avant | Après | Justification |
|---|---|---|
| `assets/models/Stewart.urdf` | `simulation/urdf/Stewart.urdf` | Niveau 1 : simulation |
| `assets/models/meshes/*.stl` (51) | `simulation/meshes/` | idem |
| `assets/models/hello_bullet.py` | `simulation/urdf/hello_bullet.py` | Test de chargement du URDF, à côté de celui-ci |
| `Link_graph.txt` | `simulation/urdf/Link_graph.txt` | Graphe des liens du URDF |
| `assets/config/platform_config.yaml` | `configurations/platform_config.yaml` | Configuration centralisée |
| `Stewart/` | `legacy/Stewart_original/` | Doublon exact de `assets/models`, archivé |
| `Stewart.zip` | `legacy/archives/Stewart.zip` | 3e copie du même contenu, archivée |
| `Stewart_CAD.f3d` | `models/geometry/cad/` | Source de la géométrie |
| `Files/analysis.ipynb` | `models/kinematics/notebooks/analysis.ipynb` | Dérivation de l'IK |
| `Files/output*.png` (7) | `results/kinematics/figures/` | Sorties du notebook |
| `Files/StewartPlatformDocument.pdf` | `docs/reports/` | Document de référence |
| `Files/URDF_LINK.png`, `Files/Stewart1 v2.png` | `docs/design/figures/` | Figures de conception |
| `Files/*.svg` | `docs/assets/icons/` | Icônes de documentation |
| `Simulation/*.mp4` (4) | `results/experiments/videos/` | Sorties de simulation |
| `stewart_visualization.html` | `results/experiments/web/` | Sortie générée |
| `GUIDE_UTILISATION.md`, `QUICK_START.md` | `docs/guides/` | Guides utilisateur |
| `README_original.md` | `docs/design/README_original.md` | Théorie upstream |
| `PROJECT_STRUCTURE.md`, `RESTRUCTURING_COMPLETION.md`, `SIMULATION_ENHANCEMENT.md`, `SIMULATION_IMPROVEMENTS.md` | `docs/reports/history/` | Rapports 2025, remplacés par ARCHITECTURE.md |
| `create_web_viz.py`, `setup_project.py` | `scripts/` | Outils |
| `tests/test_kinematics.py` | `tests/unit_tests/` | Test unitaire pur |
| `tests/test_no_gui.py`, `test_physical_platform.py`, `test_pybullet_gui.py` | `tests/integration_tests/` | Scripts nécessitant PyBullet, un affichage ou d'anciens modules |

**Restés en place** : `src/` (ADR-0001), `legacy/`, `examples/`, `scripts/` (existants), `run_simulation.py` (point d'entrée documenté), `setup.py` (doit rester à la racine), `LICENSE`, `requirements.txt`, `output/` (référencé par la configuration), `__init__.py` racine (commité, vide : candidat à suppression, voir ci-dessous).

## Suppressions (justifiées)

| Fichier | Justification |
|---|---|
| `.DS_Store`, `Files/.DS_Store`, `Simulation/.DS_Store`, `Stewart/.DS_Store` | Métadonnées macOS, sans contenu, déjà dans `.gitignore` |
| `__pycache__/*.pyc` (racine, dont 7 commités), `scripts/__pycache__/` | Bytecode régénérable, déjà dans `.gitignore` |
| Dossiers `Files/`, `Simulation/`, `assets/` | Vides après déplacement |

## Modifications de fichiers existants (chemins uniquement)

| Fichier | Modification |
|---|---|
| `simulation/urdf/Stewart.urdf` | `filename="meshes/…"` → `filename="../meshes/…"` (51 occurrences) |
| `configurations/platform_config.yaml`, `src/gui/base_gui.py`, `src/gui/pybullet_gui.py`, `src/simulation/pybullet_sim.py`, `examples/*.py`, `scripts/{create_video,system_check,setup_project}.py`, `tests/integration_tests/*.py`, `legacy/*.py` | `assets/models/Stewart.urdf` et `Stewart/Stewart.urdf` → `simulation/urdf/Stewart.urdf` ; `assets/config/…` → `configurations/…` |
| `setup.py` | `package_data` : `assets/*` → `simulation/urdf/*`, `simulation/meshes/*`, `configurations/*` |
| `scripts/launcher.py` | Chemins du guide et de la structure ; `from scripts.setup_project import main` |
| `scripts/setup_project.py` | `chdir` et `sys.path` vers la racine du projet ; suppression du lien de compatibilité `Stewart/Stewart.urdf` (il aurait recréé un URDF sans maillages) ; chemins affichés |
| `scripts/create_web_viz.py` | `sys.path` vers la racine du projet |
| `tests/unit_tests/test_kinematics.py` | `sys.path` : `..` → `../..` |
| `docs/guides/*.md`, `README.md` | `python3 create_web_viz.py` → `python3 scripts/create_web_viz.py` |
| `.gitignore` | Exceptions pour les médias versionnés (`docs/**/*.png|pdf|svg`, `results/**/figures/*.png`, `results/experiments/videos/*.mp4`). Sans elles, les fichiers déplacés auraient disparu du suivi git |

## Fichiers créés

`CLAUDE.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `CHANGELOG.md`, `RESEARCH.md`, `README.md` (réécrit), `docs/README.md`, `docs/experiments/{README,TEMPLATE}.md`, `docs/decisions/ADR-0001-conserver-package-src.md`, `docs/reports/2026-09-24_analyse_depot.md`, ce rapport, les README de `models/`, `controllers/`, `simulation/`, `ros2_ws/`, `datasets/`, `results/`, `tests/`, `legacy/`, des `.gitkeep` dans les dossiers vides et des `__init__.py` dans `tests/*_tests/`.

## Vérifications effectuées

| Vérification | Résultat |
|---|---|
| Chargement de `simulation/urdf/Stewart.urdf` dans PyBullet (DIRECT) | ✅ 50 joints, 51 formes visuelles, **0 maillage manquant** |
| `python3 -m pytest tests/unit_tests` | 10 réussis, 1 échec **identique à avant** (`test_solve_neutral_position`, attente erronée) |
| `py_compile` de tous les `.py` | ✅ |
| `SystemChecker` : structure, URDF, configuration | ✅ 10/10 dossiers, URDF + 51 maillages, YAML trouvés |
| `configurations/platform_config.yaml` → `urdf_path` | `simulation/urdf/Stewart.urdf` |
| `git check-ignore` sur les médias déplacés | ✅ Non ignorés (sauf le HTML généré, volontairement) |

Non vérifié : lancement interactif des GUI Tk et PyBullet (pas d'affichage disponible). Les modifications qui les concernent se limitent aux chaînes de chemin ci-dessus.

## Actions proposées (non réalisées, à valider)

1. **Commiter** l'état restructuré (l'essentiel du travail de 2025 n'est pas encore commité).
2. Supprimer `legacy/Stewart_original/` et `legacy/archives/Stewart.zip` (doublons exacts, ~11 Mo, récupérables dans l'historique git).
3. Supprimer `__init__.py` à la racine (fait du dépôt un package, ce qui perturbe la découverte des tests par pytest).
4. Remplacer `requirements.txt` par les dépendances réelles : `numpy`, `matplotlib`, `pybullet`, `pyyaml`, `pytest`.
5. Corriger l'attente de `test_solve_neutral_position`.
6. Réparer ou archiver `examples/basic_control.py` et `tests/integration_tests/test_{no_gui,physical_platform}.py`.
7. Retirer l'entrée `stewart-test` de `setup.py` (module inexistant).
8. Réduire les 5 lanceurs à un seul.
9. Arbitrer l'anomalie A1 (Phase 2), qui est prioritaire avant toute exploitation des résultats de simulation.

Les phases 1 à 8 de [ROADMAP.md](../../ROADMAP.md) prennent le relais pour les évolutions métier.
