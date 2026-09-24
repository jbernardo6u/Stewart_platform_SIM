# simulation/ : niveau 1

| Sous-dossier | Contenu |
|---|---|
| `urdf/` | `Stewart.urdf` (51 liens, 50 joints), `Link_graph.txt` (graphe des liens), `hello_bullet.py` (test de chargement PyBullet, à lancer depuis ce dossier) |
| `meshes/` | 51 maillages STL (échelle 0,001 appliquée dans le URDF) |
| `gazebo/`, `worlds/`, `launch/` | à créer (Phase 4) |

Le URDF référence les maillages en `../meshes/*.stl`.

Pièges connus (EXP-004) : configuration zéro = vérins en butée basse ; 11 articulations passives limitées à [0 ; 2π], recentrées à l'exécution par `StewartPlatform.setup_constraints()`. L'adaptateur PyBullet est dans `src/core/platform.py` et `src/simulation/pybullet_sim.py`.

Fermeture de boucle : voir [ARCHITECTURE.md](../ARCHITECTURE.md#niveau-1--simulation).
