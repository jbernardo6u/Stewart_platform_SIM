# ADR-0001 : Conserver le package `src/` pendant la transition

- **Date** : 2026-09-24
- **Statut** : Acceptée

## Contexte

L'arborescence cible sépare `models/`, `controllers/` et `simulation/`. Le code actif est aujourd'hui dans le package Python `src/` (`src.core`, `src.gui`, `src.hardware`, `src.simulation`), importé sous la forme `from src.core.kinematics import …` par les tests, les exemples, les scripts, les GUI et `setup.py`. La règle projet impose de ne jamais casser les API existantes.

Déplacer physiquement le code maintenant casserait tous les imports. Cela reviendrait aussi à mélanger une restructuration de fichiers avec des corrections métier en attente (anomalies A1 à A8), ce qui rendrait les régressions impossibles à attribuer.

## Décision

1. La restructuration du 2026-09-24 déplace **les ressources** (URDF, maillages, CAO, configuration, médias, documentation, tests) mais **pas le code Python de `src/`**.
2. `models/` et `controllers/` sont créés avec un README qui indique où se trouve l'implémentation actuelle.
3. La migration du code se fait **module par module**, dans la phase de la roadmap concernée, avec pour chaque module :
   - le nouveau module sous `models/…` ou `controllers/…` ;
   - un réexport dans l'ancien emplacement `src/…` (`from models.kinematics.inverse import InverseKinematics`) ;
   - des tests couvrant l'ancien et le nouveau chemin d'import.

## Conséquences

- ➕ Zéro rupture d'API ; les commandes documentées continuent de fonctionner.
- ➕ Chaque migration est petite, testée et réversible.
- ➖ Pendant la transition, deux emplacements coexistent : les README de `models/` et `controllers/` donnent la correspondance.
- ➖ Nommer les packages de premier niveau `models` et `controllers` expose à des collisions de noms. À réévaluer au moment de la première migration (option : un package unique `rem_stewart/` avec des sous-packages `models`, `controllers`).
