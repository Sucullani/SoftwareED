"""
Módulo 7 — Ensamblaje global   K_IJ += k^(e)_ij   y   F_I += f^(e)_i

Rediseño 2026-05 (post pase UX: "el vuelo Bézier genera mucho ruido visual"):

    ANTES: cada elemento "volaba" como tile Bézier desde el canvas hasta
    un slot en K. Sumando 3 capas simultáneas (tile + trazas residuales +
    pulso de aterrizaje), la animación competía con la lectura del modelo
    y saturaba el canvas con trayectorias acumuladas.

    AHORA: cero objetos volando. La relación elemento ↔ K/F se enseña
    via dos mecanismos complementarios:

    1. **HOVER causal map**: el alumno hover-ea cualquier elemento del
       canvas → resaltamos sus filas/columnas de K y sus entradas de F.
       Hover sobre una celda de K → resaltamos los elementos que la
       tocan. Exploración silenciosa, leída con el mouse — sin loops.

    2. **Pulso secuencial al ensamblar**: al ▶ Siguiente (o click en
       elemento) el elemento parpadea brevemente (200 ms) y los cells
       de K + las entradas de F que recibe contribución se iluminan en
       el mismo pulso. Misma narrativa que el Bézier pero sin tiles,
       trayectorias, ni fades a varios frames.

    3. **Vector F en el sistema**: chip toggle [K] [F] [K·u=F] expone
       las tres caras del sistema global. En K solo, en F solo (panel
       columna con magnitudes), o en `[K | F]` con los dos juntos
       — refuerza que ensamblar K y F son la misma operación lógica
       (sumar contribuciones por elemento al global, una columna o
       una matriz, según el operador).

Reglas de la capa canvas:
    * Tags `edu_m7_*`. Limpiados al inicio de cada `draw_canvas_layer`.
    * NO hay tile transitorio fuera de la capa — todo vive en la capa,
      todo se borra/redibuja en cada `mesh.redraw()`.
"""

from __future__ import annotations

from typing import Optional, Set

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.overlay_module import CanvasOverlayModule

from fem.stiffness import element_stiffness
from fem.assembly import assemble_global_system
from fem.equivalent_forces import (
    surface_load_to_nodal_forces, surface_load_to_nodal_forces_q9,
)
from models.mesh_utils import find_edge_midnode
from config.settings import (
    ELEMENT_Q9,
    EDU_FIG_BG, EDU_AXES_BG, EDU_LABEL_BG, EDU_FG, EDU_FG_MUTED,
)


# Tags canvas — el primer paso de draw_canvas_layer es delete(_TAG_BASE).
_TAG_BASE       = "edu_m7"
_TAG_ASSEMBLED  = "edu_m7_assembled"
_TAG_NEXT       = "edu_m7_next"
_TAG_HOVER      = "edu_m7_hover"
_TAG_PULSE      = "edu_m7_pulse"

_C_ASSEMBLED = "#4fa3ff"   # azul: ya ensamblado
_C_NEXT      = "#ffd54f"   # dorado: próximo en la cola
_C_HOVER     = "#ff8a65"   # naranja: highlight de hover
_C_PULSE     = "#ffffff"   # blanco: flash del pulso secuencial
_C_STRIKE    = "#ef5350"   # rojo: BCs (tachado de filas/columnas)


