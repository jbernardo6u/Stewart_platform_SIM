# legacy/ : archives non maintenues

Conservé pour référence et traçabilité. **Ne pas importer depuis le code actif.**

| Élément | Origine | Remplacé par |
|---|---|---|
| `StewartPlatform.py`, `inv_kinematics.py`, `main.py`, `draw_3d_spiral.py`, `generate_elliptical_points.py` | Code upstream (mlayek21), ex-racine | `src/core/*` |
| `stewart_gui*.py`, `main_simple.py`, `main_with_gui.py` | Prototypes GUI (2025) | `src/gui/*` |
| `motor_controller.py`, `hardware_config.py`, `physical_stewart.py` | Prototypes matériel | `src/hardware/*` (copies identiques ou quasi identiques) |
| `Stewart_original/` | Ex-`Stewart/` : URDF, maillages, `hello_bullet.py` upstream | `simulation/urdf`, `simulation/meshes` (contenu identique ; ici les chemins de maillages sont restés `meshes/…`) |
| `archives/Stewart.zip` | Archive upstream du dossier `Stewart/` (+ `__MACOSX`) | idem |

⚠️ `inv_kinematics.py` est la **référence** pour l'arbitrage de l'anomalie A1 (Phase 2). Ne pas supprimer.

Candidats à suppression après validation : `Stewart_original/` et `archives/Stewart.zip` (doublons exacts, récupérables dans l'historique git).
