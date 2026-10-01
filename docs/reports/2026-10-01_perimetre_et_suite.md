# Périmètre des dépôts, état et suite (2026-10-01)

Rapport daté : il fixe l'état au 2026-10-01 et ne sera pas réécrit. L'état courant est dans [ROADMAP.md](../../ROADMAP.md).

## 1. Deux dépôts, deux rôles

| | **Stewart-Platform** (ce dépôt, `jbernardo6u/Stewart_platform_SIM`) | **Demonstrateur_REM** (`ABMI-software/Demonstrateur_REM`) |
|---|---|---|
| Objet | **La plateforme de Stewart seule** (« motion platform », MP) | **Le banc d'attelage de précision complet** : MP de Stewart + actionneur linéaire d'approche sur rail + caméra, IMU, cible Space Lock |
| Contenu | Modèles (IK, FK, jacobien, singularités), simulation PyBullet validée, tableau de bord, et à venir : Gazebo de la MP seule, essais sur la MP réelle imprimée en 3D | Logiciel ROS 2 Jazzy du banc (`stewart_control`), firmware Arduino, perception ArUco, fusion IMU, IHM, documentation du banc |
| Rôle | Laboratoire de la MP : mettre au point et valider les modèles et la commande sur un système simple | Dépôt de référence du projet : **les développements du banc se font là** |
| Matériel | MP imprimée en 3D (à inventorier, [PROT-001](../protocols/PROT-001-inventaire-banc.md)) | Banc REM, aujourd'hui **gelé** : le système mécanique ne tient pas aux essais |

Décision : [ADR-0004](../decisions/ADR-0004-perimetre-des-depots.md).

## 2. Pourquoi simuler le banc complet sous Gazebo

Le banc d'attelage est finalisé côté logiciel, mais **sa mécanique ne tient pas** : les motoréducteurs manquent de couple face à la gravité, et la plateforme est montée couchée, avec des vérins en porte-à-faux ; le support de la caméra est fragile. Les mouvements commandés ne sont pas exécutés, ou seulement en partie, et sans répétabilité.

Le but est donc de **reproduire le même système en simulation** (même logiciel, même géométrie, mêmes capteurs) pour :

1. continuer à développer et valider le logiciel sans le matériel ;
2. **étudier le système mécanique** (efforts, couple nécessaire, rigidité) et dimensionner une version qui tienne ;
3. puis fabriquer cette version, et revalider sur le banc.

Ces développements se feront dans **Demonstrateur_REM**. Le prototype de jumeau construit ici ([EXP-009](../experiments/EXP-009-jumeau-gazebo-demonstrateur.md)) sert de point de départ, à y migrer.

## 3. État au 2026-10-01

### Stewart-Platform (MP seule)

