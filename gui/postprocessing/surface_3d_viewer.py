"""
Surface3DViewer: Toplevel con vista 3D del campo de esfuerzos/desplazamientos.

Reemplaza al modulo educativo M7 (legacy): vista del Post-Proceso
accesible via boton "🧊 Vista 3D" en la toolbar. Sincronizado con el
result_type del post: cambiar de VM a σx repinta automaticamente.

Diseno visual (rediseno 2026-05):
  - **Estilo coherente con el canvas del Post**: colormap JET identico
    al de MeshCanvas (no viridis/coolwarm de matplotlib). Esto unifica
    cromaticamente la vista 2D del contorno y la vista 3D de la superficie
    -- el alumno reconoce los mismos colores.
  - **Ejes sin ruido visual**: sin ticks, sin numeros, sin paneles de
    fondo. Solo la superficie 3D + un plano de referencia gris suave en
    z=0 que sirve de "horizonte" -- los valores positivos sobresalen, los
    negativos hunden bajo el plano.
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

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import ListedColormap

from config.settings import (
    SURFACE_3D_DEFAULT_GRID, SURFACE_3D_DISC_THRESHOLD,
    MOHR_BG, MOHR_FG,
)
from fem.probe_query import compute_raw_grid
from fem.shape_functions import get_shape_functions


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


# ── Colormap JET coherente con MeshCanvas ─────────────────────────────────
# Construimos un ListedColormap de 256 colores muestreando la misma JET
# que usa el canvas del Post (_jet_rgb_vectorized). Esto unifica la
# paleta cromatica entre vista 2D (contorno) y vista 3D (superficie).
def _build_jet_cmap() -> ListedColormap:
    t = np.linspace(0.0, 1.0, 256)
    r = np.zeros_like(t)
    g = np.zeros_like(t)
    b = np.zeros_like(t)
    m1 = t < 0.25
    m2 = (t >= 0.25) & (t < 0.5)
    m3 = (t >= 0.5) & (t < 0.75)
    m4 = t >= 0.75
    g[m1] = t[m1] / 0.25; b[m1] = 1.0
    g[m2] = 1.0; b[m2] = 1.0 - (t[m2] - 0.25) / 0.25
    r[m3] = (t[m3] - 0.5) / 0.25; g[m3] = 1.0
    r[m4] = 1.0; g[m4] = 1.0 - (t[m4] - 0.75) / 0.25
    return ListedColormap(np.column_stack([r, g, b, np.ones_like(t)]))


_JET_CMAP = _build_jet_cmap()


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
        self.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
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

        # Body: matplotlib Figure 3D
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
        ax = self._ax
        ax.clear()
        self._setup_clean_axes(ax)

        is_raw = (self._mode_var is not None and self._mode_var.get() == "raw")
        n = SURFACE_3D_DEFAULT_GRID
        N_func, _ = get_shape_functions(self.project.element_type)

        elem_data = []
        all_z = []
        per_node_raw = {}   # para detector de discontinuidades

        for eid, elem in self.project.elements.items():
            n_nodes_elem = elem.num_nodes
            v_nodes_smooth = np.array([
                (self.nodal_stresses.get(nid, {}) or {}).get(key, 0.0)
                for nid in elem.node_ids[:n_nodes_elem]
            ])

            # Pre-computar geometria X, Y sobre la grilla (n+1, n+1)
            xi = np.linspace(-1, 1, n + 1)
            eta = np.linspace(-1, 1, n + 1)
            XI, ETA = np.meshgrid(xi, eta)
            X = np.zeros_like(XI)
            Y = np.zeros_like(XI)
            Z_smooth = np.zeros_like(XI)
            pts = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in elem.node_ids[:n_nodes_elem]
            ])
            for r in range(n + 1):
                for c in range(n + 1):
                    Ns = N_func(XI[r, c], ETA[r, c])
                    X[r, c] = Ns @ pts[:, 0]
                    Y[r, c] = Ns @ pts[:, 1]
                    Z_smooth[r, c] = Ns @ v_nodes_smooth

            # Modo crudo: usar la grilla pre-computada con compute_raw_grid
            if is_raw:
                try:
                    grids = compute_raw_grid(
                        self.project, self.solution, eid, n=n,
                    )
                except Exception:
                    grids = None
                if grids is None:
                    continue
                Z = np.asarray(grids[key])
            else:
                Z = Z_smooth

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
        edge_color = "#ffe082" if is_raw else "#dddddd"

        for X, Y, Z, _elem, _v in elem_data:
            facecolors = _JET_CMAP((Z - vmin) / v_range)
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
            mode_color = "#ffb74d"
        else:
            mode_lbl = "SUAVIZADO  σ = Σ Nᵢ·σᵢ̄  (continuo)"
            mode_color = "#81c784"

        ax.set_title(
            f"{label}  ·  {mode_lbl}",
            color=mode_color, fontsize=11, pad=8, fontweight="bold",
        )

        if self._info_label is not None:
            try:
                self._info_label.configure(
                    text=f"Mostrando: {label}  ·  rango: [{vmin:.3g}, {vmax:.3g}]"
                )
            except tk.TclError:
                pass

        self._finalize_view(ax, vmin, vmax)

    # ── Render: desplazamientos ────────────────────────────────────────
    def _render_displacement(self, rtype: str):
        """Para desplazamientos no hay distincion crudo/suavizado (son C0
        continuos por construccion del MEF). Z = u_i interpolado por las
        shape functions a partir de los valores nodales.
        """
        label = _DISPLACEMENT_LABEL.get(rtype, rtype)
        ax = self._ax
        ax.clear()
        self._setup_clean_axes(ax)

        u = self.solution["u"]
        idx_map = self.project.node_index_map
        N_func, _ = get_shape_functions(self.project.element_type)
        n = SURFACE_3D_DEFAULT_GRID

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

            pts = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in elem.node_ids[:n_nodes_elem]
            ])
            xi = np.linspace(-1, 1, n + 1)
            eta = np.linspace(-1, 1, n + 1)
            XI, ETA = np.meshgrid(xi, eta)
            X = np.zeros_like(XI)
            Y = np.zeros_like(XI)
            Z = np.zeros_like(XI)
            for r in range(n + 1):
                for c in range(n + 1):
                    Ns = N_func(XI[r, c], ETA[r, c])
                    X[r, c] = Ns @ pts[:, 0]
                    Y[r, c] = Ns @ pts[:, 1]
                    Z[r, c] = Ns @ v_nodes
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

        for X, Y, Z, _elem, _v in elem_data:
            facecolors = _JET_CMAP((Z - vmin) / v_range)
            ax.plot_surface(
                X, Y, Z, facecolors=facecolors,
                edgecolor="#dddddd", linewidth=0.15,
                alpha=0.95, rcount=n, ccount=n, shade=False,
            )

        ax.set_title(
            f"Desplazamiento  {label}  (continuo C⁰ del MEF)",
            color=MOHR_FG, fontsize=11, pad=8, fontweight="bold",
        )

        if self._info_label is not None:
            try:
                self._info_label.configure(
                    text=f"Mostrando: {label}  ·  rango: [{vmin:.3e}, {vmax:.3e}]"
                )
            except tk.TclError:
                pass

        self._finalize_view(ax, vmin, vmax)

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
            color="#5c5c70", alpha=0.18, edgecolor="#888899",
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
                    color="#ef5350", lw=2.5, alpha=0.9, zorder=10,
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
