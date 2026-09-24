#!/usr/bin/env python3
"""
Interface GUI avec simulation PyBullet en temps réel
Combine les contrôles GUI avec la visualisation 3D PyBullet
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
import subprocess
import os
from src.core.platform import StewartPlatform as sp
from src.core.kinematics import InverseKinematics

class StewartGUIWithPyBullet:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Stewart Platform - GUI + PyBullet Simulation")
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
        self.continuous_update = False
        
        # Cinématique
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.clf_ik = InverseKinematics(r_P, r_B, gama_P, gama_B)
        
        # PyBullet Platform
        self.pybullet_platform = None
        
        self.setup_gui()
        self.update_info()
        
    def setup_gui(self):
        """Configure l'interface principale"""
        
        # Titre
        title = tk.Label(self.root, text="🤖 STEWART PLATFORM\nGUI + PYBULLET CONTROL", 
                        font=('Arial', 16, 'bold'), fg='white', bg='#4A90C2', justify=tk.CENTER)
        title.pack(pady=15)
        
        # Frame principal horizontal
        main_frame = tk.Frame(self.root, bg='#4A90C2')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # Colonne gauche - Contrôles
        left_frame = tk.Frame(main_frame, bg='#4A90C2', width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_frame.pack_propagate(False)
        
        # Colonne droite - Informations et contrôles simulation
        right_frame = tk.Frame(main_frame, bg='#4A90C2')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_controls(left_frame)
        self.setup_simulation_controls(right_frame)
        
    def setup_controls(self, parent):
        """Configure les contrôles de la plateforme"""
        
        # Contrôles de translation
        trans_frame = tk.LabelFrame(parent, text="TRANSLATION CONTROLS", 
                                   font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        trans_frame.pack(fill=tk.X, pady=10)
        
        # HEAVE
        self.create_control_slider(trans_frame, "HEAVE (Z)", -0.1, 0.1, 0, 
                                  lambda v: self.update_position(2, v))
        
        # SWAY  
        self.create_control_slider(trans_frame, "SWAY (Y)", -0.05, 0.05, 1,
                                  lambda v: self.update_position(1, v))
        
        # SURGE
        self.create_control_slider(trans_frame, "SURGE (X)", -0.05, 0.05, 2,
                                  lambda v: self.update_position(0, v))
        
        # Contrôles de rotation
        rot_frame = tk.LabelFrame(parent, text="ROTATION CONTROLS", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        rot_frame.pack(fill=tk.X, pady=10)
        
        # YAW
        self.create_control_slider(rot_frame, "YAW", -45, 45, 3,
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
        
        # Stocker la référence
        setattr(self, f'slider_{row}', slider)
        
    def setup_simulation_controls(self, parent):
        """Configure les contrôles de simulation"""
        
        # Frame pour contrôles PyBullet
        sim_frame = tk.LabelFrame(parent, text="PYBULLET SIMULATION", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        sim_frame.pack(fill=tk.X, pady=10)
        
        # Boutons simulation
        button_row1 = tk.Frame(sim_frame, bg='#4A90C2')
        button_row1.pack(fill=tk.X, pady=5)
        
        tk.Button(button_row1, text="🚀 START SIMULATION", font=('Arial', 11, 'bold'),
                 bg='#4CAF50', fg='white', command=self.start_simulation,
                 width=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_row1, text="⏹️ STOP SIMULATION", font=('Arial', 11, 'bold'),
                 bg='#F44336', fg='white', command=self.stop_simulation,
                 width=20).pack(side=tk.RIGHT, padx=5)
        
        button_row2 = tk.Frame(sim_frame, bg='#4A90C2')
        button_row2.pack(fill=tk.X, pady=5)
        
        tk.Button(button_row2, text="🔄 UPDATE POSITION", font=('Arial', 11, 'bold'),
                 bg='#2196F3', fg='white', command=self.update_simulation,
                 width=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_row2, text="🏠 HOME", font=('Arial', 11, 'bold'),
                 bg='#FF9800', fg='white', command=self.go_home,
                 width=20).pack(side=tk.RIGHT, padx=5)
        
        # Mode continu
        continuous_frame = tk.Frame(sim_frame, bg='#4A90C2')
        continuous_frame.pack(fill=tk.X, pady=5)
        
        self.continuous_var = tk.BooleanVar()
        tk.Checkbutton(continuous_frame, text="🔄 Continuous Update", 
                      variable=self.continuous_var, font=('Arial', 10, 'bold'),
                      fg='white', bg='#4A90C2', selectcolor='#2196F3',
                      command=self.toggle_continuous_update).pack()
        
        # Informations système
        info_frame = tk.LabelFrame(parent, text="SYSTEM INFORMATION", 
                                  font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Zone de texte pour informations
        self.info_text = tk.Text(info_frame, height=15, width=50, bg='#2C3E50', fg='#00FF00',
                                font=('Courier', 9), wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.info_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.info_text.yview)
        
    def start_simulation(self):
        """Démarre la simulation PyBullet avec GUI"""
        if not self.simulation_active:
            self.simulation_active = True
            
            def run_simulation():
                try:
                    # Variables d'environnement pour améliorer la stabilité du GUI
                    os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
                    os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
                    
                    # Créer la plateforme avec GUI
                    self.pybullet_platform = sp(self.path, self.joint_indices, 
                                               self.actuator_indices, self.design_variables)
                    
                    # Démarrer l'environnement PyBullet avec GUI
                    self.pybullet_platform.set_env(use_gui=True)
                    self.pybullet_platform.set_constraints()
                    self.pybullet_platform.init_stewart(flag=True)
                    
                    self.log_info("✅ PyBullet simulation started with GUI")
                    
                    # Maintenir la simulation active
                    import pybullet as p
                    while self.simulation_active:
                        p.stepSimulation()
                        time.sleep(1./240.)  # 240 Hz
                        
                except Exception as e:
                    self.log_info(f"❌ Simulation error: {str(e)}")
                    self.simulation_active = False
            
            # Démarrer la simulation dans un thread séparé
            sim_thread = threading.Thread(target=run_simulation)
            sim_thread.daemon = True
            sim_thread.start()
            
            self.log_info("🚀 Starting PyBullet simulation...")
        else:
            self.log_info("⚠️ Simulation already running")
            
    def stop_simulation(self):
        """Arrête la simulation PyBullet"""
        if self.simulation_active:
            self.simulation_active = False
            
            try:
                if self.pybullet_platform:
                    import pybullet as p
                    p.disconnect()
                    self.pybullet_platform = None
                    
                self.log_info("⏹️ PyBullet simulation stopped")
            except Exception as e:
                self.log_info(f"❌ Error stopping simulation: {str(e)}")
        else:
            self.log_info("⚠️ No simulation running")
            
    def update_simulation(self):
        """Met à jour la position dans PyBullet"""
        if self.simulation_active and self.pybullet_platform:
            try:
                # Créer les données de mouvement
                translation = np.array(self.current_position)
                rotation = np.array(self.current_rotation)
                
                # Calculer les longueurs des vérins
                leg_lengths = self.clf_ik.solve(translation, rotation)
                dl = leg_lengths - self.pybullet_platform.l
                
                # Envoyer la commande à PyBullet
                self.pybullet_platform.linear_actuator(dl, 0.5)  # 0.5 sec duration
                
                self.log_info(f"🔄 Position updated: T={translation}, R={rotation}")
                
            except Exception as e:
                self.log_info(f"❌ Update error: {str(e)}")
        else:
            self.log_info("⚠️ No active simulation to update")
            
    def toggle_continuous_update(self):
        """Active/désactive la mise à jour continue"""
        self.continuous_update = self.continuous_var.get()
        
        if self.continuous_update:
            self.log_info("🔄 Continuous update enabled")
            self.start_continuous_update()
        else:
            self.log_info("⏸️ Continuous update disabled")
            
    def start_continuous_update(self):
        """Démarre la mise à jour continue"""
        def continuous_loop():
            while self.continuous_update and self.simulation_active:
                self.update_simulation()
                time.sleep(0.1)  # 10 Hz update rate
                
        if self.continuous_update:
            thread = threading.Thread(target=continuous_loop)
            thread.daemon = True
            thread.start()
            
    def update_position(self, axis, value):
        """Met à jour la position"""
        self.current_position[axis] = float(value)
        self.update_info()
        
        # Mise à jour automatique si mode continu activé
        if self.continuous_update:
            self.root.after(100, self.update_simulation)
            
    def update_rotation(self, axis, value):
        """Met à jour la rotation"""
        self.current_rotation[axis] = float(value)
        self.update_info()
        
        # Mise à jour automatique si mode continu activé
        if self.continuous_update:
            self.root.after(100, self.update_simulation)
            
    def update_info(self):
        """Met à jour les informations affichées"""
        try:
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation)
            leg_lengths = self.clf_ik.solve(translation, rotation)
            
            info = f"""STEWART PLATFORM STATUS
{'='*45}

CURRENT POSITION (meters):
  X (Surge):  {self.current_position[0]:8.3f}
  Y (Sway):   {self.current_position[1]:8.3f}  
  Z (Heave):  {self.current_position[2]:8.3f}

CURRENT ROTATION (degrees):
  Roll:       {self.current_rotation[0]:8.1f}°
  Pitch:      {self.current_rotation[1]:8.1f}°
  Yaw:        {self.current_rotation[2]:8.1f}°

ACTUATOR LENGTHS (meters):
  Leg 1:      {leg_lengths[0]:8.3f}
  Leg 2:      {leg_lengths[1]:8.3f}
  Leg 3:      {leg_lengths[2]:8.3f}
  Leg 4:      {leg_lengths[3]:8.3f}
  Leg 5:      {leg_lengths[4]:8.3f}
  Leg 6:      {leg_lengths[5]:8.3f}

STATISTICS:
  Min Length: {min(leg_lengths):8.3f} m
  Max Length: {max(leg_lengths):8.3f} m
  Range:      {max(leg_lengths)-min(leg_lengths):8.3f} m

SIMULATION STATUS:
  PyBullet:   {'🟢 ACTIVE' if self.simulation_active else '🔴 STOPPED'}
  Continuous: {'🟢 ON' if self.continuous_update else '🔴 OFF'}
  Platform:   {'✅ READY' if self.pybullet_platform else '❌ NOT INIT'}
"""
            
            # Mettre à jour seulement la partie statique (éviter le spam de logs)
            self.info_text.delete(1.0, "end-50c")  # Garder les 50 derniers caractères (logs)
            self.info_text.insert(1.0, info)
            
        except Exception as e:
            self.log_info(f"❌ Info update error: {str(e)}")
            
    def log_info(self, message):
        """Ajoute un message au log"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Ajouter à la fin du texte
        self.info_text.insert(tk.END, log_message)
        self.info_text.see(tk.END)  # Scroll vers le bas
        
        # Limiter le nombre de lignes (garder les 100 dernières)
        lines = self.info_text.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.info_text.delete(1.0, f"{len(lines)-100}.0")
            
    def go_home(self):
        """Retour position d'origine"""
        # Reset des sliders
        for i in range(6):
            if hasattr(self, f'slider_{i}'):
                getattr(self, f'slider_{i}').set(0)
        
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.update_info()
        
        # Mise à jour PyBullet si actif
        if self.simulation_active:
            self.update_simulation()
            
        self.log_info("🏠 Platform returned to HOME position")
        
    def on_closing(self):
        """Gestion de la fermeture de la fenêtre"""
        self.stop_simulation()
        self.root.destroy()

def main():
    """Fonction principale"""
    print("🚀 Starting Stewart Platform GUI with PyBullet Integration...")
    
    try:
        root = tk.Tk()
        app = StewartGUIWithPyBullet(root)
        
        # Gestion de la fermeture
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("✅ GUI started successfully")
        print("💡 Instructions:")
        print("   1. Click 'START SIMULATION' to open PyBullet GUI")
        print("   2. Use sliders to control the platform")
        print("   3. Click 'UPDATE POSITION' to apply changes")
        print("   4. Enable 'Continuous Update' for real-time control")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")

if __name__ == "__main__":
    main()
