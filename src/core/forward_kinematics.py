"""
Cinématique directe, jacobien et singularités
=============================================

Complète :class:`~src.core.kinematics.InverseKinematics` (Phase 2 de la roadmap) :

- :func:`forward_kinematics` : longueurs des 6 vérins → pose de la plateforme
  (Newton-Raphson, mise à jour de l'orientation sur SO(3)) ;
- :func:`jacobian` : jacobien inverse ``J`` tel que ``dℓ/dt = J · [v ; ω]`` ;
- :func:`singularity_measures` : conditionnement et déterminant de ``J``, pour
  détecter l'approche des singularités parallèles ;
- :func:`pose_from_actuator_positions` : allongements des vérins (codeurs, joints
  prismatiques du URDF) → pose relative à la position de travail, la convention de
  ``feasibility`` et du tableau de bord.

Conventions (identiques à ``InverseKinematics.solve``, mais **en radians**, SI) :

- ``translation`` (m) : le centre de la plateforme est en ``home_pos + translation``
  dans le repère base ;
- ``rotation`` = [roll, pitch, yaw] (rad), ``R = Rx(roll)·Ry(pitch)·Rz(yaw)`` ;
- ``ω`` est la vitesse angulaire exprimée dans le repère base.

NumPy pur : aucune dépendance au simulateur.
"""

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from .kinematics import InverseKinematics

# Paramètres par défaut du solveur ; les valeurs de référence sont dans
# configurations/platform_config.yaml (section ``kinematics``), voir solver_settings().
DEFAULT_TOLERANCE = 1e-12        # m, résidu sur les longueurs
DEFAULT_MAX_ITERATIONS = 50


def rotation_matrix(rotation_rad: Sequence[float]) -> np.ndarray:
    """``R = Rx(roll)·Ry(pitch)·Rz(yaw)``, angles en radians."""
    r, p, y = rotation_rad
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return rx @ ry @ rz


def rotation_to_rpy(R: np.ndarray) -> np.ndarray:
    """Inverse de :func:`rotation_matrix` (radians), valable pour |pitch| < 90°."""
    return np.array([np.arctan2(-R[1, 2], R[2, 2]),
                     np.arcsin(np.clip(R[0, 2], -1.0, 1.0)),
                     np.arctan2(-R[0, 1], R[0, 0])])


def _skew(w: np.ndarray) -> np.ndarray:
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def _exp_so3(w: np.ndarray) -> np.ndarray:
    """Rotation d'axe ``w/|w|`` et d'angle ``|w|`` (formule de Rodrigues)."""
    theta = np.linalg.norm(w)
    if theta < 1e-15:
        return np.eye(3) + _skew(w)
    k = _skew(w / theta)
    return np.eye(3) + np.sin(theta) * k + (1 - np.cos(theta)) * (k @ k)


def _attachment_points(ik: InverseKinematics):
    P, B = ik.calculate_attachment_points()
    return np.asarray(P, dtype=float), np.asarray(B, dtype=float)


def _legs(ik, translation, R):
    """Vecteurs jambes (3x6) base → plateforme et bras de levier ``R·p_i`` (3x6)."""
    P, B = _attachment_points(ik)
    arms = R @ P
    centre = np.asarray(ik.home_pos, dtype=float) + np.asarray(translation, dtype=float)
    return centre[:, None] + arms - B, arms


def leg_lengths(ik: InverseKinematics, translation: Sequence[float],
                rotation_rad: Sequence[float]) -> np.ndarray:
    """Longueurs des vérins (m), comme ``ik.solve`` mais avec des angles en radians."""
    legs, _ = _legs(ik, translation, rotation_matrix(rotation_rad))
    return np.linalg.norm(legs, axis=0)


def _jacobian_from_R(ik, translation, R) -> np.ndarray:
    legs, arms = _legs(ik, translation, R)
    u = legs / np.linalg.norm(legs, axis=0)
    return np.hstack([u.T, np.cross(arms.T, u.T)])


