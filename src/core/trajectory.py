"""
Génération de Trajectoires pour Plateforme de Stewart
====================================================

Ce module contient les fonctions pour générer différents types de trajectoires
pour la plateforme de Stewart, incluant des trajectoires elliptiques, spirales,
et autres mouvements prédéfinis.

Classes:
    TrajectoryGenerator: Générateur de trajectoires pour la plateforme Stewart

Fonctions:
    generate_elliptical_trajectory: Génère une trajectoire elliptique
    generate_spiral_trajectory: Génère une trajectoire en spirale 3D
    generate_sinusoidal_trajectory: Génère une trajectoire sinusoïdale
    generate_demo_trajectory: Génère une trajectoire de démonstration
"""

import numpy as np
from typing import Tuple, List, Union


def generate_elliptical_trajectory(center: List[float], radii: List[float], 
                                 rotation_angle: float, n_points: int, 
                                 n_turns: int = 1) -> np.ndarray:
    """
    Génère une trajectoire elliptique dans le plan XY.
    
    Args:
        center: Centre de l'ellipse [x, y, z]
        radii: Rayons de l'ellipse [rayon_x, rayon_y]
        rotation_angle: Angle de rotation de l'ellipse en radians
        n_points: Nombre de points par tour
        n_turns: Nombre de tours à effectuer
        
    Returns:
        Array de points de trajectoire (n_points*n_turns, 3)
    """
    # Matrice de rotation autour de l'axe Z
    cos_theta = np.cos(rotation_angle)
    sin_theta = np.sin(rotation_angle)
    rotation_matrix = np.array([
        [cos_theta, -sin_theta, 0],
        [sin_theta, cos_theta, 0],
        [0, 0, 1]
    ])
    
    # Générer les angles pour un tour complet
    angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
    
    # Générer les points de l'ellipse
    points = np.stack([
        radii[0] * np.cos(angles),
        radii[1] * np.sin(angles),
        np.zeros(n_points)
    ], axis=1)
    
    # Appliquer la rotation et la translation
    points = np.dot(points, rotation_matrix.T) + np.array(center)
    
    # Répéter pour le nombre de tours souhaités
    trajectory = np.tile(points, (n_turns, 1))
    
    return trajectory


