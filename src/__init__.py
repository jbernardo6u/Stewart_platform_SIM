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

# Imports principaux pour faciliter l'utilisation, chargés à la demande (PEP 562) :
# ``from src import StewartPlatform`` fonctionne comme avant, mais importer un module
# NumPy pur (ex. ``src.core.forward_kinematics``) n'exige plus PyBullet. C'est utile
# côté ROS 2 (jumeau du démonstrateur, ros2_ws/), où PyBullet n'est pas installé.
_LAZY_EXPORTS = {
    'InverseKinematics': ('.core.kinematics', 'InverseKinematics'),
    'StewartPlatform': ('.core.platform', 'StewartPlatform'),
    'PhysicalStewartPlatform': ('.hardware.physical_platform', 'PhysicalStewartPlatform'),
}


def __getattr__(name):
    if name in _LAZY_EXPORTS:
        import importlib
        module, attr = _LAZY_EXPORTS[name]
        value = getattr(importlib.import_module(module, __name__), attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals()) + list(_LAZY_EXPORTS))

__all__ = [
    'InverseKinematics',
    'StewartPlatform', 
    'PhysicalStewartPlatform'
]
