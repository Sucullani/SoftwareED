"""
Módulo 6 — Vector de fuerzas equivalentes nodales (overlay)

**Reorientación 2026-05**: el módulo NO crea cargas. Selecciona una
carga superficial que el alumno ya definió en el Pre-Proceso y
muestra cómo se convierte en fuerzas nodales equivalentes vía
funciones de forma:

    F_i = ∫_arista  N_i(s) · q(s) · ds

Si el proyecto no tiene `surface_loads`, el módulo no aplica y muestra
un único mensaje dirigiendo al alumno al Pre-Proceso.

Pedagogía:
    El alumno *ve* la integral: flechitas distribuidas sobre la arista
    se concentran en bolitas nodales con tamaño proporcional a |F_i|.
    En Q9 con q constante el ratio 1:4:1 aparece visualmente — la bolita
    del nodo medio es 4× la de los extremos. Eso ES el resultado clásico
    L/6, 4L/6, L/6.

Reusa `fem/equivalent_forces.py` (lineal para Q4, cuadrática para Q9)
— cero duplicación de la matemática del solver.
"""

from __future__ import annotations

import math
from typing import Optional

import tkinter as tk
import ttkbootstrap as ttk

from education.overlay_module import CanvasOverlayModule
from fem.equivalent_forces import (
    surface_load_to_nodal_forces,
    surface_load_to_nodal_forces_q9,
)
from models.mesh_utils import find_edge_midnode
from config.settings import ELEMENT_Q9, EDU_LABEL_BG, EDU_FG_MUTED


_TAG = "edu_m6"
_C_EDGE_SEL = "#ff9f43"     # arista de la carga seleccionada — naranja
_C_DIST_ARROW = "#90caf9"   # flechitas distribuidas
_C_NODAL_BLOB = "#ef5350"   # bolitas nodales (resultado integrado)


# Tween animación: las flechitas decaen y las bolitas crecen en este lapso.
_ANIM_DURATION_MS = 1500


