#!/usr/bin/env python3
"""
Interface GUI Stewart Platform avec PyBullet - Version Robuste
Gère les problèmes de compatibilité PyBullet et offre des solutions de fallback
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
import subprocess
import os
import sys
from src.core.kinematics import InverseKinematics

class RobustStewartGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Stewart Platform - Robust GUI + PyBullet")
        self.root.geometry("900x700")
        self.root.configure(bg='#4A90C2')
        
        # Configuration
        self.path = "simulation/urdf/Stewart.urdf"
        self.joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
        self.actuator_indices = [9, 2, 31, 45, 38, 24]
        self.design_variables = [0.2, 0.2, 12, 12]
        
        # État
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.simulation_active = False
        self.pybullet_available = False
        self.pybullet_platform = None
        
        # Cinématique
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.clf_ik = InverseKinematics(r_P, r_B, gama_P, gama_B)
        
        # Vérifier PyBullet
        self.check_pybullet()
        
        self.setup_gui()
        self.update_info()
        
    def check_pybullet(self):
        """Vérifie si PyBullet est disponible et fonctionnel"""
        try:
            import pybullet as p
            self.pybullet_available = True
            self.log_info("✅ PyBullet disponible")
        except ImportError:
            self.pybullet_available = False
            self.log_info("❌ PyBullet non disponible - Mode cinématique seulement")
            
    def test_pybullet_gui(self):
        """Test PyBullet GUI avec gestion d'erreur robuste"""
        if not self.pybullet_available:
            return False
            
        try:
            import pybullet as p
            
            # Variables d'environnement pour stabilité
            os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            
            # Test de connexion GUI
            physics_client = p.connect(p.GUI, options="--width=800 --height=600")
            
            # Test rapide
            p.setGravity(0, 0, -9.81)
            p.disconnect()
            
            self.log_info("✅ PyBullet GUI test réussi")
            return True
            
        except Exception as e:
            self.log_info(f"❌ PyBullet GUI test échoué: {str(e)}")
            return False
        
    def setup_gui(self):
        """Configure l'interface principale"""
        
        # Titre
        title = tk.Label(self.root, text="🤖 STEWART PLATFORM\nROBUST CONTROL INTERFACE", 
                        font=('Arial', 16, 'bold'), fg='white', bg='#4A90C2')
        title.pack(pady=10)
        
        # Frame principal avec notebook
        main_notebook = ttk.Notebook(self.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Onglet Contrôles
        control_frame = tk.Frame(main_notebook, bg='#4A90C2')
        main_notebook.add(control_frame, text="🎮 Contrôles")
        
        # Onglet Simulation
        sim_frame = tk.Frame(main_notebook, bg='#4A90C2')
        main_notebook.add(sim_frame, text="🚀 Simulation")
        
        # Onglet Informations
        info_frame = tk.Frame(main_notebook, bg='#4A90C2')
        main_notebook.add(info_frame, text="ℹ️ Info")
        
        # Configuration des onglets
        self.setup_controls(control_frame)
        self.setup_simulation_tab(sim_frame)
        self.setup_info_tab(info_frame)
        
    def setup_controls(self, parent):
        """Configure les contrôles de position"""
        
        # Contrôles de translation
        trans_frame = tk.LabelFrame(parent, text="TRANSLATION", 
                                   font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        trans_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # HEAVE (Z)
        self.create_control_slider(trans_frame, "HEAVE (Z)", -0.02, 0.02, 0,
                                  lambda v: self.update_position(2, v))
        
        # SURGE (X)
        self.create_control_slider(trans_frame, "SURGE (X)", -0.02, 0.02, 1,
                                  lambda v: self.update_position(0, v))
        
        # SWAY (Y)
        self.create_control_slider(trans_frame, "SWAY (Y)", -0.02, 0.02, 2,
                                  lambda v: self.update_position(1, v))
        
        # Contrôles de rotation
        rot_frame = tk.LabelFrame(parent, text="ROTATION", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        rot_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # YAW
        self.create_control_slider(rot_frame, "YAW", -30, 30, 3,
                                  lambda v: self.update_rotation(2, v))
        
        # ROLL
        self.create_control_slider(rot_frame, "ROLL", -30, 30, 4,
                                  lambda v: self.update_rotation(0, v))
        
        # PITCH
        self.create_control_slider(rot_frame, "PITCH", -30, 30, 5,
                                  lambda v: self.update_rotation(1, v))
        
    def create_control_slider(self, parent, label, min_val, max_val, row, callback):
        """Crée un slider de contrôle"""
        
        tk.Label(parent, text=label, font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=row, column=0, sticky='w', padx=5, pady=3)
        
        slider = tk.Scale(parent, from_=min_val, to=max_val, resolution=0.001,
                         orient=tk.HORIZONTAL, length=250, bg='white',
                         command=callback)
        slider.grid(row=row, column=1, padx=5, pady=3)
        slider.set(0)
        
        # Bouton reset pour ce slider
        reset_btn = tk.Button(parent, text="0", command=lambda: slider.set(0),
                             bg='#FF9800', fg='white', width=3)
        reset_btn.grid(row=row, column=2, padx=5, pady=3)
        
        # Stocker la référence
        setattr(self, f'slider_{row}', slider)
        
    def setup_simulation_tab(self, parent):
        """Configure l'onglet simulation"""
        
        # Status PyBullet
        status_frame = tk.LabelFrame(parent, text="STATUS PYBULLET", 
                                    font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        status_frame.pack(fill=tk.X, pady=10, padx=10)
        
        status_text = "✅ PyBullet disponible" if self.pybullet_available else "❌ PyBullet non disponible"
        tk.Label(status_frame, text=status_text, font=('Arial', 11),
                fg='white', bg='#4A90C2').pack(pady=5)
        
        # Contrôles de simulation
        sim_controls = tk.LabelFrame(parent, text="CONTRÔLES SIMULATION", 
                                    font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        sim_controls.pack(fill=tk.X, pady=10, padx=10)
        
        # Boutons de simulation
        button_row1 = tk.Frame(sim_controls, bg='#4A90C2')
        button_row1.pack(fill=tk.X, pady=5)
        
        if self.pybullet_available:
            tk.Button(button_row1, text="🧪 TEST PYBULLET GUI", font=('Arial', 10, 'bold'),
                     bg='#9C27B0', fg='white', command=self.test_gui_button,
                     width=18).pack(side=tk.LEFT, padx=5)
            
            tk.Button(button_row1, text="🚀 START SIMULATION", font=('Arial', 10, 'bold'),
                     bg='#4CAF50', fg='white', command=self.start_simulation,
                     width=18).pack(side=tk.RIGHT, padx=5)
        else:
            tk.Label(button_row1, text="PyBullet non disponible", 
                    font=('Arial', 10), fg='yellow', bg='#4A90C2').pack()
        
        button_row2 = tk.Frame(sim_controls, bg='#4A90C2')
        button_row2.pack(fill=tk.X, pady=5)
        
        if self.pybullet_available:
            tk.Button(button_row2, text="⏹️ STOP SIMULATION", font=('Arial', 10, 'bold'),
                     bg='#F44336', fg='white', command=self.stop_simulation,
                     width=18).pack(side=tk.LEFT, padx=5)
            
            tk.Button(button_row2, text="🔄 UPDATE POSITION", font=('Arial', 10, 'bold'),
                     bg='#2196F3', fg='white', command=self.update_simulation,
                     width=18).pack(side=tk.RIGHT, padx=5)
        
        # Options alternatives
        alt_frame = tk.LabelFrame(parent, text="ALTERNATIVES", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        alt_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Button(alt_frame, text="📊 MATPLOTLIB 3D", font=('Arial', 10, 'bold'),
                 bg='#FF5722', fg='white', command=self.launch_matplotlib,
                 width=20).pack(pady=5)
        
        tk.Button(alt_frame, text="🌐 VISUALISATION WEB", font=('Arial', 10, 'bold'),
                 bg='#607D8B', fg='white', command=self.launch_web_viz,
                 width=20).pack(pady=5)
        
    def setup_info_tab(self, parent):
        """Configure l'onglet informations"""
        
        # Informations système
        sys_frame = tk.LabelFrame(parent, text="SYSTÈME", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        sys_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Informations cinématiques
        kine_frame = tk.LabelFrame(parent, text="CINÉMATIQUE", 
                                  font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        kine_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Zone de texte pour logs
        log_frame = tk.LabelFrame(parent, text="LOGS", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        self.info_text = tk.Text(log_frame, height=15, bg='black', fg='green',
                                font=('Courier', 9), wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.info_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.info_text.yview)
        
    def test_gui_button(self):
        """Test PyBullet GUI via bouton"""
        self.log_info("🧪 Test PyBullet GUI...")
        if self.test_pybullet_gui():
            messagebox.showinfo("Test réussi", "PyBullet GUI fonctionne correctement!")
        else:
            messagebox.showwarning("Test échoué", 
                                  "PyBullet GUI ne fonctionne pas.\nUtilisez les alternatives Matplotlib ou Web.")
        
    def start_simulation(self):
        """Démarre la simulation PyBullet"""
        if not self.pybullet_available:
            messagebox.showwarning("PyBullet indisponible", 
                                  "PyBullet n'est pas disponible. Utilisez les alternatives.")
            return
            
        if self.simulation_active:
            self.log_info("⚠️ Simulation déjà active")
            return
            
        self.simulation_active = True
        
        def run_simulation():
            try:
                # Import PyBullet
                from src.core.platform import StewartPlatform as sp
                import pybullet as p
                
                # Variables d'environnement
                os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
                os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
                
                # Créer la plateforme
                self.pybullet_platform = sp(self.path, self.joint_indices, 
                                           self.actuator_indices, self.design_variables)
                
                # Démarrer avec GUI
                self.pybullet_platform.set_env(use_gui=True)
                self.pybullet_platform.set_constraints()
                self.pybullet_platform.init_stewart(flag=True)
                
                self.log_info("✅ PyBullet simulation démarrée")
                
                # Boucle de simulation
                while self.simulation_active:
                    p.stepSimulation()
                    time.sleep(1./240.)
                    
            except Exception as e:
                self.log_info(f"❌ Erreur simulation: {str(e)}")
                self.simulation_active = False
                messagebox.showerror("Erreur Simulation", 
                                   f"Erreur PyBullet: {str(e)}\n\nUtilisez les alternatives.")
        
        # Démarrer dans un thread
        sim_thread = threading.Thread(target=run_simulation)
        sim_thread.daemon = True
        sim_thread.start()
        
    def stop_simulation(self):
        """Arrête la simulation"""
        if self.simulation_active:
            self.simulation_active = False
            try:
                if self.pybullet_platform:
                    import pybullet as p
                    p.disconnect()
                    self.pybullet_platform = None
                self.log_info("⏹️ Simulation arrêtée")
            except Exception as e:
                self.log_info(f"❌ Erreur arrêt: {str(e)}")
        
    def update_simulation(self):
        """Met à jour la position dans PyBullet"""
        if self.simulation_active and self.pybullet_platform:
            try:
                # Calculer les longueurs des vérins
                translation = np.array(self.current_position)
                rotation = np.array(self.current_rotation)
                leg_lengths = self.clf_ik.solve(translation, rotation)
                dl = leg_lengths - self.pybullet_platform.l
                
                # Envoyer à PyBullet
                self.pybullet_platform.linear_actuator(dl, 0.5)
                self.log_info("🔄 Position mise à jour dans PyBullet")
                
            except Exception as e:
                self.log_info(f"❌ Erreur mise à jour: {str(e)}")
        else:
            self.log_info("⚠️ Aucune simulation active")
        
    def launch_matplotlib(self):
        """Lance l'interface Matplotlib"""
        try:
            self.log_info("📊 Lancement Matplotlib...")
            subprocess.Popen([sys.executable, "stewart_gui_advanced.py"])
        except Exception as e:
            self.log_info(f"❌ Erreur Matplotlib: {str(e)}")
            
    def launch_web_viz(self):
        """Lance la visualisation web"""
        try:
            self.log_info("🌐 Lancement visualisation web...")
            subprocess.Popen([sys.executable, "create_web_viz.py"])
        except Exception as e:
            self.log_info(f"❌ Erreur web viz: {str(e)}")
        
    def update_position(self, axis, value):
        """Met à jour la position"""
        self.current_position[axis] = float(value)
        self.update_info()
        
    def update_rotation(self, axis, value):
        """Met à jour la rotation"""
        self.current_rotation[axis] = float(value)
        self.update_info()
        
    def update_info(self):
        """Met à jour les informations affichées"""
        try:
            # Calcul cinématique
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation) 
            leg_lengths = self.clf_ik.solve(translation, rotation)
            
            info = f"""
POSITION ACTUELLE:
  Translation: X={self.current_position[0]:.3f}, Y={self.current_position[1]:.3f}, Z={self.current_position[2]:.3f}
  Rotation: Roll={self.current_rotation[0]:.1f}°, Pitch={self.current_rotation[1]:.1f}°, Yaw={self.current_rotation[2]:.1f}°

LONGUEURS VÉRINS:
  Vérin 1: {leg_lengths[0]:.6f}m
  Vérin 2: {leg_lengths[1]:.6f}m  
  Vérin 3: {leg_lengths[2]:.6f}m
  Vérin 4: {leg_lengths[3]:.6f}m
  Vérin 5: {leg_lengths[4]:.6f}m
  Vérin 6: {leg_lengths[5]:.6f}m

STATUS:
  PyBullet: {"✅ Disponible" if self.pybullet_available else "❌ Indisponible"}
  Simulation: {"🟢 Active" if self.simulation_active else "🔴 Inactive"}
"""
            self.log_info(info)
            
        except Exception as e:
            self.log_info(f"❌ Erreur calcul: {str(e)}")
        
    def log_info(self, message):
        """Ajoute un message aux logs"""
        if hasattr(self, 'info_text'):
            self.info_text.insert(tk.END, f"{message}\n")
            self.info_text.see(tk.END)
            self.root.update_idletasks()

def main():
    root = tk.Tk()
    app = RobustStewartGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
