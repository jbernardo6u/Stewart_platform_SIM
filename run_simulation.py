#!/usr/bin/env python3
"""
One-Click Simulation Launcher
============================

Script ultra-simple pour lancer rapidement les simulations
Stewart Platform les plus populaires.

Usage:
    python3 run_simulation.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Configuration du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_banner():
    """Afficher la bannière."""
    print("🤖" + "=" * 58 + "🤖")
    print("  STEWART PLATFORM - ONE-CLICK SIMULATION LAUNCHER")
    print("🤖" + "=" * 58 + "🤖")
    print()


def print_menu():
    """Afficher le menu principal."""
    menu_items = [
        ("1", "🎯 Simple GUI", "Basic control interface - perfect for beginners"),
        ("2", "🔬 PyBullet 3D", "Real-time 3D simulation - most immersive"),
        ("3", "⚡ Advanced GUI", "Full-featured interface with presets"),
        ("4", "🔄 Elliptical Demo", "Smooth elliptical trajectory demo"),
        ("5", "🌀 Spiral Demo", "3D spiral motion with rotation"),
        ("6", "〰️ Sine Wave Demo", "Multi-axis sinusoidal patterns"),
        ("7", "🎭 Mixed Demo", "Complex combined movements"),
        ("8", "🛠️ System Check", "Verify system setup and dependencies"),
        ("9", "📚 Full Launcher", "Access all project features"),
        ("q", "🚪 Quit", "Exit the launcher")
    ]
    
    print("Select a simulation to run:")
    print("-" * 60)
    
    for key, title, description in menu_items:
        print(f"  {key:2s}. {title:15s} - {description}")
    
    print("-" * 60)


def run_command(cmd, description):
    """Exécuter une commande avec gestion d'erreur."""
    try:
        print(f"🚀 Starting {description}...")
        if isinstance(cmd, list):
            subprocess.run(cmd, cwd=project_root)
        else:
            # C'est une fonction Python à exécuter
            cmd()
        print(f"✅ {description} completed!")
        return True
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def launch_simple_gui():
    """Lancer le GUI simple."""
    try:
        from src.gui.simple_gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Error: {e}")


def launch_pybullet_gui():
    """Lancer le GUI PyBullet."""
    try:
        from src.gui.pybullet_gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Error: {e}")


def launch_advanced_gui():
    """Lancer le GUI avancé."""
    try:
        from src.gui.advanced_gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Fonction principale."""
    print_banner()
    
    # Vérifier que nous sommes dans le bon répertoire
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📂 Project root: {project_root}")
    
    # Vérifier la présence des fichiers essentiels
    essential_files = [
        "src/core/kinematics.py",
        "src/gui/simple_gui.py",
        "examples/trajectory_demo.py"
    ]
    
    missing_files = []
    for file_path in essential_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {full_path}")
        else:
            print(f"✅ Found: {full_path}")
    
    if missing_files:
        print("\n❌ Missing essential files:")
        for file_path in missing_files:
            print(f"   • {file_path}")
        print(f"\n🔧 Please check the project structure.")
        print(f"💡 Try running from the project root directory:")
        print(f"   cd {project_root}")
        print(f"   python3 run_simulation.py")
        return
    
    # Menu principal
    commands = {
        "1": (launch_simple_gui, "Simple GUI"),
        "2": (launch_pybullet_gui, "PyBullet 3D Simulation"),
        "3": (launch_advanced_gui, "Advanced GUI"),
        "4": (["python3", "examples/trajectory_demo.py", "--type", "ellipse", "--simulation"], "Elliptical Demo"),
        "5": (["python3", "examples/trajectory_demo.py", "--type", "spiral", "--simulation"], "Spiral Demo"),
        "6": (["python3", "examples/trajectory_demo.py", "--type", "sine", "--simulation"], "Sine Wave Demo"),
        "7": (["python3", "examples/trajectory_demo.py", "--type", "mixed", "--simulation"], "Mixed Demo"),
        "8": (["python3", "scripts/system_check.py"], "System Check"),
        "9": (["python3", "scripts/launcher.py"], "Full Project Launcher")
    }
    
    while True:
        try:
            print_menu()
            choice = input("\n🎯 Enter your choice: ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("\n👋 Goodbye! Thanks for using Stewart Platform!")
                break
            
            if choice in commands:
                cmd, description = commands[choice]
                print(f"\n{'='*60}")
                
                success = run_command(cmd, description)
                
                if success:
                    print(f"{'='*60}")
                    continue_choice = input("\n🔄 Run another simulation? [y/n]: ").strip().lower()
                    if continue_choice not in ['y', 'yes']:
                        print("👋 Goodbye!")
                        break
                else:
                    print(f"{'='*60}")
                    input("Press Enter to return to menu...")
            else:
                print("❌ Invalid choice. Please select a number from 1-9 or 'q' to quit.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
