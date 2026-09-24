# EXP-002 : Validation de la cinématique inverse contre le modèle URDF

- **Date** : 2026-09-24
- **Phase roadmap** : Phase 2 (caractérisation cinématique)
- **Verrous** : V-2 (cinématique), V-7 (fidélité du jumeau), V-8 (fermeture de boucle en simulation)
- **Code** : `scripts/experiments/exp002_ik_vs_urdf.py` ; test de non-régression `tests/validation_tests/test_ik_urdf_consistency.py`
- **Configuration** : r_B = r_P = 0,2 m, γ_B = γ_P = 12°, home = (0, 0, 0,257547) m ; `simulation/urdf/Stewart.urdf`
- **Données** : aucune mesure réelle (simulation uniquement)
- **Résultats** : `results/kinematics/exp002_leg_axes.csv`, `results/kinematics/exp002_dynamic.csv`

## Titre

Arbitrage de l'anomalie A1 : quelle cinématique inverse, et quel ordre d'actionneurs, correspondent au modèle URDF ?

## Contexte

Le dépôt contient deux IK : l'IK historique (`legacy/inv_kinematics.py`) et l'IK refactorisée (`src/core/kinematics.py`). Pour une même pose, elles donnent des longueurs différentes (jusqu'à 42 mm d'écart, ordre des jambes permuté). Les indices d'actionneurs utilisés partout (`[9, 2, 31, 45, 38, 24]`) avaient été calés avec l'IK historique, mais sont combinés avec l'IK refactorisée depuis juillet 2025. Toute la chaîne de simulation dépend de cette correspondance.

## Verrou scientifique

Garantir que le modèle cinématique analytique et le modèle multi-corps simulé décrivent le **même** mécanisme, dans le **même** repère, avec la **même** numérotation des jambes. Sans cela, aucune comparaison simulation/modèle ou simulation/réel n'a de sens.

## Hypothèse

H1 : l'IK refactorisée, dont les attaches suivent `φ_B` pour la base et `φ_P` pour la plateforme, reproduit la géométrie du URDF avec les jambes numérotées 1 à 6 (Slider_13 à Slider_18). L'ordre historique des actionneurs est donc faux pour cette IK.

## Méthodologie

1. **Lecture de la géométrie URDF** (PyBullet DIRECT, configuration zéro) : positions monde des attaches de la plateforme (liens `J*B`/`J*T` solidaires de `TOP1`) et des cardans de la base, axes des 6 joints prismatiques.
2. **Essai cinématique** : pour chaque configuration, angle entre la direction de jambe prédite au neutre (`home + P_i − B_i`) et l'axe du joint prismatique affecté à cette sortie de l'IK. Critère d'acceptation : < 1°.
3. **Essai dynamique** : mécanisme fermé (5 contraintes `JOINT_FIXED`, base fixe, moteurs passifs désactivés), vérins en `POSITION_CONTROL` (250 N), 1 500 pas à 240 Hz. Commande de 6 déplacements élémentaires ; mesure de la pose du centre de la plateforme (lien `indicator1`) et de l'erreur de suivi des vérins.

Configurations : **A** = IK historique + `[9, 2, 31, 45, 38, 24]` ; **B** = IK src + `[9, 2, 31, 45, 38, 24]` (état avant correction) ; **C** = IK src + `[2, 31, 45, 38, 24, 9]`.

## Résultats

**Géométrie URDF** (angles polaires autour de z) :

| Jambe | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Attache plateforme (r ≈ 0,20 m) | 257° | 162° | 138° | 42° | 18° | 282° |
| `φ_P` du modèle | 258° | 162° | 138° | 42° | 18° | 282° |
| Cardan base | ≈224° | ≈202° | ≈100° | ≈72° | ≈344° | ≈322° |
| `φ_B` du modèle | 222° | 198° | 102° | 78° | 342° | 318° |

