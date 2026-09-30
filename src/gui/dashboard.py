#!/usr/bin/env python3
"""
Tableau de bord de la plateforme Stewart (jumeau numérique REM)
===============================================================

Interface unique qui remplace les GUI Simple, Advanced et PyBullet :

- vue 3D de la simulation PyBullet, rendue hors écran dans la fenêtre (glisser pour
  tourner, molette pour zoomer) : pas de fenêtre PyBullet séparée ;
- consigne de pose sur 6 axes (curseurs ou saisie), relative à la position de travail ;
- état des 6 vérins : course utilisée, saturation, inclinaison des jambes ;
- écart consigne/mesure en direct ;
- scénarios de trajectoire vérifiés avant exécution, avec bilan de suivi.

La logique est dans ``dashboard_controller.DashboardController`` ; ce module n'est que la vue.

Usage : python3 -m src.gui.dashboard
"""

import time
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List

import numpy as np

try:
    import customtkinter as ctk
except ImportError as exc:  # pragma: no cover
    raise ImportError("customtkinter est requis : pip install -r requirements.txt") from exc

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from .dashboard_controller import AXES, DashboardController
from ..core import scenarios

LABELS = {'x': 'X', 'y': 'Y', 'z': 'Z', 'roll': 'Roulis', 'pitch': 'Tangage', 'yaw': 'Lacet'}
UNITS = {'x': 'mm', 'y': 'mm', 'z': 'mm', 'roll': '°', 'pitch': '°', 'yaw': '°'}
PRESETS = [
    ("Travail", [0, 0, 0, 0, 0, 0]),
    ("Haut", [0, 0, 60, 0, 0, 0]),
    ("Bas", [0, 0, -60, 0, 0, 0]),
    ("Désalignement", [25, -20, -30, 0, 0, 8]),
]
VIEWS = {"Iso": 'isometric', "Face": 'front', "Côté": 'side', "Dessus": 'top'}

# Couleurs (clair, sombre) : CustomTkinter choisit selon le mode d'apparence
COLORS = {
    'bg': ("#eef1f5", "#12151b"),
    'card': ("#ffffff", "#1b2029"),
    'sidebar': ("#e3e8ef", "#161a21"),
    'muted': ("#5b6472", "#8b95a5"),
    'text': ("#1b2029", "#e6e9ef"),
    'accent': ("#2f6fed", "#4c8dff"),
    'ok': ("#1f9d55", "#34c77b"),
    'warn': ("#d98a00", "#f5a524"),
    'danger': ("#d64545", "#ff5c5c"),
    'viewport': ("#dfe4ea", "#0d1015"),
}
TICK_MS = 16
PLOT_PERIOD = 0.2   # s


def _mode_color(pair):
    return pair[1] if ctk.get_appearance_mode() == "Dark" else pair[0]


class Card(ctk.CTkFrame):
    """Panneau à titre."""

    def __init__(self, master, title: str, **kwargs):
        super().__init__(master, fg_color=COLORS['card'], corner_radius=14, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title.upper(), text_color=COLORS['muted'],
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w",
                                                                   padx=16, pady=(12, 4))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.grid_rowconfigure(1, weight=1)


