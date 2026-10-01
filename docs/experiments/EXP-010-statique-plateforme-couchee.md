# EXP-010 : efforts statiques des vérins, plateforme du banc couchée

- **Date** : 2026-10-01
- **Auteur(s)** : jbernardo6u (avec Claude Code)
- **Phase roadmap** : Phase 3 (statique)
- **Verrou(s)** : V-4 (capacité en effort) ; verrou mécanique du banc REM (couple insuffisant)
- **Commit du code utilisé** : commit qui introduit cette fiche (branche `phase3-statique`)
- **Configuration** : `configurations/bench_rem.yaml` (géométrie du banc, section `statics`)
- **Données** : aucune mesure ; masses, centre de gravité, montage et effort disponible sont des **hypothèses balayées**
- **Résultats** : `results/dynamics/exp010_home.csv`, `exp010_workspace.csv`, `exp010_design_sweep.csv`, `results/dynamics/figures/exp010_statics.png`
- **Script** : `scripts/experiments/exp010_statics_lying.py` ; code `src/core/statics.py` ; tests `tests/unit_tests/test_statics.py`

## Titre

Efforts axiaux des vérins du démonstrateur REM sous le poids de la charge embarquée : plateforme couchée (montage du banc) contre plateforme debout, et sensibilité aux dimensions.

## Contexte

Sur le banc, les motoréducteurs (JGA25-370) ne parviennent pas à vaincre la gravité : les mouvements commandés ne sont pas exécutés, ou seulement en partie. La plateforme y est montée **couchée** : sa normale est horizontale, dans l'axe du rail, et la gravité agit perpendiculairement à cet axe. Hypothèse de conception d'origine : 0,5 à 1 kg embarqués, 30 N par vérin.

## Verrou scientifique

Quantifier ce que le montage couché coûte en effort par rapport au montage debout, savoir si une charge de 0,5 à 1 kg dépasse les 30 N prévus, et indiquer quelles dimensions réduiraient ces efforts pour une version qui tienne.

## Hypothèse

