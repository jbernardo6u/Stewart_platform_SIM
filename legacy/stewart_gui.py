#!/usr/bin/env python3
"""
Interface GUI pour contrôle de la plateforme Stewart
Similaire à l'image fournie avec sliders pour chaque degré de liberté
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
from src.core.platform import StewartPlatform as sp
from src.core.kinematics import InverseKinematics

class StewartPlatformGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Stewart Platform Control Interface")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2E86AB')
        
        # Configuration de la plateforme
        self.path = "simulation/urdf/Stewart.urdf"
        self.joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
        self.actuator_indices = [9, 2, 31, 45, 38, 24]
        self.design_variables = [0.2, 0.2, 12, 12]
        
        # État actuel de la plateforme
        self.current_position = [0, 0, 0]  # X, Y, Z
        self.current_rotation = [0, 0, 0]  # Roll, Pitch, Yaw
        self.auto_mode = [False, False, False, False, False, False]  # Auto pour chaque axe
        
        # Cinématique inverse
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.clf_ik = InverseKinematics(r_P, r_B, gama_P, gama_B)
        
        # Animation
        self.animation_running = False
        self.animation_thread = None
        
        self.setup_gui()
        self.update_leg_lengths()
        
    def setup_gui(self):
        """Configure l'interface utilisateur"""
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2E86AB')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title = tk.Label(main_frame, text="🤖 STEWART PLATFORM CONTROL", 
                        font=('Arial', 20, 'bold'), fg='white', bg='#2E86AB')
        title.pack(pady=(0, 20))
        
        # Frame pour les contrôles
        controls_frame = tk.Frame(main_frame, bg='#2E86AB')
        controls_frame.pack(fill=tk.BOTH, expand=True)
        
        # Colonne gauche - Contrôles de translation
        left_frame = tk.Frame(controls_frame, bg='#2E86AB')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        self.setup_translation_controls(left_frame)
        
        # Colonne droite - Contrôles de rotation
        right_frame = tk.Frame(controls_frame, bg='#2E86AB')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))
        
        self.setup_rotation_controls(right_frame)
        
        # Frame du bas - Informations et contrôles généraux
        bottom_frame = tk.Frame(main_frame, bg='#2E86AB')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        self.setup_bottom_controls(bottom_frame)
        
    def setup_translation_controls(self, parent):
        """Configure les contrôles de translation (Heave, Sway, Surge)"""
        
        title = tk.Label(parent, text="TRANSLATION CONTROLS", 
                        font=('Arial', 14, 'bold'), fg='white', bg='#2E86AB')
        title.pack(pady=(0, 10))
        
        # HEAVE (Z - Vertical)
        self.setup_slider(parent, "HEAVE", 0, -0.1, 0.1, 
                         lambda v: self.update_position(2, v), 2)
        
        # SWAY (Y - Latéral)  
        self.setup_slider(parent, "SWAY", 1, -0.05, 0.05,
                         lambda v: self.update_position(1, v), 1)
        
        # SURGE (X - Avant/Arrière)
        self.setup_slider(parent, "SURGE", 2, -0.05, 0.05,
                         lambda v: self.update_position(0, v), 0)
        
    def setup_rotation_controls(self, parent):
        """Configure les contrôles de rotation (Yaw, Roll, Pitch)"""
        
        title = tk.Label(parent, text="ROTATION CONTROLS", 
                        font=('Arial', 14, 'bold'), fg='white', bg='#2E86AB')
        title.pack(pady=(0, 10))
        
        # YAW (Z - Rotation autour de Z)
        self.setup_slider(parent, "YAW", 3, -45, 45,
                         lambda v: self.update_rotation(2, v), 5)
        
        # ROLL (X - Rotation autour de X)
        self.setup_slider(parent, "ROLL", 4, -30, 30,
                         lambda v: self.update_rotation(0, v), 3)
        
        # PITCH (Y - Rotation autour de Y)
        self.setup_slider(parent, "PITCH", 5, -30, 30,
                         lambda v: self.update_rotation(1, v), 4)
        
    def setup_slider(self, parent, label, index, min_val, max_val, callback, auto_index):
        """Crée un slider avec son label et checkbox AUTO"""
        
        # Frame pour ce slider
        slider_frame = tk.Frame(parent, bg='#2E86AB')
        slider_frame.pack(fill=tk.X, pady=10)
        
        # Label
        label_widget = tk.Label(slider_frame, text=label, 
                               font=('Arial', 12, 'bold'), fg='white', bg='#2E86AB')
        label_widget.pack(anchor=tk.W)
        
        # Frame pour slider et checkbox
        control_frame = tk.Frame(slider_frame, bg='#2E86AB')
        control_frame.pack(fill=tk.X, pady=5)
        
        # Slider
        slider = tk.Scale(control_frame, from_=min_val, to=max_val, resolution=0.001,
                         orient=tk.HORIZONTAL, length=300, 
                         bg='white', fg='black', highlightbackground='#2E86AB',
                         command=callback)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        slider.set(0)
        
        # Checkbox AUTO
        auto_var = tk.BooleanVar()
        auto_check = tk.Checkbutton(control_frame, text="AUTO", variable=auto_var,
                                   fg='white', bg='#2E86AB', selectcolor='#2E86AB',
                                   command=lambda: self.toggle_auto(auto_index, auto_var.get()))
        auto_check.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Stocker les références
        setattr(self, f'slider_{index}', slider)
        setattr(self, f'auto_var_{auto_index}', auto_var)
        
    def setup_bottom_controls(self, parent):
        """Configure les contrôles du bas"""
        
        # Frame pour les informations
        info_frame = tk.Frame(parent, bg='#333333', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Informations sur les longueurs des vérins
        self.info_label = tk.Label(info_frame, text="Leg Lengths: Calculating...", 
                                  font=('Arial', 10), fg='white', bg='#333333')
        self.info_label.pack(pady=5)
        
        # Position et rotation actuelles
        self.pos_label = tk.Label(info_frame, text="Position: [0.000, 0.000, 0.000]", 
                                 font=('Arial', 10), fg='white', bg='#333333')
        self.pos_label.pack()
        
        self.rot_label = tk.Label(info_frame, text="Rotation: [0.000, 0.000, 0.000]", 
                                 font=('Arial', 10), fg='white', bg='#333333')
        self.rot_label.pack()
        
        # Frame pour les boutons
        button_frame = tk.Frame(parent, bg='#2E86AB')
        button_frame.pack(fill=tk.X)
        
        # Boutons de contrôle
        tk.Button(button_frame, text="🏠 HOME", font=('Arial', 12, 'bold'),
                 bg='#4CAF50', fg='white', command=self.go_home).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🚨 EMERGENCY STOP", font=('Arial', 12, 'bold'),
                 bg='#F44336', fg='white', command=self.emergency_stop).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🎬 START DEMO", font=('Arial', 12, 'bold'),
                 bg='#FF9800', fg='white', command=self.start_demo).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="⏹️ STOP DEMO", font=('Arial', 12, 'bold'),
                 bg='#9E9E9E', fg='white', command=self.stop_demo).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🎥 RECORD VIDEO", font=('Arial', 12, 'bold'),
                 bg='#9C27B0', fg='white', command=self.record_video).pack(side=tk.LEFT, padx=5)
        
        # Checkbox pour les caméras (décoratif, comme dans l'image)
        camera_frame = tk.Frame(button_frame, bg='#2E86AB')
        camera_frame.pack(side=tk.RIGHT)
        
        self.camera1_var = tk.BooleanVar(value=True)
        self.camera2_var = tk.BooleanVar(value=False)
        
        tk.Checkbutton(camera_frame, text="📹 Camera 1", variable=self.camera1_var,
                       fg='white', bg='#2E86AB', selectcolor='#2E86AB').pack()
        tk.Checkbutton(camera_frame, text="📹 Camera 2", variable=self.camera2_var,
                       fg='white', bg='#2E86AB', selectcolor='#2E86AB').pack()
        
    def update_position(self, axis, value):
        """Met à jour la position sur un axe"""
        self.current_position[axis] = float(value)
        self.update_leg_lengths()
        
    def update_rotation(self, axis, value):
        """Met à jour la rotation sur un axe"""
        self.current_rotation[axis] = float(value)
        self.update_leg_lengths()
        
    def update_leg_lengths(self):
        """Calcule et affiche les longueurs des vérins"""
        try:
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation)
            
            leg_lengths = self.clf_ik.solve(translation, rotation)
            
            # Mise à jour des labels
            self.info_label.config(text=f"Leg Lengths: {', '.join([f'{l:.3f}' for l in leg_lengths])}")
            self.pos_label.config(text=f"Position: [{', '.join([f'{p:.3f}' for p in self.current_position])}]")
            self.rot_label.config(text=f"Rotation: [{', '.join([f'{r:.3f}' for r in self.current_rotation])}]°")
            
        except Exception as e:
            self.info_label.config(text=f"Error: {str(e)}")
            
    def toggle_auto(self, axis, enabled):
        """Active/désactive le mode automatique pour un axe"""
        self.auto_mode[axis] = enabled
        if enabled:
            print(f"Auto mode enabled for axis {axis}")
        else:
            print(f"Auto mode disabled for axis {axis}")
            
    def go_home(self):
        """Retour à la position d'origine"""
        for i in range(6):
            if hasattr(self, f'slider_{i}'):
                getattr(self, f'slider_{i}').set(0)
        
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.update_leg_lengths()
        print("🏠 Platform returned to HOME position")
        
    def emergency_stop(self):
        """Arrêt d'urgence"""
        self.stop_demo()
        messagebox.showwarning("EMERGENCY STOP", "🚨 Emergency stop activated!\nAll movements stopped.")
        print("🚨 EMERGENCY STOP activated")
        
    def start_demo(self):
        """Démarre une animation de démonstration"""
        if not self.animation_running:
            self.animation_running = True
            self.animation_thread = threading.Thread(target=self.demo_animation)
            self.animation_thread.daemon = True
            self.animation_thread.start()
            print("🎬 Demo animation started")
        
    def stop_demo(self):
        """Arrête l'animation de démonstration"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
        print("⏹️ Demo animation stopped")
        
    def demo_animation(self):
        """Animation de démonstration automatique"""
        demo_sequence = [
            # (heave, sway, surge, yaw, roll, pitch, duration)
            (0.05, 0, 0, 0, 0, 0, 2),      # Montée
            (0.05, 0, 0, 0, 15, 0, 2),     # + Roll
            (0.05, 0, 0, 0, 15, 15, 2),    # + Pitch
            (0.05, 0, 0, 20, 15, 15, 2),   # + Yaw
            (0.05, 0.03, 0, 20, 15, 15, 2), # + Sway
            (0.05, 0.03, 0.03, 20, 15, 15, 2), # + Surge
            (0, 0, 0, 0, 0, 0, 3),         # Retour home
        ]
        
        for heave, sway, surge, yaw, roll, pitch, duration in demo_sequence:
            if not self.animation_running:
                break
                
            # Animation progressive vers la position cible
            start_pos = self.current_position.copy()
            start_rot = self.current_rotation.copy()
            target_pos = [surge, sway, heave]
            target_rot = [roll, pitch, yaw]
            
            steps = int(duration * 10)  # 10 steps par seconde
            for step in range(steps):
                if not self.animation_running:
                    break
                    
                # Interpolation linéaire
                t = step / steps
                
                new_pos = [start_pos[i] + t * (target_pos[i] - start_pos[i]) for i in range(3)]
                new_rot = [start_rot[i] + t * (target_rot[i] - start_rot[i]) for i in range(3)]
                
                # Mise à jour des sliders et positions
                self.root.after(0, lambda p=new_pos, r=new_rot: self.update_demo_position(p, r))
                
                time.sleep(0.1)
        
        self.animation_running = False
        
    def update_demo_position(self, position, rotation):
        """Met à jour la position pendant la démo"""
        self.current_position = position
        self.current_rotation = rotation
        
        # Mise à jour des sliders
        if hasattr(self, 'slider_0'): self.slider_0.set(position[0])  # Surge
        if hasattr(self, 'slider_1'): self.slider_1.set(position[1])  # Sway
        if hasattr(self, 'slider_2'): self.slider_2.set(position[2])  # Heave
        if hasattr(self, 'slider_3'): self.slider_3.set(rotation[2])  # Yaw
        if hasattr(self, 'slider_4'): self.slider_4.set(rotation[0])  # Roll
        if hasattr(self, 'slider_5'): self.slider_5.set(rotation[1])  # Pitch
        
        self.update_leg_lengths()
        
    def record_video(self):
        """Enregistre une vidéo de la simulation actuelle"""
        try:
            # Simulation avec enregistrement
            clf = sp(self.path, self.joint_indices, self.actuator_indices, self.design_variables)
            
            # Créer une trajectoire basée sur la position actuelle
            data = [[np.array(self.current_position), np.array(self.current_rotation), 3]]
            
            clf.start_simmulation(data, simulation=True, flag=False, use_gui=False)
            messagebox.showinfo("Video Recorded", "🎥 Video saved as 'simulation.mp4'")
            print("🎥 Video recorded successfully")
            
        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to record video:\n{str(e)}")
            print(f"❌ Video recording failed: {e}")

def main():
    """Fonction principale"""
    print("🚀 Starting Stewart Platform GUI...")
    
    root = tk.Tk()
    app = StewartPlatformGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 GUI closed by user")
    except Exception as e:
        print(f"❌ Error in GUI: {e}")

if __name__ == "__main__":
    main()