**Essai cinématique** (angle entre la jambe du modèle et l'axe du vérin URDF, max sur 6 jambes) :

| Config | Écart max |
|---|---|
| A : IK historique + ordre historique | 25,2° |
| B : IK src + ordre historique | 44,3° |
| **C : IK src + jambes 1 à 6** | **0,37°** |

**Essai dynamique** (extrait, pose du centre de la plateforme) :

| Commande | A | B | C |
|---|---|---|---|
| z +10 mm | z 9,74 mm | z 9,74 mm | z 9,74 mm |
| roulis +5° | (1,16 ; 1,53 ; 1,35)° | (0,90 ; 1,45 ; 0,50)° | **(2,09 ; 0,03 ; 0,12)°** |
| tangage +5° | (−2,57 ; 0,44 ; 0,15)° | (−1,75 ; 1,94 ; 0,23)° | **(0,52 ; 1,87 ; 1,03)°** |
| lacet +5° | (0,02 ; 0,11 ; 2,44)° | (−0,24 ; −1,02 ; −0,83)° | **(0,02 ; 0,11 ; 2,44)°** |
| Erreur de suivi des vérins, max | 0,5 à 17 mm | 0,5 à 17 mm | 0,5 à 18 mm |

Autres constats : l'effort des vérins (250 N ou 5 000 N) ne change rien, et aucune articulation n'atteint sa butée.

## Analyse

- H1 est confirmée par l'essai cinématique : C reproduit l'axe de chaque vérin URDF à 0,4° près, ce qui valide simultanément `r`, `γ`, la hauteur neutre, les conventions `φ_B`/`φ_P` et l'ordre des jambes.
- L'IK historique échange base et plateforme. Cela équivaut exactement au vrai mécanisme **tourné de −60°** autour de z, avec les jambes dans l'ordre [6, 1, 2, 3, 4, 5], ce qui explique l'ordre historique `[9, 2, 31, 45, 38, 24]`. Le couple A est donc cohérent, mais ses consignes x, y, roulis et tangage sont exprimées dans un repère tourné de 60°. Pour z et le lacet, invariants par cette rotation, A et C sont strictement identiques, ce que l'essai dynamique confirme.
- B (l'état du code avant correction) cumule les deux erreurs : chaque vérin reçoit la consigne d'une autre jambe.
- L'essai dynamique **ne permet pas de validation quantitative** : dès qu'on sort de l'axe z, les vérins n'atteignent pas leur consigne (jusqu'à 18 mm d'écart), quel que soit l'effort, sans butée atteinte. Le mécanisme simulé est **cinématiquement bloqué**. Causes probables : cardans du CAO non idéaux (axes décalés de plusieurs cm), contraintes `JOINT_FIXED` imposées entre des repères distants de 1 à 2 mm, fermeture de boucle surcontrainte. Ce problème est indépendant de l'IK (il touche A, B et C) et relève de la Phase 4.

## Conclusion

H1 est **validée** sur le plan cinématique. Actions réalisées :

- l'IK de `src/core/kinematics.py` est conservée telle quelle (elle est correcte) ;
- ajout de `DEFAULT_ACTUATOR_INDICES = [2, 31, 45, 38, 24, 9]` et `DEFAULT_JOINT_INDICES` dans `src/core/platform.py`, utilisés par les scripts et exemples ; configuration YAML mise à jour ;
- correction associée A2 : `PhysicalStewartPlatform` passe les paramètres dans l'ordre attendu ;
- test de non-régression `tests/validation_tests/test_ik_urdf_consistency.py`.

Les scripts de `legacy/` qui combinent l'IK `src` avec l'ordre historique (`legacy/main*.py`, `legacy/stewart_gui*.py`) ne sont pas corrigés : ils sont archivés.

## Travaux restants

- **Phase 4** : lever le blocage cinématique du mécanisme simulé (réviser la fermeture de boucle : contraintes point-à-point `JOINT_POINT2POINT` aux centres des cardans plutôt que `JOINT_FIXED`), puis refaire l'essai dynamique avec un critère quantitatif (erreur de pose < 0,5 mm / 0,1°).
- **Phase 1** : extraire les centres exacts des cardans de la base, dont les rayons sont dispersés entre 0,175 et 0,224 m selon l'axe considéré, et quantifier l'écart au modèle paramétrique (EXP-001).
- Clarifier la hauteur neutre. Les repères URDF (attaches plateforme à z ≈ 0,358 m, premiers axes des cardans à z ≈ 0,065 m) ne se comparent pas directement à home = 0,2575 m, alors que l'inclinaison des jambes est cohérente (25,6° dans le modèle, 25,3° à 25,9° dans le URDF). Les centres de cardans restent à définir proprement (Phase 1).
