# Description: Version physique de la plateforme Stewart
from motor_controller import MotorController
from inv_kinematics import inv_kinematics as ik
import numpy as np
import time

class PhysicalStewartPlatform:
    """
    Version physique de la plateforme Stewart
    Utilise des moteurs réels au lieu de PyBullet
    """
    def __init__(self, design_variable, motor_config):
        self.design_variable = design_variable
        self.motor_config = motor_config
        
        # Initialisation du contrôleur moteur
        self.motor_controller = MotorController(
            motor_pins=motor_config['motor_pins'],
            encoder_pins=motor_config['encoder_pins'],
            motor_specs=motor_config['specs']
        )
        
        # Variables de cinématique
        self.clf = None
        self.l = None  # Longueurs initiales des vérins
        self.current_leg_lengths = np.zeros(6)
        
    def initialize_platform(self):
        """Initialise la plateforme physique"""
        print("Initializing physical Stewart Platform...")
        
        # Initialisation des moteurs
        self.motor_controller.initialize_motors()
        
        # Initialisation de la cinématique inverse
        r_P, r_B, gama_P, gama_B = self.design_variable
        self.clf = ik(r_P, r_B, gama_P, gama_B)
        
        # Calcul des longueurs initiales (position home)
        translation = np.array([0, 0, 0])
        rotation = np.array([0, 0, 0])
        self.l = self.clf.solve(translation, rotation)
        
        # Retour à la position home
        self.motor_controller.home_all_motors()
        self.current_leg_lengths = self.l.copy()
        
        print("Platform initialized successfully")
    
    def move_to_pose(self, translation, rotation, duration=2.0):
        """
        Déplace la plateforme vers une pose donnée
        Remplace linear_actuator() de la simulation
        """
        try:
            # 1. Calcul des longueurs de vérins nécessaires
            target_lengths = self.clf.solve(translation, rotation)
            
            # 2. Calcul des déplacements relatifs
            length_changes = target_lengths - self.current_leg_lengths
            
            # 3. Conversion en positions moteur (dépend de votre mécanisme)
            # Exemple: vis à pas de 2mm, 1 tour = 2mm déplacement
            motor_positions = length_changes * 1000 / 2  # mm → tours moteur
            
            # 4. Déplacement des moteurs
            print(f"Moving to pose: T={translation}, R={rotation}")
            print(f"Target lengths: {target_lengths}")
            print(f"Length changes: {length_changes}")
            
            self.motor_controller.move_to_position(motor_positions)
            
            # 5. Attendre la fin du mouvement
            time.sleep(duration)
            
            # 6. Mise à jour de l'état
            self.current_leg_lengths = target_lengths.copy()
            
            print("Movement completed")
            
        except Exception as e:
            print(f"Error during movement: {e}")
            self.motor_controller.emergency_stop()
    
    def execute_trajectory(self, trajectory_data):
        """
        Exécute une trajectoire complète
        Format: [[translation, rotation, duration], ...]
        """
        print(f"Executing trajectory with {len(trajectory_data)} points")
        
        for i, (trans, rot, duration) in enumerate(trajectory_data):
            print(f"Waypoint {i+1}/{len(trajectory_data)}")
            self.move_to_pose(trans, rot, duration)
            time.sleep(0.1)  # Pause entre les points
    
    def return_home(self):
        """Retour à la position d'origine"""
        print("Returning to home position...")
        home_translation = np.array([0, 0, 0])
        home_rotation = np.array([0, 0, 0])
        self.move_to_pose(home_translation, home_rotation, duration=3.0)
    
    def emergency_stop(self):
        """Arrêt d'urgence"""
        print("EMERGENCY STOP ACTIVATED")
        self.motor_controller.emergency_stop()
    
    def get_current_pose(self):
        """Retourne la pose actuelle estimée"""
        # Lecture des positions encodeurs
        current_positions = []
        for i in range(6):
            pos = self.motor_controller.read_encoder_position(i)
            current_positions.append(pos)
        
        # Cinématique directe (plus complexe, optionnel)
        # Pour l'instant, on retourne les longueurs des vérins
        return {
            'leg_lengths': self.current_leg_lengths,
            'motor_positions': current_positions
        }
