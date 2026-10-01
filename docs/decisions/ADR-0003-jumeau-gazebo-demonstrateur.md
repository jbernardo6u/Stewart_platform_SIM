# ADR-0003 : Jumeau Gazebo du démonstrateur, matériel remplacé à ses interfaces

- **Date** : 2026-10-01
- **Statut** : Proposée (à valider)
- **Révise** : [ADR-0002](ADR-0002-interface-commune-simulation-banc.md) sur le point « passer à ROS 2, trop tôt »
- **Portée précisée par** [ADR-0004](ADR-0004-perimetre-des-depots.md) : ce jumeau est un **prototype**, dont la suite (scène corrigée, rail, vérins limités en effort) se développe dans Demonstrateur_REM

## Contexte

- Le banc réel est développé sous **ROS 2 Jazzy** (dépôt `ABMI-software/Demonstrateur_REM`, paquet `stewart_control`) : caméra USB embarquée sur la plateforme, marqueur ArUco, IMU MPU-9250, Arduino Mega en liaison série. Sa géométrie (base de 7,5 cm, plateforme de 4 cm, vérins de 10 cm) n'est **pas** celle du URDF de ce dépôt (20 cm, 19 cm).
- Les mouvements du banc sont gelés (support de caméra fragile) : il faut valider le logiciel du banc en simulation, caméra comprise.
- ADR-0002 prévoyait une interface Python commune (`PlatformBackend`) et jugeait ROS 2 prématuré. L'existence d'un logiciel ROS 2 complet sur le banc inverse ce jugement.

## Décision

1. Le jumeau du démonstrateur remplace le matériel **à ses interfaces exactes**, pour que le code du banc tourne sans modification :
   - Arduino → `virtual_hardware` : pseudo-terminal sur `serial.port`, protocole et comportement de `pilotage_feedback_mp.ino` ;
   - caméra → capteur caméra Gazebo (intrinsèques du banc), image transmise à `aruco_node` par une sous-classe qui ne change que `_open_camera` ;
   - IMU → doublures de `smbus`/`imusensor` qui alimentent `imu_node`.
2. Gazebo Harmonic sert au **rendu des capteurs** ; le mécanisme est cinématique (FK des codeurs, poses imposées). La dynamique reste à PyBullet (Phase 3) tant que les efforts ne sont pas nécessaires dans Gazebo.
3. Modèles et émulations en Python pur dans `src/rem_bench/` (testés dans la CI de ce dépôt) ; le paquet ROS 2 `ros2_ws/src/rem_bench_sim` n'a pas de logique métier.
4. Paramètres du mécanisme et hypothèses de montage dans `configurations/bench_rem.yaml` ; la configuration des nœuds du banc est **dérivée** de leur `stewart_params.yaml` (seuls `serial.port` et les références d'orientation changent).
5. Le dépôt du banc n'est pas modifié par le jumeau. Les défauts trouvés lui sont remontés (EXP-009 : D13, D14).

## Options écartées

- **Réécrire des nœuds simulés** publiant les mêmes topics : rapide, mais ne teste pas le code du banc (IK, calibration, série, fusion).
- **Caméra virtuelle V4L2** (`v4l2loopback`) : module noyau indisponible sous WSL2.
- **Mécanisme dynamique fermé sous Gazebo** dès maintenant : fermeture de boucle délicate, inutile pour valider la chaîne logicielle et la caméra.
- **Code du jumeau dans le dépôt du banc** : possible plus tard ; il dépend aujourd'hui de la FK et des outils de ce dépôt (jumeau numérique).

## Conséquences

- ➕ Les modes manuel et automatique, et les corrections D1 à D3, se testent sans risque pour le matériel.
- ➕ Même logiciel en simulation et sur le banc : la validation simulation/réel (Phase 7) devient un rejeu.
- ➖ Deux environnements : ce dépôt (Ubuntu 22.04, PyBullet) et le jumeau (Ubuntu 24.04, Jazzy). Guide : `docs/guides/GAZEBO_BANC_REM.md`.
- ➖ Les hypothèses de montage (caméra, marqueur, vitesse des vérins) bornent la fidélité tant qu'elles ne sont pas mesurées.
- ➖ ADR-0002 (`BenchPlatform` en Python) est à réviser : le tableau de bord PyBullet ne pilote pas le banc ROS 2 ; un pont ROS 2 serait nécessaire si on le souhaite.
