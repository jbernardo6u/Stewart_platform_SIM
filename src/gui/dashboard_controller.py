"""
Logique du tableau de bord (sans interface graphique)
=====================================================

Relie la consigne de pose, la faisabilité (course des vérins), la simulation PyBullet
et la lecture des trajectoires. Testable sans affichage : ``src/gui/dashboard.py``
n'en est que la vue.

Convention : poses ``[x, y, z]`` en mm et ``[roll, pitch, yaw]`` en degrés, relatives à la
position de travail (comme ``PyBulletSimulator``).
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

from ..core.config import load_config, project_path
from ..core.feasibility import actuator_positions, check_trajectory, leg_tilt_deg, stroke_usage
from ..core.platform import StewartPlatform
from ..core import scenarios

AXES = ['x', 'y', 'z', 'roll', 'pitch', 'yaw']
PHYSICS_RATE = 240.0      # Hz, pas de PyBulletSimulator
MAX_STEPS_PER_TICK = 40   # rattrapage maximal si l'interface prend du retard
HISTORY_SECONDS = 10.0


@dataclass
class TrajectoryRun:
    """Lecture d'un scénario en cours."""
    name: str
    trajectory: scenarios.Trajectory
    time: float = 0.0
    errors: List[Tuple[float, float]] = field(default_factory=list)   # (mm, deg)

    @property
    def duration(self) -> float:
        return float(self.trajectory[0][-1])

    @property
    def finished(self) -> bool:
        return self.time >= self.duration