def generate_spiral_trajectory(num_points: int = 100, num_turns: int = 2, 
                             radius: float = 0.005, height: float = 0.002,
                             center: List[float] = [0, 0, 0]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Génère une trajectoire en spirale 3D.
    
    Args:
        num_points: Nombre total de points
        num_turns: Nombre de tours de spirale
        radius: Rayon de la spirale
        height: Hauteur totale de la spirale
        center: Centre de la spirale [x, y, z]
        
    Returns:
        Tuple (x, y, z) des coordonnées de la spirale
    """
    # Générer les paramètres de la spirale
    t = np.linspace(0, num_turns * 2 * np.pi, num_points)
    
    # Coordonnées de la spirale
    x = radius * np.cos(t) + center[0]
    y = radius * np.sin(t) + center[1]
    z = height * (t / (2 * np.pi)) + center[2]
    
    return x, y, z


def generate_sinusoidal_trajectory(amplitude: List[float], frequency: List[float],
                                 phase: List[float], duration: float, 
                                 sample_rate: float = 50.0,
                                 center: List[float] = [0, 0, 0]) -> np.ndarray:
    """
    Génère une trajectoire sinusoïdale dans les 3 axes.
    
    Args:
        amplitude: Amplitudes pour [x, y, z]
        frequency: Fréquences pour [x, y, z] en Hz
        phase: Phases pour [x, y, z] en radians
        duration: Durée totale en secondes
        sample_rate: Taux d'échantillonnage en Hz
        center: Position centrale [x, y, z]
        
    Returns:
        Array de points de trajectoire (n_points, 3)
    """
    # Générer le vecteur temps
    n_points = int(duration * sample_rate)
    t = np.linspace(0, duration, n_points)
    
    # Générer les trajectoires sinusoïdales pour chaque axe
    x = amplitude[0] * np.sin(2 * np.pi * frequency[0] * t + phase[0]) + center[0]
    y = amplitude[1] * np.sin(2 * np.pi * frequency[1] * t + phase[1]) + center[1]
    z = amplitude[2] * np.sin(2 * np.pi * frequency[2] * t + phase[2]) + center[2]
    
    # Combiner en un array de trajectoire
    trajectory = np.column_stack([x, y, z])
    
    return trajectory


def generate_figure_eight_trajectory(radius: float = 0.01, n_points: int = 100,
                                   plane: str = 'xy', center: List[float] = [0, 0, 0]) -> np.ndarray:
    """
    Génère une trajectoire en forme de huit.
    
    Args:
        radius: Rayon de la figure
        n_points: Nombre de points
        plane: Plan de la trajectoire ('xy', 'xz', 'yz')
        center: Centre de la figure [x, y, z]
        
    Returns:
        Array de points de trajectoire (n_points, 3)
    """
    # Paramètre de la courbe
    t = np.linspace(0, 2*np.pi, n_points)
    
    # Équations paramétriques du huit (lemniscate)
    if plane == 'xy':
        x = radius * np.sin(t) + center[0]
        y = radius * np.sin(t) * np.cos(t) + center[1]
        z = np.full(n_points, center[2])
    elif plane == 'xz':
        x = radius * np.sin(t) + center[0]
        y = np.full(n_points, center[1])
        z = radius * np.sin(t) * np.cos(t) + center[2]
    elif plane == 'yz':
        x = np.full(n_points, center[0])
        y = radius * np.sin(t) + center[1]
        z = radius * np.sin(t) * np.cos(t) + center[2]
    else:
        raise ValueError("Plane must be 'xy', 'xz', or 'yz'")
    
    trajectory = np.column_stack([x, y, z])
    return trajectory


def generate_demo_trajectory(trajectory_type: str = 'mixed', **kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère une trajectoire de démonstration avec translations et rotations.
    
    Args:
        trajectory_type: Type de trajectoire ('ellipse', 'spiral', 'sine', 'mixed')
        **kwargs: Arguments spécifiques au type de trajectoire
        
    Returns:
        Tuple (translations, rotations) où:
        - translations: Array (n_points, 3) avec [x, y, z]
        - rotations: Array (n_points, 3) avec [roll, pitch, yaw] en degrés
    """
    if trajectory_type == 'ellipse':
        # Trajectoire elliptique avec rotation
        center = kwargs.get('center', [0, 0, 0])
        radii = kwargs.get('radii', [0.01, 0.005])
        n_points = kwargs.get('n_points', 50)
        
        translations = generate_elliptical_trajectory(center, radii, 0, n_points)
        
        # Rotation progressive autour de Z
        angles = np.linspace(0, 360, n_points)
        rotations = np.column_stack([
            np.zeros(n_points),  # Roll
            np.zeros(n_points),  # Pitch
            angles               # Yaw
        ])
        
    elif trajectory_type == 'spiral':
        # Trajectoire spirale avec oscillation
        num_points = kwargs.get('num_points', 100)
        x, y, z = generate_spiral_trajectory(num_points=num_points)
        translations = np.column_stack([x, y, z])
        
        # Oscillation en roll et pitch
        t = np.linspace(0, 4*np.pi, num_points)
        rotations = np.column_stack([
            10 * np.sin(t),      # Roll ±10°
            10 * np.cos(t),      # Pitch ±10°
            np.zeros(num_points) # Yaw
        ])
        
    elif trajectory_type == 'sine':
        # Trajectoire sinusoïdale
        duration = kwargs.get('duration', 10.0)
        sample_rate = kwargs.get('sample_rate', 20.0)
        
        translations = generate_sinusoidal_trajectory(
            amplitude=[0.01, 0.01, 0.005],
            frequency=[0.5, 0.3, 0.2],
            phase=[0, np.pi/2, np.pi/4],
            duration=duration,
            sample_rate=sample_rate
        )
        
        # Rotation sinusoïdale
        n_points = len(translations)
        t = np.linspace(0, duration, n_points)
        rotations = np.column_stack([
            15 * np.sin(2*np.pi*0.2*t),    # Roll
            10 * np.sin(2*np.pi*0.3*t),    # Pitch
            20 * np.sin(2*np.pi*0.1*t)     # Yaw
        ])
        
    elif trajectory_type == 'mixed':
        # Trajectoire mixte complexe
        n_points = kwargs.get('n_points', 50)
        
        # Combinaison de mouvements
        t = np.linspace(0, 4*np.pi, n_points)
        
        translations = np.column_stack([
            0.01 * np.sin(t),           # X: sinusoïde
            0.005 * np.sin(2*t),        # Y: fréquence double
            0.002 * np.sin(0.5*t)       # Z: fréquence plus lente
        ])
        
        rotations = np.column_stack([
            15 * np.sin(t + np.pi/4),   # Roll
            10 * np.sin(2*t),           # Pitch
            20 * np.sin(0.5*t)          # Yaw
        ])
        
    else:
        raise ValueError(f"Unknown trajectory type: {trajectory_type}")
    
    return translations, rotations


def generate_test_sequence() -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère une séquence de test simple pour validation.
    
    Returns:
        Tuple (translations, rotations) pour une séquence de test
    """
    # Séquence de positions de test
    test_positions = [
        [0, 0, 0],          # Position neutre
        [0.01, 0, 0],       # Translation X
        [0, 0.01, 0],       # Translation Y
        [0, 0, 0.005],      # Translation Z
        [0, 0, 0],          # Retour neutre
    ]
    
    test_rotations = [
        [0, 0, 0],          # Orientation neutre
        [10, 0, 0],         # Roll
        [0, 10, 0],         # Pitch
        [0, 0, 15],         # Yaw
        [0, 0, 0],          # Retour neutre
    ]
    
    translations = np.array(test_positions)
    rotations = np.array(test_rotations)
    
    return translations, rotations


class TrajectoryGenerator:
    """
    Générateur de trajectoires pour la plateforme Stewart.
    
    Cette classe fournit des méthodes pour générer différents types de trajectoires
    prédéfinies pour la plateforme Stewart.
    """
    
    def __init__(self, position_limits: dict = None, rotation_limits: dict = None):
        """
        Initialise le générateur de trajectoires.
        
        Args:
            position_limits: Limites de position {x: (min, max), y: (min, max), z: (min, max)}
            rotation_limits: Limites de rotation {roll: (min, max), pitch: (min, max), yaw: (min, max)}
        """
        self.position_limits = position_limits or {
            'x': (-50, 50), 'y': (-50, 50), 'z': (-30, 30)
        }
        self.rotation_limits = rotation_limits or {
            'roll': (-15, 15), 'pitch': (-15, 15), 'yaw': (-30, 30)
        }
    
    def generate_elliptical(self, center: List[float], radii: List[float], 
                           rotation_angle: float, n_points: int, 
                           n_turns: int = 1) -> np.ndarray:
        """Generate elliptical trajectory."""
        return generate_elliptical_trajectory(center, radii, rotation_angle, n_points, n_turns)
    
    def generate_spiral(self, center: List[float], radius_range: Tuple[float, float],
                       height_range: Tuple[float, float], n_points: int,
                       n_turns: int = 3) -> np.ndarray:
        """Generate 3D spiral trajectory."""
        return generate_spiral_trajectory(center, radius_range, height_range, n_points, n_turns)
    
    def generate_sinusoidal(self, amplitude: List[float], frequency: List[float],
                           phase: List[float], duration: float, 
                           sampling_rate: float = 50) -> np.ndarray:
        """Generate sinusoidal trajectory."""
        return generate_sinusoidal_trajectory(amplitude, frequency, phase, duration, sampling_rate)
    
    def generate_demo(self, demo_type: str = 'mixed') -> np.ndarray:
        """Generate demonstration trajectory."""
        return generate_demo_trajectory(demo_type)
