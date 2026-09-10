"""
Surface3DViewer: Toplevel con vista 3D del campo de esfuerzos/desplazamientos.

Reemplaza al modulo educativo M7 (legacy): vista del Post-Proceso
accesible via boton "🧊 Vista 3D" en la toolbar. Sincronizado con el
result_type del post: cambiar de VM a σx repinta automaticamente.

Diseno visual (rediseno 2026-05):
  - **Estilo coherente con el canvas del Post**: mismo colormap que el
    MeshCanvas (jet/arcoiris para todos los campos; los que tienen signo se
    signo; LUTs de config/colormaps, no los de matplotlib). Esto unifica
    cromaticamente la vista 2D del contorno y la vista 3D de la superficie
    -- el alumno reconoce los mismos colores.
  - **Ejes sin ruido visual**: sin ticks, sin numeros, sin paneles de
    fondo. Solo la superficie 3D + un plano de referencia gris suave en
    z=0 que sirve de "horizonte" -- los valores positivos sobresalen, los
    negativos hunden bajo el plano.
  - **Escala de color graduada** al costado (`_draw_colorbar`), con el
    campo y la unidad del proyecto (`Von Mises [Pa]`) y los mismos ticks
    que la colorbar del lienzo 2D (`config.settings.fmt_escala`). Los ejes
    van limpios, pero la escala NO es ruido: sin ella el arcoiris no tenia
    referencia numerica y era la unica vista de resultados sin ella.
  - **Toggle binario Crudo/Suavizado** (no slider): el alumno alterna
    entre las dos vistas conceptuales sin "estados intermedios" que
    confundian (la transicion continua era visualmente ambigua).

Pipeline numerico (reusado, no duplicado):
  - Modo CRUDO: compute_raw_grid evalua σ = D·B(ξ,η)·u_e en cada punto
    de una grilla (n+1)×(n+1) por elemento -- esfuerzo discontinuo C0.
  - Modo SUAVIZADO: Σ N_i(ξ,η)·σ_i_avg con los valores nodales
    promediados -- esfuerzo C0 continuo entre elementos.

Detector de discontinuidades: aristas con varianza nodal > 10% del rango
global se dibujan en rojo grueso en modo crudo. Base cualitativa del
estimador Zienkiewicz-Zhu (1992).

Bibliografia:
  - Zienkiewicz, O. C. & Zhu, J. Z. (1992). SPR. CMAME 101.
  - Hinton, E. & Campbell, J. S. (1974). Smoothing nodal. IJNME 8.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

# matplotlib se importa en _build_lut_cmap() y __init__() para diferir el
# costo de arranque. El visor 3D se abre solo cuando el usuario lo solicita.

from config.settings import (
    SURFACE_3D_DEFAULT_GRID, SURFACE_3D_DISC_THRESHOLD,
    MOHR_BG, MOHR_FG,
    CANVAS_ELEMENT_COLOR, HEALTH_ERROR_COLOR,
    SURFACE_3D_EDGE_RAW_COLOR, SURFACE_3D_EDGE_SMOOTH_COLOR,
    SURFACE_3D_MODE_RAW_COLOR, SURFACE_3D_Z0_PLANE_COLOR,
    SURFACE_3D_Z0_EDGE_COLOR, fmt, fmt_escala,
)
from fem.probe_query import compute_raw_grids
from fem.shape_functions import get_shape_functions
from gui.scaling import fit_window


# Mapeo de result_type (radio button del post) -> clave en grids de
# probe_query y label legible. Solo esfuerzos: para Ux/Uy/|U| usamos
# rutas separadas (interpolacion via shape functions, no compute_raw_grid).
_STRESS_KEY = {
    "Sx":  ("sigma_x",   "σx"),
    "Sy":  ("sigma_y",   "σy"),
    "Txy": ("tau_xy",    "τxy"),
    "S1":  ("sigma_1",   "σ₁"),
    "S2":  ("sigma_2",   "σ₂"),
    "VM":  ("von_mises", "Von Mises"),
}

_DISPLACEMENT_LABEL = {
    "Ux":   "Ux",
    "Uy":   "Uy",
    "Umag": "|U|",
}


# ── Colormap perceptual coherente con MeshCanvas ──────────────────────────
# Construimos ListedColormaps de 256 colores a partir de los MISMOS LUT que
# usa el canvas del Post (config/colormaps): jet (arcoiris clasico ANSYS/SAP)
# para campos no negativos, coolwarm para campos con signo (centrados en 0).
# Unifica la paleta entre 2D y 3D (jet por pedido del usuario, 2026-05-31).
from config.colormaps import (
    JET_LUT, is_diverging_range, symmetric_bounds,
)


def _build_lut_cmap(lut):
    from matplotlib.colors import ListedColormap
    rgba = np.column_stack([
        lut[:, 0] / 255.0, lut[:, 1] / 255.0, lut[:, 2] / 255.0,
        np.ones(256),
    ])
    return ListedColormap(rgba)


# ── Grilla natural del elemento maestro ───────────────────────────────────
# Convencion de indices: `G[i, j]` es el punto (ξ_i, η_j), es decir
# `np.meshgrid(..., indexing="ij")`. Es la MISMA que usan
# `fem.probe_query.compute_raw_grids` (de donde sale la Z del modo crudo) y
# `gui/preprocessing/canvas_raster.py` (el contorno 2D). Con el `indexing`
# por defecto ("xy") la geometria queda indexada [η, ξ] y el campo crudo
# [ξ, η]: la superficie se dibujaba con el campo TRANSPUESTO dentro de cada
# elemento — invisible en un campo simetrico, un error grosero en cualquier
# otro. El modo suavizado no lo sufria (X, Y y Z salian del mismo meshgrid).

_N_AT_GRID_CACHE: dict = {}


def natural_grid(n: int):
    """(XI, ETA) de la grilla (n+1)×(n+1) del elemento maestro, indexada
    [i_ξ, j_η] (ver la nota de convencion de arriba)."""
    xs = np.linspace(-1.0, 1.0, n + 1)
    return np.meshgrid(xs, xs, indexing="ij")


def shape_matrix_at_grid(element_type: str, n: int) -> np.ndarray:
    """Matriz `(n+1)² × n_nodos` con N evaluada en cada punto de la grilla,
    en orden C sobre [i_ξ, j_η]. Cacheada por (tipo de elemento, n).

    Es la MISMA para todos los elementos —las coordenadas naturales no
    dependen del elemento—, asi que se evalua una vez por malla en lugar de
    (n+1)² veces por elemento: en Cook 32×32 Q9 eran ~83 000 llamadas a las
    funciones de forma por repintado.
    """
    key = (element_type, n)
    cached = _N_AT_GRID_CACHE.get(key)
    if cached is not None:
        return cached
    N_func, _ = get_shape_functions(element_type)
    XI, ETA = natural_grid(n)
    rows = [N_func(float(xi), float(eta))
            for xi, eta in zip(XI.ravel(), ETA.ravel())]
    mat = np.asarray(rows, dtype=float)
    _N_AT_GRID_CACHE[key] = mat
    return mat


def element_grid_xy(project, elem, n: int):
    """(X, Y) fisicas de la grilla natural del elemento, indexadas [i_ξ, j_η].

    Funcion pura (sin Tk): la comparte el visor 3D con
    `tests/test_post_3d_grid.py`, que verifica que geometria y campo crudo
    comparten la convencion de indices.
    """
    n_nodes_elem = elem.num_nodes
    pts = np.array(
        [[project.nodes[nid].x, project.nodes[nid].y]
         for nid in elem.node_ids[:n_nodes_elem]],
        dtype=float,
    )
    N_grid = shape_matrix_at_grid(project.element_type, n)
    # Defensivo (mismo criterio que probe_query.compute_raw_grids): un
    # proyecto Q9 con elementos de 4 nodos usa los nodos en comun.
    n_use = min(N_grid.shape[1], pts.shape[0])
    side = n + 1
    X = (N_grid[:, :n_use] @ pts[:n_use, 0]).reshape(side, side)
    Y = (N_grid[:, :n_use] @ pts[:n_use, 1]).reshape(side, side)
    return X, Y


_JET_CMAP = None       # inicializado en primera apertura del visor


def _cmap_for_range(vmin, vmax):
    """(cmap, vmin, vmax) coherente con el canvas: JET para todo (ANSYS/SAP).
    Los campos con signo se centran simetricamente en 0."""
    if is_diverging_range(vmin, vmax):
        lo, hi = symmetric_bounds(vmin, vmax)
        return _JET_CMAP, lo, hi
    return _JET_CMAP, vmin, vmax


class Surface3DViewer(tk.Toplevel):
    """Vista 3D del campo activo del Post.

    No-modal (sin grab_set): el usuario sigue interactuando con la
    toolbar del post. Al cambiar result_type o el modo de calculo, el 3D
    se refresca via `refresh()` (lo llama post_tab._on_result_changed).
    """

    DEFAULT_WIDTH = 900
    DEFAULT_HEIGHT = 700

    def __init__(self, parent, project, solution, nodal_stresses,
                  post_tab, main_window):
        super().__init__(parent)
        self.title("🧊  Vista 3D del campo")
        # Medidas de diseño: `fit_window` las recorta al area util real.
        fit_window(self, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT,
                   parent=parent, minimo=(520, 420),
                   crecer_con_contenido=False)
        self.transient(parent)
        # NO grab_set -- usuario puede seguir tocando el post mientras

        self.project = project
        self.solution = solution
        self.nodal_stresses = nodal_stresses
        self.post_tab = post_tab
        self.main_window = main_window

        # Estado interno: binario crudo/suavizado (no slider continuo).
        # Default smooth para coherencia con el comportamiento historico
        # del Post (contorno continuo).
        self._mode_var: Optional[tk.StringVar] = None  # "raw" | "smooth"
        self._show_disc = True
        self._show_z0_plane = True  # plano de referencia z=0

        # Widgets matplotlib (creados en _build_ui)
        self._fig: Optional[Figure] = None
        self._ax: Optional = None
        self._mpl_canvas: Optional[FigureCanvasTkAgg] = None
        self._info_label: Optional[ttk.Label] = None
        self._cbar = None   # escala de color; se recrea en cada repintado

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda _e: self._on_close())

        self._build_ui()
        self.refresh()

    # ── Construccion del layout ────────────────────────────────────────
    def _build_ui(self):
        # Header: titulo + label "Mostrando: ..."
        header = ttk.Frame(self, padding=(10, 8, 10, 4))
        header.pack(fill=tk.X)

        ttk.Label(
            header, text="Vista 3D del campo activo",
            font=("Segoe UI Semibold", 12),
            bootstyle="info",
        ).pack(side=tk.LEFT)

        self._info_label = ttk.Label(
            header, text="", font=("Consolas", 9), bootstyle="secondary",
        )
        self._info_label.pack(side=tk.RIGHT)

        # Body: matplotlib Figure 3D (import diferido: solo al abrir el visor)
        global _JET_CMAP
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        if _JET_CMAP is None:
            _JET_CMAP = _build_lut_cmap(JET_LUT)

        body = ttk.Frame(self, padding=(8, 4))
        body.pack(fill=tk.BOTH, expand=True)

        self._fig = Figure(figsize=(8.5, 5.5), dpi=100, facecolor=MOHR_BG)
        self._ax = self._fig.add_subplot(111, projection="3d")
        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=body)
        self._mpl_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Footer: toggle Crudo/Suavizado + toggle discontinuidades + plano z=0
        footer = ttk.Frame(self, padding=(10, 6, 10, 10))
        footer.pack(fill=tk.X)

        ttk.Label(
            footer, text="Modo:",
            font=("Segoe UI Semibold", 10),
        ).pack(side=tk.LEFT, padx=(0, 6))

        self._mode_var = tk.StringVar(value="smooth")
        ttk.Radiobutton(
            footer, text="Crudo",
            value="raw", variable=self._mode_var,
            bootstyle="warning-toolbutton",
            command=self._on_mode_changed,
        ).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(
            footer, text="Suavizado",
            value="smooth", variable=self._mode_var,
            bootstyle="success-toolbutton",
            command=self._on_mode_changed,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(footer, orient="vertical").pack(
            side=tk.LEFT, fill=tk.Y, padx=12,
        )

        self._disc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            footer, text="Marcar discontinuidades",
            variable=self._disc_var, bootstyle="warning-round-toggle",
            command=self._on_disc_toggled,
        ).pack(side=tk.LEFT, padx=4)

        self._z0_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            footer, text="Plano z=0",
            variable=self._z0_var, bootstyle="info-round-toggle",
            command=self._on_z0_toggled,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            footer, text="✕ Cerrar",
            bootstyle="secondary-outline",
            command=self._on_close,
        ).pack(side=tk.RIGHT, padx=4)

    # ── Callbacks ──────────────────────────────────────────────────────
    def _on_mode_changed(self):
        self.refresh()

    def _on_disc_toggled(self):
        self._show_disc = bool(self._disc_var.get())
        self.refresh()

    def _on_z0_toggled(self):
        self._show_z0_plane = bool(self._z0_var.get())
        self.refresh()

    def _on_close(self):
        # Notificar al post_tab para que limpie la ref
        if (self.post_tab is not None
                and getattr(self.post_tab, "surface_3d_viewer", None) is self):
            self.post_tab.surface_3d_viewer = None
        self.destroy()

    def destroy(self):
        try:
            import matplotlib.pyplot as _plt
            _plt.close(self._fig)
        except Exception:
            pass
        super().destroy()

    # ── API publica ────────────────────────────────────────────────────
    def update_solution(self, solution, nodal_stresses):
        """Actualiza refs tras re-solve. Lo llama post_tab."""
        self.solution = solution
        self.nodal_stresses = nodal_stresses
        self.refresh()

    def refresh(self):
        """Repinta la superficie. Lo llama post_tab cuando cambia el
        result_type o el modo de calculo."""
        if self._ax is None or self.solution is None:
            return
        rtype = self._active_result_type()
        is_stress = rtype in _STRESS_KEY
        if is_stress:
            self._render_stress(rtype)
        else:
            self._render_displacement(rtype)

    # ── Render: esfuerzos ──────────────────────────────────────────────
    def _render_stress(self, rtype: str):
        """Render del campo de esfuerzos en modo crudo o suavizado (binario)."""
        key, label = _STRESS_KEY[rtype]
        unidad = self._unidad_activa(is_stress=True)
        ax = self._ax
        ax.clear()
        self._clear_colorbar()
        self._setup_clean_axes(ax)

        is_raw = (self._mode_var is not None and self._mode_var.get() == "raw")
        n = SURFACE_3D_DEFAULT_GRID
        N_grid = shape_matrix_at_grid(self.project.element_type, n)
        side = n + 1

        elem_data = []
        all_z = []
        per_node_raw = {}   # para detector de discontinuidades
        # Modo crudo: grillas (n+1, n+1) de todos los elementos en una sola
        # llamada vectorizada por lotes.
        raw_grids = None
        crudo_no_disponible = False
        if is_raw:
            try:
                raw_grids = compute_raw_grids(self.project, self.solution, n=n)
            except Exception:
                # Sin traza, un fallo de ensamblaje aqui se veia como un
                # visor vacio y "(sin datos)" — indepurable.
                import traceback
                traceback.print_exc()
                raw_grids = None
            if not raw_grids:
                # El contorno 2D ya cae a suavizado cuando el crudo no esta
                # disponible (post_tab._on_result_changed); el 3D mostraba
                # "(sin datos para el campo activo)" y dejaba al alumno sin
                # superficie ni explicacion. Misma politica en las dos vistas.
                is_raw = False
                crudo_no_disponible = True

        for eid, elem in self.project.elements.items():
            n_nodes_elem = elem.num_nodes
            v_nodes_smooth = np.array([
                (self.nodal_stresses.get(nid, {}) or {}).get(key, 0.0)
                for nid in elem.node_ids[:n_nodes_elem]
            ])

            # Geometria X, Y sobre la grilla (n+1, n+1), indexada [i_ξ, j_η]
            # igual que las grillas crudas de probe_query (ver la nota de
            # convencion arriba del modulo).
            X, Y = element_grid_xy(self.project, elem, n)

            if is_raw:
                grids = raw_grids.get(eid)
                if grids is None:
                    continue
                Z = np.asarray(grids[key])
            else:
                # Z_smooth = Σ Nᵢ(ξ,η)·σᵢ̄ vectorizado sobre toda la grilla.
                n_use = min(N_grid.shape[1], len(v_nodes_smooth))
                Z = (N_grid[:, :n_use] @ v_nodes_smooth[:n_use]).reshape(
                    side, side)

            elem_data.append((X, Y, Z, elem, v_nodes_smooth))
            all_z.append(Z)

            # Acumular valores nodales raw para detector de discontinuidades
            est = (self.project.stresses or {}).get(eid)
            if est is not None:
                for i, nid in enumerate(elem.node_ids[:n_nodes_elem]):
                    if i < len(est.get("nodal_stresses", [])):
                        v_raw = est["nodal_stresses"][i].get(key, 0.0)
                        per_node_raw.setdefault(nid, []).append(v_raw)

        if not elem_data:
            ax.text2D(0.5, 0.5, "(sin datos para el campo activo)",
                       ha="center", va="center", color=MOHR_FG,
                       transform=ax.transAxes)
            self._mpl_canvas.draw_idle()
            return

        # Rango global (incluye plano z=0 si esta activo: garantiza que el
        # 0 quede dentro del rango visualizado).
        z_all = np.concatenate([Z.flatten() for Z in all_z])
        vmin = float(np.min(z_all))
        vmax = float(np.max(z_all))
        if self._show_z0_plane:
            vmin = min(vmin, 0.0)
            vmax = max(vmax, 0.0)
        if vmax - vmin < 1e-12:
            vmax = vmin + 1.0
        v_range = vmax - vmin

        # Plano de referencia z=0: gris suave que sirve de "horizonte".
        # Valores positivos sobresalen, negativos hunden. Renderizar
        # PRIMERO (z-order menor) para que la superficie quede encima.
        if self._show_z0_plane:
            self._draw_z0_plane(ax, elem_data)

        # Superficie del campo: bordes blancos en suavizado (continuo),
        # bordes amarillos en crudo (resalta las "tejas" discontinuas).
        edge_lw = 0.6 if is_raw else 0.15
        edge_color = SURFACE_3D_EDGE_RAW_COLOR if is_raw else SURFACE_3D_EDGE_SMOOTH_COLOR

        cmap, c_vmin, c_vmax = _cmap_for_range(vmin, vmax)
        c_range = max(c_vmax - c_vmin, 1e-15)
        for X, Y, Z, _elem, _v in elem_data:
            facecolors = cmap((Z - c_vmin) / c_range)
            ax.plot_surface(
                X, Y, Z, facecolors=facecolors,
                edgecolor=edge_color, linewidth=edge_lw,
                alpha=0.95, rcount=n, ccount=n, shade=False,
            )

        # Detector de discontinuidades: aristas en rojo grueso. Solo
        # tiene sentido en modo CRUDO (en suavizado no hay saltos).
        if is_raw and self._show_disc and v_range > 1e-12:
            disc_nodes = {
                nid for nid, vs in per_node_raw.items()
                if len(vs) >= 2
                and (max(vs) - min(vs)) > SURFACE_3D_DISC_THRESHOLD * v_range
            }
            if disc_nodes:
                self._draw_discontinuity_edges(ax, elem_data, disc_nodes)

        # Estado de modo en el titulo, no en los ejes (que estan limpios)
        if is_raw:
            mode_lbl = "CRUDO  σ = D·B(ξ,η)·uₑ  (discontinuo C⁰)"
            mode_color = SURFACE_3D_MODE_RAW_COLOR
        elif crudo_no_disponible:
            mode_lbl = "SUAVIZADO  σ = Σ Nᵢ·σᵢ̄  (sin datos crudos disponibles)"
            mode_color = SURFACE_3D_MODE_RAW_COLOR
        else:
            mode_lbl = "SUAVIZADO  σ = Σ Nᵢ·σᵢ̄  (continuo)"
            mode_color = CANVAS_ELEMENT_COLOR

        ax.set_title(
            f"{label}  ·  {mode_lbl}",
            color=mode_color, fontsize=11, pad=8, fontweight="bold",
        )
        if crudo_no_disponible:
            self._avisar(
                f"Modo crudo no disponible para {label} — mostrando el campo "
                f"suavizado. Volvé a resolver (F5) si acabás de editar la malla."
            )

        self._draw_colorbar(ax, cmap, c_vmin, c_vmax, label, unidad)
        self._set_info(label, vmin, vmax, "stress")
        self._finalize_view(ax, vmin, vmax)

    # ── Render: desplazamientos ────────────────────────────────────────
    def _render_displacement(self, rtype: str):
        """Para desplazamientos no hay distincion crudo/suavizado (son C0
        continuos por construccion del MEF). Z = u_i interpolado por las
        shape functions a partir de los valores nodales.
        """
        label = _DISPLACEMENT_LABEL.get(rtype, rtype)
        unidad = self._unidad_activa(is_stress=False)
        ax = self._ax
        ax.clear()
        self._clear_colorbar()
        self._setup_clean_axes(ax)

        u = self.solution["u"]
        idx_map = self.project.node_index_map
        n = SURFACE_3D_DEFAULT_GRID
        N_grid = shape_matrix_at_grid(self.project.element_type, n)
        side = n + 1

        elem_data = []
        all_z = []
        for eid, elem in self.project.elements.items():
            n_nodes_elem = elem.num_nodes
            v_nodes = []
            for nid in elem.node_ids[:n_nodes_elem]:
                base = 2 * idx_map[nid]
                ux = u[base]
                uy = u[base + 1]
                if rtype == "Ux":
                    v_nodes.append(ux)
                elif rtype == "Uy":
                    v_nodes.append(uy)
                else:  # Umag
                    v_nodes.append(math.hypot(ux, uy))
            v_nodes = np.array(v_nodes)

            X, Y = element_grid_xy(self.project, elem, n)
            n_use = min(N_grid.shape[1], len(v_nodes))
            Z = (N_grid[:, :n_use] @ v_nodes[:n_use]).reshape(side, side)
            elem_data.append((X, Y, Z, elem, v_nodes))
            all_z.append(Z)

        if not elem_data:
            ax.text2D(0.5, 0.5, "(sin datos)", ha="center", va="center",
                       color=MOHR_FG, transform=ax.transAxes)
            self._mpl_canvas.draw_idle()
            return

        z_all = np.concatenate([Z.flatten() for Z in all_z])
        vmin = float(np.min(z_all))
        vmax = float(np.max(z_all))
        if self._show_z0_plane:
            vmin = min(vmin, 0.0)
            vmax = max(vmax, 0.0)
        if vmax - vmin < 1e-12:
            vmax = vmin + 1.0
        v_range = vmax - vmin

        if self._show_z0_plane:
            self._draw_z0_plane(ax, elem_data)

        cmap, c_vmin, c_vmax = _cmap_for_range(vmin, vmax)
        c_range = max(c_vmax - c_vmin, 1e-15)
        for X, Y, Z, _elem, _v in elem_data:
            facecolors = cmap((Z - c_vmin) / c_range)
            ax.plot_surface(
                X, Y, Z, facecolors=facecolors,
                edgecolor=SURFACE_3D_EDGE_SMOOTH_COLOR, linewidth=0.15,
                alpha=0.95, rcount=n, ccount=n, shade=False,
            )

        ax.set_title(
            f"Desplazamiento  {label}  (continuo C⁰ del MEF)",
            color=MOHR_FG, fontsize=11, pad=8, fontweight="bold",
        )

        self._draw_colorbar(ax, cmap, c_vmin, c_vmax, label, unidad)
        self._set_info(label, vmin, vmax, "displacement")
        self._finalize_view(ax, vmin, vmax)

    # ── Escala de color, unidades y avisos ─────────────────────────────
    def _unidad_activa(self, is_stress: bool) -> str:
        """Unidad del sistema del proyecto para el campo activo.

        Misma fuente que la colorbar del lienzo 2D y que los encabezados de
        la tabla de resultados (`post_tab._get_units`), para que el alumno
        lea la misma unidad en las tres vistas.
        """
        try:
            unidades = self.post_tab._get_units()
        except Exception:
            import traceback
            traceback.print_exc()
            return ""
        return unidades.get("esfuerzo" if is_stress else "longitud", "")

    def _clear_colorbar(self):
        """Quita la colorbar previa. `ax.clear()` no la borra: sin esto cada
        repintado apilaba un eje nuevo y la superficie se iba achicando."""
        if self._cbar is None:
            return
        try:
            self._cbar.remove()
        except Exception:
            import traceback
            traceback.print_exc()
        self._cbar = None

    def _draw_colorbar(self, ax, cmap, c_vmin, c_vmax, label, unidad):
        """Escala de color graduada, con la misma lectura que la colorbar del
        lienzo 2D: `<campo> [<unidad>]` y ticks en notacion cientifica para
        magnitudes grandes o chicas.

        Sin ella la superficie 3D era la unica vista de resultados sin
        referencia numerica del color: el alumno veia el arcoiris y no podia
        decir cuanto vale el rojo. La tesis apoya la eleccion de la paleta
        jet justamente en que «se compensa con la escala numerica graduada
        junto al contorno» (03_diseno_implementacion).
        """
        from matplotlib.cm import ScalarMappable
        from matplotlib.colors import Normalize
        from matplotlib.ticker import FuncFormatter

        sm = ScalarMappable(norm=Normalize(vmin=c_vmin, vmax=c_vmax),
                            cmap=cmap)
        sm.set_array([])
        try:
            self._cbar = self._fig.colorbar(
                sm, ax=ax, shrink=0.62, pad=0.02, fraction=0.045,
            )
        except Exception:
            import traceback
            traceback.print_exc()
            self._cbar = None
            return
        titulo = f"{label} [{unidad}]" if unidad else label
        self._cbar.set_label(titulo, color=MOHR_FG, fontsize=9)
        self._cbar.ax.tick_params(colors=MOHR_FG, labelsize=7)
        self._cbar.ax.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _p: fmt_escala(v))
        )
        try:
            self._cbar.outline.set_edgecolor(MOHR_FG)
        except Exception:
            pass

    def _set_info(self, label, vmin, vmax, kind):
        """Lectura del rango en el header, con la unidad del proyecto.

        Usa `fmt_escala` —el mismo formateador de los ticks de la colorbar
        que tiene al lado y de la del lienzo 2D— y no `fmt`: los extremos de
        una escala se leen comparandolos entre si. Con los decimales fijos de
        `fmt(valor, "displacement")` un rango de 1e-7 m se mostraba como
        `[0.00000, 0.00000]`. Antes era `{v:.3g}` inline y sin unidad
        (incumplia la regla dura 8 y no decia en que unidad estaba).
        """
        if self._info_label is None:
            return
        unidad = self._unidad_activa(is_stress=(kind == "stress"))
        sufijo = f" {unidad}" if unidad else ""
        try:
            self._info_label.configure(
                text=(f"Mostrando: {label}  ·  rango: "
                      f"[{fmt_escala(vmin)}, {fmt_escala(vmax)}]{sufijo}")
            )
        except tk.TclError:
            pass

    def _avisar(self, mensaje: str):
        """Mensaje a la barra de estado de la ventana principal."""
        try:
            self.main_window.set_status(mensaje)
        except Exception:
            import traceback
            traceback.print_exc()

    # ── Helpers de render ──────────────────────────────────────────────
    def _draw_z0_plane(self, ax, elem_data):
        """Plano de referencia gris suave en z=0.

        Sirve de "horizonte" visual: valores positivos sobresalen, los
        negativos hunden bajo el plano. Cubre el bounding box XY del
        modelo con un cuadrilatero de 2 triangulos (alpha bajo).
        """
        all_x = []
        all_y = []
        for X, Y, _Z, _elem, _v in elem_data:
            all_x.extend([X.min(), X.max()])
            all_y.extend([Y.min(), Y.max()])
        if not all_x:
            return
        x_lo, x_hi = min(all_x), max(all_x)
        y_lo, y_hi = min(all_y), max(all_y)
        # Pequeño margen para que el plano se vea ligeramente mas grande
        # que la malla -- lectura visual mas clara.
        dx = (x_hi - x_lo) * 0.04
        dy = (y_hi - y_lo) * 0.04
        x_lo -= dx; x_hi += dx
        y_lo -= dy; y_hi += dy

        Xp = np.array([[x_lo, x_hi], [x_lo, x_hi]])
        Yp = np.array([[y_lo, y_lo], [y_hi, y_hi]])
        Zp = np.zeros_like(Xp)
        # Gris suave translucido: visible pero no compite con la superficie
        ax.plot_surface(
            Xp, Yp, Zp,
            color=SURFACE_3D_Z0_PLANE_COLOR, alpha=0.18,
            edgecolor=SURFACE_3D_Z0_EDGE_COLOR,
            linewidth=0.4, shade=False, zorder=0,
        )

    def _draw_discontinuity_edges(self, ax, elem_data, disc_nodes):
        """Aristas macro de cada elemento que toquen un nodo discontinuo
        en rojo grueso. Z usa el valor SUAVIZADO en los corners
        (consistente como hilo visual; los saltos se ven en la
        superficie misma, no en la arista)."""
        for X, Y, Z, elem, v_nodes_smooth in elem_data:
            n_nodes_elem = elem.num_nodes
            pts_world = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in elem.node_ids[:n_nodes_elem]
            ])
            corner_ids = elem.node_ids[:4]
            for k in range(4):
                a = corner_ids[k]
                b = corner_ids[(k + 1) % 4]
                if a not in disc_nodes and b not in disc_nodes:
                    continue
                ka = elem.node_ids.index(a)
                kb = elem.node_ids.index(b)
                pa = (pts_world[ka, 0], pts_world[ka, 1],
                       float(v_nodes_smooth[ka]))
                pb = (pts_world[kb, 0], pts_world[kb, 1],
                       float(v_nodes_smooth[kb]))
                ax.plot(
                    [pa[0], pb[0]], [pa[1], pb[1]], [pa[2], pb[2]],
                    color=HEALTH_ERROR_COLOR, lw=2.5, alpha=0.9, zorder=10,
                )

    @staticmethod
    def _setup_clean_axes(ax):
        """Configura los ejes 3D SIN ruido visual: sin ticks, sin numeros,
        sin paneles de fondo, sin labels. Solo queda la superficie en el
        espacio 3D y el titulo arriba. La superficie habla por si sola.
        """
        ax.set_facecolor(MOHR_BG)
        # Sin ticks/numeros en los 3 ejes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        # Sin labels de eje
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_zlabel("")
        # Paneles de fondo (las "paredes" del cubo 3D) transparentes
        for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
            try:
                pane.pane.set_facecolor((0, 0, 0, 0))
                pane.pane.set_edgecolor((0, 0, 0, 0))
            except Exception:
                pass
            # Ocultar la linea del eje
            try:
                pane.line.set_color((0, 0, 0, 0))
            except Exception:
                pass
            # Ocultar gridlines internas
            try:
                pane._axinfo["grid"]["linewidth"] = 0
                pane._axinfo["grid"]["color"] = (0, 0, 0, 0)
            except Exception:
                pass

    def _finalize_view(self, ax, vmin, vmax):
        """Ajustes finales comunes a todos los renders."""
        # Z-range que incluye el rango del campo (los vmin/vmax ya
        # incluyen z=0 si _show_z0_plane=True). Pequeno margen visual.
        z_margin = (vmax - vmin) * 0.05
        ax.set_zlim(vmin - z_margin, vmax + z_margin)
        try:
            self._fig.tight_layout(pad=0.5)
        except Exception:
            pass
        self._mpl_canvas.draw_idle()

    def _active_result_type(self) -> str:
        """Lee el radio button activo del post."""
        rv = getattr(self.post_tab, "result_var", None)
        if rv is None:
            return "VM"
        return rv.get() or "VM"
