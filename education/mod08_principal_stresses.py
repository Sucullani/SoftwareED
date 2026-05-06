"""
Módulo 8 — Direcciones principales σ1 / σ2 + Círculo de Mohr

REDISEÑADO: Modo Overlay (propuesta UX 2026).

Patología corregida:
    Antes era un Toplevel con dos paneles matplotlib (malla + Mohr) y
    una "tarjeta de estado" que duplicaba los valores que ya están en
    el círculo. El alumno perdía el contexto del modelo y la conexión
    visual entre las cruces principales y el círculo era estática.

Diseño actual:
    1. NO abre Toplevel. Las cruces principales σ1 (rojo) / σ2 (azul) se
       dibujan SOBRE el MeshCanvas real, en cada nodo, escaladas por la
       magnitud relativa.
    2. Overlay flotante con el Círculo de Mohr del nodo seleccionado.
       Arrastrable y cerrable.
    3. Doble vínculo bidireccional canvas ↔ Mohr:
         · Click en un nodo del canvas → el círculo se redibuja en ese nodo.
         · Drag de un punto sobre el círculo → ALL las cruces de la malla
           rotan consistentemente, mostrando el estado en el plano rotado.
    4. Slider de escala de las cruces dentro del overlay.

Pedagogía:
    El círculo de Mohr es la GEOMETRÍA del tensor de estado. Convertirlo
    en un control activo (arrastrable) y verlo coordinar con todas las
    cruces de la malla a la vez muestra que un solo ángulo θ define el
    estado completo en cada punto.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.overlay_module import CanvasOverlayModule


# Paleta del overlay (mantiene el lenguaje cromático establecido).
_C_S1   = "#ef5350"   # rojo  — σ1 (mayor)
_C_S2   = "#42a5f5"   # azul  — σ2 (menor)
_C_HL   = "#ffeb3b"   # amarillo — nodo seleccionado
_C_DRAG = "#ffd54f"   # punto draggable en Mohr

_TAG = "edu_m8"        # tag canvas para todos los dibujos M8


class PrincipalStressesModule(CanvasOverlayModule):
    """M8 en modo Overlay: cruces sobre canvas + Mohr en panel flotante."""

    TITLE = "⑧  Direcciones principales  σ1 / σ2"
    PHASE = "post"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 460
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False

    def __init__(self, main_window, project, element_id):
        # Resolver: corremos solver UNA vez (cachemos stresses).
        self._solver_error: Optional[str] = None
        self.solution = None
        self.element_stresses = None
        self.nodal_avg = None
        self._sel_node: Optional[int] = None
        # Ángulo de rotación global (rad). 0 = estado natural; valores no-cero
        # rotan TODAS las cruces del canvas de forma consistente. Se setea
        # arrastrando el punto draggable sobre el círculo de Mohr.
        self._theta_rot = 0.0
        self._dragging_point = False

        # Widgets (creados en build_overlay)
        self._scale_var: Optional[tk.DoubleVar] = None
        self._fig: Optional[Figure] = None
        self._ax: Optional = None
        self._canvas_mpl: Optional[FigureCanvasTkAgg] = None
        self._lbl_node: Optional[ttk.Label] = None

        if project is not None and project.elements:
            self._ensure_solved(project)
            if self._sel_node is None and self.nodal_avg:
                # Pre-selección: el nodo con mayor σ1 (más crítico)
                self._sel_node = max(
                    self.nodal_avg,
                    key=lambda n: self.nodal_avg[n].get("sigma_1", 0.0),
                )
        super().__init__(main_window, project, element_id)

    def _ensure_solved(self, project) -> bool:
        try:
            from fem.solver import solve_system
            from fem.stress import compute_all_stresses
            self.solution = solve_system(project)
            self.element_stresses, self.nodal_avg = compute_all_stresses(
                project, self.solution,
            )
            return True
        except Exception as exc:
            self._solver_error = str(exc)
            return False

    # ── Construcción del overlay ───────────────────────────────────
    def build_overlay(self, body):
        if self._solver_error:
            tk.Label(
                body, bg="#222233", fg="#ef5350",
                text=("⚠ El solver no pudo procesar el modelo:\n\n"
                       f"{self._solver_error}\n\n"
                       "Volvé al pre-proceso para revisar restricciones y cargas."),
                justify="left", anchor="w", wraplength=400,
            ).pack(fill="both", expand=True, padx=10, pady=10)
            return

        # ── Header con info del nodo ─────────────────────────────
        self._lbl_node = ttk.Label(
            body, text="", font=("Segoe UI Semibold", 10),
            foreground=_C_HL,
        )
        self._lbl_node.pack(anchor="w", pady=(0, 4))

        ttk.Label(
            body,
            text=("Click en un nodo del canvas para verlo aquí.\n"
                   "Arrastra el punto naranja del círculo para rotar todas "
                   "las cruces de la malla."),
            font=("Segoe UI", 8), foreground="#9e9e9e",
            wraplength=420, justify="left",
        ).pack(anchor="w", pady=(0, 6))

        ttk.Separator(body).pack(fill="x", pady=(0, 4))

        # ── Slider de escala de cruces ────────────────────────────
        scale_row = ttk.Frame(body)
        scale_row.pack(fill="x", pady=(0, 6))
        ttk.Label(scale_row, text="Escala cruces:",
                   font=("Segoe UI", 9)).pack(side="left")
        self._scale_var = tk.DoubleVar(value=1.0)
        ttk.Scale(scale_row, from_=0.2, to=3.0, orient="horizontal",
                   variable=self._scale_var,
                   command=lambda _v: self._mesh.redraw(),
                   ).pack(side="left", fill="x", expand=True, padx=6)

        # ── Figura matplotlib del Mohr (con click+drag wired) ────
        fig_frame = ttk.Frame(body)
        fig_frame.pack(fill="both", expand=True)

        self._fig = Figure(figsize=(4.4, 4.0), dpi=100)
        self._fig.patch.set_facecolor("#222233")
        self._ax = self._fig.add_subplot(111)
        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=fig_frame)
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True)
        # Conectar eventos del backend matplotlib (no del Tk canvas)
        self._canvas_mpl.mpl_connect("button_press_event", self._on_mohr_press)
        self._canvas_mpl.mpl_connect("motion_notify_event", self._on_mohr_motion)
        self._canvas_mpl.mpl_connect("button_release_event",
                                       self._on_mohr_release)

        ttk.Button(
            body, text="↺ Resetear rotación (θ = 0)",
            bootstyle="secondary-outline-toolbutton",
            command=self._reset_rotation,
        ).pack(anchor="e", pady=(4, 0))

        # Render inicial
        self._redraw_mohr()

    # ── Capa educativa: cruces principales sobre el canvas ─────────
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if not self.nodal_avg:
            return
        try:
            scale_factor = float(self._scale_var.get()) if self._scale_var \
                                                          else 1.0
        except (tk.TclError, ValueError):
            scale_factor = 1.0

        # Tamaño base de las cruces: ~6% del tamaño del modelo.
        all_xs = [n.x for n in self.project.nodes.values()]
        all_ys = [n.y for n in self.project.nodes.values()]
        if not all_xs:
            return
        model_size = max(max(all_xs) - min(all_xs),
                          max(all_ys) - min(all_ys), 1.0)
        max_sigma = max(
            (max(abs(v.get("sigma_1", 0)), abs(v.get("sigma_2", 0)))
             for v in self.nodal_avg.values()),
            default=1.0,
        )
        if max_sigma < 1e-12:
            max_sigma = 1.0

        # Convertir model_size a pixeles vía la escala del MeshCanvas.
        L_world = model_size * 0.06 * scale_factor
        L_px = L_world * mesh.scale

        for nid, vals in self.nodal_avg.items():
            node = self.project.nodes.get(nid)
            if node is None:
                continue
            sx_screen, sy_screen = mesh.world_to_screen(node.x, node.y)
            sx = vals.get("sigma_x", 0.0)
            sy = vals.get("sigma_y", 0.0)
            txy = vals.get("tau_xy", 0.0)
            s1, s2, theta_p = self._principals(sx, sy, txy)
            # Aplicar la rotación interactiva del Mohr a las cruces:
            # equivale a "ver el estado en un plano girado theta_rot".
            theta_total = math.radians(theta_p) + self._theta_rot

            cos_t, sin_t = math.cos(theta_total), math.sin(theta_total)

            # Brazo σ1 (rojo)
            L1 = L_px * abs(s1) / max_sigma
            mesh.canvas.create_line(
                sx_screen - L1 * cos_t, sy_screen + L1 * sin_t,
                sx_screen + L1 * cos_t, sy_screen - L1 * sin_t,
                fill=_C_S1, width=2.4, capstyle="round", tags=_TAG,
            )
            # Brazo σ2 (azul) — perpendicular
            L2 = L_px * abs(s2) / max_sigma
            mesh.canvas.create_line(
                sx_screen + L2 * sin_t, sy_screen + L2 * cos_t,
                sx_screen - L2 * sin_t, sy_screen - L2 * cos_t,
                fill=_C_S2, width=2.4, capstyle="round", tags=_TAG,
            )
            # Punto del nodo (resaltado si es el seleccionado)
            if nid == self._sel_node:
                mesh.canvas.create_oval(
                    sx_screen - 6, sy_screen - 6,
                    sx_screen + 6, sy_screen + 6,
                    fill=_C_HL, outline="#fff", width=1.8, tags=_TAG,
                )
                mesh.canvas.create_text(
                    sx_screen + 10, sy_screen - 12,
                    text=f"N{nid}", fill=_C_HL,
                    font=("Consolas", 9, "bold"), tags=_TAG,
                )
            else:
                mesh.canvas.create_oval(
                    sx_screen - 2.5, sy_screen - 2.5,
                    sx_screen + 2.5, sy_screen + 2.5,
                    fill="#90a4ae", outline="", tags=_TAG,
                )

    # ── Click en nodo del canvas → cambiar el Mohr ─────────────────
    def on_node_selected(self, node_id):
        if not self.nodal_avg:
            return
        if node_id in self.nodal_avg:
            self._sel_node = node_id
            self._redraw_mohr()
            self._mesh.redraw()

    # ── Mohr: render + interacción drag ────────────────────────────
    def _principals(self, sx, sy, txy):
        avg = (sx + sy) / 2.0
        R = math.sqrt(((sx - sy) / 2.0) ** 2 + txy ** 2)
        s1 = avg + R
        s2 = avg - R
        if abs(sx - sy) + abs(txy) > 1e-12:
            theta_p = 0.5 * math.degrees(math.atan2(2 * txy, sx - sy))
        else:
            theta_p = 0.0
        return s1, s2, theta_p

    def _redraw_mohr(self):
        if self._ax is None or not self.nodal_avg:
            return
        ax = self._ax
        ax.clear()
        ax.set_facecolor("#222233")
        ax.tick_params(colors="#dfdfdf")
        for spine in ax.spines.values():
            spine.set_color("#dfdfdf")
        ax.grid(True, color="#404055", linewidth=0.4, alpha=0.6)
        ax.axhline(0, color="#dfdfdf", lw=0.7, alpha=0.6)
        ax.axvline(0, color="#dfdfdf", lw=0.7, alpha=0.6)

        if self._sel_node is None or self._sel_node not in self.nodal_avg:
            ax.text(0.5, 0.5, "(seleccione un nodo)",
                     ha="center", va="center", color="#9e9e9e",
                     fontsize=10, transform=ax.transAxes)
            self._canvas_mpl.draw_idle()
            return

        v = self.nodal_avg[self._sel_node]
        sx = v.get("sigma_x", 0.0)
        sy = v.get("sigma_y", 0.0)
        txy = v.get("tau_xy", 0.0)
        s1, s2, theta_p = self._principals(sx, sy, txy)
        avg = (sx + sy) / 2.0
        R = (s1 - s2) / 2.0

        # Círculo
        ang = np.linspace(0, 2 * math.pi, 200)
        ax.plot(avg + R * np.cos(ang), R * np.sin(ang),
                 color="#90caf9", lw=2)

        # Punto fijo: (σx, τxy) — el alumno arrastra ESTE punto. Su posición
        # angular en el círculo respecto al centro es 2θ relativo al estado
        # natural; nosotros aplicamos un offset _theta_rot adicional que
        # rota globalmente el plano.
        # Posición actual del punto draggable:
        ang_drag = 2 * (math.radians(theta_p) + self._theta_rot)
        # Cuando theta_rot = 0 y giramos por theta_p, el punto debería
        # caer en (sx, txy). Verifiquemos:
        #   x = avg + R*cos(2*theta_p) → con identidades trig ≡ sx ✓
        # El alumno gira el punto en ±2θ; el estado en el plano rotado se
        # lee como (sx_rot, txy_rot) = (avg + R cos α, R sin α) con
        # α = 2*(theta_p + theta_rot).
        px = avg + R * math.cos(ang_drag)
        py = R * math.sin(ang_drag)
        ax.scatter([px], [py], s=130, c=_C_DRAG, edgecolors="white",
                    linewidths=1.5, zorder=10, label="(σx, τxy) [drag]")
        # Punto opuesto (σy, -τxy) sigue al draggable
        px2 = avg + R * math.cos(ang_drag + math.pi)
        py2 = R * math.sin(ang_drag + math.pi)
        ax.scatter([px2], [py2], s=80, c="#fbc02d",
                    edgecolors="white", linewidths=1.0, zorder=8)
        ax.plot([px, px2], [py, py2], color="#fbc02d", lw=1.0, ls="--",
                 alpha=0.7)

        # σ1 / σ2 en el eje horizontal (siempre fijos)
        ax.scatter([s1], [0], s=110, c=_C_S1, edgecolors="white",
                    linewidths=1.5, zorder=9)
        ax.scatter([s2], [0], s=110, c=_C_S2, edgecolors="white",
                    linewidths=1.5, zorder=9)
        ax.annotate("σ1", (s1, 0),
                     textcoords="offset points", xytext=(8, 6),
                     color=_C_S1, fontsize=10, fontweight="bold")
        ax.annotate("σ2", (s2, 0),
                     textcoords="offset points", xytext=(-22, 6),
                     color=_C_S2, fontsize=10, fontweight="bold")

        # Anotación de θ rotada (en grados respecto al estado natural)
        theta_total_deg = math.degrees(self._theta_rot) + theta_p
        ax.set_title(
            f"N{self._sel_node}  ·  σ1={s1:.2f}  σ2={s2:.2f}  "
            f"θ={theta_total_deg:+.1f}°",
            color="#dfdfdf", fontsize=10,
        )

        x_low = min(s2, -R) - R * 0.3 - 1
        x_hi = max(s1, R) + R * 0.3 + 1
        ax.set_xlim(x_low, x_hi)
        ax.set_ylim(-R * 1.5 - 1, R * 1.5 + 1)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("σ", color="#dfdfdf")
        ax.set_ylabel("τ", color="#dfdfdf")

        # Update label nodo
        if self._lbl_node is not None:
            self._lbl_node.configure(
                text=f"Nodo N{self._sel_node}  ·  "
                      f"σx={sx:.3f}  σy={sy:.3f}  τxy={txy:.3f}"
            )

        try:
            self._fig.tight_layout(pad=0.5)
        except Exception:
            pass
        self._canvas_mpl.draw_idle()

    # ── Eventos del Mohr (drag para rotar el plano) ────────────────
    def _on_mohr_press(self, event):
        if event.inaxes is not self._ax:
            return
        if self._sel_node is None or self._sel_node not in self.nodal_avg:
            return
        # Solo iniciamos drag si el click cae cerca del punto draggable.
        v = self.nodal_avg[self._sel_node]
        sx, sy, txy = (v.get("sigma_x", 0.0), v.get("sigma_y", 0.0),
                        v.get("tau_xy", 0.0))
        s1, s2, theta_p = self._principals(sx, sy, txy)
        avg = (sx + sy) / 2.0
        R = (s1 - s2) / 2.0
        if R < 1e-9:
            return
        ang_drag = 2 * (math.radians(theta_p) + self._theta_rot)
        px = avg + R * math.cos(ang_drag)
        py = R * math.sin(ang_drag)
        # Tolerancia generosa en datos: 15% del radio.
        d = math.hypot(event.xdata - px, event.ydata - py)
        if d < 0.20 * R + 1e-9:
            self._dragging_point = True

    def _on_mohr_motion(self, event):
        if not self._dragging_point:
            return
        if event.inaxes is not self._ax or event.xdata is None:
            return
        if self._sel_node is None:
            return
        v = self.nodal_avg[self._sel_node]
        sx, sy, txy = (v.get("sigma_x", 0.0), v.get("sigma_y", 0.0),
                        v.get("tau_xy", 0.0))
        s1, s2, theta_p = self._principals(sx, sy, txy)
        avg = (sx + sy) / 2.0
        R = (s1 - s2) / 2.0
        if R < 1e-9:
            return
        # Ángulo del cursor respecto al centro del círculo
        ang_cursor = math.atan2(event.ydata, event.xdata - avg)
        # Total angular sobre el círculo es 2*(theta_p + theta_rot)
        # Despejamos theta_rot:
        theta_rot = ang_cursor / 2.0 - math.radians(theta_p)
        # Normalizar a (-π/2, π/2] para que el rango sea estable
        # (rotaciones de π/2 = 90° dan vuelta completa al plano físico).
        while theta_rot > math.pi / 2:
            theta_rot -= math.pi
        while theta_rot <= -math.pi / 2:
            theta_rot += math.pi
        self._theta_rot = theta_rot
        self._redraw_mohr()
        # Redibujar canvas: las cruces de TODA la malla rotan.
        self._mesh.redraw()

    def _on_mohr_release(self, event):
        self._dragging_point = False

    def _reset_rotation(self):
        self._theta_rot = 0.0
        self._redraw_mohr()
        self._mesh.redraw()
