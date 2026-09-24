#!/usr/bin/env python3
"""
Script de Migration et Configuration
===================================

Ce script aide à configurer le projet après la réorganisation,
met à jour les chemins et vérifie que tout fonctionne correctement.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Script déplacé dans scripts/ : on travaille depuis la racine du projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


def print_header():
    print("🔧 CONFIGURATION STEWART PLATFORM")
    print("=" * 50)
    print()


def check_dependencies():
    """Vérifie et installe les dépendances."""
    print("📦 Vérification des dépendances...")
    
    required_packages = [
        'numpy',
        'matplotlib',
        'pybullet',
        'tkinter'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
                print(f"   ✅ {package}")
            else:
                __import__(package)
                print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (manquant)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Packages manquants: {', '.join(missing_packages)}")
        install = input("Installer automatiquement? (y/N): ").lower().strip()
        
        if install == 'y':
            for package in missing_packages:
                if package != 'tkinter':  # tkinter est inclus avec Python
                    try:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                        print(f"   ✅ {package} installé")
                    except subprocess.CalledProcessError:
                        print(f"   ❌ Échec installation {package}")
        else:
            print("💡 Installez manuellement avec: pip install -r requirements.txt")
    
    print()


def update_paths():
    """Met à jour les chemins dans les fichiers de lancement."""
    print("🔄 Mise à jour des chemins...")
    
    # Créer des liens symboliques pour la compatibilité
    compatibility_files = [
        ('src/core/kinematics.py', 'inv_kinematics.py'),
        ('src/core/platform.py', 'StewartPlatform.py'),
    ]
    
    for new_path, old_path in compatibility_files:
        if os.path.exists(new_path) and not os.path.exists(old_path):
            try:
                # Créer le dossier parent si nécessaire
                os.makedirs(os.path.dirname(old_path), exist_ok=True)
                
                # Créer un lien symbolique ou copier le fichier
                if os.name == 'nt':  # Windows
                    shutil.copy2(new_path, old_path)
                else:  # Linux/Mac
                    os.symlink(os.path.abspath(new_path), old_path)
                
                print(f"   ✅ Lien créé: {old_path} -> {new_path}")
            except Exception as e:
                print(f"   ⚠️ Impossible de créer le lien {old_path}: {e}")
    
    print()


def test_interfaces():
    """Teste les interfaces principales."""
    print("🧪 Test des interfaces...")
    
    tests = [
        ("Cinématique", "python3 -c \"from src.core.kinematics import InverseKinematics; ik = InverseKinematics(0.2, 0.2, 12, 12); print('OK')\""),
        ("Trajectoires", "python3 -c \"from src.core.trajectory import generate_test_sequence; print('OK')\""),
        ("Configuration", "python3 -c \"import yaml; yaml.safe_load(open('configurations/platform_config.yaml')); print('OK')\""),
    ]
    
    for name, command in tests:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ {name}")
            else:
                print(f"   ❌ {name}: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ {name}: Timeout")
        except Exception as e:
            print(f"   ❌ {name}: {e}")
    
    print()


def create_shortcuts():
    """Crée des raccourcis pour faciliter l'utilisation."""
    print("🚀 Création des raccourcis...")
    
    # Script de lancement principal
    launcher_content = '''#!/bin/bash
# Lanceur Stewart Platform
cd "$(dirname "$0")"
python3 scripts/launcher.py
'''
    
    with open('stewart-launcher.sh', 'w') as f:
        f.write(launcher_content)
    
    # Rendre exécutable
    os.chmod('stewart-launcher.sh', 0o755)
    print("   ✅ stewart-launcher.sh créé")
    
    # Script GUI direct
    gui_content = '''#!/bin/bash
# GUI Stewart Platform (Matplotlib)
cd "$(dirname "$0")"
python3 src/gui/advanced_gui.py
'''
    
    with open('stewart-gui.sh', 'w') as f:
        f.write(gui_content)
    
    os.chmod('stewart-gui.sh', 0o755)
    print("   ✅ stewart-gui.sh créé")
    
    print()


def show_usage():
    """Affiche les instructions d'utilisation."""
    print("📋 INSTRUCTIONS D'UTILISATION")
    print("-" * 40)
    print()
    print("🎮 Interfaces Principales:")
    print("   ./stewart-launcher.sh                    # Lanceur complet")
    print("   ./stewart-gui.sh                         # GUI direct (Matplotlib)")
    print("   python3 scripts/launcher.py             # Lanceur Python")
    print()
    print("📝 Exemples:")
    print("   python3 examples/trajectory_demo.py --type ellipse")
    print("   python3 examples/hardware_integration.py --test")
    print("   python3 -m pytest tests/unit_tests")
    print()
    print("📚 Documentation:")
    print("   README.md                                # Guide principal")
    print("   docs/guides/GUIDE_UTILISATION.md         # Guide détaillé")
    print("   ARCHITECTURE.md                          # Architecture du projet")
    print()
    print("🔧 Configuration:")
    print("   configurations/platform_config.yaml      # Configuration principale")
    print()


def main():
    """Fonction principale."""
    print_header()
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('src'):
        print("❌ Ce script doit être exécuté depuis la racine du projet Stewart Platform")
        return
    
    try:
        check_dependencies()
        update_paths()
        test_interfaces()
        create_shortcuts()
        show_usage()
        
        print("🎉 Configuration terminée avec succès!")
        print()
        print("💡 Pour commencer: ./stewart-launcher.sh")
        
    except KeyboardInterrupt:
        print("\n⏹️ Configuration interrompue")
    except Exception as e:
        print(f"\n❌ Erreur de configuration: {e}")


if __name__ == "__main__":
    main()
