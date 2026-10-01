# Reprise du travail : ce qu'il reste à faire

Document **vivant** (mis à jour à chaque fin de session), lu en premier au démarrage d'une session Claude Code (voir [CLAUDE.md](CLAUDE.md)). Dernière mise à jour : **2026-10-01**.

Contexte complet : [rapport du 2026-10-01](docs/reports/2026-10-01_perimetre_et_suite.md) · priorités : [ROADMAP.md](ROADMAP.md) · périmètre : [ADR-0004](docs/decisions/ADR-0004-perimetre-des-depots.md).

## 1. Où on en est

| Élément | État |
|---|---|
| PR #2 (tableau de bord), #3 (FK, jacobien, EXP-008), #4 (périmètre ADR-0004, prototype de jumeau Gazebo du banc, EXP-009) | ✅ fusionnées |
| **PR #5** (`phase3-statique`) : statique des vérins, banc couché ([EXP-010](docs/experiments/EXP-010-statique-plateforme-couchee.md)) | 🟡 **ouverte, CI verte, à fusionner** |
| Tests | 102, verts (`python3 -m pytest tests/unit_tests tests/validation_tests`) |

Résultat principal d'EXP-010 : monté couché, le banc demande **8 à 12 fois plus d'effort** que debout (jusqu'à 25 N par vérin pour 1 kg). Avec les hypothèses de conception (1 kg, 30 N), la statique seule n'explique pas le blocage observé. Une base de 13 à 15 cm (contre 7,5 cm) diviserait les efforts par 2,3.

Rappel du périmètre : **ce dépôt = la plateforme de Stewart seule**. Le banc d'attelage complet (Stewart + rail d'approche) et son jumeau Gazebo se développent dans [ABMI-software/Demonstrateur_REM](https://github.com/ABMI-software/Demonstrateur_REM).

## 2. Mesures à faire sur le banc (bloquantes pour aller plus loin)

À reporter dans `configurations/bench_rem.yaml` (section `statics` ou `geometry`), en remplaçant les hypothèses : jamais en dur dans le code.

- [ ] **Masse et centre de gravité de la partie mobile** : plaque, disque Space Lock, marqueur, cardans. Une balance, et le centre de gravité par équilibre sur une arête ou par suspension en deux points.
- [ ] **Effort disponible par vérin**, à la sortie **et** au retour, aux PWM **115, 150 et 200**. Un peson ou un dynamomètre suffit ; `motor_test_interface` du banc pilote un seul vérin.
- [ ] **Quel vérin est en haut** sur le banc couché (angle de montage de la base autour de sa normale) : il fixe le vrai pire cas. Une photo de face suffit.
- [ ] (Utile) Vitesse des vérins en mm/s : chronométrer une course connue aux mêmes PWM.
- [ ] (Utile) Échelle des codeurs : commander 10 cm, mesurer au pied à coulisse (poulie de 2 cm de diamètre et 960 ticks supposés).
- [ ] (Utile) Pose du marqueur 26 à l'alignement : 30 s de `/aruco_position` et `/aruco_orientation` en mode Acquisition (moyenne et écart-type).
- [ ] (Utile) Pose de la caméra (col de cygne) par rapport au centre de la plateforme, et position et orientation de l'IMU.

## 3. Questions en attente de réponse

- [ ] **La plateforme imprimée en 3D correspond-elle au URDF de 20 cm de ce dépôt, ou à la géométrie du banc (base de 7,5 cm, plateforme de 4 cm) ?** C'est le préalable au Gazebo de la plateforme seule et à son inventaire (PROT-001).
- [ ] Valider l'**ADR-0003** (jumeau Gazebo, proposée) et réviser l'**ADR-0002** (interface Python commune, rendue caduque par le banc ROS 2).
- [ ] Remonter au dépôt du banc les défauts **D13** (lissage puis zone morte dans `aruco_node`, jusqu'à 6,8 mm d'erreur) et **D14** (OpenCV 4.6 : `DetectorParameters()` provoque une erreur de segmentation) : issue ou PR ?

## 4. Prochaines tâches possibles (sans attendre les mesures)

### A. Valider la statique contre une simulation physique (critère de sortie de la Phase 3)
1. Plateforme URDF (PyBullet, géométrie identifiée) : lire l'effort des 6 joints prismatiques à l'équilibre (`getJointState(...)[3]` en `POSITION_CONTROL`) pour plusieurs poses, debout puis gravité tournée (plateforme couchée).
2. Masse et centre de gravité des corps mobiles pris dans le URDF (`getDynamicsInfo`), séparés en plateforme et parties des vérins.
3. Comparer avec `src/core/statics.py`. Critère : **< 2 %** (ROADMAP, Phase 3). Fiche EXP-003 et test de validation.

### B. Poids des vérins et efforts transverses (piste la plus probable du blocage)
1. Ajouter la masse de chaque vérin (corps et tige) et son centre de gravité le long de la jambe ; répartir leur poids entre les deux cardans.
2. Évaluer l'effort transverse au guidage du vérin (porte-à-faux en position couchée) et un frottement de Coulomb proportionnel (coefficient en paramètre) : effort axial nécessaire = statique + frottement.
3. Refaire l'EXP-010 avec ces termes, toujours en plages d'hypothèses, et chercher la masse et le frottement qui reproduisent le blocage.

### C. Une fois la réponse sur la plateforme imprimée en 3D
Gazebo de la plateforme seule : réutiliser l'approche d'EXP-009 (mécanisme cinématique piloté par la FK, rendu Gazebo), paramétrée par la bonne géométrie ; puis inventaire PROT-001 et premiers essais réels.

## 5. Environnement et commandes utiles

- Ce dépôt : WSL **Ubuntu 22.04**, PyBullet. Identité git : `git -c user.name=jbernardo6u -c user.email=josebernardofisico@gmail.com commit ...` ; branche par défaut **`master`** ; une branche par sujet, puis PR.
- Jumeau Gazebo du banc : WSL **Ubuntu-24.04** (ROS 2 Jazzy, Gazebo Harmonic). Espace de travail `~/rem_sim_ws`, guide [docs/guides/GAZEBO_BANC_REM.md](docs/guides/GAZEBO_BANC_REM.md). Le dépôt du banc local est `~/ros2_MP_ws` (24.04) : il contient du travail non commité, **ne pas y toucher**.
- Depuis la 22.04 : `wsl.exe -d Ubuntu-24.04 --cd /home/jbantu -- bash -lc '...'` ; échange de fichiers par `/mnt/wsl/` (zone partagée, vidée au redémarrage de WSL).
- Campagnes : `python3 scripts/experiments/exp010_statics_lying.py` (EXP-010) ; tout d'un coup : `python3 scripts/run_validation.py`.
