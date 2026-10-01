# EXP-008 : cinématique directe, jacobien et singularités

- **Date** : 2026-10-01
- **Auteur(s)** : jbernardo6u (avec Claude Code)
- **Phase roadmap** : Phase 2 (cinématique)
- **Verrou(s)** : V-2 (FK temps réel), V-3 (singularités et espace de travail), V-7 (fidélité du jumeau)
- **Commit du code utilisé** : commit qui introduit cette fiche (branche `phase2-cinematique`)
- **Configuration** : `configurations/platform_config.yaml` (`kinematics.forward`, `working_height`, `gui.dashboard.limits`)
- **Données** : aucune (géométrie identifiée EXP-001, simulation PyBullet DIRECT)
- **Résultats** : `results/kinematics/exp008_round_trip.csv`, `exp008_fk_vs_pybullet.csv`, `exp008_conditioning_yaw.csv`, `results/kinematics/figures/exp008_conditioning.png`
- **Script** : `scripts/experiments/exp008_forward_kinematics.py`
- **Code** : `src/core/forward_kinematics.py` ; tests `tests/unit_tests/test_forward_kinematics.py`, `tests/validation_tests/test_forward_kinematics_simulation.py`

## Titre

Cinématique directe par Newton-Raphson, jacobien inverse et cartographie du conditionnement de la plateforme REM.

## Contexte

Jusqu'ici, seule l'IK (pose → longueurs) existait. Le banc ne mesure que les positions de ses vérins (codeurs) : sans cinématique directe, sa pose n'est pas connue (ADR-0002). Le jacobien est aussi le point de départ de la statique (`f = J⁻ᵀ w`, Phase 3) et de la commande en vitesse (Phase 5).

## Verrou scientifique

Pour un hexapode 6-6, la FK n'a pas de solution analytique (jusqu'à 40 solutions réelles). Il faut une méthode itérative qui converge vers la bonne branche, assez vite pour le temps réel, et savoir où le mécanisme devient singulier (`det J = 0`), là où il perd sa rigidité et où la FK diverge.

## Hypothèse

- H1 : un Newton-Raphson initialisé à la dernière pose connue (ou à la position de travail) converge en moins de 10 itérations, avec une erreur aller-retour IK→FK < 1 µm, sur tout l'espace du tableau de bord.
- H2 : appliquée aux positions mesurées des joints prismatiques, la FK retrouve la pose mesurée du corps de la plateforme dans PyBullet.
- H3 : cet espace est loin des singularités ; la singularité connue des hexapodes symétriques (lacet ±90°, Fichter 1986) se trouve hors de la plage utilisée.

## Méthodologie

- **FK** : on résout `J·[δt ; δω] = ℓ_mesurées − ℓ(pose)`, puis `t ← t + δt`, `R ← exp([δω]×)·R` (mise à jour sur SO(3), sans angles d'Euler dans l'itération). Arrêt quand le résidu sur les longueurs est ≤ 10⁻¹² m.
- **Jacobien inverse** : ligne i = `[u_iᵀ, (R·p_i × u_i)ᵀ]`, `dℓ/dt = J·[v ; ω]` (repère base). Vérifié par différences finies centrées (pas de 10⁻⁷).
- **Conditionnement** : `J_n = J·diag(1, 1, 1, 1/L, 1/L, 1/L)`, avec L = 0,1996 m, rayon moyen des attaches de la plateforme, pour rendre homogènes les colonnes de translation et de rotation. Indicateur : conditionnement de `J_n` (∞ à la singularité).
- **Aller-retour** : 2000 poses uniformes dans les bornes du tableau de bord (x, y ±100 mm, z −85/+105 mm, roll et pitch ±25°, lacet ±60°), initialisation à la position de travail.
- **Simulation** : géométrie identifiée (`from_urdf`), 8 poses (position de travail, translations, rotations, pose combinée), avec et sans gravité ; FK sur `getJointState` des 6 vérins, comparée à `get_current_pose()`.
- Critères : aller-retour < 1 µm (sortie de la Phase 2) ; FK/simulation < 0,01 mm sans gravité.

## Résultats

| Mesure | Valeur |
|---|---|
| Aller-retour IK→FK, 2000 poses | 0 échec ; erreur max 1,5·10⁻¹² m et 1,1·10⁻¹¹ rad |
| Itérations | 4,8 en moyenne, 7 au plus |
| Temps de calcul (Python, NumPy) | 0,82 ms par appel |
| Jacobien / différences finies | 2,7·10⁻¹⁰ |
| FK sur joints / pose PyBullet, **sans gravité** | ≤ 0,005 mm et ≤ 0,001° |
| FK sur joints / pose PyBullet, **avec gravité** | 0,15 à 0,48 mm, 0,025 à 0,036° |
| Conditionnement à la position de travail | 4,2 |
| Conditionnement max sur le lacet ±60° (roll = pitch = 0) | 7,0 |
| Singularité | lacet ±90° exactement (det `J_n` change de signe) ; conditionnement > 30 au-delà de ±85° |

Figure `exp008_conditioning.png` : conditionnement en fonction du lacet, et cartes (roll, pitch) ±25° à lacet 0°, 45° et 75°. À 75°, le conditionnement atteint 10 à 100 dans les coins roll/pitch de même signe.

## Analyse

- H1 est validée avec une marge de six ordres de grandeur. Avec 0,8 ms par appel en Python, la FK tient dans un cycle à 100 Hz (critère de la Phase 5), et même à 1 kHz si elle est initialisée à la pose précédente (1 à 2 itérations).
- H2 est validée sans gravité : le modèle cinématique et la simulation décrivent le même mécanisme, à 5 µm près.
- **Avec gravité, la FK sur codeurs s'écarte de 0,15 à 0,5 mm de la pose réelle de la plateforme.** Ce n'est pas une erreur de FK : c'est la souplesse des liaisons de fermeture sous la charge, que les positions de vérins ne voient pas. Sur le banc, il faut s'attendre au même phénomène (jeux des cardans, flexion), probablement plus fort. Une **mesure externe de la pose** (caméra, PROT-001) est donc nécessaire pour valider la précision réelle ; les codeurs seuls ne suffisent pas.
- H3 est validée : la seule singularité rencontrée en balayant le lacet est celle de Fichter à ±90°. La plage ±60° du tableau de bord reste à un conditionnement ≤ 7. La course des vérins limite déjà le lacet à ±72° (EXP-007), là où le conditionnement vaut environ 12 : la course protège la singularité, mais avec peu de marge.

## Conclusion

H1, H2 et H3 sont validées. Critère de sortie de la Phase 2 atteint (aller-retour < 1 µm). La FK est utilisable pour estimer la pose du banc à partir des codeurs (ADR-0002) ; sa précision réelle est limitée par la souplesse du mécanisme, pas par l'algorithme.

## Travaux restants

- Recherche systématique de singularités sur l'espace de travail complet (6D), pas seulement en lacet et roll/pitch.
- Seuil de conditionnement à imposer dans `check_trajectory`, une fois la rigidité et les efforts connus (Phase 3) : la valeur limite n'est pas encore justifiée.
- Branches multiples de la FK : vérifier sur le banc qu'une initialisation à la dernière pose suffit (pas de saut de branche).
- Comparer FK sur codeurs et pose mesurée par caméra sur le banc (Phase 7), et en simulation Gazebo avec caméra (EXP-005).
