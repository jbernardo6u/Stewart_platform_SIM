#!/usr/bin/env python3
"""
Simple Stewart Platform GUI.
Provides basic position and rotation controls with real-time feedback.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from typing import Optional, Dict, Any

from .base_gui import BaseStewartGUI


class SimpleStewartGUI(BaseStewartGUI):
    """
    Simple GUI implementation with basic controls for all 6 DOF.
    Features:
    - Translation controls (X, Y, Z)
    - Rotation controls (Roll, Pitch, Yaw)
    - Real-time leg length display
    - Reset and emergency stop buttons
    """
    
    def __init__(self, root: tk.Tk, config: Optional[Dict[str, Any]] = None):
        """Initialize the simple GUI."""
        self.sliders = {}
        self.info_labels = {}
        super().__init__(root, config)
    
    def create_interface(self):
        """Create the simple GUI interface."""
        self.root.title("🤖 Stewart Platform - Simple Control")
        self.root.geometry("800x700")
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_container, text="🤖 STEWART PLATFORM CONTROL",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Control panels
        controls_frame = tk.Frame(main_container, bg=self.colors['primary'])
        controls_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Translation controls
        self.create_translation_controls(controls_frame)
        
        # Right panel - Rotation controls  
        self.create_rotation_controls(controls_frame)
        
        # Bottom panel - Information and buttons
        self.create_info_panel(main_container)
        
        # Button panel
        self.create_button_panel(main_container)
    
    def create_translation_controls(self, parent):
        """Create translation control sliders."""
        trans_frame = self.create_control_frame(parent, "TRANSLATION")
        trans_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # X translation
        x_limits = self.position_limits['x']
        x_label, x_slider = self.create_slider(
            trans_frame, "X Position (mm)", 
            x_limits[0], x_limits[1], 
            command=self.on_translation_change
        )
        x_label.pack(pady=(10, 5))
        x_slider.pack(pady=(0, 10))
        self.sliders['x'] = x_slider
        
        # Y translation
        y_limits = self.position_limits['y']
        y_label, y_slider = self.create_slider(
            trans_frame, "Y Position (mm)",
            y_limits[0], y_limits[1],
            command=self.on_translation_change
        )
        y_label.pack(pady=(10, 5))
        y_slider.pack(pady=(0, 10))
        self.sliders['y'] = y_slider
        
        # Z translation (HEAVE)
        z_limits = self.position_limits['z']
        z_label, z_slider = self.create_slider(
            trans_frame, "Z Position (HEAVE) (mm)",
            z_limits[0], z_limits[1],
            command=self.on_translation_change
        )
        z_label.pack(pady=(10, 5))
        z_slider.pack(pady=(0, 10))
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
        roll_label.pack(pady=(10, 5))
        roll_slider.pack(pady=(0, 10))
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
        pitch_slider.pack(pady=(0, 10))
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
        yaw_slider.pack(pady=(0, 10))
        self.sliders['yaw'] = yaw_slider
    
    def create_info_panel(self, parent):
        """Create information display panel."""
        info_frame = self.create_control_frame(parent, "PLATFORM STATUS")
        info_frame.pack(fill=tk.X, pady=(20, 10))
        
        # Create grid for leg lengths
        leg_frame = tk.Frame(info_frame, bg=self.colors['primary'])
        leg_frame.pack(pady=10)
        
        # Position info
        pos_frame = tk.Frame(leg_frame, bg=self.colors['primary'])
        pos_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(pos_frame, text="Position:", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['position'] = tk.Label(
            pos_frame, text="X: 0.0, Y: 0.0, Z: 0.0",
            font=('Arial', 9), fg=self.colors['text'], bg=self.colors['primary']
        )
        self.info_labels['position'].pack()
        
        # Rotation info
        rot_frame = tk.Frame(leg_frame, bg=self.colors['primary'])
        rot_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(rot_frame, text="Rotation:", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        self.info_labels['rotation'] = tk.Label(
            rot_frame, text="R: 0.0°, P: 0.0°, Y: 0.0°",
            font=('Arial', 9), fg=self.colors['text'], bg=self.colors['primary']
        )
        self.info_labels['rotation'].pack()
        
        # Leg lengths
        legs_frame = tk.Frame(leg_frame, bg=self.colors['primary'])
        legs_frame.pack(side=tk.LEFT)
        
        tk.Label(legs_frame, text="Leg Lengths (mm):", font=('Arial', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['primary']).pack()
        
        # Create labels for each leg
        self.info_labels['legs'] = []
        legs_grid = tk.Frame(legs_frame, bg=self.colors['primary'])
        legs_grid.pack()
        
        for i in range(6):
            row = i // 3
            col = i % 3
            leg_label = tk.Label(
                legs_grid, text=f"L{i+1}: 0.0",
                font=('Arial', 9), fg=self.colors['text'], 
                bg=self.colors['primary'], width=12
            )
            leg_label.grid(row=row, column=col, padx=5, pady=2)
            self.info_labels['legs'].append(leg_label)
    
    def create_button_panel(self, parent):
        """Create control buttons."""
        button_frame = tk.Frame(parent, bg=self.colors['primary'])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Reset button
        reset_btn = tk.Button(
            button_frame, text="🔄 RESET TO HOME",
            font=('Arial', 12, 'bold'),
            bg=self.colors['success'],
            fg='white',
            command=self.reset_position,
            relief='raised',
            borderwidth=2
        )
        reset_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Emergency stop button
        estop_btn = tk.Button(
            button_frame, text="⚠️ EMERGENCY STOP",
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            command=self.emergency_stop,
            relief='raised',
            borderwidth=2
        )
        estop_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Info button
        info_btn = tk.Button(
            button_frame, text="ℹ️ INFO",
            font=('Arial', 12, 'bold'),
            bg=self.colors['secondary'],
            fg='white',
            command=self.show_info,
            relief='raised',
            borderwidth=2
        )
        info_btn.pack(side=tk.RIGHT)
    
    def on_translation_change(self, value=None):
        """Handle translation slider changes."""
        self.current_position[0] = self.sliders['x'].get()
        self.current_position[1] = self.sliders['y'].get()
        self.current_position[2] = self.sliders['z'].get()
        
        # Validate position
        if self.validate_position(*self.current_position):
            self.update_kinematics()
            self.update_display()
        else:
            # Reset to previous valid position
            self.sliders['x'].set(self.current_position[0])
            self.sliders['y'].set(self.current_position[1])
            self.sliders['z'].set(self.current_position[2])
    
    def on_rotation_change(self, value=None):
        """Handle rotation slider changes."""
        self.current_rotation[0] = self.sliders['roll'].get()
        self.current_rotation[1] = self.sliders['pitch'].get()
        self.current_rotation[2] = self.sliders['yaw'].get()
        
        # Validate rotation
        if self.validate_rotation(*self.current_rotation):
            self.update_kinematics()
            self.update_display()
        else:
            # Reset to previous valid rotation
            self.sliders['roll'].set(self.current_rotation[0])
            self.sliders['pitch'].set(self.current_rotation[1])
            self.sliders['yaw'].set(self.current_rotation[2])
    
    def update_display(self):
        """Update all display elements with current values."""
        # Update position info
        pos_text = f"X: {self.current_position[0]:.1f}, Y: {self.current_position[1]:.1f}, Z: {self.current_position[2]:.1f}"
        self.info_labels['position'].config(text=pos_text)
        
        # Update rotation info
        rot_text = f"R: {self.current_rotation[0]:.1f}°, P: {self.current_rotation[1]:.1f}°, Y: {self.current_rotation[2]:.1f}°"
        self.info_labels['rotation'].config(text=rot_text)
        
        # Update leg lengths
        for i, leg_label in enumerate(self.info_labels['legs']):
            if i < len(self.current_leg_lengths):
                leg_text = f"L{i+1}: {self.current_leg_lengths[i]:.1f}"
                leg_label.config(text=leg_text)
    
    def reset_position(self):
        """Reset platform to home position and update sliders."""
        super().reset_position()
        
        # Update all sliders
        self.sliders['x'].set(0.0)
        self.sliders['y'].set(0.0)
        self.sliders['z'].set(0.0)
        self.sliders['roll'].set(0.0)
        self.sliders['pitch'].set(0.0)
        self.sliders['yaw'].set(0.0)
    
    def show_info(self):
        """Show platform information dialog."""
        info_text = f"""Stewart Platform Information:

Design Variables:
- Platform radius: {self.design_variables[0]} m
- Base radius: {self.design_variables[1]} m  
- Platform angle: {self.design_variables[2]}°
- Base angle: {self.design_variables[3]}°

Position Limits:
- X: {self.position_limits['x'][0]} to {self.position_limits['x'][1]} mm
- Y: {self.position_limits['y'][0]} to {self.position_limits['y'][1]} mm
- Z: {self.position_limits['z'][0]} to {self.position_limits['z'][1]} mm

Rotation Limits:
- Roll: {self.rotation_limits['roll'][0]}° to {self.rotation_limits['roll'][1]}°
- Pitch: {self.rotation_limits['pitch'][0]}° to {self.rotation_limits['pitch'][1]}°
- Yaw: {self.rotation_limits['yaw'][0]}° to {self.rotation_limits['yaw'][1]}°

Current Leg Lengths:
""" + "\n".join([f"- Leg {i+1}: {length:.2f} mm" for i, length in enumerate(self.current_leg_lengths)])

        tk.messagebox.showinfo("Platform Info", info_text)


def main():
    """Main function to run the simple GUI."""
    root = tk.Tk()
    app = SimpleStewartGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()


if __name__ == "__main__":
    main()
