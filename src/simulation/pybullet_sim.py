#!/usr/bin/env python3
"""
PyBullet simulation interface for Stewart Platform.
Provides 3D visualization and physics simulation capabilities.

Le mécanisme est simulé par ``StewartPlatform`` (géométrie identifiée dans le URDF,
boucles fermées, vérins asservis en position, EXP-004) : ce module n'ajoute que
l'interface attendue par les GUI (caméra, enregistrement, forces, état).

Convention des poses (``update_platform_pose`` / ``get_platform_state``) :
position en mm et rotation [roll, pitch, yaw] en degrés, **relatives à la position de
travail** (``DEFAULT_WORKING_HEIGHT`` au-dessus de la pose neutre, vérins à mi-course).
"""

import pybullet as p
import pybullet_data
import numpy as np
import time
import os
from typing import Dict, List, Tuple, Optional, Any

from ..core.platform import StewartPlatform, DEFAULT_WORKING_HEIGHT


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
        self.platform: Optional[StewartPlatform] = None
        self.working_height = DEFAULT_WORKING_HEIGHT
        self.last_command_reachable = True
        
        # Simulation settings
        self.gravity = [0, 0, -9.81]
        self.time_step = 1/240
        
        # Recording
        self.recording = False
        self.recording_id = None
        self.recording_filename: Optional[str] = None
        
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
            if not os.path.exists(self.urdf_path):
                raise FileNotFoundError(f"URDF file not found: {self.urdf_path}")
            # Géométrie identifiée (ouvre et ferme son propre client PyBullet)
            self.platform = StewartPlatform.from_urdf(self.urdf_path)

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
            
            # Robot : base fixe, boucles fermées, puis montée à la position de travail.
            # platform.physics_client reste None : la connexion appartient au simulateur.
            if not self.platform.load_robot():
                raise RuntimeError(f"Failed to load URDF: {self.urdf_path}")
            self.platform.setup_constraints()
            self.robot_id = self.platform.robot_id
            self._go_to_working_position()
            
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
            self.platform = None
    
    def step_simulation(self, steps: int = 1):
        """
        Step the physics simulation forward.

        Args:
            steps: Nombre de pas de ``time_step`` à effectuer (4 pas à 60 Hz = temps réel)
        """
        if self.connected:
            for _ in range(steps):
                p.stepSimulation()

    def _go_to_working_position(self):
        """Monte la plateforme à la position de travail (calcul au plus vite, sans attente)."""
        self.platform.move_to_working_position(self.working_height, duration=1.0,
                                               realtime=False, settle_time=0.5)
    
    def update_platform_pose(self, pose: Dict[str, Any]):
        """
        Command a platform pose: sets the actuator targets, the motion happens
        over the following ``step_simulation`` calls.
        
        Args:
            pose: Dictionary containing position (mm) and rotation (degrees), relative to
                  the working position. ``leg_lengths`` is ignored: the actuator targets
                  come from the identified inverse kinematics.
        """
        if not self.connected or self.platform is None:
            return
        
        try:
            position = pose.get('position', [0, 0, 0])
            rotation = pose.get('rotation', [0, 0, 0])  # degrees
            
            translation = np.asarray(position, dtype=float) / 1000.0 + [0, 0, self.working_height]
            self.last_command_reachable = self.platform.command_pose(translation, rotation)
            
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
            self.recording_filename = filename
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
                filename = self.recording_filename
                self.recording_id = None
                self.recording_filename = None
                return filename
            except Exception as e:
                print(f"Failed to stop recording: {e}")
        
        return None
    
    def get_platform_state(self) -> Dict[str, Any]:
        """
        Get current state of the moving platform, measured in the simulation.
        
        Returns:
            Dictionary with position (mm) and rotation (degrees) relative to the working
            position (same convention as ``update_platform_pose``), linear (m/s) and
            angular (rad/s) velocities of the platform link, actuator positions (m) and
            whether the last commanded pose was reachable
        """
        if not self.connected or self.platform is None:
            return {}
        
        try:
            position, rotation = self.platform.get_current_pose()
            pos_mm = ((np.array(position) - [0, 0, self.working_height]) * 1000.0).tolist()
            link_state = p.getLinkState(self.robot_id, self.platform.platform_link,
                                        computeLinkVelocity=1)
            
            return {
                'position': pos_mm,
                'rotation': list(rotation),
                'linear_velocity': list(link_state[6]),
                'angular_velocity': list(link_state[7]),
                'actuator_positions': [p.getJointState(self.robot_id, j)[0]
                                       for j in self.platform.actuator_indices],
                'reachable': self.last_command_reachable
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
        """Reset simulation: neutral configuration, then back to the working position."""
        if self.connected and self.platform is not None:
            self.platform.reset_to_neutral()
            self.last_command_reachable = True
            self._go_to_working_position()
    
    def apply_external_force(self, force: List[float], position: List[float]):
        """
        Apply external force to the moving platform, for the next simulation step.
        
        Args:
            force: [x, y, z] force vector in Newtons (world frame)
            position: [x, y, z] application point (world frame, m)
        """
        if self.connected and self.platform is not None:
            p.applyExternalForce(
                self.robot_id, 
                self.platform.platform_link,
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
        
        # Test pose update (mm / degrees, relative to the working position)
        test_pose = {'position': [10, 10, 20], 'rotation': [5, 5, 10]}
        sim.update_platform_pose(test_pose)
        
        # Run simulation for a few seconds
        for i in range(1000):
            sim.step_simulation()
            time.sleep(1/240)
        
        state = sim.get_platform_state()
        print(f"Platform pose: {np.round(state['position'], 2)} mm, "
              f"{np.round(state['rotation'], 2)} deg")
        
        sim.disconnect()
        print("Simulator test completed")
    else:
        print("Failed to connect simulator")


if __name__ == "__main__":
    main()
