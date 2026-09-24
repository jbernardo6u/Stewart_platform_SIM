# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [Non publié]

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
