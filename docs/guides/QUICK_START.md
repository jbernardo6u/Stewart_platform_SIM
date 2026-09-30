# Démarrage rapide

## Installation

```bash
pip install -r requirements.txt        # numpy, matplotlib, pybullet, pyyaml, customtkinter, pillow
sudo apt install python3-tk            # si Tkinter est absent
python3 scripts/system_check.py        # diagnostic
```

## Les cinq modes

```bash
python3 run_simulation.py              # menu ; ou directement : python3 run_simulation.py 1
```

| # | Mode | À quoi il sert | Commande directe |
|---|---|---|---|
| 1 | **Tableau de bord 3D** | Piloter la plateforme en simulation et voir ce que font les vérins | `python3 -m src.gui.dashboard` |
| 2 | **Rapport trajectoires** | Chiffrer l'écart de suivi de chaque scénario, sans affichage | `python3 scripts/run_trajectory.py --save` |
| 3 | **Espace de travail** | Débattements atteignables selon la course des vérins (EXP-007) | `python3 scripts/experiments/exp007_workspace_stroke.py` |
| 4 | **Validation** | Tests automatisés et campagnes EXP-001/002/004/007, avec bilan | `python3 scripts/run_validation.py` |
| 5 | **Diagnostic** | Dépendances et imports | `python3 scripts/system_check.py` |

## Tableau de bord

1. **Connecter la simulation** (barre latérale) : la plateforme monte à la position de travail, vérins à mi-course.
2. **Consigne de pose** : curseurs ou saisie (Entrée), en mm et degrés **relatifs à la position de travail**. Préréglages : Travail, Haut, Bas, Désalignement.
3. **Vérins** : course utilisée par vérin. Orange sous 10 % ou au-dessus de 90 %, rouge si la pose est hors course ; les vérins saturés sont aussi colorés en rouge dans la vue 3D. L'inclinaison des jambes est donnée à titre indicatif (limite des cardans encore inconnue).
4. **Écart consigne / mesure** : norme de l'écart de position (mm) et écart d'orientation maximal (°), sur les 10 dernières secondes simulées.
5. **Trajectoires** : la faisabilité s'affiche dès la sélection ; « Lancer » exécute le scénario puis donne l'écart RMS et maximal.
6. **Vue 3D** : glisser pour tourner, molette pour zoomer, vues Iso, Face, Côté et Dessus.

Sans simulation connectée, les curseurs et les jauges fonctionnent quand même (cinématique seule).

Les bornes des curseurs se règlent dans `configurations/platform_config.yaml`, section `gui.dashboard.limits`.

## Scénarios

| Clé | Description |
|---|---|
| `approach` | Approche d'attelage illustrative : désalignement, alignement, montée, maintien, retour |
| `square` | Carré horizontal de 40 mm |
| `orientation` | Roulis, tangage puis lacet successifs |
| `sine` | Sinusoïdes simultanées sur les six axes |

Pour en ajouter un, écrire une fonction dans `src/core/scenarios.py` et l'enregistrer dans `SCENARIOS`. Le test `tests/unit_tests/test_feasibility_scenarios.py` vérifie qu'il reste dans la course des vérins.

## Dépannage

- **Statut « rendu logiciel »** : le greffon EGL n'est pas disponible, le rendu est plus lent. Réduire `gui.dashboard.render_size`.
- **Segfault en fermant une fenêtre PyBullet** (WSLg) : bogue PyBullet/OpenGL. Il ne concerne que `examples/trajectory_demo.py --simulation`, pas le tableau de bord.
