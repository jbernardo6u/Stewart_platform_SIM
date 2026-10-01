# ros2_ws/ : espace de travail ROS 2 (Jazzy)

| Paquet | Rôle |
|---|---|
| [`src/rem_bench_sim`](src/rem_bench_sim) | Jumeau Gazebo du démonstrateur REM : Arduino virtuel, caméra et IMU simulées ; les nœuds `stewart_control` du banc tournent sans modification ([ADR-0003](../docs/decisions/ADR-0003-jumeau-gazebo-demonstrateur.md), [EXP-009](../docs/experiments/EXP-009-jumeau-gazebo-demonstrateur.md)) |

Construction, lancement et topics : [docs/guides/GAZEBO_BANC_REM.md](../docs/guides/GAZEBO_BANC_REM.md). Environnement : Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic (celui du banc), distinct de celui de PyBullet.

Règle : les paquets de `src/` n'embarquent **aucune logique métier**. Ils importent `src.rem_bench`, `src.core` (modèles, FK) du dépôt.