class StewartDashboard(ctk.CTk):
    """Fenêtre principale."""

    def __init__(self, controller: DashboardController = None):
        super().__init__(fg_color=COLORS['bg'])
        self.ctrl = controller or DashboardController()
        self.title("REM · Plateforme Stewart — tableau de bord")
        self.geometry("1560x940")
        self.minsize(1200, 760)
        self.render_size = tuple(self.ctrl.config['gui']['dashboard'].get('render_size', [960, 600]))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2, minsize=440)
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(1, weight=2)
        self._build_viewport(main)
        self._build_tracking(main)
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(16, 0))
        right.grid_columnconfigure(0, weight=1)
        self._build_pose(right)
        self._build_actuators(right)
        self._build_trajectories(right)

        self._photo = None
        self._drag = None
        self._last_tick = time.perf_counter()
        self._last_plot = 0.0
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._refresh_actuators()
        self._on_scenario_selected(self.scenario_menu.get())
        self.after(TICK_MS, self._loop)

    # --- construction ---------------------------------------------------------------
    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, fg_color=COLORS['sidebar'], corner_radius=0, width=250)
        bar.grid(row=0, column=0, sticky="nsw")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bar, text="REM · Stewart", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS['text']).grid(row=0, column=0, sticky="w", padx=20, pady=(24, 0))
        ctk.CTkLabel(bar, text="Jumeau numérique", text_color=COLORS['muted']).grid(
            row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        self._section(bar, "Simulation", 2)
        self.status = ctk.CTkLabel(bar, text="●  Déconnectée", text_color=COLORS['muted'], anchor="w")
        self.status.grid(row=3, column=0, sticky="ew", padx=20)
        self.connect_btn = ctk.CTkButton(bar, text="Connecter la simulation", height=38,
                                         command=self.toggle_connection)
        self.connect_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=(8, 8))
        self.gravity = ctk.CTkSwitch(bar, text="Gravité", command=self._on_gravity)
        self.gravity.select()
        self.gravity.grid(row=5, column=0, sticky="w", padx=20, pady=4)

        self._section(bar, "Vue 3D", 6)
        self.view_selector = ctk.CTkSegmentedButton(bar, values=list(VIEWS), command=self._on_view)
        self.view_selector.set("Iso")
        self.view_selector.grid(row=7, column=0, sticky="ew", padx=20)
        ctk.CTkLabel(bar, text="Glisser : tourner · molette : zoom", text_color=COLORS['muted'],
                     font=ctk.CTkFont(size=11)).grid(row=8, column=0, sticky="w", padx=20, pady=(4, 0))

        self._section(bar, "Actions", 9)
        ctk.CTkButton(bar, text="Réinitialiser", height=36, fg_color="transparent", border_width=1,
                      text_color=COLORS['text'], command=self.reset).grid(row=10, column=0, sticky="ew",
                                                                          padx=20, pady=4)
        bar.grid_rowconfigure(11, weight=1)
        ctk.CTkButton(bar, text="ARRÊT D'URGENCE", height=48, fg_color=COLORS['danger'],
                      hover_color=("#b93a3a", "#e04848"), font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.emergency_stop).grid(row=12, column=0, sticky="ew", padx=20, pady=(8, 12))
        self.appearance = ctk.CTkOptionMenu(bar, values=["Sombre", "Clair"], command=self._on_appearance,
                                            width=120)
        self.appearance.set("Sombre" if ctk.get_appearance_mode() == "Dark" else "Clair")
        self.appearance.grid(row=13, column=0, sticky="w", padx=20, pady=(0, 8))
        ctk.CTkLabel(bar, text="Géométrie identifiée (EXP-001)\nSuivi validé 0,28 mm (EXP-004)",
                     justify="left", text_color=COLORS['muted'], font=ctk.CTkFont(size=11)).grid(
            row=14, column=0, sticky="w", padx=20, pady=(0, 18))

    def _section(self, parent, title, row):
        ctk.CTkLabel(parent, text=title.upper(), text_color=COLORS['muted'],
                     font=ctk.CTkFont(size=11, weight="bold")).grid(row=row, column=0, sticky="w",
                                                                   padx=20, pady=(18, 4))

    def _build_viewport(self, main):
        card = Card(main, "Vue 3D")
        card.grid(row=0, column=0, sticky="nsew")
        card.body.grid_columnconfigure(0, weight=1)
        card.body.grid_rowconfigure(0, weight=1)
        self.viewport = tk.Label(card.body, bd=0, highlightthickness=0, bg=_mode_color(COLORS['viewport']),
                                 fg=_mode_color(COLORS['muted']), font=("TkDefaultFont", 13),
                                 text="Simulation déconnectée\n\nCliquez sur « Connecter la simulation »")
        self.viewport.grid(row=0, column=0, sticky="nsew")
        self.viewport.bind("<ButtonPress-1>", self._on_drag_start)
        self.viewport.bind("<B1-Motion>", self._on_drag)
        self.viewport.bind("<MouseWheel>", self._on_wheel)
        self.viewport.bind("<Button-4>", lambda e: self._zoom(0.9))
        self.viewport.bind("<Button-5>", lambda e: self._zoom(1.1))
        self.readout = ctk.CTkLabel(card.body, text="", text_color=COLORS['muted'], anchor="w",
                                    font=ctk.CTkFont(family="DejaVu Sans Mono", size=12), justify="left")
        self.readout.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def _build_tracking(self, main):
        card = Card(main, "Précision : écart entre consigne et pose mesurée")
        card.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        card.body.grid_columnconfigure(0, weight=1)
        card.body.grid_rowconfigure(1, weight=1)
        criteria = self.ctrl.config['gui']['dashboard']['tracking_criteria']
        self.criterion_mm = float(criteria['position_mm'])
        self.criterion_deg = float(criteria['orientation_deg'])
        ctk.CTkLabel(card.body, justify="left", anchor="w", text_color=COLORS['muted'],
                     font=ctk.CTkFont(size=11),
                     wraplength=560,
                     text=("Position : distance entre le centre mesuré de la plateforme et la consigne. "
                           "Orientation : plus grand écart des trois angles. "
                           f"Pointillés : précision validée (EXP-004), {self.criterion_mm:g} mm et "
                           f"{self.criterion_deg:g}°. Un pic pendant un mouvement = retard de suivi.")
                     ).grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.figure = Figure(figsize=(6, 2.4), dpi=100)
        self.ax_mm, self.ax_deg = self.figure.subplots(2, 1, sharex=True)
        (self.line_mm,) = self.ax_mm.plot([], [], lw=1.8)
        (self.line_deg,) = self.ax_deg.plot([], [], lw=1.8)
        self.crit_mm = self.ax_mm.axhline(self.criterion_mm, ls=":", lw=1.2)
        self.crit_deg = self.ax_deg.axhline(self.criterion_deg, ls=":", lw=1.2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=card.body)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        self._style_plot()

    def _build_pose(self, right):
        card = Card(right, "Consigne de pose — relative à la position de travail")
        card.grid(row=0, column=0, sticky="ew")
        body = card.body
        body.grid_columnconfigure(1, weight=1)
        self.sliders: Dict[str, ctk.CTkSlider] = {}
        self.entries: Dict[str, ctk.CTkEntry] = {}
        for i, axis in enumerate(AXES):
            lo, hi = self.ctrl.limits[axis]
            ctk.CTkLabel(body, text=LABELS[axis], width=64, anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            slider = ctk.CTkSlider(body, from_=lo, to=hi, number_of_steps=int((hi - lo) * 2),
                                   command=lambda v, a=axis: self._on_slider(a, v))
            slider.set(0)
            slider.grid(row=i, column=1, sticky="ew", padx=8)
            entry = ctk.CTkEntry(body, width=70, justify="right")
            entry.insert(0, "0.0")
            entry.bind("<Return>", lambda e, a=axis: self._on_entry(a))
            entry.bind("<FocusOut>", lambda e, a=axis: self._on_entry(a))
            entry.grid(row=i, column=2)
            ctk.CTkLabel(body, text=UNITS[axis], width=28, text_color=COLORS['muted']).grid(row=i, column=3)
            self.sliders[axis], self.entries[axis] = slider, entry
        presets = ctk.CTkFrame(body, fg_color="transparent")
        presets.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        for j, (name, pose) in enumerate(PRESETS):
            presets.grid_columnconfigure(j, weight=1)
            ctk.CTkButton(presets, text=name, height=30, fg_color="transparent", border_width=1,
                          text_color=COLORS['text'],
                          command=lambda p=pose: self.apply_pose(p)).grid(row=0, column=j, sticky="ew", padx=3)

    def _build_actuators(self, right):
        card = Card(right, "Vérins — course utilisée")
        card.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        body = card.body
        body.grid_columnconfigure(1, weight=1)
        self.bars: List[ctk.CTkProgressBar] = []
        self.bar_labels: List[ctk.CTkLabel] = []
        for i in range(6):
            ctk.CTkLabel(body, text=f"V{i + 1}", width=32, anchor="w").grid(row=i, column=0, pady=3)
            bar = ctk.CTkProgressBar(body, height=12, corner_radius=6)
            bar.grid(row=i, column=1, sticky="ew", padx=8)
            label = ctk.CTkLabel(body, text="", width=120, anchor="e",
                                 font=ctk.CTkFont(family="DejaVu Sans Mono", size=12))
            label.grid(row=i, column=2)
            self.bars.append(bar)
            self.bar_labels.append(label)
        self.tilt_label = ctk.CTkLabel(body, text="", text_color=COLORS['muted'], anchor="w")
        self.tilt_label.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.reach_banner = ctk.CTkLabel(body, text="", corner_radius=8, height=30,
                                         font=ctk.CTkFont(weight="bold"))
        self.reach_banner.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(6, 0))

    def _build_trajectories(self, right):
        card = Card(right, "Trajectoires")
        card.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        body = card.body
        body.grid_columnconfigure(0, weight=1)
        self.scenario_keys = {scenarios.SCENARIOS[k][0]: k for k in scenarios.scenario_names()}
        self.scenario_menu = ctk.CTkOptionMenu(body, values=list(self.scenario_keys),
                                               command=self._on_scenario_selected)
        self.scenario_menu.grid(row=0, column=0, sticky="ew")
        self.run_btn = ctk.CTkButton(body, text="Lancer", width=110, command=self.toggle_scenario)
        self.run_btn.grid(row=0, column=1, padx=(8, 0))
        self.feasibility_label = ctk.CTkLabel(body, text="", anchor="w", justify="left",
                                              text_color=COLORS['muted'])
        self.feasibility_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        self.progress = ctk.CTkProgressBar(body, height=8)
        self.progress.set(0)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.result_label = ctk.CTkLabel(body, text="", anchor="w", justify="left")
        self.result_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    # --- actions ----------------------------------------------------------------------
    def toggle_connection(self):
        if self.ctrl.connected:
            self.ctrl.disconnect()
            self._photo = None
            self.viewport.configure(image="", text="Simulation déconnectée\n\nCliquez sur « Connecter la simulation »")
            self.status.configure(text="●  Déconnectée", text_color=COLORS['muted'])
            self.connect_btn.configure(text="Connecter la simulation")
            return
        self.status.configure(text="●  Connexion…", text_color=COLORS['warn'])
        self.update_idletasks()
        try:
            self.ctrl.connect(offscreen=True)
        except Exception as e:
            self.status.configure(text="●  Erreur", text_color=COLORS['danger'])
            messagebox.showerror("Simulation", str(e))
            return
        self.ctrl.set_gravity(bool(self.gravity.get()))
        self.ctrl.simulator.set_camera_view(VIEWS[self.view_selector.get()])
        self.ctrl.simulator.style_scene()
        self._actuator_state = None
        renderer = "GPU (EGL)" if self.ctrl.simulator.egl_plugin is not None else "logiciel"
        self.status.configure(text=f"●  Connectée · rendu {renderer}", text_color=COLORS['ok'])
        self.connect_btn.configure(text="Déconnecter")

    def apply_pose(self, pose):
        self.ctrl.stop_scenario()
        self.ctrl.set_command(pose)
        self._sync_inputs()
        self._refresh_actuators()

    def reset(self):
        self.ctrl.reset()
        self._sync_inputs()
        self._refresh_actuators()
        self.progress.set(0)
        self.run_btn.configure(text="Lancer")

    def emergency_stop(self):
        self.ctrl.emergency_stop()
        self._sync_inputs()
        self.run_btn.configure(text="Lancer")
        self.result_label.configure(text="Arrêt d'urgence : consigne figée sur la pose mesurée",
                                    text_color=COLORS['danger'])

    def toggle_scenario(self):
        if self.ctrl.run is not None:
            self.ctrl.stop_scenario()
            self.run_btn.configure(text="Lancer")
            return
        report = self.ctrl.start_scenario(self.scenario_keys[self.scenario_menu.get()])
        if not report['feasible']:
            messagebox.showwarning("Trajectoire", "Scénario irréalisable : course des vérins dépassée")
            return
        self.run_btn.configure(text="Arrêter")
        mode = "" if self.ctrl.connected else " (cinématique seule : connectez la simulation pour mesurer le suivi)"
        self.result_label.configure(text=f"En cours…{mode}", text_color=COLORS['muted'])

    # --- événements ----------------------------------------------------------------
    def _on_slider(self, axis, value):
        pose = self.ctrl.command.copy()
        pose[AXES.index(axis)] = value
        self.ctrl.stop_scenario()
        self.ctrl.set_command(pose)
        self._set_entry(axis, value)
        self._refresh_actuators()

    def _on_entry(self, axis):
        try:
            value = float(self.entries[axis].get().replace(',', '.'))
        except ValueError:
            value = self.ctrl.command[AXES.index(axis)]
        pose = self.ctrl.command.copy()
        pose[AXES.index(axis)] = value
        self.apply_pose(pose)

    def _on_gravity(self):
        self.ctrl.set_gravity(bool(self.gravity.get()))

    def _on_view(self, name):
        if self.ctrl.connected:
            self.ctrl.simulator.set_camera_view(VIEWS[name])

    def _on_appearance(self, name):
        ctk.set_appearance_mode("dark" if name == "Sombre" else "light")
        self.viewport.configure(bg=_mode_color(COLORS['viewport']), fg=_mode_color(COLORS['muted']))
        self._style_plot()

    def _on_scenario_selected(self, label):
        report = self.ctrl.check_scenario(self.scenario_keys[label])
        duration = scenarios.get_scenario(self.scenario_keys[label])[0][-1]
        if report['feasible']:
            text = (f"Réalisable · {duration:.0f} s · course utilisée "
                    f"{report['usage_min'] * 100:.0f} à {report['usage_max'] * 100:.0f} %")
            color = COLORS['ok']
        else:
            text = f"Irréalisable : {report['saturated_ratio'] * 100:.0f} % des points hors course"
            color = COLORS['danger']
        self.feasibility_label.configure(text=text, text_color=color)

    def _on_drag_start(self, event):
        self._drag = (event.x, event.y)

    def _on_drag(self, event):
        if self._drag and self.ctrl.connected:
            dx, dy = event.x - self._drag[0], event.y - self._drag[1]
            self.ctrl.simulator.orbit_camera(d_yaw=-dx * 0.4, d_pitch=-dy * 0.3)
        self._drag = (event.x, event.y)

    def _on_wheel(self, event):
        self._zoom(0.9 if event.delta > 0 else 1.1)

    def _zoom(self, factor):
        if self.ctrl.connected:
            self.ctrl.simulator.orbit_camera(zoom=factor)

    # --- rafraîchissement ------------------------------------------------------------
    def _set_entry(self, axis, value):
        entry = self.entries[axis]
        if self.focus_get() is not entry:
            entry.delete(0, tk.END)
            entry.insert(0, f"{value:.1f}")

    def _sync_inputs(self):
        for axis, value in zip(AXES, self.ctrl.command):
            self.sliders[axis].set(value)
            self._set_entry(axis, value)

    def _refresh_actuators(self):
        ev = self.ctrl.evaluate()
        for bar, label, q, u, sat in zip(self.bars, self.bar_labels, ev['positions'], ev['usage'], ev['saturated']):
            bar.set(float(np.clip(u, 0, 1)))
            if sat:
                color = COLORS['danger']
            elif u < 0.1 or u > 0.9:
                color = COLORS['warn']
            else:
                color = COLORS['accent']
            bar.configure(progress_color=color)
            label.configure(text=f"{q * 1000:6.1f} mm {u * 100:4.0f} %",
                            text_color=COLORS['danger'] if sat else COLORS['text'])
        self._color_actuators_3d(ev['saturated'])
        self.tilt_label.configure(text=f"Inclinaison max des jambes : {ev['tilt_max']:.1f}°  "
                                       f"(position de travail : 19,7°)")
        if ev['reachable']:
            self.reach_banner.configure(text="Pose atteignable", fg_color=COLORS['card'],
                                        text_color=COLORS['ok'])
        else:
            self.reach_banner.configure(text="Pose hors course : vérins saturés", fg_color=COLORS['danger'],
                                        text_color="white")

    def _color_actuators_3d(self, saturated):
        state = tuple(bool(s) for s in saturated)
        if self.ctrl.connected and state != getattr(self, '_actuator_state', None):
            red, normal = (1.0, 0.36, 0.36, 1), self.ctrl.simulator._body_rgba
            self.ctrl.simulator.set_actuator_colors([red if s else normal for s in state])
            self._actuator_state = state

    def _refresh_readout(self):
        header = "         " + "".join(f"{LABELS[a][:4] + ' ' + UNITS[a]:>10s}" for a in AXES)
        rows = [header, "consigne " + "".join(f"{v:10.2f}" for v in self.ctrl.command)]
        if self.ctrl.measured is not None:
            rows.append("mesure   " + "".join(f"{v:10.2f}" for v in self.ctrl.measured))
        else:
            rows.append("mesure   " + f"{'— simulation déconnectée':>28s}")
        self.readout.configure(text="\n".join(rows))

    def _refresh_viewport(self):
        image = self.ctrl.simulator.render_image(*self.render_size)
        w, h = max(self.viewport.winfo_width(), 10), max(self.viewport.winfo_height(), 10)
        pil = Image.fromarray(image)
        scale = max(w / pil.width, h / pil.height)      # remplir la zone, recadrer au centre
        pil = pil.resize((max(1, int(pil.width * scale)), max(1, int(pil.height * scale))), Image.BILINEAR)
        left, top = (pil.width - w) // 2, (pil.height - h) // 2
        self._photo = ImageTk.PhotoImage(pil.crop((left, top, left + w, top + h)))
        self.viewport.configure(image=self._photo, text="")

    def _style_plot(self):
        fg, bg = _mode_color(COLORS['muted']), _mode_color(COLORS['card'])
        self.figure.set_facecolor(bg)
        for ax, line, crit, color in ((self.ax_mm, self.line_mm, self.crit_mm, COLORS['accent']),
                                      (self.ax_deg, self.line_deg, self.crit_deg, COLORS['warn'])):
            ax.set_facecolor(bg)
            ax.tick_params(colors=fg, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(fg)
                spine.set_alpha(0.3)
            ax.grid(alpha=0.15)
            line.set_color(_mode_color(color))
            crit.set_color(fg)
        self.ax_mm.set_ylabel("mm", color=fg, fontsize=9)
        self.ax_deg.set_ylabel("°", color=fg, fontsize=9)
        self.ax_deg.set_xlabel("temps simulé (s)", color=fg, fontsize=9)
        self._set_plot_titles(None, None)
        self.figure.tight_layout(pad=0.6)
        self.canvas.draw_idle()

    def _set_plot_titles(self, e_mm, e_deg):
        def title(ax, name, value, unit, color):
            text = f"{name} : " + ("—" if value is None else f"{value:.2f} {unit}" if unit == "mm"
                                   else f"{value:.3f}{unit}")
            ax.set_title(text, loc="left", fontsize=9, color=_mode_color(color), pad=3)
        title(self.ax_mm, "Écart de position", e_mm, "mm", COLORS['accent'])
        title(self.ax_deg, "Écart d'orientation", e_deg, "°", COLORS['warn'])

    def _refresh_plot(self):
        if not self.ctrl.history:
            return
        t, e_mm, e_deg = np.array(self.ctrl.history).T
        self.line_mm.set_data(t, e_mm)
        self.line_deg.set_data(t, e_deg)
        self.ax_mm.set_xlim(max(0.0, t[-1] - 10), max(10.0, t[-1]))
        self.ax_mm.set_ylim(0, max(2 * self.criterion_mm, e_mm.max() * 1.2))
        self.ax_deg.set_ylim(0, max(2 * self.criterion_deg, e_deg.max() * 1.2))
        self._set_plot_titles(e_mm[-1], e_deg[-1])
        self.canvas.draw_idle()

    def _refresh_run(self):
        if self.ctrl.run is not None:
            self.progress.set(self.ctrl.progress)
            self._sync_inputs()
            return
        report = self.ctrl.last_run_report
        if report is not None and self.run_btn.cget("text") == "Arrêter":
            self.progress.set(1.0)
            self.run_btn.configure(text="Lancer")
            if report['simulated']:
                text = (f"Terminé ({report['duration']:.1f} s) · écart RMS {report['rms_mm']:.2f} mm / "
                        f"{report['rms_deg']:.3f}° · max {report['max_mm']:.2f} mm / {report['max_deg']:.3f}°")
            else:
                text = f"Terminé ({report['duration']:.1f} s) · cinématique seule"
            self.result_label.configure(text=text, text_color=COLORS['text'])

    def _loop(self):
        now = time.perf_counter()
        dt = min(now - self._last_tick, 0.1)
        self._last_tick = now
        try:
            running = self.ctrl.run is not None
            self.ctrl.tick(dt)
            if running:
                self._refresh_actuators()
            self._refresh_run()
            self._refresh_readout()
            if self.ctrl.connected:
                self._refresh_viewport()
                if now - self._last_plot > PLOT_PERIOD:
                    self._refresh_plot()
                    self._last_plot = now
        except Exception as e:  # une erreur de rafraîchissement ne doit pas figer l'interface
            print(f"Dashboard update error: {e}")
        self.after(TICK_MS, self._loop)

    def on_closing(self):
        self.ctrl.disconnect()
        self.destroy()


def main():
    """Lance le tableau de bord."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = StewartDashboard()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.on_closing()


if __name__ == "__main__":
    main()
