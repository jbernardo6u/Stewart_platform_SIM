"""
Mécanisme physique du démonstrateur REM
=======================================

Le banc est un hexapode 6-6 : base de rayon 7,5 cm, plateforme de 4 cm. Une jambe
mesure ``length_at_zero_cm`` quand son codeur vaut 0 (position home à la mise sous
tension) ; elle s'allonge de la valeur du codeur (cm).

On utilise les **vraies** attaches (base = grand cercle), et non celles de l'IK du
banc, qui inverse base et plateforme (défaut D1 du dépôt du banc) : le jumeau
reproduit le mécanisme, les nœuds du banc gardent leur IK, et l'écart entre les deux
apparaît donc en simulation comme sur le banc.

Unités : m et rad en interne ; les codeurs du banc sont en cm.
"""

from typing import Optional, Sequence

import numpy as np

from ..core.forward_kinematics import ForwardKinematicsResult, forward_kinematics, leg_lengths
from ..core.kinematics import InverseKinematics


class BenchGeometry:
    """Géométrie du banc lue dans la section ``geometry``/``actuators`` de bench_rem.yaml."""

    def __init__(self, config: dict):
        g, a = config['geometry'], config['actuators']
        self.ik = InverseKinematics(g['radius_base'], g['radius_platform'],
                                    g['gamma_base'], g['gamma_platform'])
        self.ik.home_pos = np.asarray(g['home_position'], dtype=float)
        self.length_at_zero = float(a['length_at_zero_cm']) / 100.0
        self.stroke = np.asarray(a['stroke_cm'], dtype=float) / 100.0
        P, B = self.ik.calculate_attachment_points()
        self.platform_points = np.asarray(P, dtype=float)   # (3, 6), repère plateforme
        self.base_points = np.asarray(B, dtype=float)       # (3, 6), repère base = monde
        self._last: Optional[ForwardKinematicsResult] = None

    def leg_lengths(self, translation: Sequence[float], rotation_rad: Sequence[float]) -> np.ndarray:
        """Longueurs (m) pour une pose (translation depuis ``home_position``, rad)."""
        return leg_lengths(self.ik, translation, rotation_rad)

    def encoders_cm(self, translation, rotation_rad) -> np.ndarray:
        """Valeurs des codeurs (cm) qui placent la plateforme dans la pose demandée."""
        return (self.leg_lengths(translation, rotation_rad) - self.length_at_zero) * 100.0

    def pose_from_encoders(self, encoders_cm: Sequence[float]) -> ForwardKinematicsResult:
        """
        Pose de la plateforme (FK) à partir des codeurs (cm).

        La FK repart de la dernière solution (continuité de branche, convergence en 1 à 2
        itérations dans la boucle à 50 Hz) ; la première fois, de ``home_position``.
        """
        lengths = self.length_at_zero + np.asarray(encoders_cm, dtype=float) / 100.0
        t0 = None if self._last is None else self._last.translation
        r0 = None if self._last is None else self._last.rotation
        result = forward_kinematics(self.ik, lengths, t0, r0)
        if not result.converged:   # repli : départ de la pose home
            result = forward_kinematics(self.ik, lengths)
        if result.converged:
            self._last = result
        return result

    def platform_position_world(self, translation) -> np.ndarray:
        """Centre de la plateforme dans le monde (origine = centre de la base)."""
        return self.ik.home_pos + np.asarray(translation, dtype=float)

    def legs_world(self, translation, R: np.ndarray):
        """Attaches base (3, 6) et plateforme (3, 6) dans le monde, pour une pose."""
        top = self.platform_position_world(translation)[:, None] + R @ self.platform_points
        return self.base_points.copy(), top
