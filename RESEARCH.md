# Recherche : verrous scientifiques et techniques (REM)

Ce document liste les questions de recherche du projet. Chaque expérimentation (`docs/experiments/EXP-XXX-*.md`) doit se rattacher à au moins un verrou (`V-x`), ce qui garantit la traçabilité CIR.

## Contexte

L'attelage automatique d'une remorque demande d'aligner l'interface d'attelage du tracteur sur celle de la remorque avec une précision millimétrique, malgré des erreurs de positionnement du véhicule, des charges verticales importantes (timon) et un environnement non structuré. La plateforme Stewart fournit les 6 degrés de liberté de correction. Le jumeau numérique doit permettre de concevoir, régler et valider cette correction **avant** les essais physiques.

## Verrous

| Id | Verrou | Question | Phase |
|---|---|---|---|
| V-1 | Précision géométrique | Quel écart entre le modèle paramétrique (`r`, `γ`) et la géométrie réelle (CAO, fabrication), et quel impact sur la précision de pose ? | 1, 6 |
| V-2 | Cinématique directe temps réel | Quelle méthode de FK converge de façon fiable, dans le budget temps réel, sur tout l'espace de travail utile à l'attelage ? | 2 |
| V-3 | Singularités et espace de travail | L'espace de travail nécessaire à l'alignement REM (±x, ±y, ±z, ±lacet) est-il libre de singularités, avec une marge de conditionnement suffisante ? | 2 |
| V-4 | Capacité en effort | Les vérins supportent-ils la charge du timon sur tout l'espace de travail, y compris en dynamique ? | 3 |
| V-5 | Stabilité | Quelle stabilité en boucle fermée sous charge variable et chocs d'accostage ? | 3, 5 |
| V-6 | Énergie | Quelle consommation par cycle d'attelage, et quelles trajectoires la minimisent ? | 3, 5 |
| V-7 | Fidélité du jumeau | Quel écart simulation/réel (pose, efforts, temps) est atteignable, et quels paramètres dominent cet écart ? | 4, 7 |
| V-8 | Fermeture de boucle en simulation | Comment représenter fidèlement un mécanisme parallèle (boucles fermées) dans des moteurs pensés pour les chaînes arborescentes (PyBullet, Gazebo) ? | 4 |
| V-9 | Alignement autonome | Quelle stratégie de commande (asservissement visuel, estimation de pose) permet l'alignement sans intervention humaine ? | 8 |

## État de l'art à documenter

- Cinématique des hexapodes 6-6 : IK analytique, FK itérative (Newton-Raphson) ou polynomiale (Husty)
- Dynamique des manipulateurs parallèles : Newton-Euler, principe des travaux virtuels
- Calibration des robots parallèles : méthodes à mesure externe et auto-calibration
- Simulation multi-corps de mécanismes fermés : contraintes PyBullet, SDF/Gazebo, `ros2_control`
- Systèmes d'attelage automatique existants (industriels et académiques)

Références à compléter dans ce fichier (format : auteur, année, titre, lien, verrou concerné).

## Sources internes

- Dérivation de l'IK : `models/kinematics/notebooks/analysis.ipynb`, `docs/design/README_original.md`
- Document upstream : `docs/reports/StewartPlatformDocument.pdf`
- Diagnostic de départ : `docs/reports/2026-09-24_analyse_depot.md`
