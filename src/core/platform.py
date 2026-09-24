"""
Plateforme de Stewart - Simulation PyBullet
===========================================

Ce module contient la classe principale pour simuler une plateforme de Stewart
avec PyBullet, incluant la gestion de l'environnement et le contrôle des actionneurs.

Classes:
    StewartPlatform: Classe principale pour la simulation de la plateforme
"""

import pybullet as p
import time
import pybullet_data
import os
import numpy as np
from typing import List, Tuple, Union, Optional
from ..core.kinematics import InverseKinematics


# Correspondance avec simulation/urdf/Stewart.urdf (voir docs/experiments/EXP-002).
# Paires de liens fermant les boucles des jambes 1 à 5 (la jambe 6 est fermée par l'arbre URDF).
DEFAULT_JOINT_INDICES = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
# Joints prismatiques Slider_13..Slider_18 = jambes 1 à 6, dans l'ordre des longueurs
# renvoyées par InverseKinematics.solve().
DEFAULT_ACTUATOR_INDICES = [2, 31, 45, 38, 24, 9]


class StewartPlatform:
    """
    Classe principale pour la simulation d'une plateforme de Stewart avec PyBullet.
    
    Cette classe gère la simulation physique, le chargement du modèle URDF,
    et le contrôle des actionneurs linéaires.
    
    Attributs:
        path (str): Chemin vers le fichier URDF
        joint_indices (List): Indices des joints dans le modèle URDF
        actuator_indices (List): Indices des actionneurs linéaires
        design_variables (List): Variables de design [r_P, r_B, gamma_P, gamma_B]
        robot_id (int): ID du robot dans PyBullet
        kinematics (InverseKinematics): Instance de cinématique inverse
        l (np.ndarray): Longueurs actuelles des vérins
    """
    
    def __init__(self, urdf_path: str, joint_indices: List[Tuple[int, int]], 
                 actuator_indices: List[int], design_variables: List[float]) -> None:
        """
        Initialise la plateforme de Stewart.
        
        Args:
            urdf_path: Chemin vers le fichier URDF du modèle
            joint_indices: Liste des indices de joints [(joint1, joint2), ...]
            actuator_indices: Liste des indices des actionneurs linéaires
            design_variables: [radius_platform, radius_base, gamma_platform, gamma_base]
        """
        self.path = urdf_path
        self.joint_indices = joint_indices
        self.actuator_indices = actuator_indices
        self.design_variables = design_variables
        
        # Variables de simulation
        self.robot_id: Optional[int] = None
        self.physics_client: Optional[int] = None
        self.prev_target = np.zeros(len(actuator_indices))
        
        # Initialiser la cinématique inverse
        r_P, r_B, gamma_P, gamma_B = design_variables
        self.kinematics = InverseKinematics(r_B, r_P, gamma_B, gamma_P)
        
        # Position initiale des vérins
        self.l = np.full(len(actuator_indices), 0.173205)  # Longueur initiale
        
    def setup_environment(self, use_gui: bool = False, 
                         gui_options: str = "--width=1280 --height=720") -> bool:
        """
        Configure l'environnement PyBullet.
        
        Args:
            use_gui: True pour utiliser l'interface graphique
            gui_options: Options pour la fenêtre GUI
            
        Returns:
            True si la connexion a réussi, False sinon
        """
        try:
            # Configuration des variables d'environnement pour la stabilité
            if use_gui:
                os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
                os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            
            # Tentative de connexion
            if use_gui:
                try:
                    self.physics_client = p.connect(p.GUI, options=gui_options)
                    print("✅ Connected to PyBullet GUI")
                    
                    # Configuration de l'affichage
                    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)
                    p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1)
                    p.configureDebugVisualizer(p.COV_ENABLE_WIREFRAME, 0)
                    
                except Exception as e:
                    print(f"⚠️ GUI connection failed ({e}), using DIRECT mode")
                    self.physics_client = p.connect(p.DIRECT)
            else:
                self.physics_client = p.connect(p.DIRECT)
                print("✅ Connected to PyBullet DIRECT mode")
            
            # Configuration de base de PyBullet
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.setGravity(0, 0, -9.81)
            
            # Charger le plan de base
            plane_id = p.loadURDF("plane.urdf")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup PyBullet environment: {e}")
            return False
    
    def load_robot(self, position: List[float] = [0, 0, 0], 
                   orientation: List[float] = [0, 0, 0]) -> bool:
        """
        Charge le modèle URDF de la plateforme de Stewart.
        
        Args:
            position: Position initiale [x, y, z]
            orientation: Orientation initiale [roll, pitch, yaw] en radians
            
        Returns:
            True si le chargement a réussi, False sinon
        """
        try:
            if not os.path.exists(self.path):
                print(f"❌ URDF file not found: {self.path}")
                return False
            
            start_orientation = p.getQuaternionFromEuler(orientation)
            self.robot_id = p.loadURDF(self.path, position, start_orientation,
                                     flags=p.URDF_USE_INERTIA_FROM_FILE)
            
            print(f"✅ Robot loaded successfully with ID: {self.robot_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load robot: {e}")
            return False
    
    def setup_constraints(self) -> None:
        """Configure les contraintes de simulation pour la plateforme."""
        try:
            # Désactiver les collisions pour certains liens si nécessaire
            # Cette méthode peut être étendue selon les besoins spécifiques
            pass
        except Exception as e:
            print(f"⚠️ Warning in constraint setup: {e}")
    
    def initialize_platform(self, verbose: bool = True) -> bool:
        """
        Initialise complètement la plateforme (environnement + robot + contraintes).
        
        Args:
            verbose: True pour afficher les messages de débogage
            
        Returns:
            True si l'initialisation a réussi, False sinon
        """
        success = True
        
        if verbose:
            print("🚀 Initializing Stewart Platform...")
        
        # Charger le robot
        if not self.load_robot():
            success = False
        
        # Configurer les contraintes
        self.setup_constraints()
        
        if verbose and success:
            print("✅ Stewart Platform initialized successfully")
        elif verbose:
            print("❌ Stewart Platform initialization failed")
            
        return success
    
    def control_linear_actuators(self, delta_lengths: Union[List[float], np.ndarray], 
                               duration: float = 1.0, frequency: float = 240) -> None:
        """
        Contrôle les actionneurs linéaires pour modifier les longueurs des vérins.
        
        Args:
            delta_lengths: Changements de longueur pour chaque vérin
            duration: Durée du mouvement en secondes
            frequency: Fréquence de simulation en Hz
        """
        if self.robot_id is None:
            print("❌ Robot not loaded. Call initialize_platform() first.")
            return
        
        try:
            delta_lengths = np.array(delta_lengths)
            
            if len(delta_lengths) != len(self.actuator_indices):
                print(f"❌ Expected {len(self.actuator_indices)} delta lengths, got {len(delta_lengths)}")
                return
            
            # Calculer les nouvelles longueurs cibles
            new_targets = self.prev_target + delta_lengths
            
            # Nombre d'étapes pour le mouvement
            steps = int(duration * frequency)
            
            # Interpolation linéaire entre les positions actuelles et cibles
            for step in range(steps):
                alpha = step / steps
                current_positions = self.prev_target + alpha * delta_lengths
                
                # Appliquer les positions aux actionneurs
                for i, actuator_id in enumerate(self.actuator_indices):
                    p.setJointMotorControl2(
                        bodyIndex=self.robot_id,
                        jointIndex=actuator_id,
                        controlMode=p.POSITION_CONTROL,
                        targetPosition=current_positions[i],
                        force=1000  # Force maximale
                    )
                
                # Avancer la simulation
                p.stepSimulation()
                time.sleep(1.0 / frequency)
            
            # Mettre à jour les positions précédentes
            self.prev_target = new_targets
            self.l += delta_lengths
            
        except Exception as e:
            print(f"❌ Error controlling actuators: {e}")
    
    def move_to_pose(self, translation: Union[List[float], np.ndarray], 
                     rotation: Union[List[float], np.ndarray], 
                     duration: float = 1.0) -> None:
        """
        Déplace la plateforme vers une pose spécifiée.
        
        Args:
            translation: Translation [x, y, z] en mètres
            rotation: Rotation [roll, pitch, yaw] en degrés
            duration: Durée du mouvement en secondes
        """
        try:
            # Calculer les longueurs de vérins nécessaires
            target_lengths = self.kinematics.solve(translation, rotation)
            
            # Calculer les changements nécessaires
            delta_lengths = target_lengths - self.l
            
            # Contrôler les actionneurs
            self.control_linear_actuators(delta_lengths, duration)
            
        except Exception as e:
            print(f"❌ Error moving to pose: {e}")
    
    def get_current_pose(self) -> Tuple[List[float], List[float]]:
        """
        Obtient la pose actuelle de la plateforme.
        
        Returns:
            Tuple (position, orientation) où orientation est en degrés
        """
        if self.robot_id is None:
            return ([0, 0, 0], [0, 0, 0])
        
        try:
            position, orientation_quat = p.getBasePositionAndOrientation(self.robot_id)
            orientation_euler = p.getEulerFromQuaternion(orientation_quat)
            orientation_degrees = [np.rad2deg(angle) for angle in orientation_euler]
            
            return (list(position), orientation_degrees)
            
        except Exception as e:
            print(f"❌ Error getting current pose: {e}")
            return ([0, 0, 0], [0, 0, 0])
    
    def run_simulation_step(self) -> None:
        """Exécute une étape de simulation."""
        if self.physics_client is not None:
            p.stepSimulation()
    
    def disconnect(self) -> None:
        """Déconnecte PyBullet proprement."""
        try:
            if self.physics_client is not None:
                p.disconnect()
                self.physics_client = None
                print("🔌 PyBullet disconnected properly")
        except Exception as e:
            print(f"⚠️ Warning during disconnect: {e}")
    
    def __del__(self):
        """Destructeur pour s'assurer que PyBullet est déconnecté."""
        self.disconnect()


# Alias pour compatibilité avec l'ancien code
def clear_screen():
    """Efface l'écran (fonction utilitaire)."""
    os.system('cls' if os.name == 'nt' else 'clear')
