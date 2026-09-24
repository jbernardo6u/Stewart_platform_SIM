"""
Cinématique Inverse pour Plateforme de Stewart
==============================================

Ce module contient la classe InverseKinematics qui calcule les longueurs
des vérins nécessaires pour atteindre une position et orientation données.

Classes:
    InverseKinematics: Résout la cinématique inverse d'une plateforme de Stewart
"""

import numpy as np
from typing import Tuple, Union, List


class InverseKinematics:
    """
    Classe pour résoudre la cinématique inverse d'une plateforme de Stewart.
    
    Cette classe calcule les longueurs des 6 vérins nécessaires pour atteindre
    une position et orientation spécifiées de la plateforme mobile.
    
    Attributs:
        rb (float): Rayon de la base
        rp (float): Rayon de la plateforme mobile
        gamma_B (float): Demi-angle de la base (en radians)
        gamma_P (float): Demi-angle de la plateforme (en radians)
        home_pos (np.ndarray): Position de référence de la plateforme
        B (np.ndarray): Coordonnées des points d'attache sur la base
        P (np.ndarray): Coordonnées des points d'attache sur la plateforme
        L (np.ndarray): Positions des vérins dans le repère global
    """
    
    def __init__(self, radius_base: float, radius_platform: float, 
                 gamma_base: float, gamma_platform: float) -> None:
        """
        Initialise la classe de cinématique inverse.
        
        Args:
            radius_base: Rayon de la base (m)
            radius_platform: Rayon de la plateforme mobile (m)
            gamma_base: Demi-angle de la base (degrés)
            gamma_platform: Demi-angle de la plateforme (degrés)
        """
        self.rb = radius_base
        self.rp = radius_platform
        self.gamma_B = np.deg2rad(gamma_base)
        self.gamma_P = np.deg2rad(gamma_platform)
        
        # Position de référence de la plateforme
        self.home_pos = np.array([0, 0, 0.257547])
        
        # Matrices qui seront calculées
        self.B = None  # Points d'attache base
        self.P = None  # Points d'attache plateforme
        self.L = None  # Positions des vérins
        
    def calculate_attachment_points(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule les coordonnées des points d'attache sur la base et la plateforme.
        
        Returns:
            Tuple contenant:
                - P: Points d'attache sur la plateforme (3x6)
                - B: Points d'attache sur la base (3x6)
        """
        pi = np.pi
        
        # Angles polaires pour la base
        phi_B = np.array([
            7*pi/6 + self.gamma_B, 
            7*pi/6 - self.gamma_B,
            pi/2 + self.gamma_B, 
            pi/2 - self.gamma_B, 
            11*pi/6 + self.gamma_B, 
            11*pi/6 - self.gamma_B  
        ])
        
        # Angles polaires pour la plateforme
        phi_P = np.array([
            3*pi/2 - self.gamma_P,
            5*pi/6 + self.gamma_P,
            5*pi/6 - self.gamma_P,
            pi/6 + self.gamma_P, 
            pi/6 - self.gamma_P,
            3*pi/2 + self.gamma_P, 
        ])
        
        # Coordonnées des points d'attache sur la base
        B = self.rb * np.array([
            [np.cos(phi_B[0]), np.sin(phi_B[0]), 0],
            [np.cos(phi_B[1]), np.sin(phi_B[1]), 0],
            [np.cos(phi_B[2]), np.sin(phi_B[2]), 0],
            [np.cos(phi_B[3]), np.sin(phi_B[3]), 0],
            [np.cos(phi_B[4]), np.sin(phi_B[4]), 0],
            [np.cos(phi_B[5]), np.sin(phi_B[5]), 0]
        ])
        B = np.transpose(B)
        
        # Coordonnées des points d'attache sur la plateforme
        P = self.rp * np.array([
            [np.cos(phi_P[0]), np.sin(phi_P[0]), 0],
            [np.cos(phi_P[1]), np.sin(phi_P[1]), 0],
            [np.cos(phi_P[2]), np.sin(phi_P[2]), 0],
            [np.cos(phi_P[3]), np.sin(phi_P[3]), 0],
            [np.cos(phi_P[4]), np.sin(phi_P[4]), 0],
            [np.cos(phi_P[5]), np.sin(phi_P[5]), 0]
        ])
        P = np.transpose(P)
        
        return P, B
    
    @staticmethod
    def rotation_matrix_x(theta: float) -> np.ndarray:
        """
        Matrice de rotation autour de l'axe X.
        
        Args:
            theta: Angle de rotation en degrés
            
        Returns:
            Matrice de rotation 3x3
        """
        theta_rad = np.deg2rad(theta)
        return np.array([
            [1, 0, 0],
            [0, np.cos(theta_rad), -np.sin(theta_rad)],
            [0, np.sin(theta_rad), np.cos(theta_rad)]
        ])
    
    @staticmethod
    def rotation_matrix_y(theta: float) -> np.ndarray:
        """
        Matrice de rotation autour de l'axe Y.
        
        Args:
            theta: Angle de rotation en degrés
            
        Returns:
            Matrice de rotation 3x3
        """
        theta_rad = np.deg2rad(theta)
        return np.array([
            [np.cos(theta_rad), 0, np.sin(theta_rad)],
            [0, 1, 0],
            [-np.sin(theta_rad), 0, np.cos(theta_rad)]
        ])
    
    @staticmethod
    def rotation_matrix_z(theta: float) -> np.ndarray:
        """
        Matrice de rotation autour de l'axe Z.
        
        Args:
            theta: Angle de rotation en degrés
            
        Returns:
            Matrice de rotation 3x3
        """
        theta_rad = np.deg2rad(theta)
        return np.array([
            [np.cos(theta_rad), -np.sin(theta_rad), 0],
            [np.sin(theta_rad), np.cos(theta_rad), 0],
            [0, 0, 1]
        ])
    
    def calculate_rotation_matrix(self, rotation: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Calcule la matrice de rotation combinée pour une rotation donnée.
        
        Args:
            rotation: [roll, pitch, yaw] en degrés
            
        Returns:
            Matrice de rotation 3x3 combinée
        """
        roll, pitch, yaw = rotation
        R_x = self.rotation_matrix_x(roll)
        R_y = self.rotation_matrix_y(pitch)
        R_z = self.rotation_matrix_z(yaw)
        
        # Ordre de rotation: R = R_z * R_y * R_x
        return np.matmul(np.matmul(R_x, R_y), R_z)
    
    def solve(self, translation: Union[List[float], np.ndarray], 
              rotation: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Résout la cinématique inverse pour une position et orientation données.
        
        Args:
            translation: Translation [x, y, z] en mètres
            rotation: Rotation [roll, pitch, yaw] en degrés
            
        Returns:
            Longueurs des 6 vérins (array 1D)
        """
        # Convertir en arrays numpy si nécessaire
        trans = np.array(translation)
        rot = np.array(rotation)
        
        # Calculer les points d'attache
        self.P, self.B = self.calculate_attachment_points()
        
        # Calculer la matrice de rotation
        R = self.calculate_rotation_matrix(rot)
        
        # Calculer les positions des vérins
        # L = translation + home_position + R * P - B
        translation_matrix = np.repeat(trans[:, np.newaxis], 6, axis=1)
        home_matrix = np.repeat(self.home_pos[:, np.newaxis], 6, axis=1)
        rotated_platform = np.matmul(R, self.P)
        
        leg_vectors = translation_matrix + home_matrix + rotated_platform - self.B
        
        # Calculer les longueurs des vérins
        leg_lengths = np.linalg.norm(leg_vectors, axis=0)
        
        # Sauvegarder les positions pour usage ultérieur
        self.L = leg_vectors + self.B
        
        return leg_lengths
    
    def calculate(self, pose: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Alias for solve method - calculates leg lengths for a given pose.
        
        Args:
            pose: Position and rotation [x, y, z, roll, pitch, yaw]
                 Position in mm, rotation in radians
        
        Returns:
            Array of 6 leg lengths in mm
        """
        if len(pose) >= 6:
            return self.solve(pose[:3], pose[3:6])
        else:
            raise ValueError("Pose must contain at least 6 elements [x, y, z, roll, pitch, yaw]")
    
    def get_leg_positions(self) -> Union[np.ndarray, None]:
        """
        Retourne les positions des vérins dans le repère global.
        
        Returns:
            Positions des vérins (3x6) ou None si solve() n'a pas été appelé
        """
        return self.L
    
    def get_attachment_points(self) -> Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]:
        """
        Retourne les points d'attache de la base et de la plateforme.
        
        Returns:
            Tuple (points_plateforme, points_base) ou (None, None) si non calculés
        """
        return self.P, self.B


# Alias pour compatibilité avec l'ancien code
inv_kinematics = InverseKinematics
