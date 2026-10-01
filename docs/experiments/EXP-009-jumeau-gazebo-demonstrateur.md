# EXP-009 : jumeau Gazebo du démonstrateur REM, nœuds du banc inchangés

- **Date** : 2026-10-01
- **Auteur(s)** : jbernardo6u (avec Claude Code)
- **Phase roadmap** : Phase 4 (simulation complète), préparation des Phases 5 et 7
- **Verrou(s)** : V-7 (fidélité du jumeau), V-8 (simulation), V-2 (FK utilisée pour la pose)
- **Commit du code utilisé** : commit qui introduit cette fiche (branche `gazebo-bench-twin`) ; banc : `ABMI-software/Demonstrateur_REM@36fd541`
- **Configuration** : `configurations/bench_rem.yaml` (mécanisme, caméra, marqueur, IMU) ; `stewart_params.yaml` du banc, adapté par `src/rem_bench/sim_config.py`
- **Environnement** : Ubuntu 24.04 (WSL2), ROS 2 Jazzy, Gazebo Harmonic (gz-sim 8.9), OpenCV 4.6 (apt), GPU NVIDIA T1200, rendu hors écran EGL
- **Données** : aucune mesure réelle (banc à l'arrêt, ADR-0002 du dépôt du banc)
- **Résultats** : `results/simulation/exp009_manual.csv`, `results/simulation/figures/exp009_camera_home.png`
- **Code** : `src/rem_bench/`, `ros2_ws/src/rem_bench_sim/` ; tests `tests/unit_tests/test_rem_bench.py` ; guide `docs/guides/GAZEBO_BANC_REM.md`

## Titre

Jumeau Gazebo du démonstrateur : caméra embarquée rendue, Arduino virtuel, et code ROS 2 du banc exécuté sans modification.

## Contexte

Le banc réel (hexapode de 7,5 cm / 4 cm, vérins de 10 cm, caméra USB embarquée sur la plateforme, marqueur ArUco 26, IMU MPU-9250, Arduino Mega) est piloté par le paquet ROS 2 `stewart_control`. Ses mouvements sont gelés : le support de la caméra est trop fragile. Les modes manuel et automatique ne sont donc plus testables sur le matériel. Le jumeau existant (PyBullet, URDF de 20 cm) décrit une autre plateforme et ne parle pas ROS.

## Verrou scientifique

Valider en simulation le **logiciel réel** du banc, et non une réécriture : le jumeau doit remplacer le matériel à ses interfaces exactes (protocole série de l'Arduino, image caméra, capteur IMU), avec une image caméra assez fidèle pour que la chaîne ArUco du banc mesure correctement.

## Hypothèse

- H1 : sans modifier `stewart_control`, on peut faire tourner `aruco_node`, `imu_node`, `fusion_node`, `manual_stewart_node` et `stewart_node` sur la simulation.
- H2 : la pose ArUco mesurée sur l'image Gazebo coïncide avec la vérité, à la précision du détecteur (< 1 % de la distance, < 0,5 mm latéralement à 30 cm).
- H3 : le jumeau reproduit les défauts connus du banc (D1 inversion base/plateforme dans l'IK, D9 décalage de L0) et peut en révéler d'autres.

## Méthodologie

**Architecture** (voir [ADR-0003](../decisions/ADR-0003-jumeau-gazebo-demonstrateur.md)) :

| Matériel du banc | Remplaçant | Code du banc exécuté |
|---|---|---|
| Arduino Mega + 6 vérins | `virtual_hardware` : pseudo-terminal (`serial.port`), émulation de `pilotage_feedback_mp.ino` (tolérances 0,10/0,25 cm, PWM 115 à 230, rampe), FK des codeurs → pose physique | `manual_stewart_node`, `stewart_node` (IK, calibration, série) |
| Caméra USB | capteur caméra Gazebo embarqué sur la plateforme, intrinsèques de `calib_int.npz`, rendu EGL, pont `ros_gz_bridge` | `aruco_node` (sous-classe : seule `_open_camera` change) |
| MPU-9250 | doublures de `smbus` et `imusensor`, mesures déduites de la pose vraie | `imu_node` (calculs, remappage, référence) |
| — | `fusion_node` du banc, tel quel | `fusion_node` |

- Mécanisme : géométrie du banc (`stewart_params.yaml`) avec les **vraies** attaches (base = grand cercle, conforme au schéma `stewart_hexapod_motor_layout.png`). Gazebo est cinématique : les poses des corps sont imposées à 50 Hz (`set_pose_vector`) depuis la FK (EXP-008).
- Étalonnage simulé : `reference_orientation_deg` de la caméra et de l'IMU recalculées pour le montage simulé (orientation publiée nulle à home, comme après l'étalonnage du banc) ; `reference_position_m` conservée telle quelle (`[0, 0, 0]`).
- **Hypothèses non mesurées** (bench_rem.yaml) : caméra au bord +x de la plateforme (5 cm du centre, 2 cm au-dessus), axe optique horizontal ; marqueur à 30 cm devant ; vitesse des vérins 2 cm/s à PWM 255 ; IMU alignée sur la plateforme.
- Mesures : acquisition à home (image, ArUco/vérité), puis 9 consignes manuelles envoyées comme l'interface (`/manual_position` en cm, `/manual_orientation` en °), 12 s de stabilisation chacune (`ros2 run rem_bench_sim exp009_campaign`). Pose atteinte = FK des codeurs simulés, comparée à la consigne ; position ArUco comparée à la vérité.
- Séparation des causes : calcul hors ROS de la pose atteinte avec l'IK du banc (D1) puis avec l'IK corrigée, sans le firmware.

## Résultats

**Fonctionnement** : les 5 nœuds du banc tournent sur la simulation. Image à 25,8 Hz (30 demandés), chaîne complète caméra → `aruco_node` → `fusion_node` → `/F_pose`, IMU → `/imu_error`, `/imu_gyro`.

**Caméra et ArUco à home (marqueur à 30,0 cm)** :

| Variante du rendu | Écart des coins (px) | Profondeur estimée | Latéral |
|---|---|---|---|
| marqueur texturé, `cx`/`cy` de calibration | jusqu'à −0,98 | 30,73 cm (+2,4 %) | 0,36 mm |
| marqueur en géométrie, `cx`/`cy` + 0,5 px | ≤ 0,26 | 30,22 cm (+0,7 %) | 0,06 mm |
| image synthétique idéale (référence du détecteur) | ≤ 0,20 | — | — |

**Mode manuel** (`exp009_manual.csv`, extraits) :

| Consigne (cm, °) | Atteint dans le jumeau | IK du banc, sans firmware | IK corrigée, sans firmware |
|---|---|---|---|
| z +3 | z 2,90 | z 3,00 | z 3,00 |
| x +1, z +3 | x −0,61 | x −1,00 | x +1,00 |
| roll +5, z +3 | roll 4,02, **y −1,60** | roll 5, y −1,87 | roll 5, y 0 |
| pitch +5, z +3 | pitch 4,57, **x +1,49** | pitch 5, x +1,87 | pitch 5, x 0 |
| yaw +10, z +3 | **yaw −7,14** | yaw −10 | yaw +10 |
| (1, −1, 5), (3, −3, 8) | (−2,27 ; 0,08 ; 4,85), (2,54 ; −3,28 ; −7,79) | (−2,24 ; 0,08 ; 4,94), (2,56 ; −3,38 ; −7,85) | consigne exacte |

**Écart ArUco/vérité après stabilisation** : 2,4 mm à home, puis 5,8 à 12,1 mm (norme) après chaque mouvement.

**Mode automatique** (configuration du banc telle quelle) : `stewart_node` refuse toutes les consignes (« hors débattement commun », M1 à M6 ≈ 30 cm logiques) ; la plateforme ne bouge pas.

## Analyse

- **H1 validée.** Le code du banc tourne tel quel ; seules les interfaces matérielles sont remplacées, et le comportement observé est celui du code du banc.
- **H2 validée après deux corrections du rendu.** Gazebo place l'origine des pixels au coin, OpenCV au centre : image décalée de −0,5 px, corrigé dans le SDF. Un marqueur texturé est rendu trop petit d'environ 0,5 px par bord (filtrage de la texture) : remplacé par des quads. Le résidu (+0,7 % en profondeur, 0,06 mm latéral) est celui du détecteur sur un marqueur de 38 px.
- **H3 validée, et trois défauts nouveaux** :
  - **D1 confirmé et quantifié** : l'IK du banc **inverse x, y et le lacet** et ajoute ±1,87 cm de translation parasite pour 5° de roulis ou de tangage. Avec l'IK corrigée, la consigne serait exacte. La boucle automatique du banc ne peut pas converger sur le lacet ni en x/y tant que D1 n'est pas corrigé.
  - **D9 confirmé** : à codeurs nuls, la plateforme est 2,06 mm sous la pose home de l'IK (L0 = 18,86 cm contre 19,06 cm).
  - **Résolution du firmware** : la tolérance d'arrêt de 0,10 cm par vérin, et le seuil de 0,10 cm sous lequel une nouvelle consigne n'est pas exécutée, limitent la précision des petits mouvements : 4 mm d'erreur sur 1 cm en x, 2,9° sur 10° de lacet.
  - **D13 (nouveau) — `aruco_node` : lissage puis zone morte.** La zone morte est appliquée à la valeur **déjà lissée** (α = 0,22) : dès que α·(mesure − précédente) < 1,5 mm, la valeur reste figée. L'erreur statique peut atteindre 1,5/0,22 = **6,8 mm par axe** (0,35/0,22 = 1,6° en orientation), ce qui explique les 5,8 à 12,1 mm observés. Correction possible : zone morte sur la mesure brute, puis lissage.
  - **D14 (nouveau) — OpenCV 4.6** : `cv2.aruco.DetectorParameters()` provoque une erreur de segmentation dès qu'on règle un attribut. `create_detector_parameters()` l'essaie en premier, ce qui fait planter `aruco_node` sous Ubuntu 24.04 avec OpenCV apt (introduit le 2026-06-02, commit `173a6c3`). Le jumeau contourne en masquant ce constructeur ; correction côté banc : essayer `DetectorParameters_create()` d'abord.
  - **Mode automatique inopérant tel que configuré** : `reference_position_m: [0, 0, 0]` fait du vecteur caméra → marqueur brut (30 cm) une consigne de pose. Ça confirme le §2 du `digital_twin_plan.md` du banc : il faut une loi incrémentale *eye-in-hand* (D3 reformulé).
- Limites : géométrie de montage de la caméra et du marqueur, vitesse des vérins et mouvements du mécanisme réel non mesurés ; Gazebo cinématique (ni jeux, ni souplesse, ni dynamique) ; caméra sans distorsion ni bruit ; IMU sans bruit. Tout résultat de cette fiche est **« simulation seule »** jusqu'à confirmation sur le banc.

## Conclusion

H1, H2 et H3 sont validées. Le jumeau Gazebo exécute le logiciel réel du banc et sert déjà d'outil de diagnostic : D1 et D9 sont reproduits et chiffrés, et deux défauts nouveaux sont identifiés (D13, D14), ainsi que la limite de résolution du firmware. Il permet de tester les corrections D1–D3 et la loi *eye-in-hand* avant toute reprise des essais physiques.

## Travaux restants

- Mesurer sur le banc les hypothèses de bench_rem.yaml : montage de la caméra, position du marqueur à l'alignement, vitesse des vérins, montage de l'IMU (`digital_twin_plan.md` §5, PROT-001).
- Rendre la distorsion de la caméra (`calib_int.npz`) et calibrer le bruit caméra et IMU sur des enregistrements du mode Acquisition.
- Remonter D13 et D14 au dépôt du banc ; tester les corrections de D1, D2, D3 et la loi incrémentale dans le jumeau (critère de convergence en boucle fermée).
- Tests d'intégration ROS 2 automatisés (`launch_testing`) et CI Jazzy, sur le modèle de celle du banc.
- Mécanisme dynamique (fermeture de boucle sous Gazebo) si les efforts ou la souplesse deviennent nécessaires (Phase 3).
