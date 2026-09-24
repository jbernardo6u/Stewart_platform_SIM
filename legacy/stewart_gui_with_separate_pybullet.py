#!/usr/bin/env python3
"""
Interface GUI avec fenêtre PyBullet séparée
Lance automatiquement une simulation PyBullet en parallèle du GUI
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import threading
import time
import subprocess
import sys
import os
from inv_kinematics import inv_kinematics as ik

class StewartGUIWithSeparatePyBullet:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Stewart Platform - GUI Controller")
        self.root.geometry("700x800")
        self.root.configure(bg='#4A90C2')
        
        # Configuration
        self.design_variables = [0.2, 0.2, 12, 12]
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.clf_ik = ik(r_P, r_B, gama_P, gama_B)
        
        # État
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.pybullet_process = None
        self.simulation_running = False
        
        self.setup_gui()
        self.update_info()
        
    def setup_gui(self):
        """Configure l'interface"""
        
        # Titre
        title = tk.Label(self.root, text="🤖 STEWART PLATFORM\nCONTROLLER & SIMULATOR", 
                        font=('Arial', 16, 'bold'), fg='white', bg='#4A90C2', justify=tk.CENTER)
        title.pack(pady=15)
        
        # Instructions
        instructions = tk.Label(self.root, 
                               text="Use sliders to control the platform\nPyBullet window will show real-time simulation", 
                               font=('Arial', 10), fg='white', bg='#4A90C2', justify=tk.CENTER)
        instructions.pack(pady=5)
        
        # Frame pour les contrôles
        controls_frame = tk.Frame(self.root, bg='#4A90C2')
        controls_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.setup_platform_controls(controls_frame)
        self.setup_simulation_controls(controls_frame)
        self.setup_info_display(controls_frame)
        
    def setup_platform_controls(self, parent):
        """Configure les contrôles de la plateforme"""
        
        # Translation controls
        trans_frame = tk.LabelFrame(parent, text="TRANSLATION CONTROLS", 
                                   font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        trans_frame.pack(fill=tk.X, pady=10)
        
        self.heave_slider = self.create_slider(trans_frame, "HEAVE (Z)", -0.1, 0.1, 0,
                                              lambda v: self.update_position(2, v))
        self.sway_slider = self.create_slider(trans_frame, "SWAY (Y)", -0.05, 0.05, 1,
                                             lambda v: self.update_position(1, v))
        self.surge_slider = self.create_slider(trans_frame, "SURGE (X)", -0.05, 0.05, 2,
                                              lambda v: self.update_position(0, v))
        
        # Rotation controls
        rot_frame = tk.LabelFrame(parent, text="ROTATION CONTROLS", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        rot_frame.pack(fill=tk.X, pady=10)
        
        self.yaw_slider = self.create_slider(rot_frame, "YAW", -45, 45, 0,
                                            lambda v: self.update_rotation(2, v))
        self.roll_slider = self.create_slider(rot_frame, "ROLL", -30, 30, 1,
                                             lambda v: self.update_rotation(0, v))
        self.pitch_slider = self.create_slider(rot_frame, "PITCH", -30, 30, 2,
                                              lambda v: self.update_rotation(1, v))
        
    def create_slider(self, parent, label, min_val, max_val, row, callback):
        """Crée un slider avec label"""
        
        tk.Label(parent, text=label, font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=row, column=0, sticky='w', padx=10, pady=5)
        
        slider = tk.Scale(parent, from_=min_val, to=max_val, resolution=0.001,
                         orient=tk.HORIZONTAL, length=300, bg='white',
                         command=callback)
        slider.grid(row=row, column=1, padx=10, pady=5)
        slider.set(0)
        
        return slider
        
    def setup_simulation_controls(self, parent):
        """Configure les contrôles de simulation"""
        
        sim_frame = tk.LabelFrame(parent, text="SIMULATION CONTROLS", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        sim_frame.pack(fill=tk.X, pady=10)
        
        button_frame = tk.Frame(sim_frame, bg='#4A90C2')
        button_frame.pack(pady=10)
        
        # Boutons de contrôle
        tk.Button(button_frame, text="🚀 START PyBullet", font=('Arial', 11, 'bold'),
                 bg='#4CAF50', fg='white', command=self.start_pybullet_simulation,
                 width=15).grid(row=0, column=0, padx=5, pady=3)
        
        tk.Button(button_frame, text="⏹️ STOP PyBullet", font=('Arial', 11, 'bold'),
                 bg='#F44336', fg='white', command=self.stop_pybullet_simulation,
                 width=15).grid(row=0, column=1, padx=5, pady=3)
        
        tk.Button(button_frame, text="🏠 HOME", font=('Arial', 11, 'bold'),
                 bg='#FF9800', fg='white', command=self.go_home,
                 width=15).grid(row=1, column=0, padx=5, pady=3)
        
        tk.Button(button_frame, text="🎬 DEMO", font=('Arial', 11, 'bold'),
                 bg='#9C27B0', fg='white', command=self.start_demo,
                 width=15).grid(row=1, column=1, padx=5, pady=3)
        
        # Status
        self.status_label = tk.Label(sim_frame, text="📱 PyBullet: Stopped", 
                                    font=('Arial', 10, 'bold'), fg='yellow', bg='#4A90C2')
        self.status_label.pack(pady=5)
        
    def setup_info_display(self, parent):
        """Configure l'affichage des informations"""
        
        info_frame = tk.LabelFrame(parent, text="PLATFORM STATUS", 
                                  font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.info_text = tk.Text(info_frame, height=12, bg='#2C3E50', fg='#00FF00',
                                font=('Courier', 9), wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def start_pybullet_simulation(self):
        """Démarre la simulation PyBullet dans une fenêtre séparée"""
        if not self.simulation_running:
            try:
                # Créer un script temporaire pour la simulation PyBullet
                self.create_pybullet_script()
                
                # Lancer PyBullet dans un processus séparé
                self.pybullet_process = subprocess.Popen([
                    sys.executable, "temp_pybullet_sim.py"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                self.simulation_running = True
                self.status_label.config(text="📱 PyBullet: Running", fg='lime')
                self.log_message("✅ PyBullet simulation started in separate window")
                
                # Démarrer la surveillance du processus
                self.monitor_pybullet_process()
                
            except Exception as e:
                self.log_message(f"❌ Failed to start PyBullet: {str(e)}")
        else:
            self.log_message("⚠️ PyBullet simulation already running")
            
    def create_pybullet_script(self):
        """Crée un script temporaire pour la simulation PyBullet"""
        
        script_content = f'''#!/usr/bin/env python3
import pybullet as p
import time
import pybullet_data
import numpy as np
import os

# Configuration
path = "simulation/urdf/Stewart.urdf"
joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
actuator_indices = [9, 2, 31, 45, 38, 24]

# Variables d'environnement pour stabiliser PyBullet
os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'

try:
    # Connexion PyBullet avec GUI
    physicsClient = p.connect(p.GUI, options="--width=800 --height=600")
    print("Connected to PyBullet GUI")
    
    # Configuration caméra
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)
    p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1)
    
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    planeId = p.loadURDF("plane.urdf")
    
    # Charger la plateforme Stewart
    cubeStartPos = [0, 0, 0]
    cubeStartOrientation = p.getQuaternionFromEuler([0, 0, 0])
    robotId = p.loadURDF(path, cubeStartPos, cubeStartOrientation,
                        flags=p.URDF_USE_INERTIA_FROM_FILE, useFixedBase=1)
    
    # Configuration caméra
    camera_target_position = [0, 0, 0]
    camera_distance = 1.5
    camera_yaw = 50
    camera_pitch = -35
    p.resetDebugVisualizerCamera(cameraDistance=camera_distance, 
                                cameraYaw=camera_yaw,
                                cameraPitch=camera_pitch,
                                cameraTargetPosition=camera_target_position)
    
    # Contraintes
    for parent_joint, child_joint in joint_indices:
        constraint_id = p.createConstraint(robotId, parent_joint, robotId, child_joint, 
                                         p.JOINT_FIXED, [0,0,0.1], [0,0,0], [0,0,0])
        p.changeConstraint(constraint_id, maxForce=1e20)
    
    # Désactiver les moteurs
    n = p.getNumJoints(robotId)
    for i in range(n):
        p.setJointMotorControl2(robotId, i, controlMode=p.VELOCITY_CONTROL, force=0)
    
    print("Stewart Platform loaded successfully")
    print("Simulation ready - control from GUI interface")
    
    # Boucle de simulation
    while True:
        p.stepSimulation()
        time.sleep(1./240.)
        
except KeyboardInterrupt:
    print("Simulation stopped by user")
except Exception as e:
    print(f"Simulation error: {{e}}")
finally:
    try:
        p.disconnect()
    except:
        pass
'''
        
        with open("temp_pybullet_sim.py", "w") as f:
            f.write(script_content)
            
    def monitor_pybullet_process(self):
        """Surveille le processus PyBullet"""
        def monitor():
            if self.pybullet_process:
                self.pybullet_process.wait()  # Attendre la fin du processus
                self.simulation_running = False
                self.root.after(0, lambda: self.status_label.config(
                    text="📱 PyBullet: Stopped", fg='yellow'))
                self.root.after(0, lambda: self.log_message("📱 PyBullet simulation ended"))
                
        thread = threading.Thread(target=monitor)
        thread.daemon = True
        thread.start()
        
    def stop_pybullet_simulation(self):
        """Arrête la simulation PyBullet"""
        if self.simulation_running and self.pybullet_process:
            try:
                self.pybullet_process.terminate()
                self.pybullet_process.wait(timeout=5)
                self.simulation_running = False
                self.status_label.config(text="📱 PyBullet: Stopped", fg='yellow')
                self.log_message("⏹️ PyBullet simulation stopped")
            except Exception as e:
                self.log_message(f"❌ Error stopping PyBullet: {str(e)}")
        else:
            self.log_message("⚠️ No PyBullet simulation running")
            
    def update_position(self, axis, value):
        """Met à jour la position"""
        self.current_position[axis] = float(value)
        self.update_info()
        
    def update_rotation(self, axis, value):
        """Met à jour la rotation"""
        self.current_rotation[axis] = float(value)
        self.update_info()
        
    def update_info(self):
        """Met à jour les informations"""
        try:
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation)
            leg_lengths = self.clf_ik.solve(translation, rotation)
            
            info = f"""STEWART PLATFORM STATUS
{'='*40}

POSITION (m):    X={self.current_position[0]:7.3f}  Y={self.current_position[1]:7.3f}  Z={self.current_position[2]:7.3f}
ROTATION (°):  Roll={self.current_rotation[0]:6.1f}  Pitch={self.current_rotation[1]:6.1f}  Yaw={self.current_rotation[2]:6.1f}

ACTUATOR LENGTHS (meters):
  Leg 1: {leg_lengths[0]:.3f}    Leg 2: {leg_lengths[1]:.3f}    Leg 3: {leg_lengths[2]:.3f}
  Leg 4: {leg_lengths[3]:.3f}    Leg 5: {leg_lengths[4]:.3f}    Leg 6: {leg_lengths[5]:.3f}

STATISTICS:
  Min: {min(leg_lengths):.3f} m    Max: {max(leg_lengths):.3f} m    Range: {max(leg_lengths)-min(leg_lengths):.3f} m

SIMULATION: {'🟢 PyBullet Running' if self.simulation_running else '🔴 PyBullet Stopped'}
"""
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info)
            
        except Exception as e:
            self.log_message(f"❌ Update error: {str(e)}")
            
    def log_message(self, message):
        """Ajoute un message au log"""
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        
        # Ajouter à la fin de l'info
        current_text = self.info_text.get(1.0, tk.END)
        
        # Garder seulement les logs récents (dernières 5 lignes)
        lines = current_text.split('\n')
        if len(lines) > 25:  # Limiter à 25 lignes
            lines = lines[-20:]  # Garder les 20 dernières
            
        new_text = '\n'.join(lines) + f"\n{log_line}"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, new_text)
        self.info_text.see(tk.END)
        
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
        self.update_info()
        self.log_message("🏠 Platform returned to HOME")
        
    def start_demo(self):
        """Démarre une démonstration"""
        def demo_animation():
            self.log_message("🎬 Starting demo animation")
            
            demo_moves = [
                # (heave, sway, surge, yaw, roll, pitch, duration)
                (0.05, 0, 0, 0, 0, 0, 1),     # Montée
                (0.05, 0, 0, 0, 15, 0, 1),    # + Roll
                (0.05, 0, 0, 0, 15, 15, 1),   # + Pitch
                (0.05, 0, 0, 20, 15, 15, 1),  # + Yaw
                (0, 0, 0, 0, 0, 0, 2),        # Retour home
            ]
            
            for heave, sway, surge, yaw, roll, pitch, duration in demo_moves:
                # Animation progressive
                steps = int(duration * 10)
                for step in range(steps):
                    t = step / steps
                    
                    # Interpolation
                    new_heave = self.current_position[2] + t * (heave - self.current_position[2])
                    new_sway = self.current_position[1] + t * (sway - self.current_position[1])
                    new_surge = self.current_position[0] + t * (surge - self.current_position[0])
                    new_yaw = self.current_rotation[2] + t * (yaw - self.current_rotation[2])
                    new_roll = self.current_rotation[0] + t * (roll - self.current_rotation[0])
                    new_pitch = self.current_rotation[1] + t * (pitch - self.current_rotation[1])
                    
                    # Mise à jour des sliders
                    self.root.after(0, lambda h=new_heave: self.heave_slider.set(h))
                    self.root.after(0, lambda s=new_sway: self.sway_slider.set(s))
                    self.root.after(0, lambda s=new_surge: self.surge_slider.set(s))
                    self.root.after(0, lambda y=new_yaw: self.yaw_slider.set(y))
                    self.root.after(0, lambda r=new_roll: self.roll_slider.set(r))
                    self.root.after(0, lambda p=new_pitch: self.pitch_slider.set(p))
                    
                    time.sleep(0.1)
                    
            self.root.after(0, lambda: self.log_message("🎬 Demo completed"))
            
        thread = threading.Thread(target=demo_animation)
        thread.daemon = True
        thread.start()
        
    def on_closing(self):
        """Gestion de la fermeture"""
        self.stop_pybullet_simulation()
        
        # Nettoyer les fichiers temporaires
        try:
            os.remove("temp_pybullet_sim.py")
        except:
            pass
            
        self.root.destroy()

def main():
    """Fonction principale"""
    print("🚀 Starting Stewart Platform GUI with separate PyBullet window...")
    
    try:
        root = tk.Tk()
        app = StewartGUIWithSeparatePyBullet(root)
        
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("✅ GUI started successfully")
        print("💡 Click 'START PyBullet' to open simulation window")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")

if __name__ == "__main__":
    main()
