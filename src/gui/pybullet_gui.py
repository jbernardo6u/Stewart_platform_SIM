#!/usr/bin/env python3
"""
Stewart Platform GUI with PyBullet simulation integration.
Provides real-time 3D visualization alongside control interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
import os
from typing import Optional, Dict, Any

from .base_gui import BaseStewartGUI
from ..simulation.pybullet_sim import PyBulletSimulator


class PyBulletStewartGUI(BaseStewartGUI):
    """
    GUI with integrated PyBullet simulation.
    Features:
    - Real-time 3D visualization
    - Physics simulation
    - Interactive controls
    - Simulation recording
    - Camera controls
    """
    
    def __init__(self, root: tk.Tk, config: Optional[Dict[str, Any]] = None):
        """Initialize the PyBullet GUI."""
        self.sliders = {}
        self.info_labels = {}
        self.simulator = None
        self.simulation_active = False
        self.continuous_update = False
        self.sim_thread = None
        
        super().__init__(root, config)
        
        # Initialize PyBullet simulation
        self.initialize_simulation()
    
    def create_interface(self):
        """Create the GUI interface with simulation controls."""
        self.root.title("🤖 Stewart Platform - PyBullet Simulation")
        self.root.geometry("1200x800")
        
        # Create main container
        main_container = tk.Frame(self.root, bg=self.colors['primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title_label = ttk.Label(main_container, 
                               text="🤖 STEWART PLATFORM - PYBULLET SIMULATION",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Control panels
        controls_container = tk.Frame(main_container, bg=self.colors['primary'])
        controls_container.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Translation controls
        self.create_translation_controls(controls_container)
        
        # Right side - Rotation controls
        self.create_rotation_controls(controls_container)
        
        # Bottom panels
        self.create_simulation_controls(main_container)
        self.create_info_panel(main_container)
        self.create_control_buttons(main_container)
    
    def create_translation_controls(self, parent):
        """Create translation control sliders."""
        trans_frame = self.create_control_frame(parent, "TRANSLATION")
        trans_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # X Position
        x_limits = self.position_limits['x']
        x_label, x_slider = self.create_slider(
            trans_frame, "X Position (mm)",
            x_limits[0], x_limits[1],
            command=self.on_position_change
        )
        x_label.pack(pady=(15, 5))
        x_slider.pack(pady=(0, 15))
        self.sliders['x'] = x_slider
        
        # Y Position
        y_limits = self.position_limits['y']
        y_label, y_slider = self.create_slider(
            trans_frame, "Y Position (mm)",
            y_limits[0], y_limits[1],
            command=self.on_position_change
        )
        y_label.pack(pady=(10, 5))
        y_slider.pack(pady=(0, 15))
        self.sliders['y'] = y_slider
        
        # Z Position (HEAVE)
        z_limits = self.position_limits['z']
        z_label, z_slider = self.create_slider(
            trans_frame, "Z Position (HEAVE) (mm)",
            z_limits[0], z_limits[1],
            command=self.on_position_change
        )
        z_label.pack(pady=(10, 5))
        z_slider.pack(pady=(0, 15))
        self.sliders['z'] = z_slider
    
    def create_rotation_controls(self, parent):
        """Create rotation control sliders."""
        rot_frame = self.create_control_frame(parent, "ROTATION")
        rot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Roll
        roll_limits = self.rotation_limits['roll']
        roll_label, roll_slider = self.create_slider(
            rot_frame, "Roll (degrees)",
            roll_limits[0], roll_limits[1],
            resolution=0.5,
            command=self.on_rotation_change
        )
        roll_label.pack(pady=(15, 5))
        roll_slider.pack(pady=(0, 15))
        self.sliders['roll'] = roll_slider
        
        # Pitch
        pitch_limits = self.rotation_limits['pitch']
        pitch_label, pitch_slider = self.create_slider(
            rot_frame, "Pitch (degrees)",
            pitch_limits[0], pitch_limits[1],
            resolution=0.5,
            command=self.on_rotation_change
        )
        pitch_label.pack(pady=(10, 5))
        pitch_slider.pack(pady=(0, 15))
        self.sliders['pitch'] = pitch_slider
        
        # Yaw
        yaw_limits = self.rotation_limits['yaw']
        yaw_label, yaw_slider = self.create_slider(
            rot_frame, "Yaw (degrees)",
            yaw_limits[0], yaw_limits[1],
            resolution=0.5,
            command=self.on_rotation_change
        )
        yaw_label.pack(pady=(10, 5))
        yaw_slider.pack(pady=(0, 15))
        self.sliders['yaw'] = yaw_slider
    
    def create_simulation_controls(self, parent):
        """Create simulation control panel."""
        sim_frame = self.create_control_frame(parent, "SIMULATION CONTROLS")
        sim_frame.pack(fill=tk.X, pady=(20, 10))
        
        # Control buttons row
        controls_row = tk.Frame(sim_frame, bg=self.colors['primary'])
        controls_row.pack(pady=10)
        
        # Connect/Disconnect button
        self.sim_toggle_btn = tk.Button(
            controls_row, text="🔌 CONNECT SIM",
            font=('Arial', 11, 'bold'),
            bg=self.colors['secondary'], fg='white',
            command=self.toggle_simulation,
            relief='raised', borderwidth=2, width=18
        )
        self.sim_toggle_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Real-time update checkbox
        self.realtime_var = tk.BooleanVar(value=False)
        realtime_check = tk.Checkbutton(
            controls_row, text="Real-time Update",
            variable=self.realtime_var,
            font=('Arial', 10, 'bold'),
            fg=self.colors['text'], bg=self.colors['primary'],
            selectcolor=self.colors['secondary'],
            command=self.toggle_realtime_update
        )
        realtime_check.pack(side=tk.LEFT, padx=(10, 10))
        
        # Gravity checkbox
        self.gravity_var = tk.BooleanVar(value=True)
        gravity_check = tk.Checkbutton(
            controls_row, text="Enable Gravity",
            variable=self.gravity_var,
            font=('Arial', 10, 'bold'),
            fg=self.colors['text'], bg=self.colors['primary'],
            selectcolor=self.colors['secondary'],
            command=self.update_gravity
        )
        gravity_check.pack(side=tk.LEFT, padx=(10, 0))
        
        # Camera controls row
        camera_row = tk.Frame(sim_frame, bg=self.colors['primary'])
        camera_row.pack(pady=(10, 0))
        
        tk.Label(camera_row, text="Camera Views:", 
                font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack(side=tk.LEFT, padx=(0, 10))
        
        camera_buttons = [
            ("Front", self.set_front_view),
            ("Side", self.set_side_view),
            ("Top", self.set_top_view),
            ("Iso", self.set_iso_view)
        ]
        
        for name, command in camera_buttons:
            btn = tk.Button(
                camera_row, text=name,
                font=('Arial', 9, 'bold'),
                bg=self.colors['secondary'], fg='white',
                command=command,
                relief='raised', borderwidth=1,
                width=8
            )
            btn.pack(side=tk.LEFT, padx=2)
    
    def create_info_panel(self, parent):
        """Create information display panel."""
        info_frame = self.create_control_frame(parent, "PLATFORM STATUS")
        info_frame.pack(fill=tk.X, pady=(10, 10))
        
        # Status container
        status_container = tk.Frame(info_frame, bg=self.colors['primary'])
        status_container.pack(pady=10, fill=tk.X)
        
        # Position info
        pos_frame = tk.Frame(status_container, bg=self.colors['primary'])
        pos_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(pos_frame, text="POSITION:", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['position'] = tk.Label(
            pos_frame, text="X: 0.0, Y: 0.0, Z: 0.0",
            font=('Arial', 11), fg=self.colors['warning'], bg=self.colors['primary']
        )
        self.info_labels['position'].pack()
        
        # Rotation info
        rot_frame = tk.Frame(status_container, bg=self.colors['primary'])
        rot_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(rot_frame, text="ROTATION:", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['rotation'] = tk.Label(
            rot_frame, text="R: 0.0°, P: 0.0°, Y: 0.0°",
            font=('Arial', 11), fg=self.colors['warning'], bg=self.colors['primary']
        )
        self.info_labels['rotation'].pack()
        
        # Simulation status
        sim_status_frame = tk.Frame(status_container, bg=self.colors['primary'])
        sim_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(sim_status_frame, text="SIMULATION:", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['sim_status'] = tk.Label(
            sim_status_frame, text="Disconnected",
            font=('Arial', 11, 'bold'), fg=self.colors['accent'], bg=self.colors['primary']
        )
        self.info_labels['sim_status'].pack()
        
        # Leg lengths display
        legs_frame = self.create_control_frame(info_frame, "LEG LENGTHS (mm)")
        legs_frame.pack(fill=tk.X, pady=(15, 0))
        
        legs_grid = tk.Frame(legs_frame, bg=self.colors['primary'])
        legs_grid.pack(pady=10)
        
        self.info_labels['legs'] = []
        for i in range(6):
            row = i // 3
            col = i % 3
            
            leg_container = tk.Frame(legs_grid, bg=self.colors['secondary'], 
                                   relief='ridge', borderwidth=2)
            leg_container.grid(row=row, column=col, padx=10, pady=5, sticky='ew')
            
            tk.Label(leg_container, text=f"LEG {i+1}", 
                    font=('Arial', 9, 'bold'),
                    fg=self.colors['text'], bg=self.colors['secondary']).pack()
            
            leg_label = tk.Label(leg_container, text="0.00",
                               font=('Arial', 12, 'bold'),
                               fg=self.colors['warning'], bg=self.colors['secondary'])
            leg_label.pack()
            
            self.info_labels['legs'].append(leg_label)
    
    def create_control_buttons(self, parent):
        """Create main control buttons."""
        button_frame = tk.Frame(parent, bg=self.colors['primary'])
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Left side buttons
        left_frame = tk.Frame(button_frame, bg=self.colors['primary'])
        left_frame.pack(side=tk.LEFT)
        
        reset_btn = tk.Button(
            left_frame, text="🏠 RESET",
            font=('Arial', 12, 'bold'),
            bg=self.colors['success'], fg='white',
            command=self.reset_position,
            relief='raised', borderwidth=2, width=12
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side buttons
        right_frame = tk.Frame(button_frame, bg=self.colors['primary'])
        right_frame.pack(side=tk.RIGHT)
        
        estop_btn = tk.Button(
            right_frame, text="⚠️ E-STOP",
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'], fg='white',
            command=self.emergency_stop,
            relief='raised', borderwidth=2, width=12
        )
        estop_btn.pack(side=tk.RIGHT)
    
    # Event handlers
    def on_position_change(self, value=None):
        """Handle position slider changes."""
        self.current_position[0] = self.sliders['x'].get()
        self.current_position[1] = self.sliders['y'].get()
        self.current_position[2] = self.sliders['z'].get()
        
        self.update_kinematics()
        self.update_display()
        
        # Update simulation if connected
        if self.simulation_active and self.simulator:
            self.update_simulation_pose()
    
    def on_rotation_change(self, value=None):
        """Handle rotation slider changes."""
        self.current_rotation[0] = self.sliders['roll'].get()
        self.current_rotation[1] = self.sliders['pitch'].get()
        self.current_rotation[2] = self.sliders['yaw'].get()
        
        self.update_kinematics()
        self.update_display()
        
        # Update simulation if connected
        if self.simulation_active and self.simulator:
            self.update_simulation_pose()
    
    def update_display(self):
        """Update GUI display elements."""
        # Update position display
        pos_text = f"X: {self.current_position[0]:.1f}, Y: {self.current_position[1]:.1f}, Z: {self.current_position[2]:.1f}"
        self.info_labels['position'].config(text=pos_text)
        
        # Update rotation display
        rot_text = f"R: {self.current_rotation[0]:.1f}°, P: {self.current_rotation[1]:.1f}°, Y: {self.current_rotation[2]:.1f}°"
        self.info_labels['rotation'].config(text=rot_text)
        
        # Update leg lengths
        for i, leg_label in enumerate(self.info_labels['legs']):
            if i < len(self.current_leg_lengths):
                leg_label.config(text=f"{self.current_leg_lengths[i]:.2f}")
        
        # Update simulation status
        if self.simulation_active:
            self.info_labels['sim_status'].config(
                text="Connected", fg=self.colors['success']
            )
        else:
            self.info_labels['sim_status'].config(
                text="Disconnected", fg=self.colors['accent']
            )
    
    # Simulation methods
    def initialize_simulation(self):
        """Initialize PyBullet simulation."""
        try:
            urdf_path = self.config.get('urdf_path', 'simulation/urdf/Stewart.urdf')
            if os.path.exists(urdf_path):
                self.simulator = PyBulletSimulator(urdf_path)
            else:
                print(f"Warning: URDF file not found at {urdf_path}")
        except Exception as e:
            print(f"Error initializing simulation: {e}")
    
    def toggle_simulation(self):
        """Toggle simulation connection."""
        if self.simulation_active:
            self.disconnect_simulation()
        else:
            self.connect_simulation()
    
    def connect_simulation(self):
        """Connect to PyBullet simulation."""
        try:
            if self.simulator:
                self.simulator.connect()
                self.simulation_active = True
                self.sim_toggle_btn.config(text="🔌 DISCONNECT SIM")
                self.update_display()
                
                # Start continuous update if enabled
                if self.realtime_var.get():
                    self.start_continuous_update()
                    
                messagebox.showinfo("Simulation", "Connected to PyBullet simulation")
            else:
                messagebox.showerror("Error", "Simulator not initialized")
                
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to connect: {str(e)}")
    
    def disconnect_simulation(self):
        """Disconnect from PyBullet simulation."""
        try:
            if self.simulator:
                self.simulator.disconnect()
            
            self.simulation_active = False
            self.continuous_update = False
            self.sim_toggle_btn.config(text="🔌 CONNECT SIM")
            self.update_display()
            
            messagebox.showinfo("Simulation", "Disconnected from simulation")
            
        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to disconnect: {str(e)}")
    
    def update_simulation_pose(self):
        """Update the simulation with current platform pose."""
        if self.simulator and self.simulation_active:
            try:
                pose = {
                    'position': self.current_position.copy(),
                    'rotation': self.current_rotation.copy(),
                    'leg_lengths': self.current_leg_lengths.copy()
                }
                self.simulator.update_platform_pose(pose)
            except Exception as e:
                print(f"Error updating simulation pose: {e}")
    
    def start_continuous_update(self):
        """Start continuous simulation updates."""
        self.continuous_update = True
        if not self.sim_thread or not self.sim_thread.is_alive():
            self.sim_thread = threading.Thread(target=self.simulation_update_loop, daemon=True)
            self.sim_thread.start()
    
    def simulation_update_loop(self):
        """Continuous simulation update loop."""
        while self.continuous_update and self.simulation_active:
            try:
                self.update_simulation_pose()
                if self.simulator:
                    self.simulator.step_simulation()
                time.sleep(1/60)  # 60 FPS
            except Exception as e:
                print(f"Simulation update error: {e}")
                break
    
    def toggle_realtime_update(self):
        """Toggle real-time simulation updates."""
        if self.realtime_var.get() and self.simulation_active:
            self.start_continuous_update()
        else:
            self.continuous_update = False
    
    def update_gravity(self):
        """Update gravity setting in simulation."""
        if self.simulator and self.simulation_active:
            gravity = -9.81 if self.gravity_var.get() else 0
            self.simulator.set_gravity([0, 0, gravity])
    
    # Camera control methods
    def set_front_view(self):
        """Set camera to front view."""
        if self.simulator and self.simulation_active:
            self.simulator.set_camera_view('front')
    
    def set_side_view(self):
        """Set camera to side view."""
        if self.simulator and self.simulation_active:
            self.simulator.set_camera_view('side')
    
    def set_top_view(self):
        """Set camera to top view."""
        if self.simulator and self.simulation_active:
            self.simulator.set_camera_view('top')
    
    def set_iso_view(self):
        """Set camera to isometric view."""
        if self.simulator and self.simulation_active:
            self.simulator.set_camera_view('isometric')
    
    # Override parent methods
    def reset_position(self):
        """Reset platform and update sliders."""
        super().reset_position()
        
        # Update sliders
        for axis in ['x', 'y', 'z', 'roll', 'pitch', 'yaw']:
            if axis in self.sliders:
                self.sliders[axis].set(0.0)
        
        # Update simulation
        if self.simulation_active:
            self.update_simulation_pose()
    
    def emergency_stop(self):
        """Emergency stop with simulation disconnect."""
        self.continuous_update = False
        if self.simulation_active:
            self.disconnect_simulation()
        super().emergency_stop()
    
    def on_closing(self):
        """Handle GUI closing with simulation cleanup."""
        self.continuous_update = False
        if self.simulation_active:
            self.disconnect_simulation()
        super().on_closing()


def main():
    """Main function to run the PyBullet GUI."""
    root = tk.Tk()
    app = PyBulletStewartGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()


if __name__ == "__main__":
    main()
