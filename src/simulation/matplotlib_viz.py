#!/usr/bin/env python3
"""
Matplotlib-based visualization for Stewart Platform.
Provides 2D and 3D plotting capabilities for analysis and monitoring.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import time


class MatplotlibVisualizer:
    """
    Matplotlib-based visualizer for Stewart Platform.
    
    Features:
    - Real-time plotting
    - 3D platform visualization
    - Trajectory plotting
    - Performance analysis charts
    - Animation capabilities
    """
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """
        Initialize the visualizer.
        
        Args:
            figsize: Figure size (width, height)
        """
        self.figsize = figsize
        self.fig = None
        self.axes = {}
        self.lines = {}
        self.data_history = {
            'time': [],
            'position': {'x': [], 'y': [], 'z': []},
            'rotation': {'roll': [], 'pitch': [], 'yaw': []},
            'leg_lengths': [[] for _ in range(6)]
        }
        self.max_history = 1000  # Maximum data points to keep
        
        # Animation
        self.animation_active = False
        self.anim = None
        
        # Setup matplotlib
        plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
    
    def setup_realtime_plot(self, subplot_layout: str = '2x2') -> bool:
        """
        Setup real-time plotting interface.
        
        Args:
            subplot_layout: Layout of subplots ('2x2', '3x2', etc.)
            
        Returns:
            True if setup successful
        """
        try:
            self.fig = plt.figure(figsize=self.figsize)
            self.fig.suptitle('Stewart Platform - Real-time Monitoring', fontsize=16, fontweight='bold')
            
            if subplot_layout == '2x2':
                # Position plot
                self.axes['position'] = plt.subplot(2, 2, 1)
                self.axes['position'].set_title('Position (mm)')
                self.axes['position'].set_xlabel('Time (s)')
                self.axes['position'].set_ylabel('Position (mm)')
                self.axes['position'].grid(True)
                
                # Rotation plot
                self.axes['rotation'] = plt.subplot(2, 2, 2)
                self.axes['rotation'].set_title('Rotation (degrees)')
                self.axes['rotation'].set_xlabel('Time (s)')
                self.axes['rotation'].set_ylabel('Angle (°)')
                self.axes['rotation'].grid(True)
                
                # Leg lengths plot
                self.axes['legs'] = plt.subplot(2, 2, 3)
                self.axes['legs'].set_title('Leg Lengths (mm)')
                self.axes['legs'].set_xlabel('Time (s)')
                self.axes['legs'].set_ylabel('Length (mm)')
                self.axes['legs'].grid(True)
                
                # 3D workspace plot
                self.axes['3d'] = plt.subplot(2, 2, 4, projection='3d')
                self.axes['3d'].set_title('3D Workspace')
                self.axes['3d'].set_xlabel('X (mm)')
                self.axes['3d'].set_ylabel('Y (mm)')
                self.axes['3d'].set_zlabel('Z (mm)')
            
            # Initialize empty lines
            self._initialize_lines()
            
            plt.tight_layout()
            return True
            
        except Exception as e:
            print(f"Error setting up real-time plot: {e}")
            return False
    
    def _initialize_lines(self):
        """Initialize empty plot lines."""
        # Position lines
        if 'position' in self.axes:
            self.lines['pos_x'], = self.axes['position'].plot([], [], 'r-', label='X', linewidth=2)
            self.lines['pos_y'], = self.axes['position'].plot([], [], 'g-', label='Y', linewidth=2)
            self.lines['pos_z'], = self.axes['position'].plot([], [], 'b-', label='Z', linewidth=2)
            self.axes['position'].legend()
        
        # Rotation lines
        if 'rotation' in self.axes:
            self.lines['rot_roll'], = self.axes['rotation'].plot([], [], 'r-', label='Roll', linewidth=2)
            self.lines['rot_pitch'], = self.axes['rotation'].plot([], [], 'g-', label='Pitch', linewidth=2)
            self.lines['rot_yaw'], = self.axes['rotation'].plot([], [], 'b-', label='Yaw', linewidth=2)
            self.axes['rotation'].legend()
        
        # Leg length lines
        if 'legs' in self.axes:
            colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown']
            self.lines['legs'] = []
            for i in range(6):
                line, = self.axes['legs'].plot([], [], color=colors[i], 
                                             label=f'Leg {i+1}', linewidth=1.5)
                self.lines['legs'].append(line)
            self.axes['legs'].legend()
        
        # 3D platform representation
        if '3d' in self.axes:
            self.lines['platform_base'], = self.axes['3d'].plot([], [], [], 'ko-', 
                                                               markersize=8, linewidth=3, label='Base')
            self.lines['platform_top'], = self.axes['3d'].plot([], [], [], 'ro-', 
                                                              markersize=8, linewidth=3, label='Platform')
            self.lines['legs_3d'] = []
            for i in range(6):
                line, = self.axes['3d'].plot([], [], [], 'b-', linewidth=2, alpha=0.7)
                self.lines['legs_3d'].append(line)
    
    def update_data(self, timestamp: float, position: List[float], 
                   rotation: List[float], leg_lengths: List[float]):
        """
        Update data history with new measurements.
        
        Args:
            timestamp: Current timestamp
            position: [x, y, z] position in mm
            rotation: [roll, pitch, yaw] rotation in degrees
            leg_lengths: List of 6 leg lengths in mm
        """
        # Add new data
        self.data_history['time'].append(timestamp)
        self.data_history['position']['x'].append(position[0])
        self.data_history['position']['y'].append(position[1])
        self.data_history['position']['z'].append(position[2])
        self.data_history['rotation']['roll'].append(rotation[0])
        self.data_history['rotation']['pitch'].append(rotation[1])
        self.data_history['rotation']['yaw'].append(rotation[2])
        
        for i, length in enumerate(leg_lengths[:6]):
            self.data_history['leg_lengths'][i].append(length)
        
        # Limit history size
        if len(self.data_history['time']) > self.max_history:
            self.data_history['time'] = self.data_history['time'][-self.max_history:]
            for key in self.data_history['position']:
                self.data_history['position'][key] = self.data_history['position'][key][-self.max_history:]
            for key in self.data_history['rotation']:
                self.data_history['rotation'][key] = self.data_history['rotation'][key][-self.max_history:]
            for i in range(6):
                self.data_history['leg_lengths'][i] = self.data_history['leg_lengths'][i][-self.max_history:]
    
    def update_plots(self):
        """Update all plots with current data."""
        if not self.fig or not self.data_history['time']:
            return
        
        time_data = self.data_history['time']
        
        # Update position plots
        if 'position' in self.axes and len(time_data) > 0:
            self.lines['pos_x'].set_data(time_data, self.data_history['position']['x'])
            self.lines['pos_y'].set_data(time_data, self.data_history['position']['y'])
            self.lines['pos_z'].set_data(time_data, self.data_history['position']['z'])
            
            self.axes['position'].relim()
            self.axes['position'].autoscale_view()
        
        # Update rotation plots
        if 'rotation' in self.axes and len(time_data) > 0:
            self.lines['rot_roll'].set_data(time_data, self.data_history['rotation']['roll'])
            self.lines['rot_pitch'].set_data(time_data, self.data_history['rotation']['pitch'])
            self.lines['rot_yaw'].set_data(time_data, self.data_history['rotation']['yaw'])
            
            self.axes['rotation'].relim()
            self.axes['rotation'].autoscale_view()
        
        # Update leg length plots
        if 'legs' in self.axes and len(time_data) > 0:
            for i, line in enumerate(self.lines['legs']):
                if i < len(self.data_history['leg_lengths']):
                    line.set_data(time_data, self.data_history['leg_lengths'][i])
            
            self.axes['legs'].relim()
            self.axes['legs'].autoscale_view()
        
        # Update 3D platform visualization
        self._update_3d_platform()
        
        # Refresh display
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def _update_3d_platform(self):
        """Update 3D platform visualization."""
        if '3d' not in self.axes or not self.data_history['time']:
            return
        
        # Get latest position and rotation
        latest_pos = [
            self.data_history['position']['x'][-1] if self.data_history['position']['x'] else 0,
            self.data_history['position']['y'][-1] if self.data_history['position']['y'] else 0,
            self.data_history['position']['z'][-1] if self.data_history['position']['z'] else 0
        ]
        
        latest_rot = [
            self.data_history['rotation']['roll'][-1] if self.data_history['rotation']['roll'] else 0,
            self.data_history['rotation']['pitch'][-1] if self.data_history['rotation']['pitch'] else 0,
            self.data_history['rotation']['yaw'][-1] if self.data_history['rotation']['yaw'] else 0
        ]
        
        # Define platform geometry (simplified hexagonal platform)
        base_radius = 200  # mm
        platform_radius = 200  # mm
        
        # Base points (fixed)
        base_angles = np.linspace(0, 2*np.pi, 7)  # 6 points + closing point
        base_x = base_radius * np.cos(base_angles)
        base_y = base_radius * np.sin(base_angles)
        base_z = np.zeros_like(base_x)
        
        # Platform points (transformed)
        platform_angles = np.linspace(0, 2*np.pi, 7)
        platform_x_local = platform_radius * np.cos(platform_angles)
        platform_y_local = platform_radius * np.sin(platform_angles)
        platform_z_local = np.zeros_like(platform_x_local)
        
        # Apply rotation and translation to platform
        # Simplified transformation (for visualization purposes)
        roll_rad = np.radians(latest_rot[0])
        pitch_rad = np.radians(latest_rot[1])
        yaw_rad = np.radians(latest_rot[2])
        
        # Apply rotation (simplified - just yaw for now)
        platform_x = platform_x_local * np.cos(yaw_rad) - platform_y_local * np.sin(yaw_rad) + latest_pos[0]
        platform_y = platform_x_local * np.sin(yaw_rad) + platform_y_local * np.cos(yaw_rad) + latest_pos[1]
        platform_z = platform_z_local + latest_pos[2] + 150  # Offset for visualization
        
        # Update base and platform lines
        if 'platform_base' in self.lines:
            self.lines['platform_base'].set_data_3d(base_x, base_y, base_z)
        if 'platform_top' in self.lines:
            self.lines['platform_top'].set_data_3d(platform_x, platform_y, platform_z)
        
        # Update leg lines (connect base to platform points)
        if 'legs_3d' in self.lines:
            for i, line in enumerate(self.lines['legs_3d']):
                if i < 6:  # Only first 6 points (excluding closing point)
                    leg_x = [base_x[i], platform_x[i]]
                    leg_y = [base_y[i], platform_y[i]]
                    leg_z = [base_z[i], platform_z[i]]
                    line.set_data_3d(leg_x, leg_y, leg_z)
        
        # Auto-scale 3D plot
        self.axes['3d'].auto_scale_xyz(base_x, base_y, np.concatenate([base_z, platform_z]))
    
    def start_animation(self, interval: int = 100):
        """
        Start animated real-time plotting.
        
        Args:
            interval: Animation update interval in milliseconds
        """
        if self.fig and not self.animation_active:
            self.animation_active = True
            self.anim = animation.FuncAnimation(
                self.fig, self._animation_update, interval=interval, blit=False
            )
            plt.show(block=False)
    
    def stop_animation(self):
        """Stop animated plotting."""
        if self.anim:
            self.anim.event_source.stop()
            self.animation_active = False
    
    def _animation_update(self, frame):
        """Animation update function."""
        self.update_plots()
        return list(self.lines.values())
    
    def plot_trajectory(self, trajectory_data: Dict[str, List], title: str = "Platform Trajectory"):
        """
        Plot a complete trajectory.
        
        Args:
            trajectory_data: Dictionary with 'position' and 'rotation' data
            title: Plot title
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        time_data = trajectory_data.get('time', range(len(trajectory_data['position'])))
        positions = trajectory_data['position']
        rotations = trajectory_data['rotation']
        
        # Position plot
        axes[0, 0].plot([p[0] for p in positions], label='X', linewidth=2)
        axes[0, 0].plot([p[1] for p in positions], label='Y', linewidth=2)
        axes[0, 0].plot([p[2] for p in positions], label='Z', linewidth=2)
        axes[0, 0].set_title('Position vs Time')
        axes[0, 0].set_xlabel('Time Step')
        axes[0, 0].set_ylabel('Position (mm)')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Rotation plot
        axes[0, 1].plot([r[0] for r in rotations], label='Roll', linewidth=2)
        axes[0, 1].plot([r[1] for r in rotations], label='Pitch', linewidth=2)
        axes[0, 1].plot([r[2] for r in rotations], label='Yaw', linewidth=2)
        axes[0, 1].set_title('Rotation vs Time')
        axes[0, 1].set_xlabel('Time Step')
        axes[0, 1].set_ylabel('Angle (degrees)')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # XY trajectory
        axes[1, 0].plot([p[0] for p in positions], [p[1] for p in positions], 'b-', linewidth=2)
        axes[1, 0].plot(positions[0][0], positions[0][1], 'go', markersize=10, label='Start')
        axes[1, 0].plot(positions[-1][0], positions[-1][1], 'ro', markersize=10, label='End')
        axes[1, 0].set_title('XY Trajectory')
        axes[1, 0].set_xlabel('X (mm)')
        axes[1, 0].set_ylabel('Y (mm)')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        axes[1, 0].axis('equal')
        
        # 3D trajectory
        ax_3d = fig.add_subplot(2, 2, 4, projection='3d')
        x_data = [p[0] for p in positions]
        y_data = [p[1] for p in positions]
        z_data = [p[2] for p in positions]
        
        ax_3d.plot(x_data, y_data, z_data, 'b-', linewidth=2)
        ax_3d.scatter(x_data[0], y_data[0], z_data[0], color='green', s=100, label='Start')
        ax_3d.scatter(x_data[-1], y_data[-1], z_data[-1], color='red', s=100, label='End')
        ax_3d.set_title('3D Trajectory')
        ax_3d.set_xlabel('X (mm)')
        ax_3d.set_ylabel('Y (mm)')
        ax_3d.set_zlabel('Z (mm)')
        ax_3d.legend()
        
        plt.tight_layout()
        plt.show()
    
    def plot_workspace_analysis(self, workspace_data: Dict[str, Any]):
        """
        Plot workspace analysis results.
        
        Args:
            workspace_data: Dictionary containing workspace analysis data
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle('Stewart Platform Workspace Analysis', fontsize=16, fontweight='bold')
        
        # Reachable positions
        if 'reachable_positions' in workspace_data:
            positions = workspace_data['reachable_positions']
            x_data = [p[0] for p in positions]
            y_data = [p[1] for p in positions]
            z_data = [p[2] for p in positions]
            
            axes[0, 0].scatter(x_data, y_data, alpha=0.6, s=1)
            axes[0, 0].set_title('Reachable Workspace (XY)')
            axes[0, 0].set_xlabel('X (mm)')
            axes[0, 0].set_ylabel('Y (mm)')
            axes[0, 0].grid(True)
            axes[0, 0].axis('equal')
            
            axes[0, 1].scatter(x_data, z_data, alpha=0.6, s=1)
            axes[0, 1].set_title('Reachable Workspace (XZ)')
            axes[0, 1].set_xlabel('X (mm)')
            axes[0, 1].set_ylabel('Z (mm)')
            axes[0, 1].grid(True)
        
        # Leg length distribution
        if 'leg_length_ranges' in workspace_data:
            ranges = workspace_data['leg_length_ranges']
            legs = [f'Leg {i+1}' for i in range(len(ranges))]
            min_lengths = [r[0] for r in ranges]
            max_lengths = [r[1] for r in ranges]
            
            x_pos = np.arange(len(legs))
            width = 0.35
            
            axes[1, 0].bar(x_pos - width/2, min_lengths, width, label='Min Length', alpha=0.8)
            axes[1, 0].bar(x_pos + width/2, max_lengths, width, label='Max Length', alpha=0.8)
            axes[1, 0].set_title('Leg Length Ranges')
            axes[1, 0].set_xlabel('Leg')
            axes[1, 0].set_ylabel('Length (mm)')
            axes[1, 0].set_xticks(x_pos)
            axes[1, 0].set_xticklabels(legs)
            axes[1, 0].legend()
            axes[1, 0].grid(True)
        
        # Performance metrics
        if 'performance_metrics' in workspace_data:
            metrics = workspace_data['performance_metrics']
            metric_names = list(metrics.keys())
            metric_values = list(metrics.values())
            
            axes[1, 1].bar(metric_names, metric_values, alpha=0.8)
            axes[1, 1].set_title('Performance Metrics')
            axes[1, 1].set_ylabel('Value')
            axes[1, 1].grid(True)
            plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.show()
    
    def save_plot(self, filename: str, dpi: int = 300):
        """
        Save current plot to file.
        
        Args:
            filename: Output filename
            dpi: Resolution in dots per inch
        """
        if self.fig:
            self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')
            print(f"Plot saved to {filename}")
    
    def clear_data(self):
        """Clear all stored data history."""
        self.data_history = {
            'time': [],
            'position': {'x': [], 'y': [], 'z': []},
            'rotation': {'roll': [], 'pitch': [], 'yaw': []},
            'leg_lengths': [[] for _ in range(6)]
        }
    
    def close(self):
        """Close all matplotlib windows."""
        if self.fig:
            plt.close(self.fig)
            self.fig = None
        plt.close('all')


def demo_visualization():
    """Demonstrate the visualization capabilities."""
    import math
    
    # Create visualizer
    viz = MatplotlibVisualizer()
    viz.setup_realtime_plot()
    
    # Generate sample trajectory data
    t_max = 10  # seconds
    dt = 0.1
    time_points = np.arange(0, t_max, dt)
    
    trajectory_data = {
        'time': time_points.tolist(),
        'position': [],
        'rotation': []
    }
    
    for t in time_points:
        # Generate sinusoidal motion
        x = 30 * math.sin(t * 0.5)
        y = 20 * math.cos(t * 0.3)
        z = 15 * math.sin(t * 0.8)
        
        roll = 10 * math.sin(t * 0.4)
        pitch = 8 * math.cos(t * 0.6)
        yaw = 15 * math.sin(t * 0.2)
        
        trajectory_data['position'].append([x, y, z])
        trajectory_data['rotation'].append([roll, pitch, yaw])
        
        # Simulate leg lengths (simplified)
        base_length = 200
        leg_lengths = [base_length + 20 * math.sin(t + i * math.pi/3) for i in range(6)]
        
        # Update visualizer
        viz.update_data(t, [x, y, z], [roll, pitch, yaw], leg_lengths)
        viz.update_plots()
        
        time.sleep(0.05)  # Simulate real-time updates
    
    # Plot complete trajectory
    viz.plot_trajectory(trajectory_data, "Demo Trajectory")
    
    input("Press Enter to close...")
    viz.close()


if __name__ == "__main__":
    demo_visualization()
