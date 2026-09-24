# models/ : modèles de la plateforme (niveaux 2 à 4)

NumPy pur, sans dépendance à un simulateur ni à une GUI. Voir [ARCHITECTURE.md](../ARCHITECTURE.md).

| Sous-dossier | Contenu actuel | Implémentation actuelle |
|---|---|---|
| `geometry/` | `cad/Stewart_CAD.f3d` (source Fusion 360 du URDF) | `src/core/kinematics.py::InverseKinematics.calculate_attachment_points` (paramétrique), `src/simulation/urdf_geometry.py` (identification depuis le URDF, EXP-001) |
| `kinematics/` | `notebooks/analysis.ipynb` (dérivation de l'IK 6-6) | `src/core/kinematics.py::InverseKinematics` |
| `dynamics/` | aucun | aucune (Phase 3) |
| `calibration/` | aucun | aucune (Phase 6) |
| `identification/` | aucun | aucune (Phases 3 et 6) |

Le code reste dans `src/` pendant la transition (voir [ADR-0001](../docs/decisions/ADR-0001-conserver-package-src.md)).
