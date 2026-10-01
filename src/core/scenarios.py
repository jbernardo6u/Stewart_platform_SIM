"""
Scénarios de mouvement
======================

Trajectoires horodatées, réalisables par la plateforme, utilisées par le tableau de bord,
``scripts/run_trajectory.py`` et les tests. Chaque scénario renvoie ``(t, translations,
rotations)`` : temps (s), translations (N, 3) en m et rotations (N, 3) en degrés,
**relatives à la position de travail** (convention de ``src.core.feasibility``).

Les points de passage sont reliés par des polynômes d'ordre 5 (vitesse et accélération
nulles aux points de passage), ce qui évite les à-coups sur les vérins.
"""

from typing import Callable, Dict, List, Sequence, Tuple

import numpy as np

Trajectory = Tuple[np.ndarray, np.ndarray, np.ndarray]
SAMPLE_RATE = 60.0  # Hz


def _quintic(s: np.ndarray) -> np.ndarray:
    """Loi horaire 10s³ − 15s⁴ + 6s⁵ : vitesse et accélération nulles en 0 et 1."""
    return s ** 3 * (10 - 15 * s + 6 * s ** 2)


def waypoints_trajectory(waypoints: Sequence[Tuple[float, Sequence[float]]],
                         sample_rate: float = SAMPLE_RATE) -> Trajectory:
    """
    Trajectoire passant par des poses, avec une durée par segment.

    Args:
        waypoints: [(durée du segment en s, [x, y, z (mm), roll, pitch, yaw (deg)]), ...] ;
                   la durée du premier point est ignorée (pose de départ)
    """
    poses = np.array([w[1] for w in waypoints], dtype=float)
    times, samples = [0.0], [poses[0]]
    t0 = 0.0
    for (duration, _), start, end in zip(waypoints[1:], poses[:-1], poses[1:]):
        n = max(1, int(round(duration * sample_rate)))
        s = _quintic(np.arange(1, n + 1) / n)
        samples.extend(start + np.outer(s, end - start))
        times.extend(t0 + np.arange(1, n + 1) / sample_rate)
        t0 += n / sample_rate
    samples = np.array(samples)
    return np.array(times), samples[:, :3] / 1000.0, samples[:, 3:]


def hitch_approach() -> Trajectory:
    """
    Approche d'attelage (illustrative) : la plateforme part d'un désalignement latéral
    et angulaire, s'aligne, monte pour l'engagement, se maintient puis redescend.
    Les amplitudes seront à recaler sur le cahier des charges REM.
    """
    return waypoints_trajectory([
        (0.0, [0, 0, 0, 0, 0, 0]),
        (2.0, [25, -20, -30, 0, 0, 8]),     # désalignement initial, plateforme basse
        (1.0, [25, -20, -30, 0, 0, 8]),     # détection
        (3.0, [0, 0, -30, 0, 0, 0]),        # alignement x, y, lacet
        (2.0, [0, 0, 20, 0, 0, 0]),         # montée : engagement
        (1.5, [0, 0, 20, 0, 0, 0]),         # maintien
        (2.0, [0, 0, 0, 0, 0, 0]),          # retour à la position de travail
    ])


def translation_square(side_mm: float = 40.0) -> Trajectory:
    """Carré dans le plan horizontal, orientation constante."""
    a = side_mm / 2
    return waypoints_trajectory([
        (0.0, [0, 0, 0, 0, 0, 0]), (1.0, [a, a, 0, 0, 0, 0]), (1.5, [-a, a, 0, 0, 0, 0]),
        (1.5, [-a, -a, 0, 0, 0, 0]), (1.5, [a, -a, 0, 0, 0, 0]), (1.5, [a, a, 0, 0, 0, 0]),
        (1.0, [0, 0, 0, 0, 0, 0]),
    ])


def orientation_sweep() -> Trajectory:
    """Roulis, tangage puis lacet successifs, position fixe."""
    return waypoints_trajectory([
        (0.0, [0, 0, 0, 0, 0, 0]),
        (1.0, [0, 0, 0, 15, 0, 0]), (2.0, [0, 0, 0, -15, 0, 0]), (1.0, [0, 0, 0, 0, 0, 0]),
        (1.0, [0, 0, 0, 0, 15, 0]), (2.0, [0, 0, 0, 0, -15, 0]), (1.0, [0, 0, 0, 0, 0, 0]),
        (1.5, [0, 0, 0, 0, 0, 30]), (3.0, [0, 0, 0, 0, 0, -30]), (1.5, [0, 0, 0, 0, 0, 0]),
    ])


def multi_axis_sine(duration: float = 12.0, sample_rate: float = SAMPLE_RATE) -> Trajectory:
    """Sinusoïdes simultanées sur les six axes, démarrage et arrêt progressifs."""
    t = np.arange(0, duration + 1e-9, 1 / sample_rate)
    ramp = np.clip(np.minimum(t, duration - t) / 1.5, 0, 1)   # rampe de 1,5 s
    envelope = _quintic(ramp)
    amp = np.array([10, 10, 5, 12, 8, 15], dtype=float)       # mm, mm, mm, deg, deg, deg
    freq = np.array([0.5, 0.3, 0.2, 0.2, 0.3, 0.1])
    phase = np.array([0, np.pi / 2, np.pi / 4, 0, np.pi / 3, 0])
    samples = envelope[:, None] * amp * np.sin(2 * np.pi * freq * t[:, None] + phase)
    return t, samples[:, :3] / 1000.0, samples[:, 3:]


SCENARIOS: Dict[str, Tuple[str, Callable[[], Trajectory]]] = {
    'approach': ("Approche d'attelage", hitch_approach),
    'square': ("Carré horizontal (40 mm)", translation_square),
    'orientation': ("Balayage roulis / tangage / lacet", orientation_sweep),
    'sine': ("Sinusoïdes 6 axes", multi_axis_sine),
}


def scenario_names() -> List[str]:
    return list(SCENARIOS)


def get_scenario(name: str) -> Trajectory:
    """Trajectoire d'un scénario de ``SCENARIOS`` (clé), voir le module."""
    return SCENARIOS[name][1]()


def sample(trajectory: Trajectory, time: float) -> Tuple[np.ndarray, np.ndarray]:
    """Pose (translation m, rotation deg) interpolée à l'instant ``time`` (bornée à la fin)."""
    t, trans, rot = trajectory
    pose = np.array([np.interp(time, t, col) for col in np.hstack([trans, rot]).T])
    return pose[:3], pose[3:]