class EquivalentForcesModule(CanvasOverlayModule):
    """M6 overlay: inspecciona cargas superficiales ya definidas."""

    TITLE = "⑥  Fuerzas equivalentes  (q → F_i = ∫ N_i q ds)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 360
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False  # opera sobre cargas, no sobre un elemento elegido

    def __init__(self, main_window, project, element_id):
        # Estado
        self._active_idx: Optional[int] = None   # índice en project.surface_loads
        self._nodes_xy: list = []     # [(x, y), ...] de los nodos de la arista
        self._node_ids: list = []     # [nid, ...]
        self._F: list = []            # [(fx, fy), ...] por nodo (2 o 3 elementos)
        self._anim_t = 1.0
        self._anim_after_id: Optional[str] = None
        self._lbl_status: Optional[ttk.Label] = None
        self._chips_frame: Optional[ttk.Frame] = None
        super().__init__(main_window, project, element_id)

    # ── Construcción del overlay ───────────────────────────────────
    def build_overlay(self, body):
        loads = self._all_surface_loads()
        if not loads:
            # Sin cargas → el módulo no aplica.
            ttk.Label(
                body,
                text=("◎ Este módulo opera sobre cargas superficiales ya "
                      "definidas en el proyecto."),
                font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                wraplength=320, justify="left",
            ).pack(fill="x", padx=4, pady=(2, 6))
            ttk.Label(
                body,
                text=("👉 Definí una carga superficial en el Pre-Proceso "
                      "(sub-pestaña Carg. Superf.) y reabrí este módulo."),
                font=("Segoe UI", 9), foreground="#ffd54f",
                wraplength=320, justify="left",
            ).pack(fill="x", padx=4, pady=(2, 0))
            return

        # Lista de chips: una por carga. Click selecciona.
        ttk.Label(
            body, text="Cargas superficiales del proyecto:",
            font=("Segoe UI", 9, "bold"), foreground="#dcdcdc",
        ).pack(anchor="w", pady=(0, 2))

        self._chips_frame = ttk.Frame(body)
        self._chips_frame.pack(fill="x", pady=(0, 4))
        self._build_chips()

        # Status (qué carga está activa + nodos + magnitudes)
        self._lbl_status = ttk.Label(
            body, text="", font=("Consolas", 9),
            foreground="#cfd2d8", wraplength=320, justify="left",
        )
        self._lbl_status.pack(anchor="w", pady=(2, 0))

        # Cross-reference clickeable a M7 (ensamblaje del vector F global).
        self._pack_crossref(
            body, "mod07",
            "👉 Estas fuerzas nodales se SUMAN al vector F global. "
            "Ver ⑦ Ensamblaje.",
            wraplength=320,
        )

        # Auto-activar la primera carga (cae directo en pedagogía).
        self._select_load(0)

    def _build_chips(self):
        if self._chips_frame is None:
            return
        for w in self._chips_frame.winfo_children():
            w.destroy()
        loads = self._all_surface_loads()
        for idx, sl in enumerate(loads):
            label = (f"#{idx + 1}  N{sl.node_start}→N{sl.node_end}  "
                     f"q=[{sl.q_start:+.0f}, {sl.q_end:+.0f}]  "
                     f"θ={sl.angle:+.0f}°")
            style = ("warning-toolbutton" if idx == self._active_idx
                       else "secondary-outline-toolbutton")
            btn = ttk.Button(
                self._chips_frame, text=label, bootstyle=style,
                command=lambda i=idx: self._select_load(i),
            )
            btn.pack(fill="x", pady=1)

    # ── Selección de carga ─────────────────────────────────────────
    def _all_surface_loads(self) -> list:
        if self.project is None:
            return []
        return list(getattr(self.project, "surface_loads", []) or [])

    def _select_load(self, idx: int):
        loads = self._all_surface_loads()
        if not (0 <= idx < len(loads)):
            return
        self._active_idx = idx
        sl = loads[idx]
        self._resolve_arista_nodes(sl)
        self._compute_forces(sl)
        self._build_chips()  # repintar chip activo
        self._start_animation()
        self._refresh_status()

    def _resolve_arista_nodes(self, sl):
        """Resuelve los nodos físicos de la arista (start, [mid,] end).

        Para Q9 busca el mid-node en algún elemento del proyecto que
        contenga esa arista. Si no lo encuentra (caso bordeline), trata
        la carga como Q4 lineal.
        """
        self._nodes_xy = []
        self._node_ids = []
        if self.project is None:
            return
        n_start = self.project.nodes.get(sl.node_start)
        n_end = self.project.nodes.get(sl.node_end)
        if n_start is None or n_end is None:
            return
        is_q9 = (getattr(self.project, "element_type", None) == ELEMENT_Q9)
        mid_id = None
        if is_q9:
            for elem in self.project.elements.values():
                if elem.num_nodes != 9:
                    continue
                m = find_edge_midnode(elem, sl.node_start, sl.node_end)
                if m is not None:
                    mid_id = m
                    break
        if mid_id is not None:
            n_mid = self.project.nodes.get(mid_id)
            if n_mid is not None:
                self._node_ids = [sl.node_start, mid_id, sl.node_end]
                self._nodes_xy = [(n_start.x, n_start.y),
                                    (n_mid.x, n_mid.y),
                                    (n_end.x, n_end.y)]
                return
        # Fallback Q4 (o Q9 sin mid resoluble).
        self._node_ids = [sl.node_start, sl.node_end]
        self._nodes_xy = [(n_start.x, n_start.y), (n_end.x, n_end.y)]

    def _compute_forces(self, sl):
        if len(self._nodes_xy) == 3:
            self._F = list(surface_load_to_nodal_forces_q9(
                self._nodes_xy[0], self._nodes_xy[1], self._nodes_xy[2],
                sl.q_start, sl.q_end, sl.angle,
            ))
        elif len(self._nodes_xy) == 2:
            self._F = list(surface_load_to_nodal_forces(
                self._nodes_xy[0], self._nodes_xy[1],
                sl.q_start, sl.q_end, sl.angle,
            ))
        else:
            self._F = []

    # ── Hooks de ciclo de vida ─────────────────────────────────────
    def on_activated(self):
        self._mesh.redraw()

    def on_closed(self):
        if self._anim_after_id is not None:
            try:
                self._mesh.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None

    def on_element_selected(self, elem_id):
        # El elemento clickeado no cambia la carga activa — el alumno
        # navega por cargas via los chips, no por el canvas.
        return

    # ── Animación tween ────────────────────────────────────────────
    def _start_animation(self):
        self._anim_t = 0.0
        if self._anim_after_id is not None:
            try:
                self._mesh.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        self._step_animation()

    def _step_animation(self):
        delta = 16.0 / _ANIM_DURATION_MS
        self._anim_t = min(1.0, self._anim_t + delta)
        try:
            self._mesh.redraw()
        except Exception:
            pass
        if self._anim_t < 1.0:
            try:
                self._anim_after_id = self._mesh.after(16, self._step_animation)
            except tk.TclError:
                pass

    # ── Capa educativa sobre el canvas ─────────────────────────────
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if not self._nodes_xy or not self._F:
            return
        screen_pts = [mesh.world_to_screen(x, y) for x, y in self._nodes_xy]

        # Arista resaltada (start..end). Para Q9 dibujamos 2 segmentos.
        for i in range(len(screen_pts) - 1):
            x1, y1 = screen_pts[i]
            x2, y2 = screen_pts[i + 1]
            mesh.canvas.create_line(
                x1, y1, x2, y2, fill=_C_EDGE_SEL, width=4, tags=_TAG,
            )

        self._draw_force_animation(mesh, screen_pts)

    def _draw_force_animation(self, mesh, screen_pts):
        """Tween: t=0 → flechitas distribuidas sobre la arista;
        t=1 → bolitas en cada nodo con tamaño ∝ |F_i|.
        """
        t = self._anim_t
        if not self._F:
            return
        max_F = max(
            (math.hypot(fx, fy) for fx, fy in self._F),
            default=1.0,
        ) or 1.0

        # Bolitas en cada nodo con fade-in
        for i, (sx, sy) in enumerate(screen_pts):
            Fmag = math.hypot(self._F[i][0], self._F[i][1])
            ratio = Fmag / max_F
            r = 2 + 14 * ratio * t
            mesh.canvas.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=_C_NODAL_BLOB, outline="white",
                width=1.2 if t > 0.3 else 0.6, tags=_TAG,
            )
            if t > 0.85 and ratio > 0.05:
                mesh.canvas.create_text(
                    sx, sy - r - 8,
                    text=f"{Fmag:.0f}",
                    fill=_C_NODAL_BLOB,
                    font=("Consolas", 9, "bold"), tags=_TAG,
                )

        # Flechitas distribuidas sobre la arista total con fade-out.
        fade = max(0.0, 1.0 - t)
        if fade < 0.05:
            return
        # Para Q9 (3 pts) usamos solo la arista global start↔end como riel
        # visual; las flechitas no tienen por qué subdividirse en el mid.
        x1, y1 = screen_pts[0]
        x2, y2 = screen_pts[-1]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1.0
        # Normal exterior (rotación CW del tangente en coords screen).
        nx_out = dy / L
        ny_out = -dx / L
        n_arrows = 7
        color = _alpha_color(_C_DIST_ARROW, fade)
        for k in range(n_arrows):
            tt = (k + 0.5) / n_arrows
            ax = x1 + dx * tt
            ay = y1 + dy * tt
            mag = 28 * fade
            sx = ax - nx_out * mag
            sy = ay - ny_out * mag
            mesh.canvas.create_line(
                sx, sy, ax, ay,
                fill=color, width=2, arrow="last",
                arrowshape=(10, 12, 4), tags=_TAG,
            )

    def _refresh_status(self):
        if self._lbl_status is None:
            return
        if self._active_idx is None or not self._F:
            self._lbl_status.configure(text="")
            return
        # Listado conciso por nodo (start, [mid,] end).
        lines = []
        for i, nid in enumerate(self._node_ids):
            fx, fy = self._F[i]
            lines.append(f"N{nid}:  Fx={fx:+.2f}   Fy={fy:+.2f}")
        self._lbl_status.configure(text="\n".join(lines))


# ─── Helpers libres ────────────────────────────────────────────────
def _alpha_color(hex_color: str, alpha: float) -> str:
    """Mezcla un color hex con CANVAS_BG_COLOR según alpha (sin canal α en Tk)."""
    from config.settings import CANVAS_BG_COLOR
    a = max(0.0, min(1.0, alpha))
    bg = tuple(int(CANVAS_BG_COLOR[i:i+2], 16) for i in (1, 3, 5))
    fg = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    out = tuple(int(bg[i] + (fg[i] - bg[i]) * a) for i in range(3))
    return f"#{out[0]:02x}{out[1]:02x}{out[2]:02x}"
