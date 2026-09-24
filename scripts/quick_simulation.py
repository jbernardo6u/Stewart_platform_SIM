#!/usr/bin/env python3
"""
Script de simulation rapide pour la plateforme de Stewart.
Permet de lancer rapidement différentes simulations prédéfinies.

Usage:
    python3 quick_simulation.py
    python3 quick_simulation.py --demo ellipse
    python3 quick_simulation.py --gui pybullet
"""

import sys
import os
import argparse
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class QuickSimulationLauncher:
    """
    Lanceur de simulations rapides.
    Interface simple pour accéder aux fonctionnalités de simulation.
    """
    
    def __init__(self, root):
        """Initialiser le lanceur."""
        self.root = root
        self.root.title("🚀 Quick Simulation - Stewart Platform")
        self.root.geometry("700x600")
        self.root.configure(bg='#1B1B1B')
        
        self.demos = {
            "🔄 Elliptical Path": {
                "description": "Smooth elliptical trajectory with visualization",
                "type": "ellipse",
                "duration": "~30 seconds"
            },
            "🌀 3D Spiral": {
                "description": "Rising spiral motion with rotation",
                "type": "spiral", 
                "duration": "~45 seconds"
            },
            "〰️ Sinusoidal Motion": {
                "description": "Multi-axis sinusoidal waves",
                "type": "sine",
                "duration": "~60 seconds"
            },
            "🎭 Mixed Trajectory": {
                "description": "Combination of multiple motion types",
                "type": "mixed",
                "duration": "~90 seconds"
            },
            "🎯 Custom Control": {
                "description": "Manual position and rotation control",
                "type": "manual",
                "duration": "Interactive"
            }
        }
        
        self.setup_gui()
    
    def setup_gui(self):
        """Configurer l'interface."""
        # Header
        header_frame = tk.Frame(self.root, bg='#2E86AB', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🚀 QUICK SIMULATION",
            font=('Arial', 20, 'bold'),
            fg='white',
            bg='#2E86AB'
        )
        title_label.pack(pady=20)
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#1B1B1B')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Instructions
        instruction_label = tk.Label(
            main_frame,
            text="Select a simulation to run instantly:",
            font=('Arial', 14),
            fg='white',
            bg='#1B1B1B'
        )
        instruction_label.pack(pady=(0, 20))
        
        # Demo buttons
        for demo_name, demo_info in self.demos.items():
            self.create_demo_button(main_frame, demo_name, demo_info)
        
        # Separator
        separator = tk.Frame(main_frame, height=2, bg='#4A90C2')
        separator.pack(fill=tk.X, pady=20)
        
        # Advanced options
        advanced_label = tk.Label(
            main_frame,
            text="Advanced Options:",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#1B1B1B'
        )
        advanced_label.pack(pady=(0, 10))
        
        # GUI buttons
        gui_frame = tk.Frame(main_frame, bg='#1B1B1B')
        gui_frame.pack(fill=tk.X, pady=10)
        
        self.create_gui_button(gui_frame, "🎮 Simple GUI", "Basic control interface", self.launch_simple_gui)
        self.create_gui_button(gui_frame, "⚡ Advanced GUI", "Full-featured interface", self.launch_advanced_gui)
        self.create_gui_button(gui_frame, "🔬 PyBullet 3D", "3D simulation view", self.launch_pybullet_gui)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg='#1B1B1B')
        footer_frame.pack(fill=tk.X, pady=10)
        
        tip_label = tk.Label(
            footer_frame,
            text="💡 Tip: PyBullet GUI provides the most immersive experience with 3D visualization",
            font=('Arial', 10),
            fg='#888888',
            bg='#1B1B1B'
        )
        tip_label.pack()
    
    def create_demo_button(self, parent, demo_name, demo_info):
        """Créer un bouton de démonstration."""
        demo_frame = tk.Frame(parent, bg='#2E86AB', relief='raised', borderwidth=2)
        demo_frame.pack(fill=tk.X, pady=5)
        
        # Main button
        button = tk.Button(
            demo_frame,
            text=demo_name,
            font=('Arial', 12, 'bold'),
            bg='#4A90C2',
            fg='white',
            command=lambda: self.run_demo(demo_info['type']),
            relief='flat',
            borderwidth=0,
            width=20
        )
        button.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Description
        desc_frame = tk.Frame(demo_frame, bg='#2E86AB')
        desc_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        desc_label = tk.Label(
            desc_frame,
            text=demo_info['description'],
            font=('Arial', 11),
            fg='white',
            bg='#2E86AB',
            anchor='w'
        )
        desc_label.pack(anchor='w', pady=5)
        
        duration_label = tk.Label(
            desc_frame,
            text=f"Duration: {demo_info['duration']}",
            font=('Arial', 9),
            fg='#E8F4FD',
            bg='#2E86AB',
            anchor='w'
        )
        duration_label.pack(anchor='w')
    
    def create_gui_button(self, parent, text, description, command):
        """Créer un bouton GUI."""
        button_frame = tk.Frame(parent, bg='#1B1B1B')
        button_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        button = tk.Button(
            button_frame,
            text=text,
            font=('Arial', 10, 'bold'),
            bg='#4A90C2',
            fg='white',
            command=command,
            relief='raised',
            borderwidth=2
        )
        button.pack(fill=tk.X, pady=2)
        
        desc_label = tk.Label(
            button_frame,
            text=description,
            font=('Arial', 8),
            fg='#888888',
            bg='#1B1B1B'
        )
        desc_label.pack()
    
    def run_demo(self, demo_type):
        """Lancer une démonstration."""
        try:
            if demo_type == "manual":
                # Lancer le GUI PyBullet pour contrôle manuel
                self.launch_pybullet_gui()
            else:
                # Lancer une démonstration de trajectoire
                import subprocess
                cmd = [
                    sys.executable, 
                    str(project_root / "examples" / "trajectory_demo.py"),
                    "--type", demo_type,
                    "--simulation"
                ]
                subprocess.Popen(cmd)
                messagebox.showinfo(
                    "Simulation Started", 
                    f"🚀 {demo_type.capitalize()} simulation started!\n\n"
                    "A new window will open with the trajectory visualization."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start simulation: {str(e)}")
    
    def launch_simple_gui(self):
        """Lancer le GUI simple."""
        try:
            from src.gui.simple_gui import main as simple_gui_main
            self.root.withdraw()
            simple_gui_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Simple GUI: {str(e)}")
    
    def launch_advanced_gui(self):
        """Lancer le GUI avancé."""
        try:
            from src.gui.advanced_gui import main as advanced_gui_main
            self.root.withdraw()
            advanced_gui_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Advanced GUI: {str(e)}")
    
    def launch_pybullet_gui(self):
        """Lancer le GUI PyBullet."""
        try:
            from src.gui.pybullet_gui import main as pybullet_gui_main
            self.root.withdraw()
            pybullet_gui_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch PyBullet GUI: {str(e)}")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Quick simulation launcher for Stewart Platform")
    parser.add_argument("--demo", choices=["ellipse", "spiral", "sine", "mixed"], 
                       help="Run a specific demo directly")
    parser.add_argument("--gui", choices=["simple", "advanced", "pybullet"],
                       help="Launch a specific GUI directly")
    
    args = parser.parse_args()
    
    if args.demo:
        # Lancer directement une démonstration
        try:
            import subprocess
            cmd = [
                sys.executable,
                str(project_root / "examples" / "trajectory_demo.py"),
                "--type", args.demo,
                "--simulation"
            ]
            subprocess.run(cmd)
        except Exception as e:
            print(f"Error running demo: {e}")
            return
    
    elif args.gui:
        # Lancer directement un GUI
        try:
            if args.gui == "simple":
                from src.gui.simple_gui import main as gui_main
            elif args.gui == "advanced":
                from src.gui.advanced_gui import main as gui_main
            elif args.gui == "pybullet":
                from src.gui.pybullet_gui import main as gui_main
            
            gui_main()
        except Exception as e:
            print(f"Error launching GUI: {e}")
            return
    
    else:
        # Lancer l'interface de sélection
        root = tk.Tk()
        app = QuickSimulationLauncher(root)
        root.mainloop()


if __name__ == "__main__":
    main()
