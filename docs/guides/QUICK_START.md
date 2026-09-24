# 🚀 Quick Start - Stewart Platform Simulations

Bienvenue dans le projet Stewart Platform ! Ce guide vous aidera à démarrer rapidement avec les simulations.

## 🎯 Démarrage Ultra-Rapide (1 Minute)

### Option 1: Lanceur One-Click ⚡
```bash
python3 run_simulation.py
```
**Interface simple avec menu interactif - recommandé pour débuter !**

### Option 2: GUI PyBullet Direct 🔬
```bash
python3 -c "from src.gui.pybullet_gui import main; main()"
```
**Simulation 3D immédiate avec contrôle en temps réel**

### Option 3: Démonstration Automatique 🎭
```bash
python3 examples/trajectory_demo.py --type ellipse --simulation
```
**Voir la plateforme exécuter une trajectoire elliptique**

## 🎮 Interfaces Disponibles

| Interface | Difficulté | Description | Commande |
|-----------|------------|-------------|----------|
| **Simple GUI** | 🟢 Débutant | Contrôles de base, idéal pour apprendre | `python3 -c "from src.gui.simple_gui import main; main()"` |
| **Advanced GUI** | 🟡 Intermédiaire | Interface complète avec préréglages | `python3 -c "from src.gui.advanced_gui import main; main()"` |
| **PyBullet 3D** | 🔵 Tous niveaux | Simulation 3D en temps réel | `python3 -c "from src.gui.pybullet_gui import main; main()"` |

## 🎪 Démonstrations Prêtes à l'Emploi

### Trajectoires Automatiques
```bash
# Mouvement elliptique fluide (30s)
python3 examples/trajectory_demo.py --type ellipse --simulation

# Spirale 3D avec rotation (45s)
python3 examples/trajectory_demo.py --type spiral --simulation

# Ondes sinusoïdales multi-axes (60s)
python3 examples/trajectory_demo.py --type sine --simulation

# Trajectoire complexe mixte (90s)
python3 examples/trajectory_demo.py --type mixed --simulation
```

### Mode Interactif
```bash
# Choisir la démonstration depuis un menu
python3 examples/trajectory_demo.py
```

## 🛠️ Gestionnaires de Simulation

### Simulation Manager (Interface Avancée)
```bash
python3 scripts/simulation_manager.py
```
Interface complète avec onglets organisés par catégorie.

### Quick Simulation (Accès Rapide)
```bash
python3 scripts/quick_simulation.py
```
Lanceur rapide pour les simulations les plus populaires.

### Launcher Principal (Projet Complet)
```bash
python3 scripts/launcher.py
```
Accès à toutes les fonctionnalités du projet.

## 🔧 Vérification du Système

Avant de commencer, vérifiez que tout est bien configuré :
```bash
python3 scripts/system_check.py
```

## 📚 Utilisation Typique

### 1. Premier Test (Débutant)
```bash
# 1. Vérifier le système
python3 scripts/system_check.py

# 2. Lancer le GUI simple
python3 run_simulation.py
# Puis choisir option "1"
```

### 2. Exploration (Intermédiaire)
```bash
# 1. Voir une démonstration automatique
python3 examples/trajectory_demo.py --type ellipse --simulation

# 2. Essayer le contrôle manuel 3D
python3 run_simulation.py
# Puis choisir option "2" (PyBullet 3D)
```

### 3. Utilisation Avancée
```bash
# Interface complète avec toutes les fonctionnalités
python3 scripts/simulation_manager.py
```

## 🎯 Scénarios d'Usage

| Objectif | Recommandation | Commande |
|----------|----------------|----------|
| **Découvrir le projet** | GUI Simple | `python3 run_simulation.py` → option 1 |
| **Voir la plateforme bouger** | Démo elliptique | `python3 run_simulation.py` → option 4 |
| **Contrôle manuel en 3D** | PyBullet GUI | `python3 run_simulation.py` → option 2 |
| **Explorer toutes les fonctions** | Simulation Manager | `python3 scripts/simulation_manager.py` |
| **Test rapide du système** | System Check | `python3 run_simulation.py` → option 8 |

## 🚨 Résolution de Problèmes

### Erreur "Module not found"
```bash
# S'assurer d'être dans le bon répertoire
cd /path/to/Stewart-Platform

# Vérifier la structure
python3 scripts/system_check.py
```

### GUI ne s'affiche pas
```bash
# Vérifier tkinter
python3 -c "import tkinter; print('✅ tkinter OK')"

# Utiliser le mode console si nécessaire
python3 examples/trajectory_demo.py --type ellipse
```

### PyBullet indisponible
```bash
# Installer PyBullet (optionnel)
pip install pybullet

# Ou utiliser les GUIs sans 3D
python3 -c "from src.gui.simple_gui import main; main()"
```

## 🎉 Prêt à Commencer !

Commencez par cette commande simple :
```bash
python3 run_simulation.py
```

Puis explorez les autres options selon vos besoins !

---

**💡 Conseil**: Commencez par le `run_simulation.py` pour une expérience guidée, puis explorez les autres outils selon vos besoins !