class DashboardController:
    """État et actions du tableau de bord."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        platform_cfg = self.config['platform']
        self.working_height = float(platform_cfg['working_height'])
        self.stroke = tuple(platform_cfg['actuator_stroke'])
        self.urdf_path = project_path(self.config['simulation']['urdf_path'])
        limits = self.config['gui']['dashboard']['limits']
        self.limits = {axis: tuple(limits[axis]) for axis in AXES}
        # IK de la géométrie identifiée (EXP-001), même modèle que la simulation
        self.ik = StewartPlatform.from_urdf(self.urdf_path).kinematics

        self.command = np.zeros(6)
        self.simulator = None
        self.sim_time = 0.0
        self.measured: Optional[np.ndarray] = None
        self.history: Deque[Tuple[float, float, float]] = deque()
        self.run: Optional[TrajectoryRun] = None
        self.last_run_report: Optional[Dict] = None

    # --- consigne et faisabilité -------------------------------------------------
    def set_command(self, pose) -> None:
        """Nouvelle consigne [x, y, z (mm), roll, pitch, yaw (deg)], bornée aux limites."""
        lo = np.array([self.limits[a][0] for a in AXES])
        hi = np.array([self.limits[a][1] for a in AXES])
        self.command = np.clip(np.asarray(pose, dtype=float), lo, hi)
        if self.simulator is not None:
            self.simulator.update_platform_pose({'position': self.command[:3].tolist(),
                                                 'rotation': self.command[3:].tolist()})

    def evaluate(self, pose=None) -> Dict:
        """Positions des vérins (m), taux de course, saturation et inclinaison des jambes."""
        pose = self.command if pose is None else np.asarray(pose, dtype=float)
        t, r = pose[:3] / 1000.0, pose[3:]
        q = actuator_positions(self.ik, t, r, self.working_height)
        usage = stroke_usage(q, self.stroke)
        saturated = (usage < 0) | (usage > 1)
        return dict(positions=q, usage=usage, saturated=saturated,
                    reachable=not saturated.any(),
                    tilt_max=float(leg_tilt_deg(self.ik, t, r, self.working_height).max()))

    # --- simulation --------------------------------------------------------------
    @property
    def connected(self) -> bool:
        return self.simulator is not None

    def connect(self, offscreen: bool = True) -> None:
        """Simulation PyBullet en mode DIRECT (rendu dans le tableau de bord)."""
        from ..simulation.pybullet_sim import PyBulletSimulator
        if self.connected:
            return
        sim = PyBulletSimulator(self.urdf_path, gui=False, offscreen=offscreen)
        if not sim.connect():
            raise RuntimeError("Échec de la connexion à la simulation PyBullet")
        self.simulator = sim
        self.sim_time = 0.0
        self.history.clear()
        self.set_command(self.command)

    def disconnect(self) -> None:
        if self.simulator is not None:
            self.simulator.disconnect()
        self.simulator = None
        self.measured = None
        self.run = None

    def set_gravity(self, enabled: bool) -> None:
        if self.simulator is not None:
            self.simulator.set_gravity([0, 0, -9.81 if enabled else 0.0])

    def reset(self) -> None:
        """Arrête la trajectoire, remet la consigne et la simulation à la position de travail."""
        self.run = None
        self.command = np.zeros(6)
        if self.simulator is not None:
            self.simulator.reset_simulation()
            self.set_command(self.command)
        self.history.clear()

    def emergency_stop(self) -> None:
        """Arrête la trajectoire et fige la consigne sur la pose mesurée (ou courante)."""
        self.run = None
        if self.measured is not None:
            self.set_command(self.measured)

    # --- trajectoires -----------------------------------------------------------
    def check_scenario(self, name: str) -> Dict:
        _, trans, rot = scenarios.get_scenario(name)
        report = check_trajectory(self.ik, trans, rot, self.working_height, self.stroke)
        span = self.stroke[1] - self.stroke[0]
        report['usage_max'] = float(((report['max'] - self.stroke[0]) / span).max())
        report['usage_min'] = float(((report['min'] - self.stroke[0]) / span).min())
        return report

    def start_scenario(self, name: str) -> Dict:
        """Lance un scénario s'il est réalisable ; renvoie le rapport de faisabilité."""
        report = self.check_scenario(name)
        if report['feasible']:
            self.run = TrajectoryRun(name, scenarios.get_scenario(name))
            self.last_run_report = None
        return report

    def stop_scenario(self) -> None:
        self.run = None

    @property
    def progress(self) -> float:
        return 0.0 if self.run is None else min(1.0, self.run.time / self.run.duration)

    # --- boucle ------------------------------------------------------------------
    def tick(self, dt: float) -> None:
        """
        Avance de ``dt`` secondes : trajectoire, puis physique (au pas de 1/240 s),
        puis mesure de la pose et de l'écart consigne/mesure.
        """
        steps = int(np.clip(round(dt * PHYSICS_RATE), 1, MAX_STEPS_PER_TICK))
        dt_sim = steps / PHYSICS_RATE if self.connected else dt
        if self.run is not None:
            self.run.time += dt_sim
            t, r = scenarios.sample(self.run.trajectory, self.run.time)
            self.set_command(np.concatenate([t * 1000.0, r]))
        if self.simulator is None:
            self._finish_run_if_done()
            return
        self.simulator.step_simulation(steps=steps)
        self.sim_time += dt_sim
        state = self.simulator.get_platform_state()
        self.measured = np.array(state['position'] + state['rotation'])
        err_mm = float(np.linalg.norm(self.measured[:3] - self.command[:3]))
        err_deg = float(np.abs(self.measured[3:] - self.command[3:]).max())
        self.history.append((self.sim_time, err_mm, err_deg))
        while self.history and self.history[0][0] < self.sim_time - HISTORY_SECONDS:
            self.history.popleft()
        if self.run is not None:
            self.run.errors.append((err_mm, err_deg))
        self._finish_run_if_done()

    def _finish_run_if_done(self) -> None:
        if self.run is None or not self.run.finished:
            return
        errors = np.array(self.run.errors) if self.run.errors else np.zeros((1, 2))
        self.last_run_report = dict(
            name=self.run.name, duration=self.run.duration,
            rms_mm=float(np.sqrt(np.mean(errors[:, 0] ** 2))), max_mm=float(errors[:, 0].max()),
            rms_deg=float(np.sqrt(np.mean(errors[:, 1] ** 2))), max_deg=float(errors[:, 1].max()),
            simulated=self.connected)
        self.run = None
