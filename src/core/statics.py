"""
Statique : efforts dans les vérins
==================================

Phase 3 de la roadmap (verrou V-4). Pour une pose, on calcule les efforts axiaux des
6 vérins qui équilibrent un torseur extérieur appliqué à la plateforme (gravité de la
charge embarquée, effort d'accostage...).

Convention (cohérente avec :func:`src.core.forward_kinematics.jacobian`) :

- ``f_i`` > 0 : le vérin **pousse** la plateforme (compression du vérin, il s'oppose au
  raccourcissement) ; ``f_i`` < 0 : il **tire** (traction) ;
- puissance des vérins sur la plateforme : ``fᵀ·dℓ/dt = fᵀ·J·[v ; ω]``, donc le torseur
  qu'ils exercent vaut ``Jᵀ·f`` ;
- équilibre : ``Jᵀ·f + w_ext = 0``, soit ``f = −J⁻ᵀ·w_ext`` ;
- ``w_ext = [F ; M]`` : force (N) et moment (N·m) **au centre de la plateforme**, dans
  le repère base.

Hypothèses : liaisons parfaites (sans frottement), masse des vérins négligée, quasi-statique.
NumPy pur.
"""

from typing import Sequence

import numpy as np

from .forward_kinematics import jacobian, rotation_matrix
from .kinematics import InverseKinematics

STANDARD_GRAVITY = 9.81


def gravity_wrench(mass: float, centre_of_mass_P: Sequence[float], R: np.ndarray,
                   gravity_B: Sequence[float]) -> np.ndarray:
    """
    Torseur du poids d'une charge, au centre de la plateforme, dans le repère base.

    Args:
        mass: Masse portée par la plateforme (kg)
        centre_of_mass_P: Centre de gravité dans le repère plateforme {P} (m)
        R: Orientation de la plateforme (repère base ← plateforme)
        gravity_B: Accélération de la pesanteur exprimée dans le repère base (m/s²).
            Plateforme debout : ``[0, 0, −9,81]`` ; plateforme couchée : vecteur
            perpendiculaire à z_B (voir :func:`gravity_in_base_lying`)
    """
    F = mass * np.asarray(gravity_B, dtype=float)
    r = R @ np.asarray(centre_of_mass_P, dtype=float)
    return np.concatenate([F, np.cross(r, F)])


def gravity_in_base_lying(mount_angle_deg: float, g: float = STANDARD_GRAVITY) -> np.ndarray:
    """
    Pesanteur dans le repère base pour une plateforme **couchée** (z_B horizontal).

    ``mount_angle_deg`` est l'angle, autour de z_B, entre x_B et la verticale descendante :
    0° signifie que la gravité est selon −x_B. Cet angle dépend du montage de la base
    (quel vérin est en haut) : à mesurer sur le banc.
    """
    a = np.radians(mount_angle_deg)
    return -g * np.array([np.cos(a), np.sin(a), 0.0])


def actuator_forces(ik: InverseKinematics, translation: Sequence[float], rotation_rad: Sequence[float],
                    wrench: Sequence[float]) -> np.ndarray:
    """Efforts axiaux (N) des 6 vérins qui équilibrent ``wrench`` ([F ; M] au centre, repère base)."""
    J = jacobian(ik, translation, rotation_rad)
    return -np.linalg.solve(J.T, np.asarray(wrench, dtype=float))


def gravity_actuator_forces(ik: InverseKinematics, translation, rotation_rad, mass: float,
                            centre_of_mass_P, gravity_B) -> np.ndarray:
    """Efforts des vérins (N) dus au poids de la charge embarquée, pour une pose."""
    R = rotation_matrix(rotation_rad)
    return actuator_forces(ik, translation, rotation_rad,
                           gravity_wrench(mass, centre_of_mass_P, R, gravity_B))
