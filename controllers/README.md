# controllers/ : contrôle (niveau 5)

| Sous-dossier | Implémentation actuelle |
|---|---|
| `inverse_kinematics/` | `src/core/kinematics.py::InverseKinematics` (pose → longueurs de vérins) |
| `forward_kinematics/` | aucune (Phase 2) |
| `trajectory_generation/` | `src/core/scenarios.py` (scénarios horodatés, lois d'ordre 5), `src/core/feasibility.py` (course des vérins) ; historique : `src/core/trajectory.py` (géométrique, sans loi horaire) |
| `motion_control/` | `src/core/platform.py::StewartPlatform.move_to_pose` (bloquant) et `command_pose` (non bloquant) ; `src/gui/dashboard_controller.py` (lecture de scénarios, écart de suivi) |
| `servo_control/` | `src/hardware/motor_controller.py` (stub, correcteur P) ; interface banc prévue par [ADR-0002](../docs/decisions/ADR-0002-interface-commune-simulation-banc.md) |

Le code reste dans `src/` pendant la transition (voir [ADR-0001](../docs/decisions/ADR-0001-conserver-package-src.md)).
