# EXP-004 : Déblocage et validation de la simulation PyBullet en boucle fermée

- **Date** : 2026-09-24
- **Phase roadmap** : Phase 4 (simulation Stewart complète)
- **Verrous** : V-8 (fermeture de boucle en simulation), V-7 (fidélité du jumeau)
- **Code** : `src/core/platform.py` (`setup_constraints`, `get_current_pose`, `from_urdf`, `move_to_working_position`) ; script `scripts/experiments/exp004_closed_loop_tracking.py` ; test `tests/validation_tests/test_closed_loop_simulation.py`
- **Résultats** : `results/experiments/exp004_tracking.csv`

## Titre

Pourquoi la plateforme simulée ne suivait pas ses consignes, et correction.

## Contexte

EXP-002 a montré que la simulation en boucle fermée ne suivait correctement que l'axe z : les vérins restaient jusqu'à 18 mm en deçà de leur consigne. Sans simulation fidèle, le jumeau numérique ne peut valider ni les lois de commande ni les scénarios d'attelage.

## Verrou scientifique

Représenter fidèlement un mécanisme parallèle (6 boucles fermées) dans un moteur multi-corps pensé pour des chaînes arborescentes (PyBullet / Bullet `btMultiBody`), avec une erreur de pose inférieure à la précision visée.

## Hypothèse

H0 (initiale) : la fermeture de boucle par contraintes `JOINT_FIXED` est surcontrainte.
Elle a été **réfutée** au fil du diagnostic, qui a mis en évidence deux autres causes (voir Analyse).

## Méthodologie

Diagnostic par élimination, chaque étape étant mesurée :

1. Rang du système de torseurs de chaque jambe (6 articulations) : dégénérescence éventuelle.
2. Limites articulaires du URDF comparées aux consignes.
3. Violation des contraintes de fermeture, efforts des vérins, influence de la gravité, de l'effort maximal, du gain et du nombre d'itérations du solveur.
4. Test purement cinématique : les configurations cibles existent-elles ? (IK PyBullet sur chaque branche, sans dynamique).
5. Dynamique démarrée depuis la configuration exacte : la simulation y reste-t-elle ?
6. Comparaison de trois fermetures : historique (centres de masse collés), `JOINT_FIXED` ancrée, `JOINT_POINT2POINT`.
7. Validation finale via l'API publique `StewartPlatform` : 10 consignes (translations de 10 mm, rotations de 5 à 20°, pose combinée), modèle paramétrique contre géométrie identifiée (EXP-001), avec et sans gravité.

## Résultats

**Diagnostic**

| Étape | Constat |
|---|---|
| 1 | Jambes bien conditionnées (rang 6, σ_min ≈ 0,18 à 0,22) : pas de singularité |
| 2 | **Vérins limités à [0 ; 0,19] m et pose neutre = butée basse.** Les erreurs d'EXP-002 correspondent exactement aux courses négatives demandées (−3,6 mm → 3,60 mm d'erreur ; −15,4 mm → 15,45 mm) |
| 3 | Autour de la mi-course : erreur résiduelle de 5,6 mm, statique, réversible, indépendante du chemin, de l'effort (250 ou 5 000 N) et de la gravité. Plus le solveur est « dur », plus elle augmente |
| 4 | Les configurations cibles existent : l'IK PyBullet retrouve **exactement** (0,000 mm) les courses calculées par le modèle |
| 5 | Partie de la configuration exacte, la dynamique dérive en 500 pas vers la même erreur de 5,8 mm |
| → | **11 articulations passives ont des limites [0 ; 2π]** (artefact de l'export Fusion 360 pour des articulations libres), alors que la configuration exacte les demande légèrement négatives (≈ −0,06 rad). Le moteur physique les bloque à 0 |
| 6 | Limites recentrées sur [−π ; π] : fermeture historique 1,8 mm, **`JOINT_FIXED` ancrée 0,22 mm**, point-à-point 0,21 mm (mais jambes en rotation propre permanente, avec 3 degrés de liberté inutiles par jambe) |

**Validation finale** (erreur max sur 10 consignes, `get_current_pose()` comparée à la consigne) :

| Modèle IK | Avec gravité | Sans gravité |
|---|---|---|
| Paramétrique (r = 0,2, γ = 12°) | 0,82 mm / 0,097° | 0,68 mm / 0,095° |
| **Géométrie identifiée** (`from_urdf`) | **0,28 mm / 0,044°** | **0,008 mm / 0,0006°** |

## Analyse

- Il n'y avait aucun problème de surcontrainte (H0 réfutée) mais **deux causes** : (1) la pose neutre est en butée basse des vérins ; (2) des limites [0 ; 2π] parasites bloquent des articulations passives. Aucune des deux n'était visible sans un test cinématique pur séparé de la dynamique.
- Ce qui a guidé le diagnostic : une erreur **statique, reproductible et indépendante de l'effort**, qui augmente quand on durcit le solveur, trahit une contrainte unilatérale (butée), pas un problème de convergence.
- L'ancienne fermeture collait les **centres de masse** des liens : PyBullet exprime les repères de contrainte dans le repère du centre de masse. D'où 1,8 mm d'erreur même après correction des limites.
- La fermeture `JOINT_FIXED` ancrée est retenue : la chaîne U-P-R-U du URDF a exactement 6 degrés de liberté, donc la contrainte fixe ne laisse aucun degré de liberté inutile. Le point-à-point est aussi précis, mais les jambes tournent indéfiniment sur elles-mêmes.
- Sans gravité, la géométrie identifiée donne 8 µm : **la simulation et le modèle cinématique décrivent le même mécanisme**. Avec gravité, il reste ~0,2 à 0,3 mm dus à la souplesse des contraintes de PyBullet sous les 13 kg de la plateforme. C'est un artefact du simulateur, pas une propriété du mécanisme. Le gain de position des vérins passe de 0,1 à 0,3, ce qui réduit leur erreur de 0,19 à 0,06 mm.
- L'écart paramétrique (~0,7 mm) est d'origine géométrique (EXP-001).

## Conclusion

Le critère de sortie de la Phase 4 pour PyBullet (< 0,5 mm / 0,1°) est **atteint** avec la géométrie identifiée : 0,28 mm / 0,044° avec gravité. Corrections intégrées à `StewartPlatform` : base fixe, limites recentrées, fermeture ancrée, longueurs initiales issues de l'IK (A4), pose mesurée de la plateforme (A5), hauteur de travail, gain des vérins. Elles sont couvertes par 16 tests de validation.

## Travaux restants

- Démo `ellipse` de `generate_demo_trajectory` : elle demande un lacet de 0 à 360°, irréalisable (courses jusqu'à 253 mm pour 190 mm disponibles). Correction du générateur en Phase 5.
- `scripts/create_video.py`, `examples/basic_control.py` appellent `start_simmulation()` / `fit()`, qui n'existent que dans `legacy/StewartPlatform.py` : à porter ou archiver.
- `src/simulation/pybullet_sim.py::PyBulletSimulator` n'a aucune de ces corrections : le fusionner avec `StewartPlatform` (Phase 4).
- Corriger les limites [0 ; 2π] directement dans le URDF lors de la conversion vers Gazebo (Phase 4).
- Étudier la souplesse résiduelle sous charge (0,2 mm) pour qu'elle ne soit pas confondue avec la compliance réelle du mécanisme (Phase 3).
