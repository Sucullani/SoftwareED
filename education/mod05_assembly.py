"""
Módulo 5 — Ensamblaje global K, F + condiciones de contorno

Interfaz: malla a la izquierda, K global y F global a la derecha.
Animación "flying element": al presionar "▶ Ensamblar siguiente", la matriz
kₑ del elemento activo se ilumina sobre la malla y luego viaja hasta las
filas/columnas que le corresponden en K; las celdas objetivo se iluminan
al caer.
"""

from __future__ import annotations

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.base_module import BaseEducationalModule
from education.components import PlotPanel, TheoryDoc
from education.components.plot_panel import _theme_colors

from fem.shape_functions import get_shape_functions
from fem.stiffness import element_stiffness


class AssemblyModule(BaseEducationalModule):
    TITLE = "⑤ Ensamblaje global K, F + BCs"
    HAS_ANIMATION = False
    ANIM_FRAMES = 20
    ANIM_INTERVAL_MS = 28

    def __init__(self, parent, project, element_id):
        if project is None:
            raise ValueError("El módulo de ensamblaje requiere un proyecto cargado.")
        self._order = sorted(project.elements.keys())
        self._ptr = 0     # índice en _order del próximo elemento a ensamblar
        self._active_eid = self._order[0]
        self._show_dofs = False
        self._show_reduced = False
        self._K = np.zeros((project.total_dof, project.total_dof))
        self._F = np.zeros(project.total_dof)
        self._assembled: set[int] = set()
        self._anim_running = False
        super().__init__(parent, project, element_id, width=1400, height=880)

    # ---------- controles ----------
    def build_controls(self, parent):
        ttk.Label(parent, text="Ensamblaje",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "Cada kₑ 8×8 (o 18×18 en Q9) se suma a K global en "
                       "las filas y columnas correspondientes a los GDL "
                       "de sus nodos."
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        ttk.Label(parent, text="Elemento activo",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_elem = tk.StringVar(value=str(self._active_eid))
        self.sp_elem = ttk.Spinbox(
            parent, from_=min(self._order), to=max(self._order),
            textvariable=self.var_elem, width=8,
            command=self._on_elem_changed,
        )
        self.sp_elem.pack(anchor="w", pady=(0, 6))

        self.btn_next = ttk.Button(parent, text="▶ Ensamblar siguiente",
                                     bootstyle="success",
                                     command=self._assemble_next)
        self.btn_next.pack(fill="x", pady=(2, 2))
        ttk.Button(parent, text="⏭ Ensamblar todos",
                    bootstyle="info-outline",
                    command=self._assemble_all).pack(fill="x", pady=2)
        ttk.Button(parent, text="↺ Reset",
                    bootstyle="warning-outline",
                    command=self._reset).pack(fill="x", pady=2)

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent, text="Condiciones de contorno",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_reduced = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Mostrar sistema reducido",
                         variable=self.var_reduced,
                         bootstyle="info-round-toggle",
                         command=self._on_reduced_toggled).pack(anchor="w")

        self.var_show_dofs = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Mostrar GDL en K",
                         variable=self.var_show_dofs,
                         bootstyle="info-round-toggle",
                         command=self._on_dofs_toggled).pack(anchor="w")

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent, text="Progreso",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.lbl_progress = ttk.Label(parent, text="", font=("Consolas", 9),
                                        justify="left")
        self.lbl_progress.pack(anchor="w")

    # ---------- visualización ----------
    def build_visualization(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=4)

        # Izquierda: malla
        self.mesh_panel = PlotPanel(
            parent, figsize=(6.0, 7.0), subplots=(1, 1), show_toolbar=False,
        )
        self.mesh_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Derecha: K arriba, F abajo
        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right.rowconfigure(0, weight=4)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self.k_panel = PlotPanel(
            right, figsize=(6.5, 5.2), subplots=(1, 1), show_toolbar=False,
        )
        self.k_panel.grid(row=0, column=0, sticky="nsew")

        self.f_panel = PlotPanel(
            right, figsize=(6.5, 1.6), subplots=(1, 1), show_toolbar=False,
        )
        self.f_panel.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        # vector F inicial = cargas nodales del proyecto
        self._seed_F_from_project()
        self._redraw_all()

    # ---------- callbacks ----------
    def _on_elem_changed(self) -> None:
        try:
            eid = int(self.var_elem.get())
        except ValueError:
            return
        if eid in self.project.elements:
            self._active_eid = eid
            self._redraw_all()

    def _on_reduced_toggled(self) -> None:
        self._show_reduced = bool(self.var_reduced.get())
        self._redraw_K()

    def _on_dofs_toggled(self) -> None:
        self._show_dofs = bool(self.var_show_dofs.get())
        self._redraw_K()

    def _reset(self) -> None:
        self._K.fill(0.0)
        self._F.fill(0.0)
        self._assembled.clear()
        self._ptr = 0
        self._seed_F_from_project()
        self._redraw_all()

    def _seed_F_from_project(self) -> None:
        self._F.fill(0.0)
        for load in self.project.nodal_loads.values():
            dof_x = 2 * (load.node_id - 1)
            dof_y = 2 * (load.node_id - 1) + 1
            self._F[dof_x] += load.fx
            self._F[dof_y] += load.fy

    # ---------- animación ----------
    def _assemble_next(self) -> None:
        if self._anim_running:
            return
        if self._ptr >= len(self._order):
            return
        eid = self._order[self._ptr]
        self._active_eid = eid
        self.var_elem.set(str(eid))
        ke, dofs, coords = self._element_ke(eid)
        self._animate_fly(ke, dofs, coords, eid)

    def _assemble_all(self) -> None:
        while self._ptr < len(self._order):
            eid = self._order[self._ptr]
            ke, dofs, _ = self._element_ke(eid)
            for i_loc, i_glo in enumerate(dofs):
                for j_loc, j_glo in enumerate(dofs):
                    self._K[i_glo, j_glo] += ke[i_loc, j_loc]
            self._assembled.add(eid)
            self._ptr += 1
        self._redraw_all()

    def _element_ke(self, eid: int):
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
        dofs = elem.get_dof_indices()
        return ke, dofs, coords

    def _animate_fly(self, ke: np.ndarray, dofs: list[int],
                     coords: np.ndarray, eid: int) -> None:
        self._anim_running = True
        # Calcular posición "origen" (centroide del elemento en la malla)
        # y "destino" (bloque correspondiente en K) en coordenadas de figure.
        # Enfoque simplificado: hacemos fade-in sobre la malla y luego
        # fade-in de las celdas destino.
        frames = self.ANIM_FRAMES

        def tick(k: int) -> None:
            if k > frames:
                # Consolidar
                for i_loc, i_glo in enumerate(dofs):
                    for j_loc, j_glo in enumerate(dofs):
                        self._K[i_glo, j_glo] += ke[i_loc, j_loc]
                self._assembled.add(eid)
                self._ptr += 1
                self._anim_running = False
                self._redraw_all()
                return

            t = k / frames
            self._redraw_mesh(highlight_eid=eid, pulse=np.sin(t * np.pi))
            self._redraw_K_with_overlay(dofs, alpha=t)
            self.after(self.ANIM_INTERVAL_MS, lambda: tick(k + 1))

        tick(1)

    # ---------- dibujo ----------
    def _redraw_all(self) -> None:
        self._redraw_mesh()
        self._redraw_K()
        self._redraw_F()
        self._update_progress()

    def _update_progress(self) -> None:
        if not hasattr(self, "lbl_progress"):
            return
        n = len(self._order)
        self.lbl_progress.configure(text=(
            f"Ensamblados : {len(self._assembled)} / {n}\n"
            f"Próximo     : {self._order[self._ptr] if self._ptr < n else '—'}\n"
            f"Activo      : {self._active_eid}"
        ))

    def _redraw_mesh(self, highlight_eid: int | None = None,
                      pulse: float = 0.0) -> None:
        colors = _theme_colors()
        ax = self.mesh_panel.ax
        ax.clear()
        ax.set_facecolor(colors["bg"])
        ax.set_title("Malla", color=colors["fg"], fontsize=11)

        for eid, elem in self.project.elements.items():
            coords = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in elem.node_ids
            ], dtype=float)
            poly = list(range(4)) + [0]

            if eid in self._assembled:
                face = "#4fa3ff"; alpha = 0.25
            elif eid == self._active_eid:
                face = "#ffd54f"; alpha = 0.35 + 0.25 * pulse
            else:
                face = "#555"; alpha = 0.08
            ax.fill(coords[poly, 0], coords[poly, 1],
                    color=face, alpha=alpha, edgecolor="#45475a", lw=1.0)
            cx = float(coords[:4, 0].mean())
            cy = float(coords[:4, 1].mean())
            ax.text(cx, cy, str(eid), color=colors["fg"],
                    fontsize=8, ha="center", va="center")

        # nodos
        xs = [n.x for n in self.project.nodes.values()]
        ys = [n.y for n in self.project.nodes.values()]
        ax.scatter(xs, ys, s=28, c="#ff9f43", edgecolors=colors["fg"],
                    zorder=5)

        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        self.mesh_panel.redraw()

    def _redraw_K(self) -> None:
        colors = _theme_colors()
        ax = self.k_panel.ax
        ax.clear()
        ax.set_facecolor(colors["bg"])

        M = self._K
        if self._show_reduced:
            free = self.project.get_free_dofs()
            if free:
                M = M[np.ix_(free, free)]
                title = f"K reducida  ({len(free)} × {len(free)})"
            else:
                title = "K global (sin BCs)"
        else:
            title = f"K global  ({M.shape[0]} × {M.shape[1]})"

        vmax = float(np.max(np.abs(M))) or 1.0
        ax.imshow(M, cmap="coolwarm", vmin=-vmax, vmax=vmax)
        ax.set_title(title, color=colors["fg"], fontsize=11)

        # overlays de BCs (rojo) y cargas (naranja)
        if not self._show_reduced:
            rdofs = self.project.get_restrained_dofs()
            for d in rdofs:
                ax.axhspan(d - 0.5, d + 0.5, color="#e74c3c", alpha=0.12)
                ax.axvspan(d - 0.5, d + 0.5, color="#e74c3c", alpha=0.12)
            loaded = np.where(np.abs(self._F) > 1e-12)[0]
            for d in loaded:
                ax.axhspan(d - 0.5, d + 0.5, color="#ff9f43", alpha=0.10)

        if self._show_dofs and M.shape[0] <= 40:
            ticks = np.arange(M.shape[0])
            ax.set_xticks(ticks); ax.set_yticks(ticks)
            ax.tick_params(colors=colors["fg"], labelsize=7)
        else:
            ax.set_xticks([]); ax.set_yticks([])
        self.k_panel.redraw()

    def _redraw_K_with_overlay(self, dofs: list[int], alpha: float) -> None:
        # Dibuja K actual + destaca las celdas destino del elemento volador
        self._redraw_K()
        ax = self.k_panel.ax
        for i in dofs:
            for j in dofs:
                ax.add_patch(
                    __import__("matplotlib").patches.Rectangle(
                        (j - 0.5, i - 0.5), 1, 1,
                        color="#ffd54f", alpha=0.35 * alpha, lw=0,
                    )
                )
        self.k_panel.redraw()

    def _redraw_F(self) -> None:
        colors = _theme_colors()
        ax = self.f_panel.ax
        ax.clear()
        ax.set_facecolor(colors["bg"])
        ax.set_title("F global", color=colors["fg"], fontsize=10)
        n = self._F.shape[0]
        ax.bar(np.arange(n), self._F, color="#4fa3ff",
                edgecolor=colors["fg"])
        ax.axhline(0, color=colors["fg"], lw=0.4)
        ax.tick_params(colors=colors["fg"])
        ax.set_xticks([]); ax.set_yticks([])
        self.f_panel.redraw()

    # ---------- teoría ----------
    def build_theory(self, doc: TheoryDoc, ctx: dict) -> None:
        doc.section("Ensamblaje")
        doc.para(
            r"Cada matriz de rigidez local $\mathbf{k}_e$ se expresa en los "
            r"grados de libertad locales del elemento. El ensamblaje la "
            r"reubica sumando cada entrada $(i,j)$ en la posición "
            r"$(I,J)$ de la matriz global, donde $I$ y $J$ son los GDL "
            r"globales asociados a los nodos del elemento."
        )
        doc.equation(r"K_{IJ} \;\mathrel{+}=\; k^{(e)}_{ij}")
        doc.subsection("Condiciones de contorno")
        doc.para(
            r"Las filas/columnas de GDL restringidos (en rojo) se eliminan "
            r"para obtener el sistema reducido $\mathbf{K}_r\mathbf{u}_r="
            r"\mathbf{F}_r$, que sí es invertible."
        )
