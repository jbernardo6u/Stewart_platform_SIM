# tests/

| Dossier | Contenu | Commande |
|---|---|---|
| `unit_tests/` | Tests unitaires sans GUI ni simulateur (`test_kinematics.py`) | `python3 -m pytest tests/unit_tests` |
| `integration_tests/` | Scripts hérités nécessitant PyBullet et/ou un affichage | à lancer manuellement |
| `validation_tests/` | Comparaison simulation/réel (Phase 7) | aucun test pour l'instant |

État connu (voir `docs/reports/2026-09-24_analyse_depot.md`) :

- `unit_tests/test_kinematics.py::test_solve_neutral_position` échoue : l'attente (‖home_pos‖) est fausse, pas l'IK.
- `integration_tests/test_no_gui.py` et `test_physical_platform.py` importent des modules qui n'existent plus à la racine (`StewartPlatform`, `physical_stewart`).
- `integration_tests/test_pybullet_gui.py` ouvre une fenêtre PyBullet : core dump sans affichage.
