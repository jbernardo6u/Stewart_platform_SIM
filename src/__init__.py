"""
Stewart Platform Control System
===============================

Un système de contrôle complet pour plateforme de Stewart avec interfaces GUI,
simulation PyBullet, et intégration hardware.

Modules principaux:
- core: Logique métier et cinématique
- hardware: Interface matérielle
- gui: Interfaces graphiques
- simulation: Simulation et visualisation
- utils: Utilitaires
"""

__version__ = "1.0.0"
__author__ = "Stewart Platform Project"

# Imports principaux pour faciliter l'utilisation
from .core.kinematics import InverseKinematics
from .core.platform import StewartPlatform
from .hardware.physical_platform import PhysicalStewartPlatform

__all__ = [
    'InverseKinematics',
    'StewartPlatform', 
    'PhysicalStewartPlatform'
]
