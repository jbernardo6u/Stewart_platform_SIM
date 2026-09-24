#!/usr/bin/env python3
"""
Interface GUI simple et fiable pour Stewart Platform
Version minimaliste pour test initial
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from src.core.kinematics import InverseKinematics

class SimpleStewartGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Stewart Platform Control")
        self.root.geometry("800x600")
        self.root.configure(bg='#4A90C2')
        
        # Configuration
        self.design_variables = [0.2, 0.2, 12, 12]
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.clf_ik = InverseKinematics(r_P, r_B, gama_P, gama_B)
        
        # État
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        
        self.setup_gui()
        self.update_info()
        
    def setup_gui(self):
        """Configure l'interface"""
        
        # Titre
        title = tk.Label(self.root, text="🤖 STEWART PLATFORM CONTROL", 
                        font=('Arial', 18, 'bold'), fg='white', bg='#4A90C2')
        title.pack(pady=20)
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#4A90C2')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Contrôles de translation
        trans_frame = tk.LabelFrame(main_frame, text="TRANSLATION", 
                                   font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        trans_frame.pack(fill=tk.X, pady=10)
        
        # HEAVE (Z)
        tk.Label(trans_frame, text="HEAVE (Z)", font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.heave_scale = tk.Scale(trans_frame, from_=-0.1, to=0.1, resolution=0.001,
                                   orient=tk.HORIZONTAL, length=300, bg='white',
                                   command=lambda v: self.update_position(2, v))
        self.heave_scale.grid(row=0, column=1, padx=5, pady=5)
        
        # SWAY (Y)
        tk.Label(trans_frame, text="SWAY (Y)", font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.sway_scale = tk.Scale(trans_frame, from_=-0.05, to=0.05, resolution=0.001,
                                  orient=tk.HORIZONTAL, length=300, bg='white',
                                  command=lambda v: self.update_position(1, v))
        self.sway_scale.grid(row=1, column=1, padx=5, pady=5)
        
        # SURGE (X)
        tk.Label(trans_frame, text="SURGE (X)", font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.surge_scale = tk.Scale(trans_frame, from_=-0.05, to=0.05, resolution=0.001,
                                   orient=tk.HORIZONTAL, length=300, bg='white',
                                   command=lambda v: self.update_position(0, v))
        self.surge_scale.grid(row=2, column=1, padx=5, pady=5)
        
        # Contrôles de rotation
        rot_frame = tk.LabelFrame(main_frame, text="ROTATION", 
                                 font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        rot_frame.pack(fill=tk.X, pady=10)
        
        # YAW
        tk.Label(rot_frame, text="YAW", font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.yaw_scale = tk.Scale(rot_frame, from_=-45, to=45, resolution=0.1,
                                 orient=tk.HORIZONTAL, length=300, bg='white',
                                 command=lambda v: self.update_rotation(2, v))
        self.yaw_scale.grid(row=0, column=1, padx=5, pady=5)
        
        # ROLL
        tk.Label(rot_frame, text="ROLL", font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.roll_scale = tk.Scale(rot_frame, from_=-30, to=30, resolution=0.1,
                                  orient=tk.HORIZONTAL, length=300, bg='white',
                                  command=lambda v: self.update_rotation(0, v))
        self.roll_scale.grid(row=1, column=1, padx=5, pady=5)
        
        # PITCH
        tk.Label(rot_frame, text="PITCH", font=('Arial', 10, 'bold'),
                fg='white', bg='#4A90C2').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.pitch_scale = tk.Scale(rot_frame, from_=-30, to=30, resolution=0.1,
                                   orient=tk.HORIZONTAL, length=300, bg='white',
                                   command=lambda v: self.update_rotation(1, v))
        self.pitch_scale.grid(row=2, column=1, padx=5, pady=5)
        
        # Boutons
        button_frame = tk.Frame(main_frame, bg='#4A90C2')
        button_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(button_frame, text="🏠 HOME", font=('Arial', 12, 'bold'),
                 bg='#4CAF50', fg='white', command=self.go_home).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🚨 STOP", font=('Arial', 12, 'bold'),
                 bg='#F44336', fg='white', command=self.emergency_stop).pack(side=tk.LEFT, padx=5)
        
        # Informations
        info_frame = tk.LabelFrame(main_frame, text="SYSTEM INFO", 
                                  font=('Arial', 12, 'bold'), fg='white', bg='#4A90C2')
        info_frame.pack(fill=tk.X, pady=10)
        
        self.info_text = tk.Text(info_frame, height=8, width=80, bg='#2C3E50', fg='#00FF00',
                                font=('Courier', 10))
        self.info_text.pack(padx=5, pady=5)
        
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
            translation = np.array(self.current_position)
            rotation = np.array(self.current_rotation)
            
            leg_lengths = self.clf_ik.solve(translation, rotation)
            
            info = f"""STEWART PLATFORM STATUS
{'='*50}

POSITION (meters):
  X (Surge):  {self.current_position[0]:8.3f}
  Y (Sway):   {self.current_position[1]:8.3f}  
  Z (Heave):  {self.current_position[2]:8.3f}

ROTATION (degrees):
  Roll:       {self.current_rotation[0]:8.1f}°
  Pitch:      {self.current_rotation[1]:8.1f}°
  Yaw:        {self.current_rotation[2]:8.1f}°

LEG LENGTHS (meters):
  Leg 1:      {leg_lengths[0]:8.3f}
  Leg 2:      {leg_lengths[1]:8.3f}
  Leg 3:      {leg_lengths[2]:8.3f}
  Leg 4:      {leg_lengths[3]:8.3f}
  Leg 5:      {leg_lengths[4]:8.3f}
  Leg 6:      {leg_lengths[5]:8.3f}

Min Length:   {min(leg_lengths):8.3f}
Max Length:   {max(leg_lengths):8.3f}
Range:        {max(leg_lengths)-min(leg_lengths):8.3f}

STATUS: ✅ READY
"""
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info)
            
        except Exception as e:
            error_info = f"❌ ERROR: {str(e)}"
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, error_info)
            
    def go_home(self):
        """Retour position d'origine"""
        self.heave_scale.set(0)
        self.sway_scale.set(0)
        self.surge_scale.set(0)
        self.yaw_scale.set(0)
        self.roll_scale.set(0)
        self.pitch_scale.set(0)
        
        self.current_position = [0, 0, 0]
        self.current_rotation = [0, 0, 0]
        self.update_info()
        print("🏠 Platform returned to HOME")
        
    def emergency_stop(self):
        """Arrêt d'urgence"""
        print("🚨 EMERGENCY STOP activated")
        tk.messagebox.showwarning("EMERGENCY STOP", "🚨 All movements stopped!")

def main():
    """Fonction principale"""
    print("🚀 Starting Simple Stewart Platform GUI...")
    
    try:
        root = tk.Tk()
        app = SimpleStewartGUI(root)
        print("✅ GUI started successfully")
        root.mainloop()
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")

if __name__ == "__main__":
    main()
