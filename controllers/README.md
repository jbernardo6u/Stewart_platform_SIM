# controllers/ : contrôle (niveau 5)

| Sous-dossier | Implémentation actuelle |
|---|---|
| `inverse_kinematics/` | `src/core/kinematics.py::InverseKinematics` (pose → longueurs de vérins) |
| `forward_kinematics/` | aucune (Phase 2) |
| `trajectory_generation/` | `src/core/trajectory.py` (trajectoires géométriques, sans loi horaire) |
| `motion_control/` | `src/core/platform.py::StewartPlatform.move_to_pose` (interpolation linéaire) |
| `servo_control/` | `src/hardware/motor_controller.py` (stub, correcteur P) |

Le code reste dans `src/` pendant la transition (voir [ADR-0001](../docs/decisions/ADR-0001-conserver-package-src.md)).
