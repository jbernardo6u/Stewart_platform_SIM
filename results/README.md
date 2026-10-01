# results/ : sorties générées

Chaque résultat se rattache à une fiche `docs/experiments/EXP-XXX` et se régénère avec son script (`scripts/experiments/`, ou tout d'un coup : `python3 scripts/run_validation.py`). Les figures versionnées vont dans `**/figures/`.

| Sous-dossier | Contenu | Source |
|---|---|---|
| `geometry/` | `exp001_attachment_points.csv` : centres des cardans identifiés dans le URDF | EXP-001 |
| `kinematics/` | `exp002_leg_axes.csv`, `exp002_dynamic.csv` : IK contre URDF | EXP-002 |
| | `exp007_dof_ranges.csv`, `figures/exp007_xy_maps.png` : espace de travail limité par la course | EXP-007 |
| | `figures/output*.png` : figures du notebook `models/kinematics/notebooks/analysis.ipynb` | historique |
| `experiments/` | `exp004_tracking.csv` : suivi de pose en boucle fermée | EXP-004 |
| | `videos/` : vidéos PyBullet historiques | historique |
| | `web/` : visualisation HTML de `scripts/create_web_viz.py` (ignorée par git) | — |
| `dynamics/` | vide | Phase 3 |

Sorties de démonstration non versionnées : `output/trajectories/` (`scripts/run_trajectory.py --save`), `output/videos/` (`scripts/create_video.py`).
