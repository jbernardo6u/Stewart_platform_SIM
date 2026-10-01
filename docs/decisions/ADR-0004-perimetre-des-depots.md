# ADR-0004 : Périmètre des dépôts Stewart-Platform et Demonstrateur_REM

- **Date** : 2026-10-01
- **Statut** : Acceptée (orientation donnée par le responsable du projet le 2026-10-01)
- **Complète** : [ADR-0003](ADR-0003-jumeau-gazebo-demonstrateur.md)

## Contexte

Deux dépôts traitent de la plateforme de Stewart du projet REM :

- **Stewart-Platform** (ce dépôt) : modèles, simulation PyBullet, tableau de bord, et un prototype de jumeau Gazebo du banc (EXP-009) ;
- **Demonstrateur_REM** : logiciel ROS 2 complet du banc d'attelage de précision (MP de Stewart + actionneur linéaire d'approche), plus abouti, mais dont la mécanique ne tient pas aux essais.

Sans règle, les développements se dispersent et le prototype de jumeau risque de diverger du banc.

## Décision

1. **Stewart-Platform est le dépôt de la plateforme de Stewart seule** : modèles (IK, FK, jacobien, statique), simulation de la MP seule (PyBullet ; Gazebo à venir) et essais sur la MP réelle imprimée en 3D lorsque c'est possible.
2. **Demonstrateur_REM est le dépôt de référence du banc d'attelage complet.** Les développements du banc s'y font : jumeau Gazebo du système complet (MP, rail, caméra, IMU, cible), corrections du logiciel, étude puis refonte de la mécanique.
3. Le jumeau Gazebo du banc construit ici (`src/rem_bench`, `ros2_ws/src/rem_bench_sim`) est un **prototype**, conservé comme référence de migration. Il n'évolue plus ici, sauf correction ; sa suite se fait dans Demonstrateur_REM.
4. Les modèles génériques (FK, jacobien, singularités, statique) sont mis au point ici puis repris dans Demonstrateur_REM (`models/`), en citant la version source.

## Options écartées

- **Tout développer ici** : il faudrait dupliquer le logiciel ROS 2 du banc, qui est plus complet là-bas.
- **Tout migrer dans Demonstrateur_REM tout de suite** : on perdrait la simulation PyBullet validée et le banc d'essai léger qu'est la MP seule.

## Conséquences

- ➕ Un rôle clair par dépôt : la MP comme laboratoire de modèles, le banc comme produit.
- ➕ Le jumeau du banc complet évolue avec le code qu'il exerce.
- ➖ Il faut suivre la migration (modèles, prototype de jumeau) : le rapport [2026-10-01_perimetre_et_suite.md](../reports/2026-10-01_perimetre_et_suite.md) en liste le contenu.
- ➖ Les deux dépôts ont des environnements différents (PyBullet sous Ubuntu 22.04 ici ; ROS 2 Jazzy sous Ubuntu 24.04 pour le banc).
