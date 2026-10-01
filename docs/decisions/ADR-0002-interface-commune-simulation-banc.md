# ADR-0002 : Une interface commune pour la simulation et le banc

- **Date** : 2026-09-30
- **Statut** : Proposée (à valider avant la première connexion au banc)

## Contexte

Le banc physique existe. Le code actuel a deux chemins sans rapport :

- **simulation** : `PyBulletSimulator` (`src/simulation/pybullet_sim.py`), piloté par le tableau de bord via `DashboardController`. Validé à 0,28 mm / 0,044° (EXP-004), poses en mm et degrés relatives à la position de travail ;
- **matériel** : `PhysicalStewartPlatform` + `MotorController` (`src/hardware/`). Le contrôleur est un stub (pas de communication réelle), le modèle est paramétrique, les poses sont exprimées depuis la pose neutre, sans vérification de course. La configuration `hardware.actuators` (longueurs de 0,15 à 0,25 m) contredit le URDF (jambe de 0,281 m au neutre, course de 0 à 0,19 m).

La validation simulation/réel (Phase 7, V-7) exige de rejouer **exactement** les mêmes consignes sur les deux, et de comparer les mêmes grandeurs.

## Décision

1. Définir un contrat unique `PlatformBackend`, celui que `DashboardController` utilise déjà avec `PyBulletSimulator` :
   - `connect() -> bool`, `disconnect()` ;
   - `update_platform_pose({'position': mm, 'rotation': deg})`, pose relative à la position de travail ;
   - `step_simulation(steps)` : avance la simulation ; pour le banc, attend le cycle de commande ;
   - `get_platform_state()` : clés `position`, `rotation`, `actuator_positions`, `reachable` (+ vitesses si disponibles) ;
   - `reset_simulation()` (retour à la position de travail), `apply_external_force` optionnel.
2. Créer `BenchPlatform` (`src/hardware/bench.py`), qui implémente ce contrat au-dessus d'un pilote de communication réel (série ou autre, selon l'inventaire PROT-001) :
   - consignes = positions de vérins issues de la **même** IK que la simulation (`src.core.feasibility.actuator_positions`), géométrie du banc chargée depuis la configuration ;
   - **sécurité côté logiciel** : refus des consignes hors course (`check_trajectory`), limites de vitesse et d'accélération, chien de garde (arrêt si le tableau de bord ne répond plus), `emergency_stop` prioritaire. L'arrêt d'urgence matériel reste la protection principale ;
   - pose « mesurée » : dans un premier temps, cinématique directe à partir des codeurs (Phase 2) ; ensuite, une mesure externe (PROT-001, moyen à définir).
3. Le tableau de bord reçoit un sélecteur de source, « Simulation » ou « Banc ». Tout le reste (jauges, écart, scénarios) est partagé.
4. `PhysicalStewartPlatform` et `MotorController` restent disponibles (API préservée) et deviennent des adaptateurs internes de `BenchPlatform`, ou sont dépréciés si l'inventaire montre qu'ils ne correspondent pas au banc.

## Options écartées

- **Deux interfaces distinctes** (une pour la simulation, une pour le banc) : duplication, et aucune garantie que les consignes comparées sont identiques.
- **Passer directement à ROS2 / `ros2_control`** : c'est la cible de la Phase 5, mais trop tôt tant que l'électronique du banc et la communication ne sont pas caractérisées. Le contrat ci-dessus se transposera en nœud ROS2 sans changement de logique.

## Conséquences

- ➕ Mêmes scénarios, même faisabilité, mêmes métriques en simulation et sur le banc : la Phase 7 devient un simple rejeu.
- ➕ Les tests de `DashboardController` couvrent la logique pour les deux sources.
- ➖ Il faut d'abord l'inventaire du banc (PROT-001) : géométrie réelle, course, codeurs, électronique.
- ➖ Tant que la cinématique directe n'existe pas, la pose du banc est estimée, pas mesurée : l'écart consigne/mesure du banc ne sera significatif qu'après la Phase 2 ou avec une mesure externe.
