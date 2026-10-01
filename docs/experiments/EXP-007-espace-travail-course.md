# EXP-007 : espace de travail limité par la course des vérins

- **Date** : 2026-09-30
- **Auteur(s)** : jbernardo6u (avec Claude Code)
- **Phase roadmap** : Phase 2 (espace de travail), préparation de la Phase 5
- **Verrou(s)** : V-3 (singularités et espace de travail)
- **Commit du code utilisé** : commit qui introduit cette fiche (branche `pybullet-sim-fixes`)
- **Configuration** : `configurations/platform_config.yaml` (`working_height`, `actuator_stroke`)
- **Données** : aucune (calcul sur la géométrie identifiée, EXP-001)
- **Résultats** : `results/kinematics/exp007_dof_ranges.csv`, `results/kinematics/figures/exp007_xy_maps.png`
- **Script** : `scripts/experiments/exp007_workspace_stroke.py`

## Titre

Débattements atteignables autour de la position de travail, sous la seule contrainte de course des vérins.

## Contexte

Les interfaces bornaient les curseurs à des valeurs arbitraires (±50 mm, ±15°), et la démo « spirale » demandait un lacet de 360° que la plateforme ne peut pas réaliser. Avant de générer des trajectoires, il faut savoir ce qui est atteignable.

## Verrou scientifique

V-3 : l'espace de travail nécessaire à l'alignement REM est-il atteignable ? Cette expérience traite la première contrainte, la course des vérins. Débattement des cardans, singularités et efforts restent à traiter.

## Hypothèse

La course [0 ; 190 mm] autour de la hauteur de travail (90 mm) permet plusieurs dizaines de millimètres et de degrés sur chaque axe, mais pas un tour complet en lacet.

## Méthodologie

- IK sur la géométrie identifiée dans le URDF (`StewartPlatform.from_urdf`).
- Pour chaque degré de liberté pris seul, puis pour x et y avec un lacet de ±10° : plus grand débattement tel que les six vérins restent dans leur course (dichotomie, borne de recherche de 200 mm ou 45 à 90°).
- Carte (x, y) atteignable à orientation nulle, pour z = −60 à +60 mm.
- Indicateur : inclinaison maximale des jambes par rapport à la verticale aux extrémités (`src.core.feasibility.leg_tilt_deg`).

## Résultats

| Axe | Débattement (course seule) | Inclinaison max des jambes |
|---|---|---|
| x | ±200 mm (borne de recherche : course non limitante) | 42,3° |
| y | ±200 mm (idem) | 43,2° |
| z | −90 à +111 mm | 25,9° |
| roulis | −36,1 à +26,2° | 27,3° |
| tangage | −28,6 à +28,6° | 26,2° |
| lacet | −71,9 à +72,0° | 43,3° |
| x avec lacet ±10° | environ −175 à +184 mm | 43,3° |

Inclinaison des jambes à la position de travail : 19,7°. La carte (x, y) est pleine jusqu'à ±150 mm pour z ≤ 0 et se réduit au-dessus (environ ±120 mm à z = +60 mm).

## Analyse

- Verticalement et en rotation, la course limite bien le mouvement. Le roulis est asymétrique (−36 / +26°), à cause du décalage angulaire des attaches (γ ≈ 12,3°).
- Horizontalement, la course n'est **pas** limitante : à ±200 mm, les jambes sont inclinées de 42° (19,7° en position de travail). La limite latérale réelle viendra du **débattement des cardans** ou des singularités, inconnus à ce stade.
- Le lacet de 360° est exclu (±72° au plus) : la démo « spirale » est corrigée en oscillation de ±20°.

## Conclusion

Hypothèse validée. Les bornes d'exploration du tableau de bord (`gui.dashboard.limits` : x, y ±100 mm, z −85 à +105 mm, roulis et tangage ±25°, lacet ±60°) en découlent. En x/y, elles sont resserrées pour limiter l'inclinaison des jambes à 32° environ. **Ce ne sont pas des limites mécaniques validées.**

## Travaux restants

- Mesurer sur le banc le débattement réel des cardans (Phase 6) et l'intégrer à la faisabilité.
- Singularités et conditionnement du jacobien sur cet espace (Phase 2).
- Espace de travail en efforts sous la charge du timon (Phase 3, V-4).
