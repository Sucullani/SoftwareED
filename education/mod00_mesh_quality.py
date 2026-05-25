"""
Módulo 0 — Calidad geométrica de la malla

REDISEÑADO: Modo Overlay "vista rayos X" (propuesta UX 2026).

Patología corregida:
    Antes era un Toplevel con sidebar denso (radio chart + slider de
    distorsión + texto explicativo) y una lista plana de elementos. El
    alumno tenía que saltar entre el panel y el mapa para entender qué
    elemento estaba mirando.

Diseño actual:
    1. NO abre Toplevel. Activa una "vista rayos X" sobre el MeshCanvas:
       cada elemento se pinta verde / amarillo / rojo según su estado de
       calidad combinado (capa overlay del canvas).
    2. Un overlay flotante muestra el RADAR de 4 ejes (JR, AR, SJ, Tap/Adm)
       del elemento bajo el cursor — el alumno hover-ea sobre la malla y
       el radar refleja en tiempo real.
    3. Drag de un nodo del elemento bajo análisis distorsiona el modelo
       interactivamente — las métricas se recalculan a 60 fps. Se hace
       sobre una COPIA temporal de las coords (NO muta el project hasta
       que el alumno suelta y confirma).
    4. Histograma de calidad horizontal compacto en el footer del overlay,
       mostrando la distribución de elementos por status.

Pedagogía:
    El alumno ve la calidad "en su sitio" — sobre la malla real que está
    construyendo o cargando, no sobre una copia auxiliar. El drag
    interactivo convierte la métrica en algo cinético: el Jacobian cae
    al mover el nodo, y eso ES el aprendizaje, no una tabla de números.
"""

from __future__ import annotations

from typing import Optional, Tuple

import math
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.overlay_module import CanvasOverlayModule
from fem.mesh_quality import (
    jacobian_ratio, scaled_jacobian,
    robinson_aspect, robinson_taper, midside_center_admissibility,
    internal_angles,
)
from config.settings import ELEMENT_Q4, ELEMENT_Q9, EDU_AXES_BG


# Paleta de calidad (alineada con HEALTH_*).
_GOOD = "#43a047"
_OK   = "#fdd835"
_BAD  = "#e53935"

_TAG = "edu_m0"

# Nodo en drag: tolerancia de hit-test en pixeles.
_DRAG_HIT_PX = 14


