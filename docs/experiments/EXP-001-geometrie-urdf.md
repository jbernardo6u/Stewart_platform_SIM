# EXP-001 : Géométrie réelle du modèle URDF contre le modèle paramétrique

- **Date** : 2026-09-24
- **Phase roadmap** : Phase 1 (caractérisation géométrique)
- **Verrous** : V-1 (précision géométrique), V-7 (fidélité du jumeau)
- **Code** : `src/simulation/urdf_geometry.py::identify_urdf_geometry` ; script `scripts/experiments/exp001_urdf_geometry.py` ; test `tests/validation_tests/test_urdf_geometry.py`
- **Configuration** : `configurations/platform_config.yaml` (section `platform.identified`)
- **Données** : `simulation/urdf/Stewart.urdf` (export Fusion 360)
- **Résultats** : `results/geometry/exp001_attachment_points.csv`

## Titre

Identification des points d'attache réels (centres des cardans) décrits par le URDF, et écart au modèle paramétrique (r, γ, h).

## Contexte

L'IK utilise un modèle paramétrique : 6 attaches sur un cercle de rayon r, par paires écartées de ±γ, et une hauteur neutre h (`r_B = r_P = 0,2 m`, `γ = 12°`, `h = 0,257547 m`). Le jumeau numérique doit décrire la géométrie du mécanisme réel, ici représenté par son modèle CAO/URDF. EXP-002 avait montré que les directions de jambes concordent à 0,4° près, sans quantifier les écarts de position.

## Verrou scientifique

Déterminer si le modèle paramétrique suffit à la précision visée (sub-millimétrique pour l'attelage), ou s'il faut une géométrie identifiée point par point, ce qui préfigure la calibration du système réel (Phase 6).

## Hypothèse

H1 : chaque jambe du URDF est une chaîne U-P-R-U dont les cardans sont idéaux (axes concourants), ce qui permet d'identifier exactement les centres d'articulation.
H2 : le modèle paramétrique s'écarte de cette géométrie de l'ordre du millimètre.

## Méthodologie

1. Parcours automatique de l'arbre URDF depuis chaque vérin : 2 révolutes au-dessus (cardan de base), puis rotation propre et 2 révolutes en dessous (cardan supérieur).
2. Centre de chaque cardan : milieu du plus court segment entre ses deux axes (configuration zéro). La longueur de ce segment mesure le défaut du cardan.
3. Repère base centré sur le barycentre des attaches base ; repère plateforme centré sur le barycentre des attaches plateforme (centre de rotation de l'IK).
4. Comparaison point par point avec le modèle paramétrique.

## Résultats

| Grandeur | Modèle paramétrique | URDF identifié |
|---|---|---|
| Écart max entre axes d'un cardan | (idéal) | **0,0008 mm** |
| Rayons base / plateforme | 0,2 / 0,2 m | **0,19958 / 0,19958 m** |
| γ_B | 12° | **12,295°** |
| γ_P | 12° | 12,19° à 12,40° selon la jambe |
| Hauteur neutre (centre plateforme / centre base) | (0 ; 0 ; 0,257547) m | **(−1,169 ; +0,420 ; 253,489) mm** |
| Planéité des attaches plateforme | plan | dispersion de **1,075 mm** en z |
| Écart par point, base | | **1,113 mm** (identique pour les 6 jambes) |
| Écart par point, plateforme | | **0,84 à 1,56 mm** |
| Course des vérins | | [0 ; 0,19] m, **pose neutre = butée basse** |

## Analyse

- H1 est validée : les cardans du URDF sont idéaux, donc le mécanisme est un 6-UPU exact et ses points d'attache sont définis sans ambiguïté.
- H2 est validée : le modèle paramétrique s'écarte de 0,8 à 1,6 mm par attache. L'écart de la base est un simple facteur d'échelle (r et γ). Celui de la plateforme combine un décentrage de 1,2 mm, une asymétrie angulaire et une non-planéité de 1 mm, que le modèle (r, γ) ne peut pas représenter.
- Conséquence mesurée dans EXP-004 : en simulation, le modèle paramétrique laisse **0,68 mm / 0,095°** d'erreur de pose, contre **0,008 mm / 0,0006°** pour la géométrie identifiée (sans gravité).
- La hauteur neutre de 4 mm d'écart n'a presque pas d'effet, car les consignes de vérin sont calculées en relatif (l(pose) − l(neutre)).
- La pose neutre de l'IK correspond aux **vérins en butée basse**. Tout mouvement doit donc se faire autour d'une hauteur de travail (0,09 m, mi-course).

## Conclusion

H1 et H2 sont validées. La géométrie identifiée devient la référence du jumeau numérique : `InverseKinematics.from_attachment_points(...)` et `StewartPlatform.from_urdf(...)`. Le modèle paramétrique reste disponible (API inchangée), avec une précision limitée à ~1 mm.

## Travaux restants

- Phase 6 : appliquer la même démarche au système **réel** (mesure des centres de cardans par laser tracker ou bras de mesure) et comparer à la CAO.
- Vérifier dans la CAO si le décentrage de 1,2 mm et la non-planéité de la plateforme sont voulus ou sont des défauts de modélisation.
- Charger la géométrie depuis `configurations/` plutôt que depuis le URDF à l'exécution (chargeur de configuration, Phase 1).
