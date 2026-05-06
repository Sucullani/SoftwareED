"""
M7 — Discontinuidad de esfuerzos y promediado nodal (Post-Proceso)

Modulo educativo que muestra graficamente por que los esfuerzos calculados
en los puntos de Gauss y extrapolados a los nodos del elemento NO son
continuos en los nodos compartidos por varios elementos. Animacion 3D
toggle entre:

- "Crudo": cada elemento dibuja su propia superficie σ(x,y); se ven
  escalones/saltos en los nodos compartidos.
- "Promediado": la superficie es continua porque se promedia σ entre
  elementos vecinos en cada nodo (smoothing C0).

Uso pedagogico:
1) Resolver el modelo (F5).
2) Abrir el modulo desde POST-PROCESO -> Educacion.
3) Cambiar la componente (Sx, Sy, Txy, VM) y observar las
   discontinuidades.
4) Pulsar "Animar transicion" para ver el morphing crudo -> promediado.

Datos: usa lo que ya calcula `fem.stress.compute_all_stresses`:
- element_stresses[eid]["nodal_stresses"] (por elemento, extrapolado de Gauss)
- nodal_avg_stresses[nid] (promediado en nodos compartidos)
"""

from __future__ import annotations

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox

from education.base_module import PostModule
from education.components import PlotPanel
from fem.shape_functions import get_shape_functions


_COMPONENTS = [
    ("Von Mises", "von_mises"),
    ("σx",        "sigma_x"),
    ("σy",        "sigma_y"),
    ("τxy",       "tau_xy"),
]