def jacobian(ik: InverseKinematics, translation: Sequence[float],
             rotation_rad: Sequence[float]) -> np.ndarray:
    """
    Jacobien inverse (6x6) : ``dℓ/dt = J · [v ; ω]``.

    La ligne i vaut ``[u_iᵀ, (R·p_i × u_i)ᵀ]``, avec ``u_i`` le vecteur unitaire de la
    jambe i et ``R·p_i`` le bras de levier depuis le centre de la plateforme. ``v`` (m/s)
    est la vitesse du centre, ``ω`` (rad/s) la vitesse angulaire, toutes deux dans le
    repère base. En statique, les efforts des vérins valent ``f = J⁻ᵀ · w`` (Phase 3).
    """
    return _jacobian_from_R(ik, translation, rotation_matrix(rotation_rad))


def characteristic_length(ik: InverseKinematics) -> float:
    """Rayon moyen des attaches de la plateforme (m), pour adimensionner ``J``."""
    P, _ = _attachment_points(ik)
    return float(np.linalg.norm(P[:2], axis=0).mean())


def singularity_measures(ik: InverseKinematics, translation: Sequence[float],
                         rotation_rad: Sequence[float]) -> dict:
    """
    Indicateurs de proximité d'une singularité parallèle (``det J = 0``).

    Les colonnes de rotation de ``J`` sont en mètres, celles de translation sans unité :
    on les rend homogènes en exprimant ``ω`` multipliée par la longueur caractéristique
    ``L`` (:func:`characteristic_length`), soit ``J_n = J · diag(1, 1, 1, 1/L, 1/L, 1/L)``.

    Returns:
        dict : ``condition`` (conditionnement de ``J_n``, ∞ à la singularité),
        ``inverse_condition`` (1/condition, 0 à la singularité),
        ``determinant`` (de ``J_n``), ``min_singular_value`` (de ``J_n``)
    """
    J = jacobian(ik, translation, rotation_rad)
    L = characteristic_length(ik)
    Jn = J @ np.diag([1, 1, 1, 1 / L, 1 / L, 1 / L])
    s = np.linalg.svd(Jn, compute_uv=False)
    inv_cond = float(s[-1] / s[0])
    return dict(condition=float(np.inf) if inv_cond == 0 else 1 / inv_cond,
                inverse_condition=inv_cond, determinant=float(np.linalg.det(Jn)),
                min_singular_value=float(s[-1]))


@dataclass
class ForwardKinematicsResult:
    """Résultat de :func:`forward_kinematics` (SI : m, rad)."""
    translation: np.ndarray       # (3,) m, même convention que ``solve``
    rotation: np.ndarray          # (3,) rad, [roll, pitch, yaw]
    rotation_matrix: np.ndarray   # (3, 3)
    converged: bool
    iterations: int
    residual: float               # m, max |ℓ(pose) - ℓ_mesurées|
    condition: float              # conditionnement de J à la solution (voir singularity_measures)

    @property
    def rotation_deg(self) -> np.ndarray:
        """Rotation en degrés, pour comparer aux consignes de ``solve``."""
        return np.degrees(self.rotation)