- H1 : en position couchée, les efforts axiaux sont bien plus élevés que debout, car des jambes presque parallèles à la normale (inclinées d'environ 14°) reprennent mal une charge latérale.
- H2 : élargir la base ou abaisser la plateforme (incliner les jambes) réduit nettement ces efforts.

## Méthodologie

- Statique : `f = −J⁻ᵀ·w`, avec `J` le jacobien de la Phase 2 (EXP-008) et `w` le torseur du poids de la charge au centre de la plateforme. Liaisons parfaites, masse des vérins négligée, quasi-statique. `f > 0` : le vérin pousse.
- Géométrie : banc (base de 7,5 cm, plateforme de 4 cm, γ = 11,3°/17,3°, home à 18,5 cm), mécanisme physique du jumeau (`src/rem_bench`).
- Couché : gravité perpendiculaire à z_B, d'angle de montage inconnu autour de la normale, **balayé de 0 à 360° par pas de 5° ; on retient le pire cas**. Debout : gravité selon −z_B.
- Charge : 0,5 et 1 kg ; centre de gravité de 0 à 6 cm devant la plaque (disque Space Lock et marqueur).
- Poses : home physique (codeurs à 0), mi-course (codeurs à 5 cm), et 4000 poses de l'espace de compensation (±2 cm en x et y, ±4 cm selon la normale, ±10° en roulis et tangage, ±15° en lacet, autour de la mi-course), dont 3998 dans la course.
- Sensibilité : rayon de base de 6 à 15 cm × hauteur home de 12 à 25 cm, 1 kg, couché, pire montage.
- Vérification : équilibre `Jᵀf + w = 0` et travail virtuel vérifiés à 10⁻⁹ près ; cas debout centré comparé à la formule `m·g / (6 cos θ)` (tests unitaires).

## Résultats

**Pose home, 1 kg** (effort maximal sur les 6 vérins) :

| Centre de gravité | Debout | Couchée, pire montage | Rapport |
|---|---|---|---|
| 0 cm | 1,69 N | 15,8 N | ×9,4 |
| 6 cm | 1,69 N | 13,7 N | ×8,1 |
| 0 cm, mi-course | 1,67 N | 20,0 N | ×12,0 |

À 0,5 kg, les efforts sont deux fois plus faibles (7,9 N à home, couché).

**Espace de compensation, 1 kg** : couchée, médiane 20,7 N, 95 % des poses sous 23,6 N, maximum 24,9 N ; debout, médiane 3,1 N, maximum 4,5 N. Aucune pose ne dépasse 30 N. Conditionnement ≤ 10,4.

**Masse admissible pour 30 N par vérin (couchée, pire montage)** : 1,9 kg à home, 1,5 kg à mi-course, 1,27 kg sur 95 % de l'espace de compensation.

**Sensibilité (couchée, home, 1 kg)** : 15,8 N pour le banc actuel (7,5 cm, 18,5 cm, jambes à 14°). Avec une base de 13 à 15 cm, on descend à 6,4–7 N, soit 2,3 fois moins (jambes à 28–33°). Abaisser la plateforme à 12 cm donne 9,2 N. Plus la plateforme est haute et la base étroite, plus les efforts croissent : 26 N pour 6 cm et 25 cm.

## Analyse

- **H1 validée** : le montage couché multiplie les efforts axiaux par **8 à 12** par rapport au montage debout. Les jambes étant presque parallèles à la normale, une charge latérale ne peut être reprise que par de grands efforts opposés deux à deux : des vérins poussent, d'autres tirent.
- Avec l'hypothèse de conception (1 kg, 30 N), **la statique seule n'explique pas l'échec** : on reste sous 25 N. Il faut donc, au moins en partie, chercher la cause ailleurs :
  - la masse réelle embarquée est peut-être supérieure à 1,3 kg (plaque, disque Space Lock, marqueur, cardans, et une part du poids des vérins) ;
  - l'effort réellement disponible est sans doute bien inférieur à 30 N : plage de PWM utile limitée à 100–200, retour lent de 210 à 240, 12 V, réducteur non documenté ;
  - les **efforts transverses** ne sont pas modélisés : poids propre des vérins en porte-à-faux, flexion des tiges, frottement dans les guidages et les cardans sous charge latérale. En position couchée, ils peuvent dominer et bloquer des vérins qui ne travaillent qu'en axial dans ce modèle ;
  - certains vérins doivent **tirer** : leur sens de travail est inversé par rapport à la conception debout (compression seule), ce qui n'a peut-être pas été pris en compte dans le choix des moteurs.
- **H2 validée** : la géométrie est un levier fort. Pour une version qui tienne en position couchée, il faut des jambes plus inclinées : base nettement plus large que la plateforme (13 à 15 cm contre 7,5 cm) et/ou plateforme plus basse. Le gain est de ×2 à ×2,5 sur les efforts, à vérifier contre l'espace de travail et les singularités (EXP-007, EXP-008 adaptés).
- Limites : masse, centre de gravité, montage, effort disponible et frottements non mesurés ; masse des vérins négligée ; pas de dynamique (les accélérations des scénarios s'ajoutent).

## Conclusion

H1 et H2 sont validées. Couchée, la plateforme demande 8 à 12 fois plus d'effort que debout, jusqu'à 25 N par vérin pour 1 kg. C'est sous les 30 N de conception, mais avec peu de marge (1,3 kg admissibles sur 95 % de l'espace). Le blocage observé sur le banc s'explique donc probablement par la combinaison de ces efforts, d'une masse ou d'un effort disponible différents des hypothèses, et d'efforts transverses non modélisés. Élargir la base est le moyen le plus efficace de réduire les efforts.

## Travaux restants

- Mesurer sur le banc : masse et centre de gravité de la partie mobile, angle de montage (quel vérin est en haut), effort disponible par vérin en sortie et en retour (à PWM 115, 150 et 200), frottement.
- Ajouter la masse des vérins et les efforts transverses (flexion, frottement de guidage) au modèle.
- Valider la statique contre une simulation physique (PyBullet ou Gazebo dynamique), critère de sortie de la Phase 3 (< 2 %).
- Dynamique des scénarios (accélérations) et énergie (Phase 3, V-5, V-6).
- Dans Demonstrateur_REM : vérins limités en effort dans le jumeau Gazebo, pour reproduire le blocage observé (ADR-0004).
