"""
Arduino virtuel du démonstrateur REM
====================================

Émule ``pilotage_feedback_mp.ino`` (Demonstrateur_REM) au niveau du protocole série,
pour que ``stewart_node``, ``manual_stewart_node``, ``posHome_node`` et
``motor_test_interface`` tournent **sans modification** sur la simulation :

- au démarrage : ``Arduino connecte via USB - Pret`` ;
- réception : ``t1,...,t6\\n`` (cm, consignes absolues depuis le zéro des codeurs) ;
- à chaque boucle (20 ms) : ``p1,...,p6`` (cm, 2 décimales).

Comportement des vérins, comme le firmware : arrêt quand ``|erreur| ≤ 0,10 cm``,
redémarrage quand ``|erreur| ≥ 0,25 cm`` (ou à toute consigne qui s'écarte de plus
de 0,10 cm), PWM ``pwm_min + 35·|erreur|`` borné à ``pwm_max``, rampe de 12 par
boucle. La vitesse d'un vérin est supposée proportionnelle au PWM
(``speed_cm_s_at_full_pwm``, **hypothèse à mesurer**). Les butées physiques bornent
la course. Le PID du firmware est calculé mais n'agit pas sur le PWM : il n'est pas
émulé.

:class:`PtySerialLink` fournit le port série : une paire de pseudo-terminaux, dont
l'extrémité esclave est exposée par un lien symbolique stable (``serial.port`` de la
configuration de simulation). Ni ``socat`` ni droits administrateur ne sont requis.
"""

import os
import termios
import tty
from typing import List, Optional

import numpy as np


class VirtualArduinoFirmware:
    """Modèle des 6 vérins et du protocole, sans entrée/sortie (testable seul)."""

    MOTOR_COUNT = 6

    def __init__(self, actuators_cfg: dict, initial_positions_cm=None):
        a = actuators_cfg
        self.stop_tol = float(a['stop_tolerance_cm'])
        self.restart_tol = float(a['restart_tolerance_cm'])
        self.pwm_min = int(a['pwm_min'])
        self.pwm_max = int(a['pwm_max'])
        self.pwm_ramp = int(a['pwm_ramp_step'])
        self.pwm_per_cm = float(a['pwm_per_cm'])
        self.loop_period = float(a['loop_period_s'])
        self.speed_full = float(a['speed_cm_s_at_full_pwm'])
        self.ready_message = str(a['ready_message'])
        self.lower, self.upper = (float(v) for v in a['stroke_cm'])
        n = self.MOTOR_COUNT
        self.position = np.zeros(n) if initial_positions_cm is None else np.array(initial_positions_cm, float)
        self.target = self.position.copy()
        self.active = np.zeros(n, dtype=bool)
        self.pwm = np.zeros(n, dtype=int)
        self._buffer = ''

    # --- réception (lireConsignesSerie) ---
    def receive(self, data: str) -> List[List[float]]:
        """Ajoute des caractères reçus ; applique et renvoie les consignes complètes."""
        applied = []
        for c in data:
            if c == '\n':
                applied.append(self._apply_line(self._buffer))
                self._buffer = ''
            elif c != '\r':
                self._buffer += c
        return applied

    def _apply_line(self, line: str) -> List[float]:
        values = []
        for index, field in enumerate((line + ',').split(',')[:-1][:self.MOTOR_COUNT]):
            target = _to_float(field)   # String.toFloat() : 0 si invalide
            self.target[index] = target
            if abs(target - self.position[index]) >= self.stop_tol:
                self.active[index] = True
            values.append(target)
        return values

    # --- une boucle du firmware ---
    def step(self, dt: Optional[float] = None) -> None:
        """Avance d'une boucle (``loop_period_s`` par défaut) : états, PWM, déplacement."""
        dt = self.loop_period if dt is None else dt
        for i in range(self.MOTOR_COUNT):
            error = self.target[i] - self.position[i]
            if self.active[i] and abs(error) <= self.stop_tol:
                self.active[i] = False
            elif not self.active[i] and abs(error) >= self.restart_tol:
                self.active[i] = True
            if not self.active[i]:
                self.pwm[i] = 0
                continue
            pwm_target = int(np.clip(self.pwm_min + int(abs(error) * self.pwm_per_cm),
                                     self.pwm_min, self.pwm_max))
            if self.pwm[i] < pwm_target:
                self.pwm[i] = min(self.pwm[i] + self.pwm_ramp, pwm_target)
            elif self.pwm[i] > pwm_target:
                self.pwm[i] = max(self.pwm[i] - self.pwm_ramp, pwm_target)
            move = np.sign(error) * self.speed_full * self.pwm[i] / 255.0 * dt
            # Le firmware n'arrête un vérin qu'à la boucle suivante : il peut dépasser la
            # consigne d'un pas, comme le vrai mécanisme (inertie négligée).
            self.position[i] = float(np.clip(self.position[i] + move, self.lower, self.upper))

    def feedback_line(self) -> str:
        """Ligne de retour envoyée à chaque boucle : positions (cm) à 2 décimales."""
        return ','.join(f'{p:.2f}' for p in self.position)


def _to_float(text: str) -> float:
    """Équivalent de ``String.toFloat()`` d'Arduino : préfixe numérique, 0 sinon."""
    text = text.strip()
    for end in range(len(text), 0, -1):
        try:
            return float(text[:end])
        except ValueError:
            continue
    return 0.0


class PtySerialLink:
    """
    Port série virtuel : paire de pseudo-terminaux, côté nœud exposé par ``link_path``.

    Le côté maître est lu et écrit par l'Arduino virtuel ; les nœuds ouvrent
    ``link_path`` avec pyserial comme ``/dev/ttyACM0`` (le débit est ignoré).
    """

    def __init__(self, link_path: str):
        self.link_path = os.path.abspath(os.path.expanduser(link_path))
        self.master_fd, self._slave_fd = os.openpty()
        tty.setraw(self._slave_fd)
        attrs = termios.tcgetattr(self._slave_fd)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(self._slave_fd, termios.TCSANOW, attrs)
        os.set_blocking(self.master_fd, False)
        self.slave_name = os.ttyname(self._slave_fd)
        os.makedirs(os.path.dirname(self.link_path), exist_ok=True)
        if os.path.islink(self.link_path) or os.path.exists(self.link_path):
            os.remove(self.link_path)
        os.symlink(self.slave_name, self.link_path)
        self._pending = ''

    def read_text(self) -> str:
        """Caractères disponibles côté maître (non bloquant)."""
        chunks = []
        while True:
            try:
                data = os.read(self.master_fd, 4096)
            except (BlockingIOError, OSError):
                break
            if not data:
                break
            chunks.append(data.decode(errors='ignore'))
        return ''.join(chunks)

    def write_line(self, line: str) -> None:
        """Écrit une ligne terminée par ``\\r\\n`` (comme ``Serial.println``)."""
        try:
            os.write(self.master_fd, (line + '\r\n').encode())
        except (BlockingIOError, OSError):
            pass   # personne ne lit : le tampon du pty est plein, on perd la ligne comme une UART

    def close(self) -> None:
        for fd in (self.master_fd, self._slave_fd):
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.islink(self.link_path):
            os.remove(self.link_path)
