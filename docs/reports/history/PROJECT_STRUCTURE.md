# 🏗️ NOUVELLE STRUCTURE DU PROJET STEWART PLATFORM

## 📁 Structure proposée

```
stewart-platform/
│
├── 📁 src/                          # Code source principal
│   ├── __init__.py
│   ├── 📁 core/                     # Logique métier principale
│   │   ├── __init__.py
│   │   ├── kinematics.py           # Cinématique inverse (inv_kinematics.py)
│   │   ├── platform.py             # Classe Stewart Platform principale
│   │   └── trajectory.py           # Génération de trajectoires
│   │
│   ├── 📁 hardware/                 # Interface matérielle
│   │   ├── __init__.py
│   │   ├── motor_controller.py     # Contrôle des moteurs
│   │   ├── physical_platform.py    # Interface plateforme physique
│   │   └── config.py              # Configuration hardware
│   │
│   ├── 📁 gui/                     # Interfaces graphiques
│   │   ├── __init__.py
│   │   ├── 📁 widgets/             # Composants GUI réutilisables
│   │   │   ├── __init__.py
│   │   │   ├── sliders.py          # Widgets de contrôle
│   │   │   └── displays.py         # Affichage d'informations
│   │   ├── simple_gui.py           # Interface simple
│   │   ├── advanced_gui.py         # Interface avec matplotlib
│   │   ├── pybullet_gui.py         # Interface PyBullet
│   │   └── web_generator.py        # Générateur visualisation web
│   │
│   ├── 📁 simulation/              # Simulation et visualisation
│   │   ├── __init__.py
│   │   ├── pybullet_sim.py         # Simulation PyBullet
│   │   ├── matplotlib_viz.py       # Visualisation matplotlib
│   │   └── web_viz.py              # Visualisation web
│   │
│   └── 📁 utils/                   # Utilitaires
│       ├── __init__.py
│       ├── math_utils.py           # Fonctions mathématiques
│       ├── file_utils.py           # Gestion fichiers
│       └── logger.py               # Logging
│
├── 📁 assets/                      # Ressources statiques
│   ├── 📁 models/                  # Modèles 3D (URDF, STL)
│   │   ├── stewart.urdf
│   │   └── 📁 meshes/
│   ├── 📁 config/                  # Fichiers de configuration
│   │   ├── platform_config.yaml
│   │   └── hardware_config.yaml
│   └── 📁 images/                  # Images et icônes
│
├── 📁 tests/                       # Tests unitaires
│   ├── __init__.py
│   ├── test_kinematics.py
│   ├── test_platform.py
│   └── test_gui.py
│
├── 📁 examples/                    # Exemples d'utilisation
│   ├── basic_control.py
│   ├── trajectory_demo.py
│   └── hardware_integration.py
│
├── 📁 docs/                        # Documentation
│   ├── user_guide.md
│   ├── api_reference.md
│   └── hardware_setup.md
│
├── 📁 scripts/                     # Scripts utilitaires
│   ├── launcher.py                 # Lanceur principal
│   ├── install_deps.py             # Installation dépendances
│   └── create_video.py             # Génération vidéo
│
├── 📁 output/                      # Fichiers générés
│   ├── videos/
│   ├── logs/
│   └── exports/
│
├── requirements.txt                # Dépendances Python
├── setup.py                       # Installation du package
├── README.md                       # Documentation principale
└── .gitignore                     # Fichiers à ignorer par Git
```

## 🔄 Migration des fichiers actuels

### Core (Logique métier)
- `inv_kinematics.py` → `src/core/kinematics.py`
- `StewartPlatform.py` → `src/core/platform.py`
- `generate_elliptical_points.py` → `src/core/trajectory.py`
- `draw_3d_spiral.py` → `src/core/trajectory.py`

### Hardware
- `motor_controller.py` → `src/hardware/motor_controller.py`
- `physical_stewart.py` → `src/hardware/physical_platform.py`
- `hardware_config.py` → `src/hardware/config.py`

### GUI
- `stewart_gui_simple.py` → `src/gui/simple_gui.py`
- `stewart_gui_advanced.py` → `src/gui/advanced_gui.py`
- `stewart_gui_with_pybullet.py` → `src/gui/pybullet_gui.py`
- `create_web_viz.py` → `src/gui/web_generator.py`

### Assets
- `Stewart/` → `assets/models/`
- Configuration files → `assets/config/`

### Scripts
- `launcher.py` → `scripts/launcher.py`
- `main.py` → `examples/basic_control.py`
- `test_*.py` → `tests/`

## 📦 Avantages de cette structure

1. **🎯 Séparation claire des responsabilités**
2. **📚 Code réutilisable et modulaire**
3. **🔧 Facilite les tests unitaires**
4. **📖 Documentation organisée**
5. **🚀 Installation comme package Python**
6. **🔄 Évolutivité pour futures fonctionnalités**
