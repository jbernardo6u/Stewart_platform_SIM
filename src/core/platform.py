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
# Lien TOP1 : plateforme mobile.
DEFAULT_PLATFORM_LINK = 15
# Hauteur de travail (m) au-dessus de la pose neutre de l'IK. La pose neutre correspond
# à la configuration zéro du URDF, c'est-à-dire aux vérins en butée basse (course [0, 0.19] m) :
# les mouvements autour de la pose neutre sont donc impossibles vers le bas (EXP-004).
DEFAULT_WORKING_HEIGHT = 0.09
# Centre de la plateforme (barycentre des centres des cardans supérieurs, centre de rotation
# de l'IK) exprimé dans le repère du lien TOP1. Identifié depuis le URDF (EXP-001).
DEFAULT_PLATFORM_CENTRE_IN_LINK = [-0.042041, 0.195039, -0.042205]


def rotation_to_rpy_deg(R: np.ndarray) -> List[float]:
    """Inverse de R = Rx(roll)·Ry(pitch)·Rz(yaw), convention de InverseKinematics (degrés)."""
    roll = np.arctan2(-R[1, 2], R[2, 2])
    pitch = np.arcsin(np.clip(R[0, 2], -1.0, 1.0))
    yaw = np.arctan2(-R[0, 1], R[0, 0])
    return [float(np.degrees(a)) for a in (roll, pitch, yaw)]


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
                 actuator_indices: List[int], design_variables: List[float],
                 kinematics: Optional[InverseKinematics] = None) -> None:
        """
        Initialise la plateforme de Stewart.
        
        Args:
            urdf_path: Chemin vers le fichier URDF du modèle
            joint_indices: Liste des indices de joints [(joint1, joint2), ...]
            actuator_indices: Liste des indices des actionneurs linéaires
            design_variables: [radius_platform, radius_base, gamma_platform, gamma_base]
            kinematics: IK à utiliser à la place du modèle paramétrique construit depuis
                        design_variables (par exemple une géométrie identifiée, voir from_urdf)
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
        self.kinematics = kinematics or InverseKinematics(r_B, r_P, gamma_B, gamma_P)
        
        # Longueurs initiales des vérins : pose neutre de l'IK = configuration zéro du URDF
        self.l = self.kinematics.solve([0, 0, 0], [0, 0, 0])
        self.platform_link = DEFAULT_PLATFORM_LINK
        self.platform_centre_in_link = np.array(DEFAULT_PLATFORM_CENTRE_IN_LINK)
        self.constraint_ids: List[int] = []
        # Gain de l'asservissement de position PyBullet des vérins. La valeur par défaut
        # de PyBullet (0,1) laisse ~0,2 mm d'erreur de vérin sous le poids de la plateforme (EXP-004).
        self.actuator_position_gain = 0.3
        self.actuator_max_force = 1000.0
        self._home_platform_pose = None  # (position, matrice de rotation) de la plateforme à la pose neutre
        
    @classmethod
    def from_urdf(cls, urdf_path: str,
                  joint_indices: List[Tuple[int, int]] = DEFAULT_JOINT_INDICES,
                  actuator_indices: List[int] = DEFAULT_ACTUATOR_INDICES,
                  platform_link: int = DEFAULT_PLATFORM_LINK) -> "StewartPlatform":
        """
        Plateforme dont l'IK utilise la géométrie réelle identifiée dans le URDF (EXP-001),
        au lieu du modèle paramétrique (r, γ). C'est la configuration la plus fidèle.
        """
        from ..simulation.urdf_geometry import identify_urdf_geometry
        geo = identify_urdf_geometry(urdf_path, actuator_indices, platform_link)
        ik = InverseKinematics.from_attachment_points(geo['base_points'], geo['platform_points'],
                                                      geo['home_position'])
        design = [ik.rp, ik.rb, 0.0, 0.0]
        platform = cls(urdf_path, joint_indices, actuator_indices, design, kinematics=ik)
        platform.platform_link = platform_link
        platform.platform_centre_in_link = np.array(geo['platform_centre_in_link'])
        return platform

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
                   orientation: List[float] = [0, 0, 0], use_fixed_base: bool = True) -> bool:
        """
        Charge le modèle URDF de la plateforme de Stewart.
        
        Args:
            position: Position initiale [x, y, z]
            orientation: Orientation initiale [roll, pitch, yaw] en radians
            use_fixed_base: Base fixée au monde (la base d'une plateforme de Stewart ne bouge pas)
            
        Returns:
            True si le chargement a réussi, False sinon
        """
        try:
            if not os.path.exists(self.path):
                print(f"❌ URDF file not found: {self.path}")
                return False
            
            start_orientation = p.getQuaternionFromEuler(orientation)
            self.robot_id = p.loadURDF(self.path, position, start_orientation,
                                     useFixedBase=use_fixed_base,
                                     flags=p.URDF_USE_INERTIA_FROM_FILE)
            
            print(f"✅ Robot loaded successfully with ID: {self.robot_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load robot: {e}")
            return False
    
    def setup_constraints(self) -> None:
        """
        Ferme les boucles cinématiques de la plateforme (voir EXP-004).

        - Les limites [0, 2π] exportées par Fusion 360 sur certaines articulations passives
          sont recentrées sur [-π, π] : sinon ces articulations butent à 0 et bloquent le mécanisme.
        - Chaque paire (lien de jambe, lien de plateforme) de ``joint_indices`` est liée par une
          contrainte fixe ancrée sur la pose relative des deux liens en configuration zéro.
          Les repères de contrainte PyBullet sont exprimés dans le repère du centre de masse
          de chaque lien ; ancrer en [0, 0, 0] (ancienne version) collait les centres de masse.
        - Les moteurs par défaut des articulations passives sont désactivés.

        Doit être appelée juste après le chargement, robot en configuration zéro.
        """
        if self.robot_id is None:
            return
        try:
            for j in range(p.getNumJoints(self.robot_id)):
                info = p.getJointInfo(self.robot_id, j)
                if info[2] == p.JOINT_REVOLUTE and info[8] == 0.0 and abs(info[9] - 2 * np.pi) < 1e-4:
                    p.changeDynamics(self.robot_id, j, jointLowerLimit=-np.pi, jointUpperLimit=np.pi)

            for leg_link, platform_link in self.joint_indices:
                self.constraint_ids.append(self._create_anchored_fixed_constraint(leg_link, platform_link))

            for j in range(p.getNumJoints(self.robot_id)):
                p.setJointMotorControl2(self.robot_id, j, p.VELOCITY_CONTROL, force=0)

            state = p.getLinkState(self.robot_id, self.platform_link, computeForwardKinematics=1)
            self._home_platform_pose = (np.array(state[4]),
                                        np.array(p.getMatrixFromQuaternion(state[5])).reshape(3, 3))
        except Exception as e:
            print(f"⚠️ Warning in constraint setup: {e}")

    def _create_anchored_fixed_constraint(self, link_a: int, link_b: int) -> int:
        """Contrainte fixe entre deux liens, qui conserve leur pose relative actuelle."""
        state_a = p.getLinkState(self.robot_id, link_a, computeForwardKinematics=1)
        state_b = p.getLinkState(self.robot_id, link_b, computeForwardKinematics=1)
        anchor = np.array(state_a[4])  # origine du repère du lien a, en coordonnées monde
        frames = []
        for com_pos, com_orn in ((state_a[0], state_a[1]), (state_b[0], state_b[1])):
            rot = np.array(p.getMatrixFromQuaternion(com_orn)).reshape(3, 3)
            frames.append((list(rot.T @ (anchor - np.array(com_pos))),
                           p.invertTransform([0, 0, 0], com_orn)[1]))
        (pos_a, orn_a), (pos_b, orn_b) = frames
        cid = p.createConstraint(self.robot_id, link_a, self.robot_id, link_b, p.JOINT_FIXED,
                                 [0, 0, 0], pos_a, pos_b, orn_a, orn_b)
        p.changeConstraint(cid, maxForce=1e20)
        return cid
    
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
                               duration: float = 1.0, frequency: float = 240,
                               realtime: bool = True, settle_time: float = 0.0) -> None:
        """
        Contrôle les actionneurs linéaires pour modifier les longueurs des vérins.
        
        Args:
            delta_lengths: Changements de longueur pour chaque vérin
            duration: Durée du mouvement en secondes
            frequency: Fréquence de simulation en Hz
            realtime: Attendre entre deux pas (visualisation) ; False pour calculer au plus vite
            settle_time: Durée de maintien de la consigne finale après le mouvement (s)
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
            
            # Interpolation linéaire entre les positions actuelles et cibles,
            # puis maintien de la consigne finale pendant settle_time
            hold_steps = int(settle_time * frequency)
            for step in range(steps + hold_steps):
                alpha = min(1.0, (step + 1) / steps) if steps > 0 else 1.0
                current_positions = self.prev_target + alpha * delta_lengths
                
                # Appliquer les positions aux actionneurs
                for i, actuator_id in enumerate(self.actuator_indices):
                    p.setJointMotorControl2(
                        bodyIndex=self.robot_id,
                        jointIndex=actuator_id,
                        controlMode=p.POSITION_CONTROL,
                        targetPosition=current_positions[i],
                        force=self.actuator_max_force,
                        positionGain=self.actuator_position_gain
                    )
                
                # Avancer la simulation
                p.stepSimulation()
                if realtime:
                    time.sleep(1.0 / frequency)
            
            # Mettre à jour les positions précédentes
            self.prev_target = new_targets
            self.l += delta_lengths
            
        except Exception as e:
            print(f"❌ Error controlling actuators: {e}")
    
    def move_to_pose(self, translation: Union[List[float], np.ndarray], 
                     rotation: Union[List[float], np.ndarray], 
                     duration: float = 1.0, **actuator_options) -> None:
        """
        Déplace la plateforme vers une pose spécifiée.

        La pose est exprimée par rapport à la pose neutre de l'IK, où les vérins sont
        en butée basse : travailler autour de ``DEFAULT_WORKING_HEIGHT`` (voir
        ``move_to_working_position``).
        
        Args:
            translation: Translation [x, y, z] en mètres
            rotation: Rotation [roll, pitch, yaw] en degrés
            duration: Durée du mouvement en secondes
            **actuator_options: ``realtime``, ``settle_time`` (voir control_linear_actuators)
        """
        try:
            # Calculer les longueurs de vérins nécessaires
            target_lengths = self.kinematics.solve(translation, rotation)
            
            # Calculer les changements nécessaires
            delta_lengths = target_lengths - self.l
            
            # Contrôler les actionneurs
            self.control_linear_actuators(delta_lengths, duration, **actuator_options)
            
        except Exception as e:
            print(f"❌ Error moving to pose: {e}")

    def move_to_working_position(self, height: float = DEFAULT_WORKING_HEIGHT,
                                 duration: float = 2.0, **actuator_options) -> None:
        """Monte la plateforme à mi-course des vérins, d'où tous les mouvements sont possibles."""
        self.move_to_pose([0, 0, height], [0, 0, 0], duration, **actuator_options)
    
    def get_current_pose(self) -> Tuple[List[float], List[float]]:
        """
        Obtient la pose actuelle de la plateforme mobile, mesurée dans la simulation.

        La pose est exprimée comme les consignes de ``move_to_pose`` : translation (m) du
        centre de la plateforme depuis la pose neutre, et rotation [roll, pitch, yaw] en
        degrés (convention R = Rx·Ry·Rz). Elle se compare donc directement à la consigne.
        
        Returns:
            Tuple (position, orientation) où orientation est en degrés
        """
        if self.robot_id is None or self._home_platform_pose is None:
            return ([0, 0, 0], [0, 0, 0])
        
        try:
            state = p.getLinkState(self.robot_id, self.platform_link, computeForwardKinematics=1)
            origin = np.array(state[4])
            rot = np.array(p.getMatrixFromQuaternion(state[5])).reshape(3, 3)
            home_origin, home_rot = self._home_platform_pose
            c = self.platform_centre_in_link
            translation = (origin + rot @ c) - (home_origin + home_rot @ c)
            return ([float(v) for v in translation], rotation_to_rpy_deg(rot @ home_rot.T))
            
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