| Élément | État | Référence |
|---|---|---|
| Simulation PyBullet en boucle fermée | ✅ 0,28 mm / 0,044° | EXP-004 |
| IK validée contre le URDF | ✅ | EXP-002 |
| FK, jacobien, singularités | ✅ aller-retour 10⁻¹² m, 0,8 ms | EXP-008 (PR #3 fusionnée) |
| Tableau de bord (CustomTkinter) | ✅ | PR #2 |
| Gazebo de la MP seule | ⬜ | §5 |
| Essais sur la MP imprimée en 3D | ⬜ inventaire à faire | PROT-001, ADR-0002 |

### Prototype de jumeau du banc complet (branche `gazebo-bench-twin`, PR à venir)

Le code ROS 2 du banc (`aruco_node`, `imu_node`, `fusion_node`, `manual_stewart_node`, `stewart_node`) tourne sans modification sur Gazebo Harmonic. Arduino virtuel sur pseudo-terminal, caméra rendue aux intrinsèques du banc, IMU simulée ([ADR-0003](../decisions/ADR-0003-jumeau-gazebo-demonstrateur.md), [guide](../guides/GAZEBO_BANC_REM.md)).

**Acquis, indépendants de la scène** : rendu ArUco fidèle (0,7 % en profondeur, 0,06 mm latéral à 30 cm) ; défauts du banc chiffrés (D1 : x, y et lacet inversés par l'IK ; D9 : décalage de L0) ; deux défauts nouveaux, D13 (lissage puis zone morte dans `aruco_node`, jusqu'à 6,8 mm d'erreur statique) et D14 (OpenCV 4.6 : `DetectorParameters()` provoque une erreur de segmentation) ; limite de résolution du firmware (tolérance de 0,10 cm).

**Scène à refaire** : le prototype suppose une caméra embarquée sur la plateforme, un marqueur fixe et une plateforme debout. La description du banc établie d'après photos (2026-10-01) dit l'inverse :

| | Prototype actuel | Banc d'après les photos |
|---|---|---|
| Caméra (Arducam IMX219) | sur la plateforme mobile | **fixe**, au bout d'un bras col de cygne, dans le disque Space Lock côté cible |
| Marqueur ArUco 26 | fixe, côté cible | **sur la plaque mobile**, au centre du second disque Space Lock |
| Plateforme | debout, normale verticale | **couchée** : normale horizontale, dans l'axe du rail, vers la cible ; vérins en porte-à-faux |
| Distance caméra → marqueur | 30 cm (hypothèse) | ≈ 20 cm (overlay relevé, marqueur tenu à la main) |
| Actionneur d'approche | absent | rail linéaire à moteur pas à pas, contrôleur séparé, course de 800 mm à confirmer |
| Vérins | toujours à la consigne (cinématique) | **couple insuffisant** : le jumeau ne doit pas masquer ce verrou |

Une réponse antérieure (« caméra embarquée sur la plateforme ») contredit les photos : **à confirmer**. « Embarquée » désignait peut-être le disque Space Lock.

## 4. Repères proposés pour le banc complet (à valider)

- `{W}` monde : Z vers le haut, gravité −Z (REP-103), X le long du rail, vers la cible.
- `{R}` chariot du rail : translation `s(t)` selon X.
- `{B}` base Stewart, en haut de la colonne : **z_B = +X_W** (plateforme couchée) ; rotation autour de z_B (quel vérin est en haut) **À MESURER**.
- `{P}` plaque mobile : convention de l'IK du banc (centre en `(0, 0, 0,185) + T` dans `{B}`, `R = Rx·Ry·Rz`).
- `{M}` marqueur 26 : sur la plaque, z_M vers la caméra ; décalage et rotation dans le plan **À MESURER**.
- `{C}` caméra : fixe, face au marqueur (z_C ≈ −z_M, d'où un roll de ±180°, normal) ; pose **À MESURER**, et elle change à chaque réglage du col de cygne. D'où la proposition d'une calibration main-œil à chaque session, en déplaçant la plateforme de valeurs connues.
- `{T}` interface Space Lock côté cible, solidaire de `{C}`.

Points d'attention relevés dans le dépôt du banc : IMU et plateforme couchée (pitch ≈ ±90°, singularité d'Euler dans `compute_rpy` si l'IMU est sur la plaque) ; mesure caméra dépendante de la pose de la plateforme, utilisée comme consigne absolue par `stewart_node` (D3) ; `reference_position_m: [0, 0, 0]` ; `calib_ext3.npz` étranger au montage actuel ; détection à 8–10 Hz et latence de 198 ms, contre 33 Hz dans la configuration et 0,2 s de délai maximal dans la fusion ; demi-angles 11,3°/17,3° à rapprocher de la pré-étude (Da, Db, Ea, Eb) ; échelle des codeurs (poulie Ø 2 cm, 960 ticks, voie A seule) ; PWM du firmware jusqu'à 230 dans la zone de couple faible ; aucun nœud ROS pour le rail.

## 5. Suite

### Dans Stewart-Platform (MP seule)

1. Fusionner la PR du prototype de jumeau (référence pour la migration).
2. **Inventaire de la MP imprimée en 3D** (PROT-001) : géométrie, course, électronique ; préciser si elle correspond au URDF de 20 cm ou au banc de 7,5 cm.
3. **Gazebo de la MP seule** : réutiliser l'approche du prototype (mécanisme cinématique piloté par la FK, rendu Gazebo), paramétrée par la géométrie de la MP choisie ; ensuite, si nécessaire, mécanisme fermé dynamique.
4. **Statique en position couchée** : efforts `f = J⁻ᵀ·w` sur l'espace de travail avec le jacobien de la Phase 2. Masse et centre de gravité en paramètres. Cela répond directement au verrou de couple (Phase 3, V-4).
5. Essais sur la MP réelle si son électronique le permet : même interface que la simulation (ADR-0002, à réviser).

### Dans Demonstrateur_REM (banc complet, développements de référence)

1. Migrer le prototype : `src/rem_bench` → `models/` et `simulation/` du banc ; `ros2_ws/src/rem_bench_sim` → paquet de simulation du banc ; FK de la Phase 2 → `models/kinematics`.
2. Refaire la scène d'après les photos : caméra fixe sur col de cygne, marqueur sur la plaque, plateforme couchée, gravité, distance d'environ 20 cm, cadence de 8–10 Hz et latence de 200 ms.
3. Ajouter le rail (actionneur d'approche) et son contrôleur virtuel.
4. Vérins limités en effort (calage au-delà de l'effort disponible) : reproduire le verrou mécanique au lieu de le masquer.
5. Corriger D1, D2, D3, D13, D14, puis tester une loi de commande qui tienne compte de la pose courante, avec un critère de convergence en boucle fermée.
6. Dimensionner une mécanique qui tienne (couple, rigidité), à partir des efforts simulés.

### Informations à obtenir sur le banc (paramètres de configuration, jamais en dur)

Confirmation du montage caméra/marqueur ; pose de la base (hauteur de colonne, rotation autour de la normale) ; pose de la caméra ; pose du marqueur sur la plaque ; pose de référence à l'alignement (30 s en mode Acquisition, moyenne et écart-type) ; montage de l'IMU ; course du rail ; masse et centre de gravité de la partie mobile ; vitesse et effort des vérins ; échelle des codeurs (10 cm commandés, mesurés au pied à coulisse).
