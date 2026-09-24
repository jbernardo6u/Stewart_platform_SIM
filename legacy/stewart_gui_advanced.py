#!/usr/bin/env python3
"""
Interface GUI Avancée pour Stewart Platform
Style similaire à l'image avec rendu 3D en temps réel
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D

from src.core.platform import StewartPlatform as sp
from src.core.kinematics import InverseKinematics

class StewartPlatformAdvancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Stewart Platform - Advanced Control Interface")
        self.root.geometry("1400x900")
        self.root.configure(bg='#4A90C2')  # Bleu comme dans l'image
        
        # Configuration
        self.path = "simulation/urdf/Stewart.urdf"
        self.joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
        self.actuator_indices = [9, 2, 31, 45, 38, 24]
        self.design_variables = [0.2, 0.2, 12, 12]
        
        # État
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.current_leg_lengths = np.zeros(6)
        
        # Cinématique
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.clf_ik = InverseKinematics(r_P, r_B, gama_P, gama_B)
        
        # Animation
        self.animation_running = False
        
        self.setup_gui()
        self.setup_3d_plot()
        self.update_platform()
        
    def setup_gui(self):
        """Configure l'interface principale"""
        
        # Frame principal horizontal
        main_frame = tk.Frame(self.root, bg='#4A90C2')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Colonne gauche - Contrôles
        left_frame = tk.Frame(main_frame, bg='#4A90C2', width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Colonne droite - Visualisation 3D
        right_frame = tk.Frame(main_frame, bg='#2C3E50')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_controls(left_frame)
        self.setup_3d_visualization(right_frame)
        
    def setup_controls(self, parent):
        """Configure les contrôles à gauche"""
        
        # Titre
        title = tk.Label(parent, text="STEWART PLATFORM\nCONTROL", 
                        font=('Arial', 16, 'bold'), fg='white', bg='#4A90C2',
                        justify=tk.CENTER)
        title.pack(pady=(0, 20))
        
        # Contrôles de translation
        self.setup_translation_group(parent)
        
        # Séparateur
        separator1 = tk.Frame(parent, height=2, bg='white')
        separator1.pack(fill=tk.X, pady=20)
        
        # Contrôles de rotation
        self.setup_rotation_group(parent)
        
        # Séparateur
        separator2 = tk.Frame(parent, height=2, bg='white')
        separator2.pack(fill=tk.X, pady=20)
        
        # Boutons de contrôle
        self.setup_control_buttons(parent)
        
        # Informations
        self.setup_info_panel(parent)
        
    def setup_translation_group(self, parent):
        """Groupe des contrôles de translation"""
        
        # HEAVE (Z - Vertical)
        heave_frame = self.create_slider_frame(parent, "HEAVE", -0.1, 0.1, 
                                              lambda v: self.update_position(2, v))
        self.heave_slider = heave_frame['slider']
        self.heave_auto = heave_frame['auto_var']
        
        # SWAY (Y - Latéral)
        sway_frame = self.create_slider_frame(parent, "SWAY", -0.05, 0.05,
                                             lambda v: self.update_position(1, v))
        self.sway_slider = sway_frame['slider']
        self.sway_auto = sway_frame['auto_var']
        
        # SURGE (X - Avant/Arrière)
        surge_frame = self.create_slider_frame(parent, "SURGE", -0.05, 0.05,
                                              lambda v: self.update_position(0, v))
        self.surge_slider = surge_frame['slider']
        self.surge_auto = surge_frame['auto_var']
        
    def setup_rotation_group(self, parent):
        """Groupe des contrôles de rotation"""
        
        # YAW
        yaw_frame = self.create_slider_frame(parent, "YAW", -45, 45,
                                            lambda v: self.update_rotation(2, v))
        self.yaw_slider = yaw_frame['slider']
        self.yaw_auto = yaw_frame['auto_var']
        
        # ROLL
        roll_frame = self.create_slider_frame(parent, "ROLL", -30, 30,
                                             lambda v: self.update_rotation(0, v))
        self.roll_slider = roll_frame['slider']
        self.roll_auto = roll_frame['auto_var']
        
        # PITCH
        pitch_frame = self.create_slider_frame(parent, "PITCH", -30, 30,
                                              lambda v: self.update_rotation(1, v), auto_enabled=True)
        self.pitch_slider = pitch_frame['slider']
        self.pitch_auto = pitch_frame['auto_var']
        
    def create_slider_frame(self, parent, label, min_val, max_val, callback, auto_enabled=False):
        """Crée un frame avec slider et checkbox AUTO"""
        
        # Frame principal
        frame = tk.Frame(parent, bg='#4A90C2')
        frame.pack(fill=tk.X, pady=8)
        
        # Label
        label_widget = tk.Label(frame, text=label, font=('Arial', 11, 'bold'),
                               fg='white', bg='#4A90C2')
        label_widget.pack(anchor=tk.W)
        
        # Frame pour slider et auto
        control_frame = tk.Frame(frame, bg='#4A90C2')
        control_frame.pack(fill=tk.X, pady=2)
        
        # Slider avec style personnalisé
        slider = tk.Scale(control_frame, from_=min_val, to=max_val, resolution=0.001,
                         orient=tk.HORIZONTAL, length=250, width=20,
                         bg='white', fg='black', highlightbackground='#4A90C2',
                         troughcolor='#E0E0E0', activebackground='#2196F3',
                         command=callback)
        slider.pack(side=tk.LEFT, padx=(0, 10))
        slider.set(0)
        
        # Checkbox AUTO
        auto_var = tk.BooleanVar(value=auto_enabled)
        auto_check = tk.Checkbutton(control_frame, text="AUTO", variable=auto_var,
                                   font=('Arial', 9, 'bold'), fg='white', bg='#4A90C2',
                                   selectcolor='#2196F3', activebackground='#4A90C2',
                                   activeforeground='white')
        auto_check.pack(side=tk.RIGHT)
        
        return {'slider': slider, 'auto_var': auto_var, 'frame': frame}
        
    def setup_control_buttons(self, parent):
        """Boutons de contrôle principal"""
        
        button_frame = tk.Frame(parent, bg='#4A90C2')
        button_frame.pack(fill=tk.X, pady=10)
        
        # Style des boutons
        button_style = {
            'font': ('Arial', 10, 'bold'),
            'width': 12,
            'height': 2
        }
        
        # HOME
        tk.Button(button_frame, text="🏠 HOME", bg='#4CAF50', fg='white',
                 command=self.go_home, **button_style).pack(pady=2, fill=tk.X)
        
        # EMERGENCY
        tk.Button(button_frame, text="🚨 STOP", bg='#F44336', fg='white',
                 command=self.emergency_stop, **button_style).pack(pady=2, fill=tk.X)
        
        # DEMO
        tk.Button(button_frame, text="🎬 DEMO", bg='#FF9800', fg='white',
                 command=self.toggle_demo, **button_style).pack(pady=2, fill=tk.X)
        
        # RECORD
        tk.Button(button_frame, text="🎥 RECORD", bg='#9C27B0', fg='white',
                 command=self.record_video, **button_style).pack(pady=2, fill=tk.X)
        
    def setup_info_panel(self, parent):
        """Panneau d'informations"""
        
        info_frame = tk.Frame(parent, bg='#2C3E50', relief=tk.SUNKEN, bd=2)
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Titre
        tk.Label(info_frame, text="SYSTEM STATUS", font=('Arial', 10, 'bold'),
                fg='white', bg='#2C3E50').pack(pady=5)
        
        # Labels d'information
        self.pos_info = tk.Label(info_frame, text="Position: [0.000, 0.000, 0.000]",
                                font=('Courier', 9), fg='#00FF00', bg='#2C3E50')
        self.pos_info.pack(pady=2)
        
        self.rot_info = tk.Label(info_frame, text="Rotation: [0.000, 0.000, 0.000]",
                                font=('Courier', 9), fg='#00FF00', bg='#2C3E50')
        self.rot_info.pack(pady=2)
        
        self.leg_info = tk.Label(info_frame, text="Legs: OK",
                                font=('Courier', 9), fg='#00FF00', bg='#2C3E50')
        self.leg_info.pack(pady=2)
        
        # Caméras (décoratif)
        camera_frame = tk.Frame(info_frame, bg='#2C3E50')
        camera_frame.pack(pady=5)
        
        self.cam1_var = tk.BooleanVar(value=True)
        self.cam2_var = tk.BooleanVar(value=False)
        
        tk.Checkbutton(camera_frame, text="📹 Camera 1", variable=self.cam1_var,
                      font=('Arial', 8), fg='white', bg='#2C3E50',
                      selectcolor='#4A90C2').pack()
        tk.Checkbutton(camera_frame, text="📹 Camera 2", variable=self.cam2_var,
                      font=('Arial', 8), fg='white', bg='#2C3E50',
                      selectcolor='#4A90C2').pack()
        
    def setup_3d_visualization(self, parent):
        """Configure la visualisation 3D à droite"""
        
        # Titre
        title = tk.Label(parent, text="3D VISUALIZATION", font=('Arial', 14, 'bold'),
                        fg='white', bg='#2C3E50')
        title.pack(pady=10)
        
        # Figure matplotlib
        self.fig = Figure(figsize=(8, 6), facecolor='#2C3E50')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#34495E')
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_3d_plot(self):
        """Configure le plot 3D initial"""
        
        self.ax.clear()
        self.ax.set_facecolor('#34495E')
        
        # Limites
        self.ax.set_xlim([-0.3, 0.3])
        self.ax.set_ylim([-0.3, 0.3])
        self.ax.set_zlim([0, 0.4])
        
        # Labels
        self.ax.set_xlabel('X (Surge)', color='white')
        self.ax.set_ylabel('Y (Sway)', color='white')
        self.ax.set_zlabel('Z (Heave)', color='white')
        
        # Couleurs des axes
        self.ax.tick_params(colors='white')
        
        # Base de la plateforme (hexagone)
        base_angles = np.linspace(0, 2*np.pi, 7)
        base_x = 0.2 * np.cos(base_angles)
        base_y = 0.2 * np.sin(base_angles)
        base_z = np.zeros_like(base_x)
        
        self.base_plot, = self.ax.plot(base_x, base_y, base_z, 'b-', linewidth=3, label='Base')
        
        # Plateforme mobile (hexagone)
        self.platform_plot, = self.ax.plot([], [], [], 'r-', linewidth=3, label='Platform')
        
        # Vérins (6 lignes)
        self.leg_plots = []
        for i in range(6):
            line, = self.ax.plot([], [], [], 'orange', linewidth=2)
            self.leg_plots.append(line)
        
        self.ax.legend()
        
        # Position initiale
        self.update_3d_plot()
        
    def update_3d_plot(self):
        """Met à jour le plot 3D"""
        
        try:
            # Position et orientation de la plateforme
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation) * np.pi / 180
            
            # Hexagone de la plateforme mobile
            platform_angles = np.linspace(0, 2*np.pi, 7)
            platform_radius = 0.15
            
            # Points de base de la plateforme (dans le repère local)
            local_x = platform_radius * np.cos(platform_angles)
            local_y = platform_radius * np.sin(platform_angles)
            local_z = np.zeros_like(local_x)
            
            # Matrice de rotation
            rx, ry, rz = rotation
            
            # Rotations autour des axes
            Rx = np.array([[1, 0, 0],
                          [0, np.cos(rx), -np.sin(rx)],
                          [0, np.sin(rx), np.cos(rx)]])
            
            Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                          [0, 1, 0],
                          [-np.sin(ry), 0, np.cos(ry)]])
            
            Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                          [np.sin(rz), np.cos(rz), 0],
                          [0, 0, 1]])
            
            R = Rz @ Ry @ Rx
            
            # Transformation des points
            platform_points = np.vstack([local_x, local_y, local_z])
            rotated_points = R @ platform_points
            
            # Translation
            final_x = rotated_points[0] + translation[0]
            final_y = rotated_points[1] + translation[1]
            final_z = rotated_points[2] + translation[2] + 0.25  # Hauteur de base
            
            # Mise à jour de la plateforme
            self.platform_plot.set_data(final_x, final_y)
            self.platform_plot.set_3d_properties(final_z)
            
            # Mise à jour des vérins
            base_angles = np.linspace(0, 2*np.pi, 6, endpoint=False)
            for i, angle in enumerate(base_angles):
                # Point de base
                base_x = 0.18 * np.cos(angle)
                base_y = 0.18 * np.sin(angle)
                base_z = 0
                
                # Point de plateforme correspondant
                platform_x = final_x[i]
                platform_y = final_y[i]
                platform_z = final_z[i]
                
                # Ligne du vérin
                self.leg_plots[i].set_data([base_x, platform_x], [base_y, platform_y])
                self.leg_plots[i].set_3d_properties([base_z, platform_z])
            
            # Redessiner
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erreur 3D plot: {e}")
    
    def update_position(self, axis, value):
        """Met à jour la position"""
        self.current_position[axis] = float(value)
        self.update_platform()
        
    def update_rotation(self, axis, value):
        """Met à jour la rotation"""
        self.current_rotation[axis] = float(value)
        self.update_platform()
        
    def update_platform(self):
        """Met à jour la plateforme complète"""
        try:
            # Calcul cinématique inverse
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation)
            
            self.current_leg_lengths = self.clf_ik.solve(translation, rotation)
            
            # Mise à jour des informations
            self.pos_info.config(text=f"Position: [{', '.join([f'{p:.3f}' for p in self.current_position])}]")
            self.rot_info.config(text=f"Rotation: [{', '.join([f'{r:.1f}' for r in self.current_rotation])}]°")
            self.leg_info.config(text=f"Legs: {', '.join([f'{l:.3f}' for l in self.current_leg_lengths])}")
            
            # Mise à jour du plot 3D
            self.update_3d_plot()
            
        except Exception as e:
            self.leg_info.config(text=f"Error: {str(e)}", fg='red')
            
    def go_home(self):
        """Retour position d'origine"""
        self.heave_slider.set(0)
        self.sway_slider.set(0)
        self.surge_slider.set(0)
        self.yaw_slider.set(0)
        self.roll_slider.set(0)
        self.pitch_slider.set(0)
        
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.update_platform()
        
    def emergency_stop(self):
        """Arrêt d'urgence"""
        self.animation_running = False
        messagebox.showwarning("EMERGENCY STOP", "🚨 All movements stopped!")
        
    def toggle_demo(self):
        """Lance/arrête la démo"""
        if not self.animation_running:
            self.start_demo_animation()
        else:
            self.animation_running = False
            
    def start_demo_animation(self):
        """Animation de démonstration"""
        self.animation_running = True
        
        def animate():
            t = 0
            while self.animation_running:
                # Mouvements sinusoïdaux
                heave = 0.05 * np.sin(t * 0.5)
                roll = 20 * np.sin(t * 0.3)
                pitch = 15 * np.cos(t * 0.4)
                yaw = 30 * np.sin(t * 0.2)
                
                # Mise à jour des sliders
                self.root.after(0, lambda: self.heave_slider.set(heave))
                self.root.after(0, lambda: self.roll_slider.set(roll))
                self.root.after(0, lambda: self.pitch_slider.set(pitch))
                self.root.after(0, lambda: self.yaw_slider.set(yaw))
                
                t += 0.1
                time.sleep(0.05)
                
        thread = threading.Thread(target=animate)
        thread.daemon = True
        thread.start()
        
    def record_video(self):
        """Enregistre une vidéo"""
        try:
            clf = sp(self.path, self.joint_indices, self.actuator_indices, self.design_variables)
            data = [[np.array(self.current_position), np.array(self.current_rotation), 2]]
            clf.start_simmulation(data, simulation=True, flag=False, use_gui=False)
            messagebox.showinfo("Success", "🎥 Video saved as 'simulation.mp4'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record: {str(e)}")

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = StewartPlatformAdvancedGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
