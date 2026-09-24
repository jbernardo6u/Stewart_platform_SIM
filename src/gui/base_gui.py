#!/usr/bin/env python3
"""
Base GUI class for Stewart Platform interfaces.
Provides common functionality and structure for all GUI implementations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any

from ..core.kinematics import InverseKinematics
from ..core.platform import StewartPlatform


class BaseStewartGUI(ABC):
    """
    Abstract base class for Stewart Platform GUI interfaces.
    
    Provides common functionality including:
    - Basic GUI setup and styling
    - Platform state management
    - Kinematics calculations
    - Control validation
    - Threading support for animations
    """
    
    def __init__(self, root: tk.Tk, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base GUI.
        
        Args:
            root: Tkinter root window
            config: Configuration dictionary with platform parameters
        """
        self.root = root
        self.config = config or self._get_default_config()
        
        # Platform configuration
        self.design_variables = self.config.get('design_variables', [0.2, 0.2, 12, 12])
        self.position_limits = self.config.get('position_limits', {
            'x': (-50, 50), 'y': (-50, 50), 'z': (-30, 30)
        })
        self.rotation_limits = self.config.get('rotation_limits', {
            'roll': (-15, 15), 'pitch': (-15, 15), 'yaw': (-30, 30)
        })
        
        # Current state
        self.current_position = [0.0, 0.0, 0.0]  # X, Y, Z (mm)
        self.current_rotation = [0.0, 0.0, 0.0]  # Roll, Pitch, Yaw (degrees)
        self.current_leg_lengths = [0.0] * 6
        
        # Control state
        self.auto_mode = [False] * 6  # Auto mode for each DOF
        self.animation_running = False
        self.animation_thread = None
        self.update_lock = threading.Lock()
        
        # Initialize kinematics
        r_P, r_B, gama_P, gama_B = self.design_variables
        self.kinematics = InverseKinematics(r_P, r_B, gama_P, gama_B)
        
        # GUI styling
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#4A90C2', 
            'accent': '#F24236',
            'success': '#2ECC40',
            'warning': '#FF851B',
            'text': 'white',
            'bg': '#1B1B1B'
        }
        
        # Initialize GUI
        self.setup_base_gui()
        self.create_interface()
        self.update_display()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the platform."""
        return {
            'design_variables': [0.2, 0.2, 12, 12],
            'position_limits': {
                'x': (-50, 50), 'y': (-50, 50), 'z': (-30, 30)
            },
            'rotation_limits': {
                'roll': (-15, 15), 'pitch': (-15, 15), 'yaw': (-30, 30)
            },
            'urdf_path': 'simulation/urdf/Stewart.urdf'
        }
    
    def setup_base_gui(self):
        """Setup basic GUI properties and styling."""
        self.root.configure(bg=self.colors['primary'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', 
                       background=self.colors['primary'],
                       foreground=self.colors['text'],
                       font=('Arial', 18, 'bold'))
        
        style.configure('Heading.TLabel',
                       background=self.colors['primary'],
                       foreground=self.colors['text'],
                       font=('Arial', 12, 'bold'))
        
        style.configure('Info.TLabel',
                       background=self.colors['primary'],
                       foreground=self.colors['text'],
                       font=('Arial', 10))
    
    @abstractmethod
    def create_interface(self):
        """Create the specific GUI interface. Must be implemented by subclasses."""
        pass
    
    def create_control_frame(self, parent: tk.Widget, title: str) -> tk.LabelFrame:
        """
        Create a styled control frame.
        
        Args:
            parent: Parent widget
            title: Frame title
            
        Returns:
            Configured LabelFrame
        """
        frame = tk.LabelFrame(parent, text=title,
                             font=('Arial', 12, 'bold'),
                             fg=self.colors['text'],
                             bg=self.colors['primary'],
                             relief='ridge',
                             borderwidth=2)
        return frame
    
    def create_slider(self, parent: tk.Widget, label: str, 
                     min_val: float, max_val: float, 
                     initial: float = 0.0,
                     resolution: float = 0.1,
                     command: Optional[callable] = None) -> Tuple[tk.Label, tk.Scale]:
        """
        Create a labeled slider control.
        
        Args:
            parent: Parent widget
            label: Slider label
            min_val: Minimum value
            max_val: Maximum value
            initial: Initial value
            resolution: Step resolution
            command: Callback function
            
        Returns:
            Tuple of (label_widget, scale_widget)
        """
        label_widget = tk.Label(parent, text=label,
                               font=('Arial', 10, 'bold'),
                               fg=self.colors['text'],
                               bg=self.colors['primary'])
        
        scale_widget = tk.Scale(parent, from_=min_val, to=max_val,
                               resolution=resolution, orient=tk.HORIZONTAL,
                               length=300, font=('Arial', 9),
                               fg=self.colors['text'],
                               bg=self.colors['secondary'],
                               highlightbackground=self.colors['primary'],
                               troughcolor=self.colors['bg'],
                               command=command)
        scale_widget.set(initial)
        
        return label_widget, scale_widget
    
    def update_kinematics(self):
        """Update inverse kinematics calculation."""
        try:
            with self.update_lock:
                # Convert degrees to radians for kinematics
                roll_rad = np.radians(self.current_rotation[0])
                pitch_rad = np.radians(self.current_rotation[1]) 
                yaw_rad = np.radians(self.current_rotation[2])
                
                # Calculate leg lengths
                pose = [
                    self.current_position[0],  # X (mm)
                    self.current_position[1],  # Y (mm)
                    self.current_position[2],  # Z (mm)
                    roll_rad,                  # Roll (rad)
                    pitch_rad,                 # Pitch (rad)
                    yaw_rad                    # Yaw (rad)
                ]
                
                self.current_leg_lengths = self.kinematics.calculate(pose)
                
        except Exception as e:
            messagebox.showerror("Kinematics Error", f"Error calculating leg lengths: {str(e)}")
            # Reset to safe position
            self.reset_position()
    
    def validate_position(self, x: float, y: float, z: float) -> bool:
        """
        Validate if position is within limits.
        
        Args:
            x, y, z: Position coordinates
            
        Returns:
            True if position is valid
        """
        x_min, x_max = self.position_limits['x']
        y_min, y_max = self.position_limits['y']
        z_min, z_max = self.position_limits['z']
        
        return (x_min <= x <= x_max and 
                y_min <= y <= y_max and 
                z_min <= z <= z_max)
    
    def validate_rotation(self, roll: float, pitch: float, yaw: float) -> bool:
        """
        Validate if rotation is within limits.
        
        Args:
            roll, pitch, yaw: Rotation angles in degrees
            
        Returns:
            True if rotation is valid
        """
        roll_min, roll_max = self.rotation_limits['roll']
        pitch_min, pitch_max = self.rotation_limits['pitch']
        yaw_min, yaw_max = self.rotation_limits['yaw']
        
        return (roll_min <= roll <= roll_max and
                pitch_min <= pitch <= pitch_max and
                yaw_min <= yaw <= yaw_max)
    
    def reset_position(self):
        """Reset platform to neutral position."""
        self.current_position = [0.0, 0.0, 0.0]
        self.current_rotation = [0.0, 0.0, 0.0]
        self.update_kinematics()
        self.update_display()
    
    def start_animation(self, animation_func: callable, *args, **kwargs):
        """
        Start an animation in a separate thread.
        
        Args:
            animation_func: Function to run in animation thread
            *args, **kwargs: Arguments for animation function
        """
        if self.animation_running:
            self.stop_animation()
        
        self.animation_running = True
        self.animation_thread = threading.Thread(
            target=animation_func, args=args, kwargs=kwargs, daemon=True
        )
        self.animation_thread.start()
    
    def stop_animation(self):
        """Stop current animation."""
        self.animation_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
    
    def emergency_stop(self):
        """Emergency stop - reset everything to safe state."""
        self.stop_animation()
        self.reset_position()
        messagebox.showwarning("Emergency Stop", "Platform reset to safe position")
    
    @abstractmethod
    def update_display(self):
        """Update GUI display with current values. Must be implemented by subclasses."""
        pass
    
    def on_closing(self):
        """Handle GUI closing event."""
        self.stop_animation()
        self.root.destroy()
