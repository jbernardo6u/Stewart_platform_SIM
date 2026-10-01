"""
Faisabilité des poses et des trajectoires
=========================================

Vérifie qu'une pose ou une trajectoire reste dans la course des vérins, avant de
l'envoyer à la simulation ou au banc.

Convention : translations en mètres et rotations [roll, pitch, yaw] en degrés,
**relatives à la position de travail** (``working_height`` au-dessus de la pose neutre
de l'IK, où les vérins sont en butée basse). La position d'un vérin est son
allongement depuis la pose neutre, comme la consigne du joint prismatique du URDF.

Seule la course est vérifiée. L'inclinaison des jambes (``leg_tilt_deg``) est fournie à
titre indicatif : la limite des cardans n'est pas connue. Ni singularités, ni efforts
(Phases 2 et 3 de la roadmap).
"""

from typing import Dict, Sequence, Tuple

import numpy as np

from .kinematics import InverseKinematics


def actuator_positions(ik: InverseKinematics, translations, rotations,
                       working_height: float) -> np.ndarray:
    """
    Positions des vérins (m) pour une ou plusieurs poses.

    Args:
        ik: Cinématique inverse (idéalement la géométrie identifiée, ``StewartPlatform.from_urdf``)
        translations: (3,) ou (N, 3), en m, relatives à la position de travail
        rotations: (3,) ou (N, 3), en degrés
        working_height: Hauteur de travail (m)

    Returns:
        (6,) pour une pose, (N, 6) pour une trajectoire
    """
    t = np.atleast_2d(np.asarray(translations, dtype=float))
    r = np.atleast_2d(np.asarray(rotations, dtype=float))
    neutral = ik.solve([0, 0, 0], [0, 0, 0])
    q = np.array([ik.solve(ti + [0, 0, working_height], ri) - neutral for ti, ri in zip(t, r)])
    return q[0] if np.ndim(translations) == 1 else q


def leg_tilt_deg(ik: InverseKinematics, translation, rotation, working_height: float) -> np.ndarray:
    """
    Inclinaison (degrés) de chaque jambe par rapport à la verticale, pour une pose.

    Indicateur du débattement demandé aux cardans, dont la limite réelle n'est pas
    encore connue (à mesurer sur le banc) : 19° environ à la position de travail.
    """
    ik.solve(np.asarray(translation, dtype=float) + [0, 0, working_height], rotation)
    legs = ik.L - ik.B
    return np.degrees(np.arccos(legs[2] / np.linalg.norm(legs, axis=0)))


def check_trajectory(ik: InverseKinematics, translations, rotations, working_height: float,
                     stroke: Tuple[float, float]) -> Dict:
    """
    Vérifie qu'une trajectoire reste dans la course des vérins.

    Returns:
        dict avec ``positions`` (N, 6) m, ``saturated`` (N,) bool, ``feasible`` bool,
        ``saturated_ratio`` (fraction de points saturés), ``min``/``max`` (6,) m,
        ``margin`` (m) : plus petite distance aux butées (négative si saturée)
    """
    q = np.atleast_2d(actuator_positions(ik, np.atleast_2d(translations), np.atleast_2d(rotations),
                                         working_height))
    lo, hi = stroke
    saturated = np.any((q < lo) | (q > hi), axis=1)
    margin = float(min((q - lo).min(), (hi - q).min()))
    return dict(positions=q, saturated=saturated, feasible=not saturated.any(),
                saturated_ratio=float(saturated.mean()), min=q.min(axis=0), max=q.max(axis=0),
                margin=margin)


def stroke_usage(positions: Sequence[float], stroke: Tuple[float, float]) -> np.ndarray:
    """Fraction de course utilisée par vérin (0 = butée basse, 1 = butée haute), non bornée."""
    lo, hi = stroke
    return (np.asarray(positions, dtype=float) - lo) / (hi - lo)
