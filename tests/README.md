# tests/

| Dossier | Contenu | Commande |
|---|---|---|
| `unit_tests/` | Tests unitaires sans GUI ni simulateur (`test_kinematics.py`, `test_physical_platform_config.py`) | `python3 -m pytest tests/unit_tests` |
| `integration_tests/` | Scripts hérités nécessitant PyBullet et/ou un affichage | à lancer manuellement |
| `validation_tests/` | Cohérence modèle ↔ URDF (`test_ik_urdf_consistency.py`, EXP-002, PyBullet DIRECT) ; simulation/réel en Phase 7 | `python3 -m pytest tests/validation_tests` |

État connu (voir `docs/reports/2026-09-24_analyse_depot.md`) :

- `integration_tests/test_no_gui.py` et `test_physical_platform.py` importent des modules qui n'existent plus à la racine (`StewartPlatform`, `physical_stewart`).
- `integration_tests/test_pybullet_gui.py` ouvre une fenêtre PyBullet : core dump sans affichage.
