"""
M9 - Comparacion Q4 vs Q9 (sandbox, POST-PROCESO)

Modulo educativo sandbox que permite al alumno comparar la precision y
convergencia de elementos Q4 bilineales vs Q9 bicuadraticos sobre el MISMO
modelo. El modulo opera sobre copias profundas del proyecto; nunca muta el
`self.project` original.

Flujo:
    1. Al abrir: clonar el proyecto 2 veces (sandbox_q4 y sandbox_q9).
    2. Slider "nivel de refinamiento" N en {0, 1, 2}.
    3. Al cambiar N: subdividir ambos sandbox, expandir uno a Q9, resolver
       ambos y redibujar los 2 paneles de von Mises lado a lado.
    4. Tabla numerica debajo con: numero de DOF, u_max, sigma_VM_max/min,
       tiempo de solve y error relativo Q4 vs Q9.

El modulo NO requiere que el proyecto este resuelto; el modulo resuelve sus
propias copias en cada cambio.
"""

from __future__ import annotations

import copy
import time
import tkinter as tk
import ttkbootstrap as ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.base_module import PostModule
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from fem.shape_functions import get_shape_functions
from models.mesh_utils import subdivide_q4_mesh, expand_q4_to_q9, shrink_q9_to_q4
from config.settings import ELEMENT_Q4, ELEMENT_Q9, fmt


_COMPONENTS = [
    ("Von Mises", "von_mises"),
    (" σx",        "sigma_x"),
    (" σy",        "sigma_y"),
    (" τxy",       "tau_xy"),
]


