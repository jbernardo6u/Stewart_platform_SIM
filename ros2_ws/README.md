# ros2_ws/ : espace de travail ROS2

Vide : le projet ne contient encore aucun code ROS2. Nodes, topics, services et actions envisagés : [ARCHITECTURE.md](../ARCHITECTURE.md#architecture-ros2-envisagée-phase-5).

Règle : les packages de `src/` ici n'embarquent **aucune logique métier**. Ils importent `models` et `controllers`.
