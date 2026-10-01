# PROT-001 : inventaire et caractérisation du banc physique

- **Version** : 1 (2026-09-30)
- **But** : relever les caractéristiques réelles du banc et les comparer au modèle, avant toute connexion logicielle ([ADR-0002](../decisions/ADR-0002-interface-commune-simulation-banc.md)) et avant la calibration (Phase 6).
- **Sortie** : ce tableau rempli, les photos et mesures brutes dans `datasets/AAAA-MM-JJ_PROT-001_inventaire/`, puis une section `bench:` dans `configurations/platform_config.yaml`.

Pour chaque grandeur, noter la valeur, l'**incertitude** et la **méthode** (réglet, pied à coulisse, fiche technique, pesée…). Une grandeur inconnue se note « ? » : c'est aussi une information.

## 1. Géométrie

| Grandeur | Modèle (URDF identifié, EXP-001) | Banc | Incertitude | Méthode |
|---|---|---|---|---|
| Rayon des centres de cardans, base | 199,6 mm | | | |
| Rayon des centres de cardans, plateforme | 199,6 mm | | | |
| Demi-angle entre attaches voisines, base (γ_B) | 12,3° | | | |
| Demi-angle, plateforme (γ_P) | 12,3° | | | |
| Hauteur plateforme au neutre (centre à centre des cardans) | 253,5 mm | | | |
| Coordonnées des 12 centres de cardans (si mesurables) | `results/geometry/exp001_attachment_points.csv` | | | |
| Planéité de la plateforme | 1,1 mm d'écart (URDF) | | | |

## 2. Vérins

| Grandeur | Modèle | Banc | Incertitude | Méthode |
|---|---|---|---|---|
| Type (vis à billes, trapézoïdale, autre) | — | | | |
| Longueur rentrée (centre à centre des cardans) | 281 mm | | | |
| Course utile | 190 mm | | | |
| Pas de vis | 2 mm/tr ? (`src/hardware/config.py`) | | | |
| Moteur, rapport de réduction | JGA25-371, 1:371 ? | | | |
| Codeur : impulsions/tour, côté moteur ou sortie | 11 ? / ~7 ? (incohérent) | | | |
| Résolution linéaire résultante (µm/impulsion) | — | | | |
| Vitesse linéaire maximale | 100 m/s (valeur URDF par défaut) | | | |
| Effort maximal (poussée/traction) | 100 N (valeur URDF par défaut) | | | |
| Butées fin de course (capteurs ? mécaniques ?) | — | | | |
| Référence de position au démarrage (homing) | — | | | |

## 3. Articulations

| Grandeur | Modèle | Banc | Incertitude | Méthode |
|---|---|---|---|---|
| Type d'articulation base / plateforme (cardan, rotule) | cardan + pivot (6-UPU) | | | |
| Débattement angulaire maximal | inconnu (limite l'espace de travail en x/y, EXP-007) | | | |
| Jeu mesurable | — | | | |

## 4. Masses et charge

| Grandeur | Modèle | Banc | Incertitude | Méthode |
|---|---|---|---|---|
| Masse de la plateforme mobile | 13,2 kg (URDF) | | | |
| Masse de chaque vérin | — | | | |
| Charge à porter : timon, effort vertical nominal et maximal | — | | | |
| Efforts latéraux à l'accostage | — | | | |

## 5. Électronique et communication

| Grandeur | Banc |
|---|---|
| Contrôleur (Arduino, Raspberry Pi, autre) et firmware | |
| Pilotes moteur, alimentation (V, A) | |
| Liaison avec le PC (série USB, Ethernet…), débit, protocole | |
| Fréquence de la boucle d'asservissement embarquée | |
| Arrêt d'urgence matériel (présent, câblage) | |

## 6. Moyens de mesure de pose disponibles

| Moyen | Disponible ? | Précision attendue | Remarques |
|---|---|---|---|
| Comparateurs / palpeurs | | | |
| Vision (caméra + marqueurs ArUco/AprilTag) | | | |
| Centrale inertielle sur la plateforme | | | |
| Laser tracker / bras de mesure | | | |

## Suite

1. Remplir et versionner les mesures brutes (`datasets/`).
2. Ajouter la section `bench:` à la configuration ; arbitrer l'incohérence de `hardware.actuators`.
3. Si la géométrie du banc diffère du URDF de plus de ~1 mm, créer une géométrie « banc » pour l'IK (même mécanisme que `InverseKinematics.from_attachment_points`).
4. Fiche EXP-008 : comparaison modèle/banc.
