# tests/

| Dossier | Contenu | Commande |
|---|---|---|
| `unit_tests/` | Tests unitaires sans GUI ni simulateur (`test_kinematics.py`, `test_kinematics_custom_points.py`, `test_physical_platform_config.py`, `test_feasibility_scenarios.py`, `test_forward_kinematics.py`, `test_rem_bench.py`, `test_statics.py`) | `python3 -m pytest tests/unit_tests` |
| `integration_tests/` | `test_physical_platform.py` : script manuel pour le banc réel (matériel requis) | `python3 tests/integration_tests/test_physical_platform.py` |
| `validation_tests/` | Modèle ↔ URDF ↔ simulation, PyBullet DIRECT (~15 s) : `test_ik_urdf_consistency.py` (EXP-002), `test_urdf_geometry.py` (EXP-001), `test_closed_loop_simulation.py` (EXP-004), `test_forward_kinematics_simulation.py` (EXP-008), `test_pybullet_simulator.py`, `test_dashboard_controller.py` (logique du tableau de bord, rendu hors écran) ; simulation/réel en Phase 7 | `python3 -m pytest tests/validation_tests` |

Les anciens scripts `test_no_gui.py` et `test_pybullet_gui.py` (imports obsolètes, fenêtre PyBullet qui plante sans affichage) sont archivés dans `legacy/tests/integration_tests/` : les tests de validation les couvrent.

Tout lancer, campagnes comprises : `python3 scripts/run_validation.py`. La CI GitHub (`.github/workflows/tests.yml`) exécute `unit_tests` et `validation_tests` à chaque push.
