# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [Non publié]

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