class StressDiscontinuityModule(PostModule):
    """Modulo educativo M7: discontinuidad de esfuerzos y smoothing nodal."""

    TITLE = "M7 · Discontinuidad de esfuerzos"
    HAS_ANIMATION = True
    ANIMATION_DURATION_MS = 4000

    def __init__(self, parent, project, element_id):
        # PostModule._ensure_solved corre UNA vez en super().__init__ y
        # cachea self.solution / self.element_stresses / self.nodal_avg.
        self._mode_var = None     # "raw" | "avg"
        self._comp_var = None     # clave de _COMPONENTS
        self._morph_t = 1.0        # 0 = crudo, 1 = promediado (interpolable)
        super().__init__(parent, project, element_id, width=1180, height=820)

    # ------------------------------------------------------------------
    # CONTROLES (panel izquierdo)
    # ------------------------------------------------------------------
    def build_controls(self, parent):
        # Si el solver falló, mostrar el error y salir (helper de PostModule).
        if self._maybe_show_solver_error(parent):
            return

        ttk.Label(parent, text="Modo de visualizacion",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        self._mode_var = tk.StringVar(value="avg")
        for label, val in (("Crudo (discontinuo)", "raw"),
                           ("Promediado (continuo)", "avg")):
            ttk.Radiobutton(
                parent, text=label, value=val, variable=self._mode_var,
                bootstyle="success", command=self._on_mode_change,
            ).pack(anchor="w", padx=4, pady=2)

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent, text="Componente",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self._comp_var = tk.StringVar(value="von_mises")
        for label, val in _COMPONENTS:
            ttk.Radiobutton(
                parent, text=label, value=val, variable=self._comp_var,
                bootstyle="info", command=self._refresh_views,
            ).pack(anchor="w", padx=4, pady=1)

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent,
                  text=("La animacion interpola entre 'Crudo' (cada elemento\n"
                        "tiene su propia superficie) y 'Promediado'\n"
                        "(σ promediada en nodos compartidos -> continuidad C0)."),
                  font=("Segoe UI", 8), foreground="#aaa", wraplength=240,
                  justify="left",
                  ).pack(anchor="w", pady=(0, 8))

    def _on_mode_change(self):
        # Salto inmediato sin interpolacion
        self._morph_t = 1.0 if self._mode_var.get() == "avg" else 0.0
        self._refresh_views()

    # ------------------------------------------------------------------
    # VISUALIZACION (3D principal a la derecha)
    # ------------------------------------------------------------------
    def build_visualization(self, parent):
        if not self.has_solution:
            ttk.Label(parent, text="(modulo deshabilitado por error en el solver)",
                      bootstyle="warning"
                      ).pack(expand=True)
            return
        self._plot = PlotPanel(parent, figsize=(8.5, 6.5),
                               subplots=(1, 1), projection="3d")
        self._plot.pack(fill="both", expand=True)
        self._refresh_views()

    def _value_at_node_in_elem(self, eid, idx_in_elem, comp_key, t):
        """Devuelve el valor a renderizar en un nodo segun el modo morph.

        t = 0 -> crudo (valor del elemento); t = 1 -> promediado nodal.
        """
        if self.element_stresses is None:
            return 0.0
        elem = self.project.elements[eid]
        nid = elem.node_ids[idx_in_elem]
        v_raw = self.element_stresses[eid]["nodal_stresses"][idx_in_elem].get(
            comp_key, 0.0
        )
        v_avg = (self.nodal_avg.get(nid, {}) or {}).get(comp_key, v_raw)
        return (1.0 - t) * v_raw + t * v_avg

    def _refresh_views(self):
        if not self.has_solution:
            return
        ax = self._plot.axes[0]
        ax.clear()
        # Re-aplicar estilo 3D
        ax.set_facecolor("#222233")
        ax.tick_params(colors="#dfdfdf")
        try:
            ax.zaxis.label.set_color("#dfdfdf")
            ax.tick_params(axis="z", colors="#dfdfdf")
        except Exception:
            pass

        comp_key = self._comp_var.get() if self._comp_var else "von_mises"
        comp_label = next((lab for lab, v in _COMPONENTS if v == comp_key),
                          comp_key)

        # Funciones de forma dinámicas: Q4 (4) o Q9 (9) según el proyecto.
        N_fn, _ = get_shape_functions(self.project.element_type)
        n_nodes_elem = len(N_fn(0.0, 0.0))

        # Calcular rango global para coherencia de color (usando todos los
        # nodos del elemento).
        all_vals = []
        for eid in self.project.elements:
            for i in range(n_nodes_elem):
                all_vals.append(self._value_at_node_in_elem(
                    eid, i, comp_key, self._morph_t
                ))
        if not all_vals:
            self._plot.redraw()
            return
        vmin, vmax = float(min(all_vals)), float(max(all_vals))
        if vmax - vmin < 1e-12:
            vmax = vmin + 1.0
        import matplotlib.pyplot as _plt
        cmap = _plt.get_cmap("plasma")

        # Subdivision por elemento para suavizar dentro de cada quad
        n_sub = 8

        for eid, elem in self.project.elements.items():
            try:
                pts = np.array([
                    [self.project.nodes[n].x, self.project.nodes[n].y]
                    for n in elem.node_ids[:n_nodes_elem]
                ])
            except KeyError:
                continue
            v_nodes = np.array([
                self._value_at_node_in_elem(eid, i, comp_key, self._morph_t)
                for i in range(n_nodes_elem)
            ])

            xi = np.linspace(-1, 1, n_sub)
            eta = np.linspace(-1, 1, n_sub)
            XI, ETA = np.meshgrid(xi, eta)
            X = np.zeros_like(XI)
            Y = np.zeros_like(XI)
            Z = np.zeros_like(XI)
            # Interpolación usando las funciones de forma del elemento
            # (bilineal para Q4, bicuadrática para Q9).
            for r in range(n_sub):
                for c in range(n_sub):
                    Ns = N_fn(XI[r, c], ETA[r, c])
                    X[r, c] = Ns @ pts[:, 0]
                    Y[r, c] = Ns @ pts[:, 1]
                    Z[r, c] = Ns @ v_nodes
            facecolors = cmap((Z - vmin) / (vmax - vmin))
            ax.plot_surface(
                X, Y, Z, facecolors=facecolors,
                edgecolor="white", linewidth=0.2, alpha=0.92,
                rcount=n_sub, ccount=n_sub, shade=False,
            )

        ax.set_xlabel("X", color="#dfdfdf")
        ax.set_ylabel("Y", color="#dfdfdf")
        ax.set_zlabel(comp_label, color="#dfdfdf")
        if self._morph_t < 0.5:
            mode_lbl = "Crudo (discontinuo)"
        elif self._morph_t > 0.95:
            mode_lbl = "Promediado (continuo)"
        else:
            mode_lbl = f"Transicion t={self._morph_t:.2f}"
        ax.set_title(f"σ_{comp_label} — {mode_lbl}",
                     color="#dfdfdf", fontsize=11, pad=10)
        self._plot.redraw()

    # ------------------------------------------------------------------
    # ANIMACION
    # ------------------------------------------------------------------
    def animate_step(self, t):
        self._morph_t = float(t)
        self._refresh_views()

    # ------------------------------------------------------------------
    # TEORIA
    # ------------------------------------------------------------------
    def build_theory(self, doc, ctx):
        doc.section("Por que los esfuerzos son discontinuos")
        doc.para(
            "El metodo de los elementos finitos asegura continuidad C0 de "
            "los desplazamientos, pero NO de los esfuerzos. σ = D B u^e "
            "se calcula por separado en cada elemento, y B contiene "
            "derivadas de las funciones de forma -> σ es discontinuo en "
            "los nodos compartidos."
        )
        doc.section("Promediado nodal")
        doc.para(
            "Una tecnica de post-proceso muy comun es promediar σ en cada "
            "nodo a partir de los valores que aportan todos los elementos "
            "que lo comparten. Esto produce un campo C0 visualmente mas "
            "agradable, pero hay que recordar que es una operacion de "
            "smoothing, no una solucion mas precisa."
        )
        doc.section("Lectura pedagogica")
        doc.para(
            "Si dos elementos vecinos muestran valores nodales muy distintos "
            "antes del promediado, ese 'salto' es un indicador cualitativo "
            "de error de discretizacion. Es la base de los estimadores de "
            "error tipo Zienkiewicz-Zhu."
        )
