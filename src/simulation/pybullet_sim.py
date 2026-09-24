#!/usr/bin/env python3
"""
PyBullet simulation interface for Stewart Platform.
Provides 3D visualization and physics simulation capabilities.
"""

import pybullet as p
import pybullet_data
import numpy as np
import time
import os
from typing import Dict, List, Tuple, Optional, Any


class PyBulletSimulator:
    """
    PyBullet-based simulator for Stewart Platform.
    
    Features:
    - 3D visualization
    - Physics simulation
    - Camera controls
    - Recording capabilities
    - Debug visualization
    """
    
    def __init__(self, urdf_path: str, gui: bool = True):
        """
        Initialize the PyBullet simulator.
        
        Args:
            urdf_path: Path to the URDF file
            gui: Whether to use GUI mode
        """
        self.urdf_path = urdf_path
        self.gui = gui
        self.physics_client = None
        self.robot_id = None
        self.plane_id = None
        self.connected = False
        
        # Simulation settings
        self.gravity = [0, 0, -9.81]
        self.time_step = 1/240
        
        # Recording
        self.recording = False
        self.recording_id = None
        
        # Camera settings
        self.camera_settings = {
            'distance': 2.0,
            'yaw': 45,
            'pitch': -30,
            'target': [0, 0, 0]
        }
        
        # Debug settings
        self.debug_display = False
        self.force_display = False
    
    def connect(self) -> bool:
        """
        Connect to PyBullet physics engine.
        
        Returns:
            True if connection successful
        """
        try:
            if self.gui:
                self.physics_client = p.connect(p.GUI)
            else:
                self.physics_client = p.connect(p.DIRECT)
            
            # Configure simulation
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.setGravity(*self.gravity)
            p.setTimeStep(self.time_step)
            p.setRealTimeSimulation(0)
            
            # Load environment
            self.plane_id = p.loadURDF("plane.urdf")
            
            # Load robot
            if os.path.exists(self.urdf_path):
                start_pos = [0, 0, 0]
                start_orientation = p.getQuaternionFromEuler([0, 0, 0])
                self.robot_id = p.loadURDF(
                    self.urdf_path, 
                    start_pos, 
                    start_orientation,
                    flags=p.URDF_USE_INERTIA_FROM_FILE
                )
            else:
                raise FileNotFoundError(f"URDF file not found: {self.urdf_path}")
            
            # Set initial camera
            self.set_camera_view('isometric')
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to PyBullet: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PyBullet."""
        if self.connected:
            if self.recording:
                self.stop_recording()
            p.disconnect()
            self.connected = False
            self.physics_client = None
            self.robot_id = None
            self.plane_id = None
    
    def step_simulation(self):
        """Step the physics simulation forward."""
        if self.connected:
            p.stepSimulation()
    
    def update_platform_pose(self, pose: Dict[str, Any]):
        """
        Update platform pose in simulation.
        
        Args:
            pose: Dictionary containing position, rotation, and leg_lengths
        """
        if not self.connected or self.robot_id is None:
            return
        
        try:
            position = pose.get('position', [0, 0, 0])
            rotation = pose.get('rotation', [0, 0, 0])  # degrees
            leg_lengths = pose.get('leg_lengths', [0] * 6)
            
            # Convert position to meters (assuming input is in mm)
            pos_m = [p / 1000.0 for p in position]
            
            # Convert rotation to radians and create quaternion
            roll_rad = np.radians(rotation[0])
            pitch_rad = np.radians(rotation[1])
            yaw_rad = np.radians(rotation[2])
            orientation = p.getQuaternionFromEuler([roll_rad, pitch_rad, yaw_rad])
            
            # Update base position and orientation
            p.resetBasePositionAndOrientation(self.robot_id, pos_m, orientation)
            
            # Update actuator lengths (if applicable)
            # This would require knowledge of joint indices from URDF
            # For now, we'll just update the main platform pose
            
        except Exception as e:
            print(f"Error updating platform pose: {e}")
    
    def set_gravity(self, gravity: List[float]):
        """
        Set gravity vector.
        
        Args:
            gravity: [x, y, z] gravity vector
        """
        if self.connected:
            self.gravity = gravity
            p.setGravity(*gravity)
    
    def set_camera_view(self, view_type: str):
        """
        Set camera to predefined view.
        
        Args:
            view_type: 'front', 'side', 'top', 'isometric'
        """
        if not self.connected:
            return
        
        views = {
            'front': {'distance': 2.0, 'yaw': 0, 'pitch': 0, 'target': [0, 0, 0]},
            'side': {'distance': 2.0, 'yaw': 90, 'pitch': 0, 'target': [0, 0, 0]},
            'top': {'distance': 2.0, 'yaw': 0, 'pitch': -90, 'target': [0, 0, 0]},
            'isometric': {'distance': 2.5, 'yaw': 45, 'pitch': -30, 'target': [0, 0, 0]}
        }
        
        if view_type in views:
            settings = views[view_type]
            self.camera_settings.update(settings)
            
            p.resetDebugVisualizerCamera(
                cameraDistance=settings['distance'],
                cameraYaw=settings['yaw'],
                cameraPitch=settings['pitch'],
                cameraTargetPosition=settings['target']
            )
    
    def set_debug_display(self, enabled: bool):
        """
        Enable/disable debug information display.
        
        Args:
            enabled: Whether to show debug info
        """
        if self.connected:
            self.debug_display = enabled
            # Toggle debug visualizer panels
            if enabled:
                p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)
            else:
                p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    
    def set_force_display(self, enabled: bool):
        """
        Enable/disable force vector display.
        
        Args:
            enabled: Whether to show force vectors
        """
        if self.connected:
            self.force_display = enabled
            # Implementation for force vector visualization would go here
            # This requires additional PyBullet debug drawing
    
    def start_recording(self, filename: Optional[str] = None) -> bool:
        """
        Start video recording.
        
        Args:
            filename: Output filename (optional)
            
        Returns:
            True if recording started successfully
        """
        if not self.connected or self.recording:
            return False
        
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"output/stewart_simulation_{timestamp}.mp4"
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            self.recording_id = p.startStateLogging(
                p.STATE_LOGGING_VIDEO_MP4, 
                filename
            )
            self.recording = True
            return True
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop video recording.
        
        Returns:
            Filename of recorded video if successful
        """
        if self.connected and self.recording and self.recording_id is not None:
            try:
                p.stopStateLogging(self.recording_id)
                self.recording = False
                filename = f"stewart_simulation_{int(time.time())}.mp4"
                self.recording_id = None
                return filename
            except Exception as e:
                print(f"Failed to stop recording: {e}")
        
        return None
    
    def get_platform_state(self) -> Dict[str, Any]:
        """
        Get current platform state from simulation.
        
        Returns:
            Dictionary with position, orientation, and velocities
        """
        if not self.connected or self.robot_id is None:
            return {}
        
        try:
            pos, orn = p.getBasePositionAndOrientation(self.robot_id)
            lin_vel, ang_vel = p.getBaseVelocity(self.robot_id)
            
            # Convert position back to mm
            pos_mm = [p * 1000.0 for p in pos]
            
            # Convert quaternion to euler angles (degrees)
            euler_rad = p.getEulerFromQuaternion(orn)
            euler_deg = [np.degrees(angle) for angle in euler_rad]
            
            return {
                'position': pos_mm,
                'rotation': euler_deg,
                'linear_velocity': list(lin_vel),
                'angular_velocity': list(ang_vel)
            }
            
        except Exception as e:
            print(f"Error getting platform state: {e}")
            return {}
    
    def get_joint_states(self) -> List[Dict[str, float]]:
        """
        Get states of all joints.
        
        Returns:
            List of joint state dictionaries
        """
        if not self.connected or self.robot_id is None:
            return []
        
        try:
            joint_states = []
            num_joints = p.getNumJoints(self.robot_id)
            
            for i in range(num_joints):
                joint_info = p.getJointInfo(self.robot_id, i)
                joint_state = p.getJointState(self.robot_id, i)
                
                joint_data = {
                    'index': i,
                    'name': joint_info[1].decode('utf-8'),
                    'type': joint_info[2],
                    'position': joint_state[0],
                    'velocity': joint_state[1],
                    'force': joint_state[3]
                }
                joint_states.append(joint_data)
            
            return joint_states
            
        except Exception as e:
            print(f"Error getting joint states: {e}")
            return []
    
    def reset_simulation(self):
        """Reset simulation to initial state."""
        if self.connected and self.robot_id is not None:
            # Reset platform to initial pose
            start_pos = [0, 0, 0]
            start_orientation = p.getQuaternionFromEuler([0, 0, 0])
            p.resetBasePositionAndOrientation(self.robot_id, start_pos, start_orientation)
            
            # Reset velocities
            p.resetBaseVelocity(self.robot_id, [0, 0, 0], [0, 0, 0])
    
    def apply_external_force(self, force: List[float], position: List[float]):
        """
        Apply external force to the platform.
        
        Args:
            force: [x, y, z] force vector in Newtons
            position: [x, y, z] position to apply force (local coordinates)
        """
        if self.connected and self.robot_id is not None:
            p.applyExternalForce(
                self.robot_id, 
                -1,  # Apply to base link
                force, 
                position, 
                p.WORLD_FRAME
            )
    
    def get_contact_info(self) -> List[Dict[str, Any]]:
        """
        Get contact information between platform and environment.
        
        Returns:
            List of contact point dictionaries
        """
        if not self.connected or self.robot_id is None:
            return []
        
        try:
            contacts = p.getContactPoints(bodyA=self.robot_id)
            contact_info = []
            
            for contact in contacts:
                contact_data = {
                    'body_a': contact[1],
                    'body_b': contact[2],
                    'link_a': contact[3],
                    'link_b': contact[4],
                    'position': contact[5],
                    'normal': contact[7],
                    'distance': contact[8],
                    'normal_force': contact[9]
                }
                contact_info.append(contact_data)
            
            return contact_info
            
        except Exception as e:
            print(f"Error getting contact info: {e}")
            return []


def main():
    """Test the PyBullet simulator."""
    # Test basic functionality
    sim = PyBulletSimulator("simulation/urdf/Stewart.urdf")
    
    if sim.connect():
        print("Simulator connected successfully")
        
        # Test pose update
        test_pose = {
            'position': [10, 10, 20],
            'rotation': [5, 5, 10],
            'leg_lengths': [100] * 6
        }
        
        sim.update_platform_pose(test_pose)
        
        # Run simulation for a few seconds
        for i in range(1000):
            sim.step_simulation()
            time.sleep(1/240)
        
        sim.disconnect()
        print("Simulator test completed")
    else:
        print("Failed to connect simulator")


if __name__ == "__main__":
    main()