class MeshQualityModule(CanvasOverlayModule):
    """M0 en modo Overlay: vista rayos X + radar flotante + drag de nodo."""

    TITLE = "Ⓜ  Calidad de la malla"
    PHASE = "pre"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 380
    OVERLAY_HEIGHT = 460
    REQUIRES_ELEMENT = False

    def __init__(self, main_window, project, element_id):
        # Distorsión interactiva. Cuando el alumno drag-ea un nodo del
        # elemento bajo análisis, lo guardamos aquí (no muta el project).
        # Diccionario {node_id: (dx_world, dy_world)} aplicado solo al render.
        self._distortion: dict = {}
        self._dragging_node: Optional[int] = None
        self._drag_started_at: Optional[Tuple[float, float]] = None  # x_world, y_world

        # Hover state: elemento actualmente bajo cursor (radar refleja eso)
        self._hover_elem_id: Optional[int] = None

        # matplotlib refs
        self._fig: Optional[Figure] = None
        self._ax_radar: Optional = None
        self._ax_hist: Optional = None
        self._canvas_mpl: Optional[FigureCanvasTkAgg] = None
        self._lbl_status: Optional[ttk.Label] = None
        self._btn_reset: Optional[ttk.Button] = None

        super().__init__(main_window, project, element_id)

    # ── Construcción del overlay (compacto UX 2026) ───────────────
    def build_overlay(self, body):
        # Status del elemento bajo cursor. El color verde/amarillo/rojo de
        # la malla + el radar reactivo al hover ya comunican la idea
        # central — sin hints textuales de "hover sobre la malla" ni
        # "drag de un nodo".
        self._lbl_status = ttk.Label(
            body, text="", font=("Consolas", 9), foreground="#cfd2d8",
            justify="left", wraplength=360,
        )
        self._lbl_status.pack(anchor="w", pady=(0, 2))

        # Figura: radar arriba (polar), histograma horizontal abajo.
        fig_frame = ttk.Frame(body)
        fig_frame.pack(fill="both", expand=True)

        self._fig = Figure(figsize=(3.8, 4.2), dpi=100)
        from education.components.edu_plot_style import (
            apply_edu_style_figure, apply_edu_style_2d, apply_edu_style_polar,
        )
        apply_edu_style_figure(self._fig)
        self._ax_radar = self._fig.add_subplot(2, 1, 1, projection="polar")
        self._ax_hist  = self._fig.add_subplot(2, 1, 2)
        apply_edu_style_polar(self._ax_radar)
        apply_edu_style_2d(self._ax_hist, show_spines=False)
        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=fig_frame)
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True)

        # Botón reset distorsión: SOLO visible si hay distorsión activa
        # (lo creamos invisible — el método `_show_reset_if_distorted`
        # lo grídea cuando el alumno empieza a arrastrar nodos).
        self._btn_reset = ttk.Button(
            body, text="↺ Reset",
            bootstyle="secondary-outline-toolbutton",
            command=self._reset_distortion,
        )
        # NO pack al inicio — se muestra solo cuando hay algo que resetear

        # Cross-reference clickeable al siguiente paso del pipeline FEM
        # (el método `_pack_crossref` se agrega en `overlay_module.py` por D2).
        self._pack_crossref(
            body, "mod02",
            "👉 Una malla sana ⇒ det J > 0 en cada Gauss. Ver ② Jacobiano.",
            wraplength=360,
        )

        self._refresh_overlay()

    # ── Hooks: nos enganchamos al hover y al drag ──────────────────
    def on_activated(self):
        # Hover de elementos (capa educativa nativa)
        self._mesh.on_hover_element = self._on_hover_element
        # Drag de nodos:
        #   - PRESS: click consumer del MeshCanvas. Si agarra un nodo del
        #     elemento bajo cursor, consume el click — la malla NO cambia
        #     de selección por debajo del drag (uniforme con M2/M4/M5b).
        #   - MOTION + RELEASE: binds aditivos al tk.Canvas, independientes
        #     del hit-test (no compiten con nada del canvas).
        self._click_consumer = self._on_node_press_consume
        self._mesh.add_click_consumer(self._click_consumer)
        c = self._mesh.canvas
        self._bid_move = c.bind("<B1-Motion>", self._on_node_drag, add="+")
        self._bid_rel  = c.bind("<ButtonRelease-1>", self._on_node_release,
                                  add="+")
        # Render inicial con los colores de calidad
        self._mesh.redraw()

    def on_closed(self):
        self._mesh.on_hover_element = None
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass
        c = self._mesh.canvas
        for bid_pair in ((getattr(self, "_bid_move", None), "<B1-Motion>"),
                          (getattr(self, "_bid_rel",  None), "<ButtonRelease-1>")):
            bid, evt = bid_pair
            if bid:
                try:
                    c.unbind(evt, bid)
                except Exception:
                    pass

    # ── Capa educativa: pintar elementos por calidad ───────────────
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if not self.project or not self.project.elements:
            return

        for elem in self.project.elements.values():
            try:
                coords = self._coords_with_distortion(elem)
            except Exception:
                continue
            if coords is None or len(coords) < 4:
                continue

            color = self._color_for(coords)

            # Polígono macro (4 esquinas) con fill semi-translúcido
            pts = []
            for c in coords[:4]:
                sx, sy = mesh.world_to_screen(c[0], c[1])
                pts.extend([sx, sy])
            mesh.canvas.create_polygon(
                *pts, fill=color, outline="", stipple="gray50",
                tags=_TAG,
            )

            # Outline más grueso si es el elemento bajo cursor
            if self._hover_elem_id == elem.id:
                mesh.canvas.create_polygon(
                    *pts, outline="#fff", width=2.4, fill="", tags=_TAG,
                )

        # Anillo amarillo en el nodo en drag
        if self._dragging_node is not None:
            node = self.project.nodes.get(self._dragging_node)
            if node is not None:
                # Aplicar distorsión también al render del anillo
                dx, dy = self._distortion.get(self._dragging_node, (0.0, 0.0))
                sx, sy = mesh.world_to_screen(node.x + dx, node.y + dy)
                mesh.canvas.create_oval(
                    sx - 9, sy - 9, sx + 9, sy + 9,
                    outline="#ffeb3b", width=2.2, tags=_TAG,
                )

    # ── Coloring: status combinado del elemento ────────────────────
    def _color_for(self, coords: np.ndarray) -> str:
        """Verde / amarillo / rojo a partir de las métricas combinadas.

        Reusa los thresholds canónicos de fem.mesh_quality (no duplicar):
        un elemento es 'Buena' si TODAS las métricas pasan; 'Mala' si
        cualquiera falla por margen amplio; 'Aceptable' en el medio.
        """
        et = self.project.element_type
        try:
            q_sj = scaled_jacobian(coords, et)
            r_j  = jacobian_ratio(coords, et)
            ar   = robinson_aspect(coords[:4])
            if et == ELEMENT_Q9 and len(coords) >= 9:
                adm = midside_center_admissibility(coords[:9])
                fourth = adm["q_D"]
                gates = adm["gates_ok"]
            else:
                fourth = robinson_taper(coords[:4]) if et == ELEMENT_Q4 else None
                gates = True
        except Exception:
            return _BAD

        # Heurística simplificada (alineada con _status_from_metrics):
        # Buena si SJ > 0.6, R_J > 0.7, AR < 4, taper < 0.4 (Q4) o gates ok
        if et == ELEMENT_Q4:
            if (q_sj > 0.6 and r_j > 0.7 and ar < 4
                    and (fourth is not None and fourth < 0.4)):
                return _GOOD
            if (q_sj > 0.3 and r_j > 0.4 and ar < 8
                    and (fourth is None or fourth < 0.7)):
                return _OK
            return _BAD
        else:  # Q9
            if not gates:
                return _BAD
            if q_sj > 0.6 and r_j > 0.7 and ar < 4:
                return _GOOD
            if q_sj > 0.3 and r_j > 0.4 and ar < 8:
                return _OK
            return _BAD

    # ── Hover de elemento → actualizar radar ───────────────────────
    def _on_hover_element(self, elem_id, _sx, _sy):
        if elem_id == self._hover_elem_id:
            return
        self._hover_elem_id = elem_id
        self._refresh_overlay()
        self._mesh.redraw()

    # ── Drag de nodo (distorsión interactiva, no muta el project) ──
    def _on_node_press_consume(self, event) -> bool:
        """Click consumer: si el click cae sobre un nodo del elemento bajo
        cursor, inicia el drag y consume el click (return True). Si no
        agarra ningún nodo, retorna False — el canvas ejecuta su hit-test
        normal y el alumno puede cambiar de selección.
        """
        if self._hover_elem_id is None or self.project is None:
            return False
        elem = self.project.elements.get(self._hover_elem_id)
        if elem is None:
            return False
        candidate = None
        best_d = float("inf")
        for nid in elem.node_ids:
            node = self.project.nodes.get(nid)
            if node is None:
                continue
            dx, dy = self._distortion.get(nid, (0.0, 0.0))
            sx, sy = self._mesh.world_to_screen(node.x + dx, node.y + dy)
            d = math.hypot(sx - event.x, sy - event.y)
            if d < best_d:
                best_d = d
                candidate = nid
        if candidate is None or best_d > _DRAG_HIT_PX:
            return False
        self._dragging_node = candidate
        node = self.project.nodes[candidate]
        # Inicio del drag en coords-mundo (cursor)
        wx, wy = self._mesh.screen_to_world(event.x, event.y)
        self._drag_started_at = (wx - node.x, wy - node.y)
        return True

    def _on_node_drag(self, event):
        if self._dragging_node is None or self._drag_started_at is None:
            return
        node = self.project.nodes.get(self._dragging_node)
        if node is None:
            return
        wx, wy = self._mesh.screen_to_world(event.x, event.y)
        # Cursor estaba en (node + offset_inicial). Para mantener la
        # sensación de "agarrar el nodo donde lo agarré", la distorsión
        # = (wx - offset.x) - node.x  =  wx - node.x - offset.x.
        ox, oy = self._drag_started_at
        dx = wx - node.x - ox
        dy = wy - node.y - oy
        self._distortion[self._dragging_node] = (dx, dy)
        self._refresh_overlay()
        self._mesh.redraw()
        self._show_reset_if_distorted()

    def _on_node_release(self, _event):
        if self._dragging_node is None:
            return
        # Mantenemos la distorsión visible. NO mutamos el project — el
        # alumno usa el botón "Resetear distorsión" para volver al estado
        # natural. Esto es lo más conservador (evita mutaciones por accidente
        # mientras se exploran métricas).
        self._dragging_node = None
        self._drag_started_at = None

    def _reset_distortion(self):
        self._distortion.clear()
        self._refresh_overlay()
        self._mesh.redraw()
        self._show_reset_if_distorted()

    def _show_reset_if_distorted(self):
        """Muestra/oculta el botón Reset según si hay distorsión activa.

        Sin distorsión: botón oculto (sin ruido). Con distorsión: visible
        en la esquina inferior derecha del overlay."""
        if self._btn_reset is None:
            return
        has_dist = any(
            abs(dx) > 1e-9 or abs(dy) > 1e-9
            for dx, dy in self._distortion.values()
        )
        try:
            if has_dist:
                self._btn_reset.pack(anchor="e", pady=(2, 0))
            else:
                self._btn_reset.pack_forget()
        except Exception:
            pass

    # ── Coords con distorsión aplicada (para todas las métricas) ──
    def _coords_with_distortion(self, elem) -> Optional[np.ndarray]:
        coords = []
        for nid in elem.node_ids:
            node = self.project.nodes.get(nid)
            if node is None:
                return None
            dx, dy = self._distortion.get(nid, (0.0, 0.0))
            coords.append((node.x + dx, node.y + dy))
        return np.array(coords, dtype=float)

    # ── Refresh del overlay (radar + histograma + status) ──────────
    def _refresh_overlay(self):
        if self._ax_radar is None or self._ax_hist is None:
            return
        # ── Radar del elemento bajo cursor ────────────────────────
        ax = self._ax_radar
        ax.clear()
        from education.components.edu_plot_style import (
            apply_edu_style_polar, EDU_PLOT_LABEL_COLOR, EDU_PLOT_TITLE_COLOR,
        )
        apply_edu_style_polar(ax)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)

        elem = (self.project.elements.get(self._hover_elem_id)
                if self._hover_elem_id is not None else None)
        if elem is not None:
            try:
                coords = self._coords_with_distortion(elem)
                if coords is not None and len(coords) >= 4:
                    et = self.project.element_type
                    q_sj = scaled_jacobian(coords, et)
                    r_j  = jacobian_ratio(coords, et)
                    ar_raw = robinson_aspect(coords[:4])
                    if et == ELEMENT_Q4:
                        fourth = robinson_taper(coords[:4])
                        fourth_label = "Tap"
                        # Tap: 0 = perfecto, 1 = degenerado → usamos 1-tap
                        fourth_norm = max(0.0, 1.0 - fourth)
                    else:
                        if len(coords) >= 9:
                            adm = midside_center_admissibility(coords[:9])
                            fourth_norm = max(0.0, min(1.0, adm["q_D"]))
                            fourth_label = "Adm"
                        else:
                            fourth_norm = 0.0
                            fourth_label = "Adm"

                    # Normalizamos AR: 1 = ideal, ≥4 = degradado
                    ar_norm = max(0.0, min(1.0, 1.0 / max(1.0, ar_raw)))

                    # Categorías y valores [0,1]
                    cats = ["JR", "AR", "SJ", fourth_label]
                    vals = [
                        max(0.0, min(1.0, r_j)),
                        ar_norm,
                        max(0.0, min(1.0, q_sj)),
                        fourth_norm,
                    ]
                    n = len(cats)
                    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
                    angles += angles[:1]
                    vals_loop = vals + vals[:1]

                    # Linea/fill mas finos y suaves — radar legible sin ruido.
                    ax.plot(angles, vals_loop, color=_BAD, linewidth=1.1)
                    ax.fill(angles, vals_loop, color=_BAD, alpha=0.18)
                    ax.set_xticks(angles[:-1])
                    ax.set_xticklabels(cats, color=EDU_PLOT_LABEL_COLOR,
                                         fontsize=8)
                    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
                    ax.set_yticklabels(["", "", "", ""])
                    ax.set_ylim(0, 1)
                    ax.set_title(f"E{elem.id}  ·  radar 4 ejes",
                                 color=EDU_PLOT_TITLE_COLOR,
                                 fontsize=9, pad=8)

                    if self._lbl_status is not None:
                        self._lbl_status.configure(text=(
                            f"E{elem.id}  ·  SJ={q_sj:.2f}  JR={r_j:.2f}  "
                            f"AR={ar_raw:.2f}  {fourth_label}={vals[3]:.2f}"
                        ))
            except Exception as exc:
                ax.text(0.5, 0.5, f"({exc})",
                         ha="center", va="center", color="#9e9e9e",
                         transform=ax.transAxes, fontsize=8)
        else:
            ax.text(0.5, 0.5, "(hover sobre la malla)",
                     ha="center", va="center", color="#7a7e88",
                     transform=ax.transAxes, fontsize=8)
            ax.set_xticks([]); ax.set_yticks([])
            if self._lbl_status is not None:
                self._lbl_status.configure(text="(hover sobre un elemento)")

        # ── Histograma compacto: cuántos elementos por status ────
        ax2 = self._ax_hist
        ax2.clear()
        from education.components.edu_plot_style import (
            apply_edu_style_2d, EDU_PLOT_LABEL_COLOR, EDU_PLOT_TITLE_COLOR,
        )
        apply_edu_style_2d(ax2, show_spines=False)
        counts = {"Buena": 0, "Aceptable": 0, "Mala": 0}
        if self.project and self.project.elements:
            for e in self.project.elements.values():
                coords = self._coords_with_distortion(e)
                if coords is None or len(coords) < 4:
                    continue
                color = self._color_for(coords)
                if color == _GOOD:
                    counts["Buena"] += 1
                elif color == _OK:
                    counts["Aceptable"] += 1
                else:
                    counts["Mala"] += 1
        cats = list(counts.keys())
        vals = [counts[k] for k in cats]
        bar_colors = [_GOOD, _OK, _BAD]
        # Alpha bajo para que las barras no compitan visualmente.
        bars = ax2.barh(cats, vals, color=bar_colors, alpha=0.78,
                          edgecolor="none", height=0.6)
        ax2.set_title(f"Distribución ({sum(vals)} elem)",
                      color=EDU_PLOT_TITLE_COLOR, fontsize=9, pad=4)
        # Valor numérico al final de cada barra
        max_v = max(vals) if max(vals) > 0 else 1
        for bar, v in zip(bars, vals):
            ax2.text(bar.get_width() + max_v * 0.02,
                     bar.get_y() + bar.get_height() / 2,
                     str(v), color=EDU_PLOT_LABEL_COLOR, fontsize=8,
                     va="center")

        try:
            self._fig.tight_layout(pad=0.4)
        except Exception:
            pass
        self._canvas_mpl.draw_idle()
