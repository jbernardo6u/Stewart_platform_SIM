# Jumeau Gazebo du démonstrateur REM

Simulation du banc réel (dépôt `ABMI-software/Demonstrateur_REM`) sous Gazebo Harmonic. Les nœuds ROS 2 du banc (`stewart_control`) tournent **sans modification** : l'Arduino, la caméra et l'IMU sont remplacés à leurs interfaces. Décision : [ADR-0003](../decisions/ADR-0003-jumeau-gazebo-demonstrateur.md). Validation : [EXP-009](../experiments/EXP-009-jumeau-gazebo-demonstrateur.md).

## Prérequis

- Ubuntu 24.04, ROS 2 **Jazzy**, Gazebo **Harmonic** : `ros-jazzy-ros-gz` (fournit `ros_gz_sim`, `ros_gz_bridge` et les liaisons Python `gz.transport13`/`gz.msgs10`), `ros-jazzy-cv-bridge`, `python3-opencv` (4.6, apt), `python3-serial`, `python3-yaml`.
- Le dépôt du banc (paquet `stewart_control`) et ce dépôt.
- Sous WSL2 : un GPU (rendu hors écran EGL). Ni `socat`, ni `v4l2loopback`, ni droits administrateur ne sont nécessaires.

## Construction

Un espace de travail séparé, qui ne touche pas celui du banc :

```bash
mkdir -p ~/rem_sim_ws && cd ~/rem_sim_ws
git clone https://github.com/jbernardo6u/Stewart_platform_SIM.git Stewart-Platform
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install \
  --base-paths ~/rem_sim_ws/Stewart-Platform/ros2_ws/src ~/ros2_MP_ws/ros2_ws/src
source install/setup.bash
```

`--symlink-install` est nécessaire : `rem_bench_sim` retrouve ainsi le dépôt Stewart-Platform (`src/rem_bench`). Sinon, définir `STEWART_PLATFORM_ROOT`.

## Lancement

```bash
ros2 launch rem_bench_sim bench_sim.launch.py mode:=acquisition   # caméra, IMU, fusion ; aucun vérin
ros2 launch rem_bench_sim bench_sim.launch.py mode:=manual        # + manual_stewart_node
ros2 launch rem_bench_sim bench_sim.launch.py mode:=auto          # + stewart_node (commande automatique)
ros2 launch rem_bench_sim bench_sim.launch.py mode:=manual gui:=true   # fenêtre Gazebo
```

Au lancement, `~/.rem_bench_sim/` reçoit :

- `stewart_params_sim.yaml` : le `stewart_params.yaml` du banc, avec `serial.port` vers le port virtuel et les références d'orientation recalculées pour le montage simulé (`STEWART_CONFIG`) ;
- `motor_runtime_state.json` « home confirmé » (`STEWART_RUNTIME_DIR`) : l'état du banc réel (`~/.stewart_control`) n'est jamais modifié ;
- `ttyVIRT` : lien vers le pseudo-terminal de l'Arduino virtuel ;
- `world/rem_bench.sdf` : le monde, généré depuis `configurations/bench_rem.yaml`.

## Piloter et observer

Commandes manuelles, comme l'interface du banc (position en cm, orientation en degrés, relatives à home) :

```bash
ros2 topic pub --once /manual_orientation std_msgs/msg/Float32MultiArray "{data: [0, 0, 0]}"
ros2 topic pub --once /manual_position    std_msgs/msg/Float32MultiArray "{data: [0, 0, 3]}"
```

| Topic | Origine | Contenu |
|---|---|---|
| `/aruco_position`, `/aruco_orientation`, `/camera/image_raw` | `aruco_node` du banc | mesure caméra (m, °), aperçu annoté |
| `/imu_error`, `/imu_gyro` | `imu_node` du banc | orientation (°), vitesse angulaire |
| `/F_pose` | `fusion_node` du banc | pose fusionnée |
| `/stewart/longueurs` | nœud de commande du banc | consignes des vérins (cm) |
| `/rem_bench/camera/image` | Gazebo | image brute de la caméra embarquée |
| `/sim/encoders_cm` | jumeau | codeurs simulés (cm) |
| `/sim/platform_pose` | jumeau | pose physique vraie de la plateforme (repère base) |
| `/sim/marker_in_camera` | jumeau | pose vraie du marqueur dans l'optique caméra |

Campagne EXP-009 (pendant `mode:=manual`) : `ros2 run rem_bench_sim exp009_campaign --ros-args -p output_dir:=<dossier>`.

L'interface PySide6 du banc (`interface_node`) lance elle-même les fichiers launch du matériel : elle n'est pas encore utilisable avec le jumeau. Elle peut cependant observer les topics.

## Paramètres et hypothèses

`configurations/bench_rem.yaml` distingue les valeurs relevées sur le banc des **hypothèses** à mesurer : montage de la caméra et de l'IMU, position du marqueur, vitesse des vérins. Les modifier ne demande que de relancer (le monde est régénéré).

## Écarts connus avec le banc

- Gazebo est cinématique : ni jeux, ni souplesse, ni dynamique des vérins (seulement l'émulation du firmware).
- Caméra : sténopé idéal aux intrinsèques du banc, sans distorsion ni bruit (le nœud ArUco simulé utilise une distorsion nulle).
- Le jumeau contourne le défaut D14 (OpenCV 4.6 : `DetectorParameters()` provoque une erreur de segmentation). Le banc reste à corriger.
