#!/usr/bin/env python3
"""
Simulation Manager - Interface simplifiée pour toutes les simulations
====================================================================

Ce script fournit une interface unifiée pour accéder à toutes les fonctionnalités
de simulation de la plateforme de Stewart de manière intuitive.

Features:
- Accès rapide aux démonstrations prédéfinies
- Lancement direct des GUIs de simulation
- Scénarios de test intégrés
- Configuration automatique
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import subprocess
import threading
from pathlib import Path

# Configuration du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SimulationManager:
    """Gestionnaire principal des simulations."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Simulation Manager - Stewart Platform")
        self.root.geometry("900x700")
        self.root.configure(bg='#0B1426')
        
        # Couleurs du thème
        self.colors = {
            'bg_primary': '#0B1426',
            'bg_secondary': '#1E3A5F',
            'bg_accent': '#2E86AB',
            'fg_primary': '#FFFFFF',
            'fg_secondary': '#E8F4FD',
            'accent': '#4A90C2',
            'success': '#00D2A7',
            'warning': '#FFB347',
            'error': '#FF6B6B'
        }
        
        # Scénarios de simulation disponibles
        self.scenarios = {
            "Demos": {
                "🔄 Elliptical Motion": {
                    "command": ["python3", "examples/trajectory_demo.py", "--type", "ellipse", "--simulation"],
                    "description": "Smooth elliptical trajectory with gentle movements",
                    "level": "Beginner",
                    "duration": "30s"
                },
                "🌀 3D Spiral": {
                    "command": ["python3", "examples/trajectory_demo.py", "--type", "spiral", "--simulation"],
                    "description": "Rising spiral with combined translation and rotation",
                    "level": "Intermediate",
                    "duration": "45s"
                },
                "〰️ Sinusoidal Waves": {
                    "command": ["python3", "examples/trajectory_demo.py", "--type", "sine", "--simulation"],
                    "description": "Multi-axis sinusoidal motion patterns",
                    "level": "Advanced",
                    "duration": "60s"
                },
                "🎭 Mixed Patterns": {
                    "command": ["python3", "examples/trajectory_demo.py", "--type", "mixed", "--simulation"],
                    "description": "Complex combination of multiple motion types",
                    "level": "Expert",
                    "duration": "90s"
                }
            },
            "Interactive": {
                "🎯 Manual Control": {
                    "command": "pybullet_gui",
                    "description": "Real-time manual control with 3D visualization",
                    "level": "All Levels",
                    "duration": "Interactive"
                },
                "⚡ Advanced Control": {
                    "command": "advanced_gui",
                    "description": "Full-featured control with presets and automation",
                    "level": "Intermediate+",
                    "duration": "Interactive"
                },
                "🎮 Simple Control": {
                    "command": "simple_gui",
                    "description": "Basic position and rotation control interface",
                    "level": "Beginner",
                    "duration": "Interactive"
                }
            },
            "Testing": {
                "🔬 Kinematics Test": {
                    "command": ["python3", "tests/test_kinematics.py"],
                    "description": "Validate inverse kinematics calculations",
                    "level": "Technical",
                    "duration": "10s"
                },
                "📊 System Check": {
                    "command": ["python3", "scripts/system_check.py"],
                    "description": "Verify system dependencies and configuration",
                    "level": "Technical", 
                    "duration": "15s"
                }
            }
        }
        
        self.setup_gui()
    
    def setup_gui(self):
        """Configurer l'interface principale."""
        # Header avec gradient effect
        self.create_header()
        
        # Notebook pour les catégories
        self.create_notebook()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Créer l'en-tête avec style."""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_accent'], height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Titre principal
        title_label = tk.Label(
            header_frame,
            text="🎮 SIMULATION MANAGER",
            font=('Arial', 24, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_accent']
        )
        title_label.pack(pady=(20, 5))
        
        # Sous-titre
        subtitle_label = tk.Label(
            header_frame,
            text="Stewart Platform - Unified Simulation Interface",
            font=('Arial', 12),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_accent']
        )
        subtitle_label.pack()
        
        # Statistiques rapides
        stats_frame = tk.Frame(header_frame, bg=self.colors['bg_accent'])
        stats_frame.pack(pady=10)
        
        total_scenarios = sum(len(category) for category in self.scenarios.values())
        stats_text = f"📊 {total_scenarios} Scenarios Available  •  🚀 Ready to Launch  •  ⚡ One-Click Access"
        
        stats_label = tk.Label(
            stats_frame,
            text=stats_text,
            font=('Arial', 10),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_accent']
        )
        stats_label.pack()
    
    def create_notebook(self):
        """Créer le notebook avec les catégories."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurer le style du notebook
        style.configure('TNotebook', background=self.colors['bg_primary'])
        style.configure('TNotebook.Tab', 
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['fg_primary'],
                       padding=[20, 10])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['bg_accent'])],
                 foreground=[('selected', self.colors['fg_primary'])])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Créer les onglets pour chaque catégorie
        for category_name, scenarios in self.scenarios.items():
            self.create_category_tab(category_name, scenarios)
    
    def create_category_tab(self, category_name, scenarios):
        """Créer un onglet pour une catégorie de scénarios."""
        # Frame principal de l'onglet
        tab_frame = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(tab_frame, text=f"  {category_name}  ")
        
        # Description de la catégorie
        if category_name == "Demos":
            desc = "Pre-built trajectory demonstrations showcasing platform capabilities"
        elif category_name == "Interactive":
            desc = "Real-time control interfaces for manual operation and testing"
        else:  # Testing
            desc = "Technical validation tools and system diagnostics"
        
        desc_label = tk.Label(
            tab_frame,
            text=desc,
            font=('Arial', 11),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_primary'],
            wraplength=800
        )
        desc_label.pack(pady=(20, 30))
        
        # Container pour les scénarios
        scenarios_frame = tk.Frame(tab_frame, bg=self.colors['bg_primary'])
        scenarios_frame.pack(fill=tk.BOTH, expand=True, padx=40)
        
        # Créer les cartes de scénarios
        for i, (scenario_name, scenario_info) in enumerate(scenarios.items()):
            self.create_scenario_card(scenarios_frame, scenario_name, scenario_info, i)
    
    def create_scenario_card(self, parent, scenario_name, scenario_info, index):
        """Créer une carte pour un scénario."""
        # Frame principal de la carte
        card_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], 
                             relief='raised', borderwidth=2)
        card_frame.pack(fill=tk.X, pady=10)
        
        # Header de la carte
        header_frame = tk.Frame(card_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # Nom du scénario
        name_label = tk.Label(
            header_frame,
            text=scenario_name,
            font=('Arial', 14, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_secondary']
        )
        name_label.pack(side=tk.LEFT)
        
        # Badges de niveau et durée
        badges_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        badges_frame.pack(side=tk.RIGHT)
        
        level_color = {
            'Beginner': self.colors['success'],
            'Intermediate': self.colors['warning'], 
            'Advanced': self.colors['error'],
            'Expert': '#8B5CF6',
            'All Levels': self.colors['accent'],
            'Technical': '#6B7280'
        }
        
        level_badge = tk.Label(
            badges_frame,
            text=scenario_info['level'],
            font=('Arial', 9, 'bold'),
            fg='white',
            bg=level_color.get(scenario_info['level'], self.colors['accent']),
            padx=8, pady=2
        )
        level_badge.pack(side=tk.RIGHT, padx=(10, 0))
        
        duration_badge = tk.Label(
            badges_frame,
            text=scenario_info['duration'],
            font=('Arial', 9),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_accent'],
            padx=8, pady=2
        )
        duration_badge.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Description
        desc_frame = tk.Frame(card_frame, bg=self.colors['bg_secondary'])
        desc_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        desc_label = tk.Label(
            desc_frame,
            text=scenario_info['description'],
            font=('Arial', 11),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_secondary'],
            wraplength=600,
            justify='left'
        )
        desc_label.pack(side=tk.LEFT, anchor='w')
        
        # Bouton de lancement
        launch_button = tk.Button(
            desc_frame,
            text="🚀 Launch",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg=self.colors['accent'],
            command=lambda: self.launch_scenario(scenario_name, scenario_info),
            relief='raised',
            borderwidth=2,
            padx=20, pady=8
        )
        launch_button.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_status_bar(self):
        """Créer la barre de statut."""
        self.status_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=30)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="💡 Ready to launch simulations - Select a scenario above",
            font=('Arial', 10),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=15, pady=6)
        
        # Info sur les raccourcis
        shortcut_label = tk.Label(
            self.status_frame,
            text="⌨️ Tip: Use 'python3 scripts/quick_simulation.py --help' for command line options",
            font=('Arial', 9),
            fg='#888888',
            bg=self.colors['bg_secondary']
        )
        shortcut_label.pack(side=tk.RIGHT, padx=15, pady=6)
    
    def update_status(self, message, color=None):
        """Mettre à jour le statut."""
        if color is None:
            color = self.colors['fg_secondary']
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def launch_scenario(self, scenario_name, scenario_info):
        """Lancer un scénario de simulation."""
        try:
            self.update_status(f"🚀 Launching {scenario_name}...", self.colors['success'])
            
            command = scenario_info['command']
            
            if isinstance(command, str):
                # Commande GUI
                if command == "simple_gui":
                    from src.gui.simple_gui import main as gui_main
                elif command == "advanced_gui":
                    from src.gui.advanced_gui import main as gui_main
                elif command == "pybullet_gui":
                    from src.gui.pybullet_gui import main as gui_main
                
                # Lancer dans un thread séparé
                def launch_gui():
                    try:
                        gui_main()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to launch GUI: {str(e)}")
                    finally:
                        self.update_status("💡 Ready to launch simulations")
                
                thread = threading.Thread(target=launch_gui, daemon=True)
                thread.start()
                
            else:
                # Commande subprocess
                subprocess.Popen(command, cwd=project_root)
                self.update_status(f"✅ {scenario_name} started successfully", self.colors['success'])
                
                # Reset status after delay
                self.root.after(3000, lambda: self.update_status("💡 Ready to launch simulations"))
            
        except Exception as e:
            error_msg = f"❌ Failed to launch {scenario_name}: {str(e)}"
            self.update_status(error_msg, self.colors['error'])
            messagebox.showerror("Launch Error", error_msg)


def main():
    """Fonction principale."""
    root = tk.Tk()
    app = SimulationManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