def forward_kinematics(ik: InverseKinematics, lengths: Sequence[float],
                       initial_translation: Optional[Sequence[float]] = None,
                       initial_rotation_rad: Optional[Sequence[float]] = None,
                       tolerance: float = DEFAULT_TOLERANCE,
                       max_iterations: int = DEFAULT_MAX_ITERATIONS) -> ForwardKinematicsResult:
    """
    Cinématique directe par Newton-Raphson : pose telle que ``ik`` donne ``lengths``.

    À chaque itération, on résout ``J · [δt ; δω] = ℓ_mesurées - ℓ(pose)`` puis on met
    à jour ``t ← t + δt`` et ``R ← exp([δω]×)·R`` (pas d'angles d'Euler dans
    l'itération, donc pas de blocage de cardan). La solution dépend de l'estimation
    initiale (une 6-6 générale a jusqu'à 40 solutions) : partir de la dernière pose
    connue, ou de la pose neutre par défaut. Convergence quadratique près de la solution.

    Args:
        ik: Cinématique inverse (géométrie et ``home_pos``)
        lengths: Longueurs des 6 vérins (m), dans l'ordre de ``ik.solve``
        initial_translation: Estimation initiale (m), par défaut [0, 0, 0]
        initial_rotation_rad: Estimation initiale (rad), par défaut [0, 0, 0]
        tolerance: Résidu visé sur les longueurs (m)
        max_iterations: Nombre maximal d'itérations

    Returns:
        :class:`ForwardKinematicsResult` ; ``converged`` est faux si le résidu reste
        au-dessus de ``tolerance`` (pose inatteignable, ou singularité).
    """
    target = np.asarray(lengths, dtype=float)
    if target.shape != (6,):
        raise ValueError("lengths doit contenir 6 longueurs")
    t = np.zeros(3) if initial_translation is None else np.asarray(initial_translation, dtype=float).copy()
    R = rotation_matrix(np.zeros(3) if initial_rotation_rad is None else initial_rotation_rad)

    residual = np.inf
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        legs, _ = _legs(ik, t, R)
        error = target - np.linalg.norm(legs, axis=0)
        residual = float(np.abs(error).max())
        if residual <= tolerance:
            iterations -= 1
            break
        J = _jacobian_from_R(ik, t, R)
        try:
            step = np.linalg.solve(J, error)
        except np.linalg.LinAlgError:
            break
        t = t + step[:3]
        R = _exp_so3(step[3:]) @ R
    else:
        legs, _ = _legs(ik, t, R)
        residual = float(np.abs(target - np.linalg.norm(legs, axis=0)).max())

    # Réorthonormalisation (dérive numérique des produits successifs)
    u, _, vt = np.linalg.svd(R)
    R = u @ vt
    rpy = rotation_to_rpy(R)
    return ForwardKinematicsResult(translation=t, rotation=rpy, rotation_matrix=R,
                                   converged=residual <= tolerance, iterations=iterations,
                                   residual=residual,
                                   condition=singularity_measures(ik, t, rpy)['condition'])


def pose_from_actuator_positions(ik: InverseKinematics, positions: Sequence[float],
                                 working_height: float,
                                 initial_translation: Optional[Sequence[float]] = None,
                                 initial_rotation_rad: Optional[Sequence[float]] = None,
                                 **solver) -> ForwardKinematicsResult:
    """
    Pose à partir des allongements des vérins (codeurs du banc, joints du URDF).

    Inverse de :func:`src.core.feasibility.actuator_positions` : ``positions`` (m) est
    l'allongement depuis la pose neutre de l'IK ; la translation renvoyée est **relative
    à la position de travail** (``working_height`` au-dessus de la pose neutre), comme
    les consignes du tableau de bord. L'estimation initiale, si elle est donnée, suit la
    même convention.
    """
    neutral = np.linalg.norm(_legs(ik, np.zeros(3), np.eye(3))[0], axis=0)
    offset = np.array([0.0, 0.0, working_height])
    t0 = offset if initial_translation is None else np.asarray(initial_translation, dtype=float) + offset
    result = forward_kinematics(ik, neutral + np.asarray(positions, dtype=float), t0,
                                initial_rotation_rad, **solver)
    result.translation = result.translation - offset
    return result


def solver_settings(config: dict) -> dict:
    """Paramètres du solveur lus dans la configuration (section ``kinematics.forward``)."""
    fk = (config.get('kinematics') or {}).get('forward') or {}
    return dict(tolerance=float(fk.get('tolerance', DEFAULT_TOLERANCE)),
                max_iterations=int(fk.get('max_iterations', DEFAULT_MAX_ITERATIONS)))