class Q4vsQ9ComparisonModule(PostModule):
    """Modulo M9: comparacion Q4 vs Q9 con subdivision de malla (sandbox).

    Sandbox: trabaja sobre copias profundas, NO usa el helper auto-solve
    de PostModule (cada copia se resuelve en _compute_side).
    """

    TITLE = "M9 · Comparacion Q4 vs Q9 (sandbox)"
    HAS_ANIMATION = False
    AUTO_SOLVE = False  # M9 gestiona sus propios solves por copia.

    def __init__(self, parent, project, element_id):
        self._base_project = copy.deepcopy(project) if project else None
        if self._base_project is not None:
            if any(e.num_nodes == 9 for e in self._base_project.elements.values()):
                shrink_q9_to_q4(self._base_project)
            self._base_project.file_path = None
            self._base_project.is_modified = False
        self._level_var = None
        self._comp_var = None
        self._deform_var = None

        self._result_q4 = None
        self._result_q9 = None

        self._fig = None
        self._canvas = None
        self._ax_q4 = None
        self._ax_q9 = None
        self._cbar = None

        self._stats_labels = {}

        super().__init__(parent, project, element_id, width=1320, height=860)

    # ------------------------------------------------------------------
    # CONTROLES (panel izquierdo)
    # ------------------------------------------------------------------
    def build_controls(self, parent):
        if self._base_project is None or not self._base_project.elements:
            ttk.Label(parent, text="El proyecto no tiene elementos. Carga un\n"
                                    "ejemplo o define una malla antes de abrir M9.",
                      bootstyle="warning", wraplength=240
                      ).pack(anchor="w", padx=4, pady=8)
            return

        ttk.Label(parent, text="Nivel de refinamiento",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self._level_var = tk.IntVar(value=0)
        for lvl, desc in ((0, "N=0 (malla original)"),
                          (1, "N=1 (4× elementos)"),
                          (2, "N=2 (16× elementos)")):
            ttk.Radiobutton(
                parent, text=desc, value=lvl, variable=self._level_var,
                bootstyle="info", command=self._on_param_change,
            ).pack(anchor="w", padx=4, pady=1)

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent, text="Componente",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self._comp_var = tk.StringVar(value="von_mises")
        for label, val in _COMPONENTS:
            ttk.Radiobutton(
                parent, text=label, value=val, variable=self._comp_var,
                bootstyle="success", command=self._refresh_views,
            ).pack(anchor="w", padx=4, pady=1)

        ttk.Separator(parent).pack(fill="x", pady=8)

        self._deform_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            parent, text="Mostrar malla deformada",
            variable=self._deform_var, bootstyle="round-toggle",
            command=self._refresh_views,
        ).pack(anchor="w", padx=4, pady=2)

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent,
                  text=("M9 trabaja sobre copias profundas del modelo: "
                        "subdivide la malla y expande una copia a Q9 para "
                        "comparar lado a lado. El proyecto original NO se "
                        "modifica."),
                  font=("Segoe UI", 8), foreground="#aaa", wraplength=240,
                  justify="left",
                  ).pack(anchor="w", pady=(0, 8))

        ttk.Button(parent, text="↻  Recalcular", bootstyle="info-outline",
                   command=self._recompute_and_refresh,
                   ).pack(anchor="w", padx=4, pady=(4, 12), fill="x")

    def _on_param_change(self):
        self._recompute_and_refresh()

    # ------------------------------------------------------------------
    # VISUALIZACION (paneles Q4 | Q9 + tabla de stats)
    # ------------------------------------------------------------------
    def build_visualization(self, parent):
        if self._base_project is None or not self._base_project.elements:
            ttk.Label(parent, text="(modulo deshabilitado)",
                      bootstyle="warning").pack(expand=True)
            return

        top = ttk.Frame(parent)
        top.pack(fill="both", expand=True)
        bottom = ttk.Labelframe(parent, text=" Metricas comparativas ",
                                 padding=10)
        bottom.pack(fill="x", padx=4, pady=(6, 4))

        self._fig = Figure(figsize=(9.0, 5.2), dpi=100, facecolor="#222233")
        self._ax_q4 = self._fig.add_subplot(1, 2, 1)
        self._ax_q9 = self._fig.add_subplot(1, 2, 2)
        for ax in (self._ax_q4, self._ax_q9):
            ax.set_facecolor("#222233")
            ax.tick_params(colors="#dfdfdf")
            ax.set_aspect("equal")
        self._canvas = FigureCanvasTkAgg(self._fig, master=top)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._build_stats_panel(bottom)

        self._recompute_and_refresh()

    def _build_stats_panel(self, parent):
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=1)
        parent.columnconfigure(3, weight=1)

        headers = ("", "Q4", "Q9", "Diferencia")
        for i, h in enumerate(headers):
            ttk.Label(parent, text=h, font=("Segoe UI Semibold", 10),
                      foreground="#4fa3ff" if i > 0 else "#dfdfdf",
                      ).grid(row=0, column=i, sticky="w", padx=6, pady=2)

        rows = [
            ("num_elems",   "Elementos"),
            ("num_dof",     "GDL (grados de libertad)"),
            ("u_max",       "|u|_max"),
            ("vm_max",      "σ_VM max"),
            ("vm_min",      "σ_VM min"),
            ("time_ms",     "Tiempo solve (ms)"),
        ]
        for r, (key, lbl) in enumerate(rows, start=1):
            ttk.Label(parent, text=lbl).grid(row=r, column=0, sticky="w",
                                              padx=6, pady=1)
            for c, side in enumerate(("q4", "q9", "diff"), start=1):
                lab = ttk.Label(parent, text="—",
                                 foreground="#e0e0e0",
                                 font=("Consolas", 10))
                lab.grid(row=r, column=c, sticky="w", padx=6, pady=1)
                self._stats_labels[(key, side)] = lab

    # ------------------------------------------------------------------
    # LOGICA DE COMPUTO (sandbox)
    # ------------------------------------------------------------------
    def _recompute_and_refresh(self):
        if self._base_project is None or not self._base_project.elements:
            return
        level = int(self._level_var.get()) if self._level_var else 0

        try:
            self._result_q4 = self._compute_side(level, as_q9=False)
            self._result_q9 = self._compute_side(level, as_q9=True)
        except Exception as exc:
            for ax in (self._ax_q4, self._ax_q9):
                ax.clear()
                ax.text(0.5, 0.5, f"Error:\n{exc}", transform=ax.transAxes,
                        ha="center", va="center", color="#ef5350")
            if self._canvas is not None:
                self._canvas.draw_idle()
            return

        self._refresh_views()
        self._refresh_stats()

    def _compute_side(self, level, as_q9):
        """Clona el base, subdivide, (opcional) expande a Q9, resuelve."""
        proj = copy.deepcopy(self._base_project)
        proj.file_path = None
        if level > 0:
            subdivide_q4_mesh(proj, levels=level)
        if as_q9:
            expand_q4_to_q9(proj)
        t0 = time.perf_counter()
        sol = solve_system(proj)
        t1 = time.perf_counter()
        elem_stresses, nodal_avg = compute_all_stresses(proj, sol)
        return {
            "project": proj,
            "solution": sol,
            "elem_stresses": elem_stresses,
            "nodal_avg": nodal_avg,
            "solve_ms": (t1 - t0) * 1000.0,
        }

    # ------------------------------------------------------------------
    # RENDER (2 paneles lado a lado)
    # ------------------------------------------------------------------
    def _refresh_views(self):
        if self._result_q4 is None or self._result_q9 is None:
            return
        comp_key = self._comp_var.get() if self._comp_var else "von_mises"
        comp_label = next((lab.strip() for lab, v in _COMPONENTS
                           if v == comp_key), comp_key)
        show_deform = bool(self._deform_var.get()) if self._deform_var else False

        vmin, vmax = self._common_range(comp_key)
        cmap = matplotlib.pyplot.get_cmap("plasma")

        self._render_side(self._ax_q4, self._result_q4, comp_key, comp_label,
                          vmin, vmax, cmap, title_prefix="Q4",
                          show_deform=show_deform)
        self._render_side(self._ax_q9, self._result_q9, comp_key, comp_label,
                          vmin, vmax, cmap, title_prefix="Q9",
                          show_deform=show_deform)

        if self._cbar is not None:
            try:
                self._cbar.remove()
            except Exception:
                pass
            self._cbar = None
        sm = matplotlib.cm.ScalarMappable(
            norm=matplotlib.colors.Normalize(vmin=vmin, vmax=vmax), cmap=cmap
        )
        sm.set_array([])
        self._cbar = self._fig.colorbar(sm, ax=[self._ax_q4, self._ax_q9],
                                         fraction=0.03, pad=0.03)
        self._cbar.ax.tick_params(colors="#dfdfdf")
        self._cbar.set_label(comp_label, color="#dfdfdf")

        self._canvas.draw_idle()

    def _common_range(self, comp_key):
        """Rango [vmin, vmax] combinando Q4 y Q9 para colorbar homogeneo."""
        vals = []
        for result in (self._result_q4, self._result_q9):
            for nid, nd in result["nodal_avg"].items():
                vals.append(nd.get(comp_key, 0.0))
        if not vals:
            return 0.0, 1.0
        vmin, vmax = float(min(vals)), float(max(vals))
        if vmax - vmin < 1e-12:
            vmax = vmin + 1.0
        return vmin, vmax

    def _render_side(self, ax, result, comp_key, comp_label,
                     vmin, vmax, cmap, title_prefix, show_deform):
        ax.clear()
        ax.set_facecolor("#222233")
        ax.tick_params(colors="#dfdfdf")
        ax.set_aspect("equal")

        proj = result["project"]
        u = result["solution"]["u"]
        N_fn, _ = get_shape_functions(proj.element_type)
        n_nodes_elem = 4 if proj.element_type == ELEMENT_Q4 else 9

        u_abs_max = float(np.max(np.abs(u))) if len(u) else 1.0
        bbox = self._project_bbox(proj)
        span = max(bbox[1] - bbox[0], bbox[3] - bbox[2], 1e-9)
        deform_scale = (0.08 * span / u_abs_max) if (show_deform and u_abs_max > 0) else 0.0

        n_sub = 6
        xi = np.linspace(-1, 1, n_sub)
        eta = np.linspace(-1, 1, n_sub)
        XI, ETA = np.meshgrid(xi, eta)

        for eid, elem in proj.elements.items():
            try:
                pts = np.array([
                    [proj.nodes[n].x + deform_scale * u[2 * (n - 1)],
                     proj.nodes[n].y + deform_scale * u[2 * (n - 1) + 1]]
                    for n in elem.node_ids[:n_nodes_elem]
                ])
            except KeyError:
                continue

            v_nodes = np.array([
                (result["nodal_avg"].get(n, {}) or {}).get(comp_key, 0.0)
                for n in elem.node_ids[:n_nodes_elem]
            ])

            X = np.zeros_like(XI)
            Y = np.zeros_like(XI)
            Z = np.zeros_like(XI)
            for r in range(n_sub):
                for c in range(n_sub):
                    Ns = N_fn(XI[r, c], ETA[r, c])
                    X[r, c] = Ns @ pts[:, 0]
                    Y[r, c] = Ns @ pts[:, 1]
                    Z[r, c] = Ns @ v_nodes
            ax.pcolormesh(X, Y, Z, cmap=cmap, vmin=vmin, vmax=vmax,
                          shading="gouraud", antialiased=True)

            # Contorno del elemento (vertices macro) para dibujar aristas
            corners = pts[:4] if n_nodes_elem == 9 else pts
            xs = list(corners[:, 0]) + [corners[0, 0]]
            ys = list(corners[:, 1]) + [corners[0, 1]]
            ax.plot(xs, ys, color="#ffffff", linewidth=0.35, alpha=0.55)

        n_elems = proj.num_elements
        n_dof = proj.total_dof
        ax.set_title(f"{title_prefix} — elems={n_elems}, DOF={n_dof}",
                     color="#dfdfdf", fontsize=10, pad=6)

    @staticmethod
    def _project_bbox(proj):
        xs = [n.x for n in proj.nodes.values()]
        ys = [n.y for n in proj.nodes.values()]
        return min(xs), max(xs), min(ys), max(ys)

    # ------------------------------------------------------------------
    # TABLA DE STATS
    # ------------------------------------------------------------------
    def _refresh_stats(self):
        if self._result_q4 is None or self._result_q9 is None:
            return
        s4 = self._stats_of(self._result_q4)
        s9 = self._stats_of(self._result_q9)
        pairs = [
            ("num_elems", f"{s4['num_elems']}",       f"{s9['num_elems']}"),
            ("num_dof",   f"{s4['num_dof']}",         f"{s9['num_dof']}"),
            ("u_max",     f"{s4['u_max']:.5e}",       f"{s9['u_max']:.5e}"),
            ("vm_max",    fmt(s4['vm_max'], 'stress'), fmt(s9['vm_max'], 'stress')),
            ("vm_min",    fmt(s4['vm_min'], 'stress'), fmt(s9['vm_min'], 'stress')),
            ("time_ms",   f"{s4['time_ms']:.1f}",     f"{s9['time_ms']:.1f}"),
        ]
        for key, v4, v9 in pairs:
            self._stats_labels[(key, "q4")].configure(text=v4)
            self._stats_labels[(key, "q9")].configure(text=v9)

        # Diferencia relativa (referencia Q9 para u_max, vm_max, vm_min)
        def _rel(a, b):
            if abs(b) < 1e-15:
                return "—"
            return f"{100.0 * (a - b) / abs(b):+.2f} %"

        self._stats_labels[("num_elems", "diff")].configure(
            text=f"x{s9['num_elems'] / max(s4['num_elems'], 1):.0f}")
        self._stats_labels[("num_dof", "diff")].configure(
            text=f"x{s9['num_dof'] / max(s4['num_dof'], 1):.2f}")
        self._stats_labels[("u_max", "diff")].configure(
            text=_rel(s4["u_max"], s9["u_max"]))
        self._stats_labels[("vm_max", "diff")].configure(
            text=_rel(s4["vm_max"], s9["vm_max"]))
        self._stats_labels[("vm_min", "diff")].configure(
            text=_rel(s4["vm_min"], s9["vm_min"]))
        ratio_t = s9["time_ms"] / max(s4["time_ms"], 1e-6)
        self._stats_labels[("time_ms", "diff")].configure(
            text=f"x{ratio_t:.1f}")

    @staticmethod
    def _stats_of(result):
        proj = result["project"]
        u = result["solution"]["u"]
        vm_vals = [
            (nd.get("von_mises", 0.0))
            for nd in result["nodal_avg"].values()
        ]
        if not vm_vals:
            vm_vals = [0.0]
        return {
            "num_elems": proj.num_elements,
            "num_dof":   proj.total_dof,
            "u_max":     float(np.max(np.abs(u))) if len(u) else 0.0,
            "vm_max":    float(max(vm_vals)),
            "vm_min":    float(min(vm_vals)),
            "time_ms":   result["solve_ms"],
        }

    # ------------------------------------------------------------------
    # TEORIA
    # ------------------------------------------------------------------
    def build_theory(self, doc, ctx):
        doc.section("Por que Q9 converge mas rapido que Q4")
        doc.para(
            "Q4 es un elemento bilineal: sus funciones de forma son lineales "
            "en xi y eta por separado. La deformacion resultante epsilon = B u "
            "es CONSTANTE dentro de cada elemento para los terminos lineales "
            "y no puede representar gradientes lineales de deformacion. Q9 "
            "es biquadratico: representa gradientes lineales de deformacion "
            "de forma exacta, lo que lo vuelve muchisimo mas preciso en "
            "problemas con flexion o tensiones concentradas."
        )
        doc.section("Refinamiento h vs refinamiento p")
        doc.para(
            "Aumentar el nivel N del slider (h-refinement) subdivide cada "
            "elemento en 4 sub-elementos, multiplicando el numero de DOF. "
            "Pasar de Q4 a Q9 manteniendo la misma malla (p-refinement) "
            "aumenta el orden del polinomio dentro de cada elemento. Ambas "
            "tecnicas convergen a la solucion exacta, pero Q9 lo hace con "
            "menos DOF totales en la mayoria de los problemas."
        )
        doc.section("Interpretacion de la tabla")
        doc.para(
            "La columna 'Diferencia' muestra (Q4 - Q9) / |Q9| en porcentaje "
            "para u_max y sigma_VM (Q9 se toma como referencia mas precisa). "
            "A medida que N crece, las dos columnas se acercan — ese es el "
            "fenomeno de convergencia."
        )
