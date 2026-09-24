#!/usr/bin/env python3
"""
Advanced Stewart Platform GUI.
Provides comprehensive controls including presets, animations, and advanced features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import json
import threading
import time
import math
from typing import Optional, Dict, Any, List, Tuple

from .base_gui import BaseStewartGUI
from ..core.trajectory import TrajectoryGenerator


class AdvancedStewartGUI(BaseStewartGUI):
    """
    Advanced GUI implementation with comprehensive controls.
    Features:
    - All basic controls
    - Preset positions
    - Animation sequences
    - Trajectory generation
    - Auto mode for each axis
    - Position saving/loading
    - Real-time monitoring
    - Advanced status display
    """
    
    def __init__(self, root: tk.Tk, config: Optional[Dict[str, Any]] = None):
        """Initialize the advanced GUI."""
        self.sliders = {}
        self.info_labels = {}
        self.auto_vars = {}
        self.preset_positions = {}
        self.trajectory_generator = TrajectoryGenerator()
        
        super().__init__(root, config)
        
        self.load_presets()
    
    def create_interface(self):
        """Create the advanced GUI interface."""
        self.root.title("🤖 Stewart Platform - Advanced Control")
        self.root.geometry("1400x900")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_control_tab()
        self.create_presets_tab()
        self.create_animation_tab()
        self.create_monitoring_tab()
    
    def create_control_tab(self):
        """Create the main control tab."""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="🎮 Control")
        
        # Title
        title_label = ttk.Label(control_frame, text="🤖 STEWART PLATFORM - ADVANCED CONTROL",
                               style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # Main content
        main_content = tk.Frame(control_frame, bg=self.colors['primary'])
        main_content.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Control panels
        controls_container = tk.Frame(main_content, bg=self.colors['primary'])
        controls_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Translation
        self.create_translation_controls(controls_container)
        
        # Right panel - Rotation
        self.create_rotation_controls(controls_container)
        
        # Bottom panel - Info and buttons
        self.create_control_info_panel(main_content)
        self.create_control_buttons(main_content)
    
    def create_translation_controls(self, parent):
        """Create enhanced translation controls with auto mode."""
        trans_frame = self.create_control_frame(parent, "TRANSLATION CONTROLS")
        trans_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # X translation with auto mode
        self.create_axis_control(trans_frame, 'x', 'X Position (mm)', 
                                self.position_limits['x'], self.on_translation_change)
        
        # Y translation with auto mode
        self.create_axis_control(trans_frame, 'y', 'Y Position (mm)',
                                self.position_limits['y'], self.on_translation_change)
        
        # Z translation with auto mode
        self.create_axis_control(trans_frame, 'z', 'Z Position (HEAVE) (mm)',
                                self.position_limits['z'], self.on_translation_change)
    
    def create_rotation_controls(self, parent):
        """Create enhanced rotation controls with auto mode."""
        rot_frame = self.create_control_frame(parent, "ROTATION CONTROLS")
        rot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Roll with auto mode
        self.create_axis_control(rot_frame, 'roll', 'Roll (degrees)',
                                self.rotation_limits['roll'], self.on_rotation_change, 0.5)
        
        # Pitch with auto mode
        self.create_axis_control(rot_frame, 'pitch', 'Pitch (degrees)',
                                self.rotation_limits['pitch'], self.on_rotation_change, 0.5)
        
        # Yaw with auto mode
        self.create_axis_control(rot_frame, 'yaw', 'Yaw (degrees)',
                                self.rotation_limits['yaw'], self.on_rotation_change, 0.5)
    
    def create_axis_control(self, parent, axis: str, label: str, limits: Tuple[float, float], 
                           callback: callable, resolution: float = 1.0):
        """Create a complete axis control with slider and auto mode."""
        container = tk.Frame(parent, bg=self.colors['primary'])
        container.pack(fill=tk.X, pady=(10, 15))
        
        # Header with auto checkbox
        header = tk.Frame(container, bg=self.colors['primary'])
        header.pack(fill=tk.X)
        
        # Auto mode checkbox
        self.auto_vars[axis] = tk.BooleanVar()
        auto_check = tk.Checkbutton(
            header, text="AUTO", variable=self.auto_vars[axis],
            font=('Arial', 9, 'bold'), fg=self.colors['warning'],
            bg=self.colors['primary'], selectcolor=self.colors['secondary'],
            command=lambda: self.toggle_auto_mode(axis)
        )
        auto_check.pack(side=tk.RIGHT)
        
        # Label
        axis_label = tk.Label(header, text=label, font=('Arial', 10, 'bold'),
                             fg=self.colors['text'], bg=self.colors['primary'])
        axis_label.pack(side=tk.LEFT)
        
        # Slider
        slider = tk.Scale(container, from_=limits[0], to=limits[1],
                         resolution=resolution, orient=tk.HORIZONTAL,
                         length=350, font=('Arial', 9),
                         fg=self.colors['text'], bg=self.colors['secondary'],
                         highlightbackground=self.colors['primary'],
                         troughcolor=self.colors['bg'],
                         command=callback)
        slider.pack(fill=tk.X, pady=(5, 0))
        slider.set(0.0)
        
        self.sliders[axis] = slider
    
    def create_presets_tab(self):
        """Create the presets management tab."""
        presets_frame = ttk.Frame(self.notebook)
        self.notebook.add(presets_frame, text="📁 Presets")
        
        main_frame = tk.Frame(presets_frame, bg=self.colors['primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(main_frame, text="🔖 POSITION PRESETS", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Preset buttons grid
        presets_container = tk.Frame(main_frame, bg=self.colors['primary'])
        presets_container.pack(fill=tk.BOTH, expand=True)
        
        # Default presets
        self.create_preset_buttons(presets_container)
        
        # Custom preset controls
        self.create_custom_preset_controls(main_frame)
    
    def create_preset_buttons(self, parent):
        """Create grid of preset position buttons."""
        presets_grid = tk.Frame(parent, bg=self.colors['primary'])
        presets_grid.pack(fill=tk.BOTH, expand=True)
        
        preset_configs = [
            ("🏠 HOME", [0, 0, 0, 0, 0, 0]),
            ("⬆️ UP", [0, 0, 20, 0, 0, 0]),
            ("⬇️ DOWN", [0, 0, -20, 0, 0, 0]),
            ("⬅️ LEFT", [-30, 0, 0, 0, 0, 0]),
            ("➡️ RIGHT", [30, 0, 0, 0, 0, 0]),
            ("🔄 ROLL +", [0, 0, 0, 10, 0, 0]),
            ("🔄 ROLL -", [0, 0, 0, -10, 0, 0]),
            ("🔽 PITCH +", [0, 0, 0, 0, 10, 0]),
            ("🔼 PITCH -", [0, 0, 0, 0, -10, 0]),
            ("🔃 YAW +", [0, 0, 0, 0, 0, 15]),
            ("🔂 YAW -", [0, 0, 0, 0, 0, -15]),
            ("🎯 TEST", [15, 15, 10, 5, 5, 10])
        ]
        
        # Create buttons in grid
        for i, (name, position) in enumerate(preset_configs):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(
                presets_grid, text=name,
                font=('Arial', 10, 'bold'),
                bg=self.colors['secondary'],
                fg=self.colors['text'],
                width=15, height=2,
                command=lambda pos=position: self.load_preset_position(pos),
                relief='raised', borderwidth=2
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Configure grid weights
            presets_grid.grid_columnconfigure(col, weight=1)
        
        # Configure row weights
        for row in range((len(preset_configs) + 3) // 4):
            presets_grid.grid_rowconfigure(row, weight=1)
    
    def create_animation_tab(self):
        """Create the animation control tab."""
        anim_frame = ttk.Frame(self.notebook)
        self.notebook.add(anim_frame, text="🎬 Animation")
        
        main_frame = tk.Frame(anim_frame, bg=self.colors['primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(main_frame, text="🎥 ANIMATION SEQUENCES", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Animation controls
        self.create_animation_controls(main_frame)
        
        # Trajectory controls
        self.create_trajectory_controls(main_frame)
    
    def create_animation_controls(self, parent):
        """Create animation control buttons."""
        anim_frame = self.create_control_frame(parent, "PREDEFINED ANIMATIONS")
        anim_frame.pack(fill=tk.X, pady=(0, 20))
        
        animations = [
            ("🌊 Wave Motion", self.wave_animation),
            ("🔄 Circular Motion", self.circular_animation),
            ("📈 Figure-8", self.figure8_animation),
            ("🎢 Random Motion", self.random_animation),
            ("🔺 Triangle Path", self.triangle_animation),
            ("⏹️ Stop Animation", self.stop_animation)
        ]
        
        button_frame = tk.Frame(anim_frame, bg=self.colors['primary'])
        button_frame.pack(pady=10)
        
        for i, (name, func) in enumerate(animations):
            row = i // 3
            col = i % 3
            
            color = self.colors['accent'] if 'Stop' in name else self.colors['success']
            
            btn = tk.Button(
                button_frame, text=name,
                font=('Arial', 11, 'bold'),
                bg=color, fg='white',
                width=18, height=2,
                command=func,
                relief='raised', borderwidth=2
            )
            btn.grid(row=row, column=col, padx=10, pady=5)
    
    def create_monitoring_tab(self):
        """Create real-time monitoring tab."""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 Monitoring")
        
        main_frame = tk.Frame(monitor_frame, bg=self.colors['primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(main_frame, text="📈 REAL-TIME MONITORING", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Monitoring displays
        self.create_monitoring_displays(main_frame)
    
    def create_control_info_panel(self, parent):
        """Create information panel for control tab."""
        info_frame = self.create_control_frame(parent, "PLATFORM STATUS")
        info_frame.pack(fill=tk.X, pady=(20, 10))
        
        status_container = tk.Frame(info_frame, bg=self.colors['primary'])
        status_container.pack(pady=10, fill=tk.X)
        
        # Position display
        pos_frame = tk.Frame(status_container, bg=self.colors['primary'])
        pos_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(pos_frame, text="POSITION (mm):", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['position'] = tk.Label(
            pos_frame, text="X: 0.0 | Y: 0.0 | Z: 0.0",
            font=('Arial', 11, 'bold'), fg=self.colors['warning'], bg=self.colors['primary']
        )
        self.info_labels['position'].pack()
        
        # Rotation display
        rot_frame = tk.Frame(status_container, bg=self.colors['primary'])
        rot_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        tk.Label(rot_frame, text="ROTATION (deg):", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['rotation'] = tk.Label(
            rot_frame, text="R: 0.0 | P: 0.0 | Y: 0.0",
            font=('Arial', 11, 'bold'), fg=self.colors['warning'], bg=self.colors['primary']
        )
        self.info_labels['rotation'].pack()
        
        # Leg lengths display
        legs_frame = self.create_control_frame(info_frame, "LEG LENGTHS (mm)")
        legs_frame.pack(fill=tk.X, pady=(10, 0))
        
        legs_grid = tk.Frame(legs_frame, bg=self.colors['primary'])
        legs_grid.pack(pady=5)
        
        self.info_labels['legs'] = []
        for i in range(6):
            row = i // 3
            col = i % 3
            
            leg_frame = tk.Frame(legs_grid, bg=self.colors['secondary'], relief='ridge', borderwidth=1)
            leg_frame.grid(row=row, column=col, padx=8, pady=5, sticky='ew')
            
            tk.Label(leg_frame, text=f"LEG {i+1}", font=('Arial', 9, 'bold'),
                    fg=self.colors['text'], bg=self.colors['secondary']).pack()
            
            leg_label = tk.Label(leg_frame, text="0.00", font=('Arial', 12, 'bold'),
                                fg=self.colors['warning'], bg=self.colors['secondary'])
            leg_label.pack()
            
            self.info_labels['legs'].append(leg_label)
    
    def create_control_buttons(self, parent):
        """Create control buttons for main tab."""
        button_frame = tk.Frame(parent, bg=self.colors['primary'])
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Left side buttons
        left_buttons = tk.Frame(button_frame, bg=self.colors['primary'])
        left_buttons.pack(side=tk.LEFT)
        
        reset_btn = tk.Button(
            left_buttons, text="🏠 RESET HOME",
            font=('Arial', 12, 'bold'),
            bg=self.colors['success'], fg='white',
            command=self.reset_position,
            relief='raised', borderwidth=2, width=15
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side buttons
        right_buttons = tk.Frame(button_frame, bg=self.colors['primary'])
        right_buttons.pack(side=tk.RIGHT)
        
        estop_btn = tk.Button(
            right_buttons, text="⚠️ EMERGENCY STOP",
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'], fg='white',
            command=self.emergency_stop,
            relief='raised', borderwidth=2, width=18
        )
        estop_btn.pack(side=tk.RIGHT)
    
    # Event handlers
    def on_translation_change(self, value=None):
        """Handle translation changes with auto mode check."""
        if not self.auto_vars['x'].get():
            self.current_position[0] = self.sliders['x'].get()
        if not self.auto_vars['y'].get():
            self.current_position[1] = self.sliders['y'].get()
        if not self.auto_vars['z'].get():
            self.current_position[2] = self.sliders['z'].get()
        
        self.update_kinematics()
        self.update_display()
    
    def on_rotation_change(self, value=None):
        """Handle rotation changes with auto mode check."""
        if not self.auto_vars['roll'].get():
            self.current_rotation[0] = self.sliders['roll'].get()
        if not self.auto_vars['pitch'].get():
            self.current_rotation[1] = self.sliders['pitch'].get()
        if not self.auto_vars['yaw'].get():
            self.current_rotation[2] = self.sliders['yaw'].get()
        
        self.update_kinematics()
        self.update_display()
    
    def toggle_auto_mode(self, axis: str):
        """Toggle auto mode for an axis."""
        if self.auto_vars[axis].get():
            # Enable auto mode - disable slider
            self.sliders[axis].config(state='disabled')
        else:
            # Disable auto mode - enable slider
            self.sliders[axis].config(state='normal')
    
    def load_preset_position(self, position: List[float]):
        """Load a preset position."""
        if len(position) >= 6:
            # Update current state
            self.current_position = position[:3]
            self.current_rotation = position[3:6]
            
            # Update sliders if not in auto mode
            if not self.auto_vars['x'].get():
                self.sliders['x'].set(position[0])
            if not self.auto_vars['y'].get():
                self.sliders['y'].set(position[1])
            if not self.auto_vars['z'].get():
                self.sliders['z'].set(position[2])
            if not self.auto_vars['roll'].get():
                self.sliders['roll'].set(position[3])
            if not self.auto_vars['pitch'].get():
                self.sliders['pitch'].set(position[4])
            if not self.auto_vars['yaw'].get():
                self.sliders['yaw'].set(position[5])
            
            self.update_kinematics()
            self.update_display()
    
    def update_display(self):
        """Update all display elements."""
        # Update position and rotation display
        pos_text = f"X: {self.current_position[0]:.1f} | Y: {self.current_position[1]:.1f} | Z: {self.current_position[2]:.1f}"
        self.info_labels['position'].config(text=pos_text)
        
        rot_text = f"R: {self.current_rotation[0]:.1f} | P: {self.current_rotation[1]:.1f} | Y: {self.current_rotation[2]:.1f}"
        self.info_labels['rotation'].config(text=rot_text)
        
        # Update leg lengths
        for i, leg_label in enumerate(self.info_labels['legs']):
            if i < len(self.current_leg_lengths):
                leg_label.config(text=f"{self.current_leg_lengths[i]:.2f}")
    
    # Animation methods
    def wave_animation(self):
        """Start wave motion animation."""
        def wave_motion():
            t = 0
            while self.animation_running:
                # Wave motion in Z and roll
                z = 15 * math.sin(t * 2)
                roll = 8 * math.sin(t * 1.5)
                
                if self.auto_vars['z'].get():
                    self.current_position[2] = z
                if self.auto_vars['roll'].get():
                    self.current_rotation[0] = roll
                
                self.update_kinematics()
                self.root.after_idle(self.update_display)
                
                t += 0.1
                time.sleep(0.05)
        
        self.start_animation(wave_motion)
    
    def circular_animation(self):
        """Start circular motion animation."""
        def circular_motion():
            t = 0
            radius = 20
            while self.animation_running:
                # Circular motion in X-Y plane
                x = radius * math.cos(t)
                y = radius * math.sin(t)
                
                if self.auto_vars['x'].get():
                    self.current_position[0] = x
                if self.auto_vars['y'].get():
                    self.current_position[1] = y
                
                self.update_kinematics()
                self.root.after_idle(self.update_display)
                
                t += 0.1
                time.sleep(0.05)
        
        self.start_animation(circular_motion)
    
    def figure8_animation(self):
        """Start figure-8 motion animation."""
        def figure8_motion():
            t = 0
            while self.animation_running:
                # Figure-8 pattern
                x = 25 * math.sin(t)
                y = 25 * math.sin(t) * math.cos(t)
                
                if self.auto_vars['x'].get():
                    self.current_position[0] = x
                if self.auto_vars['y'].get():
                    self.current_position[1] = y
                
                self.update_kinematics()
                self.root.after_idle(self.update_display)
                
                t += 0.15
                time.sleep(0.05)
        
        self.start_animation(figure8_motion)
    
    def random_animation(self):
        """Start random motion animation."""
        def random_motion():
            while self.animation_running:
                # Generate random target position
                target_pos = [
                    np.random.uniform(-30, 30) if self.auto_vars['x'].get() else self.current_position[0],
                    np.random.uniform(-30, 30) if self.auto_vars['y'].get() else self.current_position[1],
                    np.random.uniform(-20, 20) if self.auto_vars['z'].get() else self.current_position[2]
                ]
                
                target_rot = [
                    np.random.uniform(-10, 10) if self.auto_vars['roll'].get() else self.current_rotation[0],
                    np.random.uniform(-10, 10) if self.auto_vars['pitch'].get() else self.current_rotation[1],
                    np.random.uniform(-20, 20) if self.auto_vars['yaw'].get() else self.current_rotation[2]
                ]
                
                # Smoothly interpolate to target
                steps = 50
                for i in range(steps):
                    if not self.animation_running:
                        break
                    
                    alpha = i / steps
                    
                    for j in range(3):
                        if j == 0 and self.auto_vars['x'].get():
                            self.current_position[j] = self.current_position[j] * (1 - alpha) + target_pos[j] * alpha
                        elif j == 1 and self.auto_vars['y'].get():
                            self.current_position[j] = self.current_position[j] * (1 - alpha) + target_pos[j] * alpha
                        elif j == 2 and self.auto_vars['z'].get():
                            self.current_position[j] = self.current_position[j] * (1 - alpha) + target_pos[j] * alpha
                        
                        axes = ['roll', 'pitch', 'yaw']
                        if self.auto_vars[axes[j]].get():
                            self.current_rotation[j] = self.current_rotation[j] * (1 - alpha) + target_rot[j] * alpha
                    
                    self.update_kinematics()
                    self.root.after_idle(self.update_display)
                    time.sleep(0.05)
                
                time.sleep(1)  # Pause at target
        
        self.start_animation(random_motion)
    
    def triangle_animation(self):
        """Start triangular path animation."""
        def triangle_motion():
            # Define triangle vertices
            vertices = [
                [25, 0], [0, 25], [-25, 0], [25, 0]  # Close the triangle
            ]
            
            while self.animation_running:
                for i in range(len(vertices) - 1):
                    if not self.animation_running:
                        break
                    
                    start = vertices[i]
                    end = vertices[i + 1]
                    
                    # Interpolate between vertices
                    steps = 30
                    for j in range(steps):
                        if not self.animation_running:
                            break
                        
                        alpha = j / steps
                        x = start[0] * (1 - alpha) + end[0] * alpha
                        y = start[1] * (1 - alpha) + end[1] * alpha
                        
                        if self.auto_vars['x'].get():
                            self.current_position[0] = x
                        if self.auto_vars['y'].get():
                            self.current_position[1] = y
                        
                        self.update_kinematics()
                        self.root.after_idle(self.update_display)
                        time.sleep(0.08)
        
        self.start_animation(triangle_motion)
    
    # Additional methods
    def load_presets(self):
        """Load preset positions from configuration."""
        # This could load from a file in the future
        pass
    
    def create_custom_preset_controls(self, parent):
        """Create controls for saving custom presets."""
        custom_frame = self.create_control_frame(parent, "CUSTOM PRESETS")
        custom_frame.pack(fill=tk.X, pady=(20, 0))
        
        button_container = tk.Frame(custom_frame, bg=self.colors['primary'])
        button_container.pack(pady=10)
        
        save_btn = tk.Button(
            button_container, text="💾 SAVE CURRENT",
            font=('Arial', 11, 'bold'),
            bg=self.colors['success'], fg='white',
            command=self.save_current_position,
            relief='raised', borderwidth=2
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        load_btn = tk.Button(
            button_container, text="📂 LOAD FROM FILE",
            font=('Arial', 11, 'bold'),
            bg=self.colors['secondary'], fg='white',
            command=self.load_position_file,
            relief='raised', borderwidth=2
        )
        load_btn.pack(side=tk.LEFT)
    
    def create_trajectory_controls(self, parent):
        """Create trajectory generation controls."""
        traj_frame = self.create_control_frame(parent, "TRAJECTORY GENERATION")
        traj_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Implementation for trajectory controls would go here
        placeholder = tk.Label(traj_frame, text="Trajectory controls coming soon...",
                              font=('Arial', 10), fg=self.colors['text'], bg=self.colors['primary'])
        placeholder.pack(pady=20)
    
    def create_monitoring_displays(self, parent):
        """Create monitoring display widgets."""
        # Implementation for real-time monitoring would go here
        placeholder = tk.Label(parent, text="Real-time monitoring displays coming soon...",
                              font=('Arial', 14), fg=self.colors['text'], bg=self.colors['primary'])
        placeholder.pack(pady=50)
    
    def save_current_position(self):
        """Save current position to file."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                position_data = {
                    "position": self.current_position,
                    "rotation": self.current_rotation,
                    "timestamp": time.time()
                }
                with open(filename, 'w') as f:
                    json.dump(position_data, f, indent=2)
                messagebox.showinfo("Save Complete", f"Position saved to {filename}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving position: {str(e)}")
    
    def load_position_file(self):
        """Load position from file."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                position = data["position"] + data["rotation"]
                self.load_preset_position(position)
                messagebox.showinfo("Load Complete", f"Position loaded from {filename}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading position: {str(e)}")


def main():
    """Main function to run the advanced GUI."""
    root = tk.Tk()
    app = AdvancedStewartGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()


if __name__ == "__main__":
    main()
