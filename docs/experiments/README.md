# Expérimentations : traçabilité CIR

Chaque expérimentation (simulation ou banc) fait l'objet d'une fiche `EXP-XXX-titre-court.md`, créée à partir de [TEMPLATE.md](TEMPLATE.md), selon le format :

Titre · Contexte · Verrou scientifique · Hypothèse · Méthodologie · Résultats · Analyse · Conclusion · Travaux restants

Règles :

- numérotation séquentielle, jamais réutilisée ;
- une fiche se rattache à au moins un verrou `V-x` de [RESEARCH.md](../../RESEARCH.md) et à une phase de [ROADMAP.md](../../ROADMAP.md) ;
- les données brutes vont dans `datasets/`, les sorties dans `results/`, et la fiche y renvoie ;
- noter le hash du commit utilisé pour que le résultat soit reproductible ;
- une expérience ratée est aussi documentée, parce qu'elle justifie l'incertitude scientifique.

## Registre

| Id | Titre | Phase | Verrou | Statut |
|---|---|---|---|---|
| EXP-001 | Géométrie paramétrique contre URDF | 1 | V-1 | Planifiée |
| EXP-002 | Validation de l'IK contre PyBullet (arbitrage A1) | 2 | V-2, V-7 | Planifiée |