class AssemblyModule(CanvasOverlayModule):
    """M7: ensamblaje sin vuelo Bézier — hover causal + pulso secuencial.

    Modos de vista:
        - MODE_K       : heatmap de K global
        - MODE_F       : vector F como columna vertical (barras horizontales)
        - MODE_SYSTEM  : [K | F] lado a lado (visualización del sistema)
    """

    TITLE = "⑦  Ensamblaje   K_IJ += k^(e)_ij   ·   F_I += f^(e)_i"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 520
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False

    MODE_K = "K"
    MODE_F = "F"
    MODE_SYSTEM = "system"

    # Pulso de ensamblaje: 6 frames × 35 ms ≈ 210 ms. Sin curva Bézier,
    # sin tile volador — solo flash de elemento + cells de K/F.
    PULSE_FRAMES = 6
    PULSE_INTERVAL_MS = 35

    # ── Construcción ──────────────────────────────────────────────
    def build_overlay(self, body):
        if self.project is None or not self.project.elements:
            tk.Label(body, text="Cargá un proyecto con elementos para M7.",
                     bg=EDU_AXES_BG, fg=EDU_FG, pady=20).pack()
            self._lbl_progress = None
            self._canvas_mpl = None
            return

        # Estado del ensamblado
        self._order = sorted(self.project.elements.keys())
        self._ptr = 0
        n_dof = self.project.total_dof
        self._K = np.zeros((n_dof, n_dof))
        self._F = np.zeros(n_dof)
        self._assembled: set = set()
        self._anim_running = False
        self._pulse_after_id: Optional[str] = None
        self._mode = self.MODE_K
        self._show_reduced = False
        # Hover state: elemento bajo cursor del CANVAS o (i, j) bajo cursor
        # del heatmap K. Mutuamente excluyentes — el último que cambió gana.
        self._hover_elem: Optional[int] = None
        self._hover_cell: Optional[tuple] = None
        # Pulso transitorio: elemento + DOFs cuyas celdas/entradas parpadean
        # durante PULSE_FRAMES * PULSE_INTERVAL_MS.
        self._pulse_eid: Optional[int] = None
        self._pulse_dofs: list = []
        self._pulse_frame_idx = 0

        # ── Toolbar superior compacta ────────────────────────────
        bar = tk.Frame(body, bg=EDU_AXES_BG)
        bar.pack(fill="x", pady=(0, 4))

        ttk.Button(bar, text="▶ Siguiente", bootstyle="success",
                   command=self._assemble_next).pack(side="left", padx=2)
        ttk.Button(bar, text="⏭ Todos",
                   bootstyle="info-outline-toolbutton",
                   command=self._assemble_all).pack(side="left", padx=2)
        ttk.Button(bar, text="↺ Reset",
                   bootstyle="warning-outline-toolbutton",
                   command=self._reset_assembly).pack(side="left", padx=2)

        ttk.Separator(bar, orient="vertical").pack(side="left",
                                                     fill="y", padx=6)

        # Chip toggle: vista K | F | sistema K·u=F.
        self._var_mode = tk.StringVar(value=self._mode)
        for val, lbl in (
            (self.MODE_K, "K"),
            (self.MODE_F, "F"),
            (self.MODE_SYSTEM, "K · u = F"),
        ):
            ttk.Radiobutton(
                bar, text=lbl, value=val, variable=self._var_mode,
                bootstyle="info-outline-toolbutton",
                command=self._on_mode_change,
            ).pack(side="left", padx=1)

        ttk.Separator(bar, orient="vertical").pack(side="left",
                                                     fill="y", padx=6)
        self._var_reduced = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="Reducida",
                        variable=self._var_reduced,
                        bootstyle="info-round-toggle",
                        command=self._on_reduced_toggle).pack(side="left",
                                                                padx=2)

        # ── Heatmap K / F / sistema ─────────────────────────────
        self._fig = Figure(figsize=(4.8, 4.6), dpi=100)
        from education.components.edu_plot_style import apply_edu_style_figure
        apply_edu_style_figure(self._fig)
        try:
            self._fig.subplots_adjust(left=0.06, right=0.98,
                                        top=0.92, bottom=0.04)
        except Exception:
            pass
        # Creamos el (los) ejes en cada `_redraw_panel` según el modo,
        # porque el layout cambia (K cuadrada vs F columna vs K|F lado a lado).
        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=body)
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True)
        self._canvas_mpl.mpl_connect("motion_notify_event", self._on_axes_motion)
        self._canvas_mpl.mpl_connect("axes_leave_event", self._on_axes_leave)
        self._canvas_mpl.mpl_connect("button_press_event", self._on_axes_click)

        # ── Footer compacto ──────────────────────────────────────
        self._lbl_progress = tk.Label(
            body, text="", bg=EDU_AXES_BG, fg=_C_NEXT,
            font=("Consolas", 9, "bold"), anchor="w",
        )
        self._lbl_progress.pack(fill="x", pady=(4, 0))

        # Hook hover del MeshCanvas — guardamos el callback previo para
        # restaurarlo en `on_closed`.
        self._saved_hover = self._mesh.on_hover_element
        self._mesh.on_hover_element = self._on_canvas_hover_element

        self._pre_compute_f_contributions()
        self._redraw_panel()
        self._update_progress()

        # Cross-reference decorativa (Post-Proceso no es un módulo overlay).
        self._pack_crossref(
            body, None,
            "👉 Al aplicar BCs y resolver  K·u = F,  obtenemos "
            "desplazamientos + tensiones (📊 Post-Proceso).",
            wraplength=500,
        )

    # ── Capa canvas ────────────────────────────────────────────────
    def draw_canvas_layer(self, mesh):
        c = mesh.canvas
        c.delete(_TAG_BASE)
        if self.project is None or not self.project.elements:
            return

        # 1) Elementos ya ensamblados: azul suave.
        for eid in self._assembled:
            self._draw_element_outline(mesh, eid, _C_ASSEMBLED, width=3,
                                         glow_width=6, tag=_TAG_ASSEMBLED)

        # 2) Próximo elemento de la cola: dorado prominente.
        if self._ptr < len(self._order):
            next_eid = self._order[self._ptr]
            if next_eid not in self._assembled:
                self._draw_element_outline(mesh, next_eid, _C_NEXT, width=3,
                                             glow_width=9, tag=_TAG_NEXT)

        # 3) Hover desde K (celda → elementos que contribuyen).
        if self._hover_cell is not None:
            for eid in self._elements_for_cell(*self._hover_cell):
                self._draw_element_outline(mesh, eid, _C_HOVER, width=2,
                                             glow_width=5, tag=_TAG_HOVER)

        # 4) Hover desde canvas (elemento bajo cursor) — outline propio.
        if self._hover_elem is not None \
                and self._hover_elem in self.project.elements:
            self._draw_element_outline(mesh, self._hover_elem, _C_HOVER,
                                         width=2, glow_width=5, tag=_TAG_HOVER)

        # 5) Pulso transitorio: parpadeo blanco sobre el elemento en
        #    proceso de ensamblar (alternancia binaria por frame).
        if self._pulse_eid is not None and (self._pulse_frame_idx % 2) == 0:
            self._draw_element_outline(mesh, self._pulse_eid, _C_PULSE,
                                         width=2.4, glow_width=12,
                                         tag=_TAG_PULSE)

    def _draw_element_outline(self, mesh, eid, color, width, glow_width, *, tag):
        elem = self.project.elements.get(eid)
        if elem is None:
            return
        try:
            pts = [self.project.nodes[nid] for nid in elem.node_ids[:4]]
        except KeyError:
            return
        flat = []
        for n in pts:
            sx, sy = mesh.world_to_screen(n.x, n.y)
            flat.extend([sx, sy])
        flat.extend(flat[:2])
        try:
            mesh.canvas.create_line(*flat, fill=color, width=glow_width,
                                      tags=(_TAG_BASE, tag))
            mesh.canvas.create_line(*flat, fill="#ffffff", width=1,
                                      tags=(_TAG_BASE, tag))
        except tk.TclError:
            pass

    # ── Mecánica del ensamblaje ────────────────────────────────────
    def _element_ke(self, eid):
        elem = self.project.elements[eid]
        coords = np.array([
            [self.project.nodes[nid].x, self.project.nodes[nid].y]
            for nid in elem.node_ids
        ], dtype=float)
        material = self.project.materials.get(elem.material_name)
        if material is None:
            material = list(self.project.materials.values())[0]
        ke, _ = element_stiffness(
            coords, material.E, material.nu,
            elem.thickness, self.project.analysis_type,
            self.project.element_type,
        )
        dofs = elem.get_dof_indices(self.project)
        return ke, dofs

    def _pre_compute_f_contributions(self):
        """Calcula F GLOBAL "objetivo" + descompone en contribuciones por
        elemento + dict de DOFs cargados por cada elemento.

        F se ensambla en el solver desde 3 fuentes (nodal_loads,
        surface_loads, body forces). Para la pedagogía de M7 dividimos las
        contribuciones por elemento de la siguiente forma:

        - **nodal_loads**: se asignan al PRIMER elemento (orden de creación)
          que contiene el nodo cargado. Decisión arbitraria pero necesaria
          porque las cargas nodales NO pertenecen físicamente a un elemento.
        - **surface_loads**: contribuyen a los nodos de la arista del
          elemento dueño.
        - **body forces** (gravedad): se reparten dentro del elemento via
          ∫ Nᵢ ρg dΩ — ya por-elemento.

        Esto permite que `_assemble_next(eid)` sume `F_e_per_elem[eid]`
        al F global como contribución del elemento.
        """
        n_dof = self.project.total_dof
        self._F_target = np.zeros(n_dof)
        self._F_per_elem: dict = {eid: np.zeros(n_dof)
                                   for eid in self.project.elements}

        # Body forces vía la API canónica del solver (devuelve F target
        # incluyendo body/surface/nodal). Lo usamos como referencia visual.
        try:
            _, F_full, _ = assemble_global_system(self.project)
            self._F_target = F_full
        except Exception:
            pass

        idx_map = self.project.node_index_map
        # Asignación de nodal_loads al primer elemento que contiene el nodo.
        for load in self.project.nodal_loads.values():
            owner_eid = self._first_element_with_node(load.node_id)
            if owner_eid is None:
                continue
            base = 2 * idx_map[load.node_id]
            self._F_per_elem[owner_eid][base] += load.fx
            self._F_per_elem[owner_eid][base + 1] += load.fy

        # Surface loads: contribuyen al elemento dueño (sl.element_id) o,
        # si no fue setteado, al primer elemento que contiene a ambos nodos.
        for sl in self.project.surface_loads:
            owner_eid = sl.element_id if sl.element_id is not None else None
            if owner_eid is None:
                owner_eid = self._first_element_with_edge(sl.node_start,
                                                            sl.node_end)
            if owner_eid is None:
                continue
            n_a = self.project.nodes.get(sl.node_start)
            n_b = self.project.nodes.get(sl.node_end)
            if n_a is None or n_b is None:
                continue
            elem = self.project.elements.get(owner_eid)
            mid_nid = None
            if elem is not None and self.project.element_type == ELEMENT_Q9:
                mid_nid = find_edge_midnode(elem, sl.node_start, sl.node_end)
            if mid_nid is not None:
                n_m = self.project.nodes.get(mid_nid)
                if n_m is not None:
                    (fx_a, fy_a), (fx_m, fy_m), (fx_b, fy_b) = (
                        surface_load_to_nodal_forces_q9(
                            (n_a.x, n_a.y), (n_m.x, n_m.y), (n_b.x, n_b.y),
                            sl.q_start, sl.q_end, sl.angle,
                        )
                    )
                    base_a = 2 * idx_map[sl.node_start]
                    base_m = 2 * idx_map[mid_nid]
                    base_b = 2 * idx_map[sl.node_end]
                    fe = self._F_per_elem[owner_eid]
                    fe[base_a]     += fx_a; fe[base_a + 1] += fy_a
                    fe[base_m]     += fx_m; fe[base_m + 1] += fy_m
                    fe[base_b]     += fx_b; fe[base_b + 1] += fy_b
                    continue
            (fx_a, fy_a), (fx_b, fy_b) = surface_load_to_nodal_forces(
                (n_a.x, n_a.y), (n_b.x, n_b.y),
                sl.q_start, sl.q_end, sl.angle,
            )
            base_a = 2 * idx_map[sl.node_start]
            base_b = 2 * idx_map[sl.node_end]
            fe = self._F_per_elem[owner_eid]
            fe[base_a]     += fx_a; fe[base_a + 1] += fy_a
            fe[base_b]     += fx_b; fe[base_b + 1] += fy_b

        # Body forces (gravedad) — diferencia entre F_target y la suma de
        # las contribuciones explícitas calculadas arriba. Esto captura
        # cualquier fuente no contemplada (e.g. gravedad volumétrica) sin
        # duplicar código del solver. La diferencia se reparte
        # uniformemente entre elementos que contengan al DOF.
        explicit_sum = np.zeros(n_dof)
        for fe in self._F_per_elem.values():
            explicit_sum += fe
        residual = self._F_target - explicit_sum
        if np.any(np.abs(residual) > 1e-9):
            # Reparto: a cada DOF residual, asignamos su contribución al
            # primer elemento que contiene el nodo asociado. Es la misma
            # heurística que para nodal_loads.
            for dof, val in enumerate(residual):
                if abs(val) < 1e-12:
                    continue
                node_idx = dof // 2
                # node_id desde index_map inverso
                inv_map = {v: k for k, v in idx_map.items()}
                node_id = inv_map.get(node_idx)
                if node_id is None:
                    continue
                owner_eid = self._first_element_with_node(node_id)
                if owner_eid is not None:
                    self._F_per_elem[owner_eid][dof] += val

    def _first_element_with_node(self, node_id) -> Optional[int]:
        for eid in self._order:
            elem = self.project.elements.get(eid)
            if elem and node_id in elem.node_ids:
                return eid
        return None

    def _first_element_with_edge(self, n_a, n_b) -> Optional[int]:
        for eid in self._order:
            elem = self.project.elements.get(eid)
            if not elem:
                continue
            ids = elem.node_ids[:4]
            if n_a in ids and n_b in ids:
                return eid
        return None

    def _assemble_next(self):
        if self._anim_running or self._ptr >= len(self._order):
            return
        eid = self._order[self._ptr]
        self._do_assemble(eid)

    def _do_assemble(self, eid: int):
        """Suma k_e a K, F_e a F, marca el elemento como ensamblado y
        dispara el pulso (parpadeo del elemento + flash de DOFs)."""
        ke, dofs = self._element_ke(eid)
        for i_loc, i_glo in enumerate(dofs):
            for j_loc, j_glo in enumerate(dofs):
                self._K[i_glo, j_glo] += ke[i_loc, j_loc]
        fe = self._F_per_elem.get(eid)
        if fe is not None:
            self._F += fe
        self._assembled.add(eid)
        # Avanzar el puntero saltando elementos adelantados por click.
        while (self._ptr < len(self._order)
                and self._order[self._ptr] in self._assembled):
            self._ptr += 1
        self._start_pulse(eid, list(dofs))
        self._redraw_panel()
        self._update_progress()
        self._mesh.redraw()

    def _start_pulse(self, eid: int, dofs: list):
        """Inicia el pulso secuencial: 6 frames de flash blanco en el
        elemento + en los DOFs ensamblados. Reemplaza al vuelo Bézier."""
        # Cancela un pulso previo si existe.
        if self._pulse_after_id:
            try:
                self._mesh.canvas.after_cancel(self._pulse_after_id)
            except tk.TclError:
                pass
            self._pulse_after_id = None
        self._pulse_eid = eid
        self._pulse_dofs = dofs
        self._pulse_frame_idx = 0
        self._anim_running = True
        self._step_pulse()

    def _step_pulse(self):
        if self._pulse_frame_idx >= self.PULSE_FRAMES:
            self._pulse_eid = None
            self._pulse_dofs = []
            self._anim_running = False
            self._pulse_after_id = None
            self._mesh.redraw()
            self._redraw_panel()
            return
        self._pulse_frame_idx += 1
        # Redibuja SOLO las capas overlay (parpadeo binario del pulso, en el
        # tag edu_m7) + matplotlib (flash de cells). La base ya esta dibujada
        # (redraw completo en _do_assemble antes de iniciar el pulso); evitar
        # el redraw() completo por frame mantiene el pulso fluido a ~30 fps.
        self._mesh.redraw_overlays_only()
        self._redraw_panel()
        try:
            self._pulse_after_id = self._mesh.canvas.after(
                self.PULSE_INTERVAL_MS, self._step_pulse,
            )
        except tk.TclError:
            self._anim_running = False

    def _assemble_all(self):
        if self._anim_running:
            return
        for eid in self._order:
            if eid in self._assembled:
                continue
            ke, dofs = self._element_ke(eid)
            for i_loc, i_glo in enumerate(dofs):
                for j_loc, j_glo in enumerate(dofs):
                    self._K[i_glo, j_glo] += ke[i_loc, j_loc]
            fe = self._F_per_elem.get(eid)
            if fe is not None:
                self._F += fe
            self._assembled.add(eid)
        self._ptr = len(self._order)
        self._redraw_panel()
        self._update_progress()
        self._mesh.redraw()

    def _reset_assembly(self):
        if self._anim_running:
            return
        self._K.fill(0.0)
        self._F.fill(0.0)
        self._assembled.clear()
        self._ptr = 0
        self._hover_elem = None
        self._hover_cell = None
        self._redraw_panel()
        self._update_progress()
        self._mesh.redraw()

    # ── Override de selección del canvas (click-to-assemble) ─────
    def on_element_selected(self, elem_id: int) -> None:
        """Click en elemento del canvas: si no ensamblado, lo manda al
        frente de la cola y dispara su ensamblaje inmediato.

        Pedagogía: el ORDEN de ensamblaje no afecta K ni F finales —
        esa es la lección. El alumno puede empezar por el "más interesante"
        (con BC, con carga) y ver cómo crece K + F desde ahí."""
        if self._anim_running:
            return
        if elem_id is None or elem_id not in self.project.elements:
            return
        if elem_id in self._assembled:
            return
        remaining = [e for e in self._order if e not in self._assembled
                      and e != elem_id]
        head = [e for e in self._order if e in self._assembled]
        self._order = head + [elem_id] + remaining
        self._ptr = len(head)
        self._do_assemble(elem_id)

    def on_element_deselected(self) -> None:
        """Deseleccionar mientras un pulso está en curso: cancelar el
        after pendiente y limpiar el estado, para que el outline del
        elemento no siga parpadeando sobre un elemento ya deseleccionado
        (hasta ~210 ms residuales)."""
        super().on_element_deselected()
        if self._pulse_after_id:
            try:
                self._mesh.canvas.after_cancel(self._pulse_after_id)
            except tk.TclError:
                pass
            self._pulse_after_id = None
        self._pulse_eid = None
        self._pulse_dofs = []
        self._pulse_frame_idx = 0
        self._anim_running = False
        try:
            self._mesh.redraw()
        except Exception:
            pass

    def _on_canvas_hover_element(self, eid: Optional[int],
                                   *args, **kwargs) -> None:
        """Callback hover del MeshCanvas.

        El MeshCanvas dispara la firma `(elem_id, x_px, y_px)` — capturamos
        los extras con `*args` para tolerar futuras evoluciones del API
        sin romper. eid=None cuando el cursor sale del modelo."""
        if eid != self._hover_elem:
            self._hover_elem = eid
            self._hover_cell = None  # los dos hovers son mutuamente exclusivos
            self._redraw_panel()
            self._mesh.redraw()
        # Notify previous hook (chained — el módulo no se monopoliza el hover).
        if self._saved_hover is not None:
            try:
                self._saved_hover(eid, *args, **kwargs)
            except Exception:
                pass

    # ── Render del panel (K | F | sistema) ─────────────────────────
    def _on_mode_change(self):
        self._mode = self._var_mode.get()
        self._redraw_panel()

    def _on_reduced_toggle(self):
        self._show_reduced = bool(self._var_reduced.get())
        self._redraw_panel()

    def _redraw_panel(self):
        if self._canvas_mpl is None:
            return
        self._fig.clear()
        if self._mode == self.MODE_K:
            ax_k = self._fig.add_subplot(111)
            self._render_K(ax_k)
            self._ax_k = ax_k
            self._ax_f = None
        elif self._mode == self.MODE_F:
            ax_f = self._fig.add_subplot(111)
            self._render_F(ax_f)
            self._ax_k = None
            self._ax_f = ax_f
        else:  # MODE_SYSTEM — K y F lado a lado
            gs = self._fig.add_gridspec(1, 2, width_ratios=[4, 1], wspace=0.12)
            ax_k = self._fig.add_subplot(gs[0, 0])
            ax_f = self._fig.add_subplot(gs[0, 1])
            self._render_K(ax_k)
            self._render_F(ax_f, compact=True)
            self._ax_k = ax_k
            self._ax_f = ax_f
            # Ecuación central del MEF en LaTeX (mathtext) — la vista
            # SISTEMA es donde "K·u=F" deja de ser una etiqueta de control
            # y pasa a ser la ecuación que se resuelve. Aquí sí va como
            # fórmula renderizada, no como texto de botón.
            from education.components.edu_plot_style import EDU_PLOT_TITLE_COLOR
            try:
                self._fig.suptitle(r"$\mathbf{K}\,\mathbf{u} = \mathbf{F}$",
                                   color=EDU_PLOT_TITLE_COLOR, fontsize=13,
                                   y=0.99)
            except Exception:
                pass
        try:
            self._canvas_mpl.draw_idle()
        except tk.TclError:
            pass

    def _resolve_M(self):
        """Devuelve (M, dof_view) según show_reduced. dof_view es el mapping
        índice-visible→DOF-global (para el hit-test del hover)."""
        if self._show_reduced:
            free = self.project.get_free_dofs()
            if free:
                M = self._K[np.ix_(free, free)]
                F = self._F[free]
                return M, F, list(free)
            return self._K, self._F, list(range(self._K.shape[0]))
        return self._K, self._F, list(range(self._K.shape[0]))

    def _render_K(self, ax):
        ax.clear()
        from education.components.edu_plot_style import (
            apply_edu_style_2d, EDU_PLOT_TITLE_COLOR,
        )
        apply_edu_style_2d(ax, show_spines=False)

        M, _, _ = self._resolve_M()
        n = M.shape[0]
        vmax = float(np.max(np.abs(M))) or 1.0
        nz = 1e-12 * vmax

        if n > 40:
            ax.set_xlim(-0.5, n - 0.5)
            ax.set_ylim(n - 0.5, -0.5)
            ax.set_aspect("equal")
            iy, ix = np.where(np.abs(M) > nz)
            if iy.size:
                mags = np.abs(M[iy, ix])
                sizes = 6 + 30 * (mags / vmax)
                ax.scatter(ix, iy, s=sizes, c=M[iy, ix],
                           cmap="coolwarm", vmin=-vmax, vmax=vmax,
                           edgecolors="none", alpha=0.85)
            suffix = " · sparsity"
        else:
            ax.imshow(M, cmap="coolwarm", vmin=-vmax, vmax=vmax,
                       interpolation="nearest")
            if n <= 16:
                for i in range(n):
                    for j in range(n):
                        v = M[i, j]
                        if abs(v) > nz:
                            intensity = abs(v) / vmax
                            color = (EDU_LABEL_BG if intensity > 0.55
                                       else "#dcdcdc")
                            ax.text(j, i, f"{v:.2g}",
                                     ha="center", va="center",
                                     color=color, fontsize=7)
            suffix = ""

        # Tachado de DOFs restringidos (solo en vista global).
        if not self._show_reduced:
            rdofs = self.project.get_restrained_dofs()
            for d in rdofs:
                ax.axhspan(d - 0.5, d + 0.5, color=_C_STRIKE, alpha=0.10)
                ax.axvspan(d - 0.5, d + 0.5, color=_C_STRIKE, alpha=0.10)

        # Hover causal map: elemento → DOFs (filas/columnas amarillas) o
        # pulso secuencial (cells del elemento recién ensamblado en blanco).
        self._render_hover_K_highlight(ax, n)
        self._render_pulse_K_highlight(ax, n)

        if self._show_reduced:
            title = f"K reducida ({M.shape[0]}×{M.shape[0]}){suffix}"
        else:
            title = f"K ({n}×{n}){suffix}"
        ax.set_title(title, color=EDU_PLOT_TITLE_COLOR, fontsize=9, pad=4)
        ax.set_xticks([]); ax.set_yticks([])

    def _render_F(self, ax, *, compact: bool = False):
        ax.clear()
        from education.components.edu_plot_style import (
            apply_edu_style_2d, EDU_PLOT_TITLE_COLOR,
        )
        apply_edu_style_2d(ax, show_spines=False)

        _, F, dof_view = self._resolve_M()
        n = F.shape[0]
        vmax = float(np.max(np.abs(F))) or 1.0

        # Barras horizontales: cada DOF es una fila; el ancho es el valor.
        ys = np.arange(n)
        colors = ["#90caf9" if v >= 0 else "#ef5350" for v in F]
        ax.barh(ys, F, color=colors, edgecolor="none", alpha=0.85)
        ax.set_ylim(n - 0.5, -0.5)
        ax.set_xlim(-vmax * 1.15, vmax * 1.15)
        ax.axvline(0, color="#404055", lw=0.7)

        # Etiquetas numéricas cuando F es chico
        if n <= 16:
            for i, v in enumerate(F):
                if abs(v) < 1e-12 * vmax:
                    continue
                ha = "left" if v >= 0 else "right"
                dx = 0.04 * vmax * (1 if v >= 0 else -1)
                ax.text(v + dx, i, f"{v:+.3g}",
                         ha=ha, va="center", color="#dcdcdc", fontsize=7)

        # BCs en rojo translúcido
        if not self._show_reduced:
            rdofs = self.project.get_restrained_dofs()
            for d in rdofs:
                ax.axhspan(d - 0.5, d + 0.5, color=_C_STRIKE, alpha=0.10)

        # Hover causal map sobre F
        self._render_hover_F_highlight(ax, n)
        self._render_pulse_F_highlight(ax, n)

        if compact:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("F", color=EDU_PLOT_TITLE_COLOR, fontsize=9, pad=4)
        else:
            ax.set_yticks([])
            ax.set_title(f"F  ({n} entradas)",
                         color=EDU_PLOT_TITLE_COLOR, fontsize=9, pad=4)

    def _render_hover_K_highlight(self, ax, n):
        """Resalta las filas/columnas del elemento bajo hover."""
        if self._hover_elem is None or self._hover_elem in self._assembled:
            return
        elem = self.project.elements.get(self._hover_elem)
        if elem is None:
            return
        try:
            dofs = elem.get_dof_indices(self.project)
        except Exception:
            return
        for d in dofs:
            if self._show_reduced:
                continue
            if not (0 <= d < n):
                continue
            ax.axhspan(d - 0.5, d + 0.5, color=_C_HOVER, alpha=0.18)
            ax.axvspan(d - 0.5, d + 0.5, color=_C_HOVER, alpha=0.18)

    def _render_pulse_K_highlight(self, ax, n):
        """Flash blanco sobre las celdas del elemento durante el pulso."""
        if not self._pulse_dofs or self._show_reduced:
            return
        # Frames pares = visible; impares = invisible (parpadeo binario).
        if (self._pulse_frame_idx % 2) == 1:
            return
        for d in self._pulse_dofs:
            if not (0 <= d < n):
                continue
            ax.axhspan(d - 0.5, d + 0.5, color=_C_PULSE, alpha=0.10)
            ax.axvspan(d - 0.5, d + 0.5, color=_C_PULSE, alpha=0.10)

    def _render_hover_F_highlight(self, ax, n):
        if self._hover_elem is None or self._hover_elem in self._assembled:
            return
        elem = self.project.elements.get(self._hover_elem)
        if elem is None:
            return
        try:
            dofs = elem.get_dof_indices(self.project)
        except Exception:
            return
        for d in dofs:
            if self._show_reduced:
                continue
            if not (0 <= d < n):
                continue
            ax.axhspan(d - 0.5, d + 0.5, color=_C_HOVER, alpha=0.22)

    def _render_pulse_F_highlight(self, ax, n):
        if not self._pulse_dofs or self._show_reduced:
            return
        if (self._pulse_frame_idx % 2) == 1:
            return
        for d in self._pulse_dofs:
            if not (0 <= d < n):
                continue
            ax.axhspan(d - 0.5, d + 0.5, color=_C_PULSE, alpha=0.14)

    # ── Hover sobre los ejes matplotlib (K / F) ───────────────────
    def _on_axes_motion(self, event):
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        ax = event.inaxes
        if ax is self._ax_k:
            j = int(round(event.xdata)); i = int(round(event.ydata))
            n = self._K.shape[0]
            if not self._show_reduced and 0 <= i < n and 0 <= j < n:
                # Hover sobre celda K[i,j]: highlight elementos que la tocan.
                new = (i, j)
                if new != self._hover_cell:
                    self._hover_cell = new
                    self._hover_elem = None
                    self._redraw_panel()
                    self._mesh.redraw()
                # Actualizar status bar con el valor de la celda.
                v = float(self._K[i, j])
                if self._lbl_progress is not None:
                    try:
                        self._lbl_progress.configure(
                            text=(f"K[{i},{j}] = {v:+.4g}  ·  "
                                  f"Ensamblados {len(self._assembled)}/"
                                  f"{len(self._order)}")
                        )
                    except tk.TclError:
                        pass
        elif ax is self._ax_f:
            i = int(round(event.ydata))
            n = self._F.shape[0]
            if 0 <= i < n:
                v = float(self._F[i])
                if self._lbl_progress is not None:
                    try:
                        self._lbl_progress.configure(
                            text=(f"F[{i}] = {v:+.4g}  ·  "
                                  f"Ensamblados {len(self._assembled)}/"
                                  f"{len(self._order)}")
                        )
                    except tk.TclError:
                        pass

    def _on_axes_leave(self, event):
        if self._hover_cell is not None:
            self._hover_cell = None
            self._redraw_panel()
            self._mesh.redraw()
        self._update_progress()

    def _on_axes_click(self, event):
        """Click sobre K en una celda restringida: animación 'tachado' del
        BC (igual semántica que la versión vuelo Bézier — útil para
        visualizar el efecto del reducer)."""
        if event.inaxes is not self._ax_k or self._show_reduced:
            return
        if event.xdata is None or event.ydata is None:
            return
        i_dof = int(round(event.ydata))
        j_dof = int(round(event.xdata))
        rdofs = set(self.project.get_restrained_dofs())
        if i_dof in rdofs or j_dof in rdofs:
            self._animate_strike(i_dof if i_dof in rdofs else j_dof,
                                  axis="row" if i_dof in rdofs else "col")

    def _animate_strike(self, dof, axis):
        n = self._K.shape[0]
        ax = self._ax_k
        line = ax.plot([], [], color=_C_STRIKE, lw=3, alpha=0.9,
                        zorder=20)[0]
        if axis == "row":
            x_full = [-0.5, n - 0.5]; y_full = [dof, dof]
        else:
            x_full = [dof, dof]; y_full = [-0.5, n - 0.5]

        def step(k):
            try:
                if k > 12:
                    line.remove()
                    self._canvas_mpl.draw_idle()
                    return
                t = k / 12.0
                if axis == "row":
                    cx = (x_full[0] + x_full[1]) / 2
                    line.set_data(
                        [cx - (cx - x_full[0]) * t,
                         cx + (x_full[1] - cx) * t],
                        y_full,
                    )
                else:
                    cy = (y_full[0] + y_full[1]) / 2
                    line.set_data(
                        x_full,
                        [cy - (cy - y_full[0]) * t,
                         cy + (y_full[1] - cy) * t],
                    )
                self._canvas_mpl.draw_idle()
                self._mesh.canvas.after(30, lambda: step(k + 1))
            except (tk.TclError, ValueError, AttributeError):
                return
        step(1)

    def _elements_for_cell(self, i: int, j: int) -> Set[int]:
        """Elementos cuyo set de DOFs contiene a `i` Y `j` — esos son los
        que contribuyen a K[i,j]. Si no encuentra, retorna set vacío.
        Restringido a elementos ya ensamblados (sino la causal map mostraría
        contribuciones que todavía no son visibles en K)."""
        out: Set[int] = set()
        for eid in self._assembled:
            elem = self.project.elements.get(eid)
            if elem is None:
                continue
            try:
                dofs = set(elem.get_dof_indices(self.project))
            except Exception:
                continue
            if i in dofs and j in dofs:
                out.add(eid)
        return out

    def _update_progress(self):
        if self._lbl_progress is None:
            return
        n = len(self._order)
        try:
            done = len(self._assembled)
            nxt = (f"E{self._order[self._ptr]}"
                    if self._ptr < n else "—")
            self._lbl_progress.configure(text=(
                f"Ensamblados {done}/{n}  ·  Próximo {nxt}"
            ))
        except tk.TclError:
            pass

    # ── Cleanup al cerrar ──────────────────────────────────────────
    def on_closed(self):
        self._anim_running = False
        if self._pulse_after_id:
            try:
                self._mesh.canvas.after_cancel(self._pulse_after_id)
            except tk.TclError:
                pass
            self._pulse_after_id = None
        # Restaurar el hook hover.
        try:
            if self._mesh.on_hover_element == self._on_canvas_hover_element:
                self._mesh.on_hover_element = self._saved_hover
        except Exception:
            pass
        try:
            self._mesh.canvas.delete(_TAG_BASE)
        except tk.TclError:
            pass
