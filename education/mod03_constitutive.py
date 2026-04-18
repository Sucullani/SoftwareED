"""
Módulo 3 — Matriz constitutiva D

Interfaz:
    Izquierda: video Manim (MP4) embebido explicando tensión / deformación
    Derecha:   matriz D 3×3 renderizada en LaTeX real (mathtext)

Controles: E, ν, caso plano.
"""

from __future__ import annotations

import os

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.base_module import BaseEducationalModule
from education.components import (
    PlotPanel, ParamInput, TheoryDoc, VideoPlayer,
    render_matrix_latex, render_expression_latex,
)
from education.components.plot_panel import _theme_colors

from fem.constitutive import constitutive_matrix
from config.settings import ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN


VIDEO_DIR = os.path.join("resources", "videos")
VIDEO_FILE = os.path.join(VIDEO_DIR, "constitutive_intro.mp4")


class ConstitutiveModule(BaseEducationalModule):
    TITLE = "③ Matriz constitutiva D"
    HAS_ANIMATION = False

    def __init__(self, parent, project, element_id):
        self._E = 210e9
        self._nu = 0.3
        self._case = ANALYSIS_PLANE_STRESS
        # tomar defaults del proyecto si existen
        if project is not None:
            try:
                mat = getattr(project, "material", None)
                if mat is not None:
                    self._E = float(getattr(mat, "E", self._E))
                    self._nu = float(getattr(mat, "nu", self._nu))
                at = getattr(project, "analysis_type", None)
                if at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
                    self._case = at
            except Exception:
                pass
        super().__init__(parent, project, element_id, width=1320, height=820)

    # ---------- controles ----------
    def build_controls(self, parent):
        ttk.Label(parent, text="Matriz constitutiva D",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "D relaciona tensión y deformación: σ = D · ε.\n"
                       "En 2D tiene dos formas según el problema:\n"
                       "• Tensión plana (placas delgadas).\n"
                       "• Deformación plana (secciones muy largas)."
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Parámetros
        self.inp_E = ParamInput(
            parent, label="E", value=self._E, unit="Pa",
            fmt="{:.3e}", vmin=1.0,
            on_change=self._on_E_changed,
        )
        self.inp_E.pack(fill="x", pady=(2, 4))

        self.inp_nu = ParamInput(
            parent, label="ν", value=self._nu, unit="",
            fmt="{:.3f}", vmin=-0.99, vmax=0.499,
            on_change=self._on_nu_changed,
        )
        self.inp_nu.pack(fill="x", pady=(2, 8))

        ttk.Label(parent, text="Caso plano",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(4, 4))
        self.var_case = tk.StringVar(value=self._case)
        ttk.Combobox(parent, textvariable=self.var_case, state="readonly",
                      values=[ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN],
                      bootstyle="info").pack(fill="x", pady=(0, 8))
        self.var_case.trace_add("write", lambda *a: self._on_case_changed())

        ttk.Separator(parent).pack(fill="x", pady=6)

        ttk.Label(parent, text="Ejemplos típicos",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(4, 4))
        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "Tensión plana: placa delgada cargada en su plano "
                       "(σz = 0).\n"
                       "Deformación plana: viga profunda o muro de contención "
                       "muy largos (εz = 0)."
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Atajos al video
        ttk.Label(parent, text="Saltos en el video",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(4, 4))
        row = ttk.Frame(parent); row.pack(fill="x", pady=(0, 4))
        ttk.Button(row, text="⏮ 0s", bootstyle="secondary-outline", width=6,
                    command=lambda: self._seek(0)).pack(side="left", padx=2)
        ttk.Button(row, text="⏵ 10s", bootstyle="secondary-outline", width=6,
                    command=lambda: self._seek(10)).pack(side="left", padx=2)
        ttk.Button(row, text="⏵ 30s", bootstyle="secondary-outline", width=6,
                    command=lambda: self._seek(30)).pack(side="left", padx=2)

    # ---------- visualización ----------
    def build_visualization(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        # Izquierda: video
        left = ttk.Labelframe(parent, text="Explicación en video",
                               bootstyle="info", padding=4)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.video = VideoPlayer(
            left,
            source=VIDEO_FILE if os.path.exists(VIDEO_FILE) else None,
            autoplay=False, loop=True,
        )
        self.video.grid(row=0, column=0, sticky="nsew")

        # Derecha: matriz D
        right = ttk.Labelframe(parent, text="Matriz D (3×3)",
                                bootstyle="info", padding=4)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self.d_panel = PlotPanel(
            right, figsize=(5.5, 4.2),
            subplots=(1, 1), show_toolbar=False,
        )
        self.d_panel.grid(row=0, column=0, sticky="nsew")

        self.f_panel = PlotPanel(
            right, figsize=(5.5, 1.6),
            subplots=(1, 1), show_toolbar=False,
        )
        self.f_panel.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        self._redraw()

    # ---------- callbacks ----------
    def _on_E_changed(self, v: float) -> None:
        self._E = float(v)
        self._redraw()

    def _on_nu_changed(self, v: float) -> None:
        self._nu = float(v)
        self._redraw()

    def _on_case_changed(self) -> None:
        self._case = self.var_case.get()
        self._redraw()

    def _seek(self, seconds: float) -> None:
        try:
            self.video.seek(seconds)
            self.video.play()
        except Exception:
            pass

    # ---------- dibujo ----------
    def _redraw(self) -> None:
        colors = _theme_colors()

        try:
            D = constitutive_matrix(self._E, self._nu, self._case)
        except Exception as exc:
            D = None
            err = str(exc)

        if D is None:
            ax = self.d_panel.ax
            ax.clear()
            ax.set_xticks([]); ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.text(0.5, 0.5, f"Error: {err}",
                     ha="center", va="center", color="#e74c3c",
                     transform=ax.transAxes, fontsize=10)
            self.d_panel.redraw()
            return

        # Normalizar para que los números no exploten con E=2.1e11
        scale, scale_prefix = self._scale_factor(D)
        Dn = D / scale
        prefix = self._latex_prefix(scale_prefix)

        render_matrix_latex(
            self.d_panel.ax, Dn, fmt="{:+.3f}",
            fontsize=14, color=colors["fg"],
            title=f"{self._case}   —   E = {self._E:.3e} Pa,  ν = {self._nu:.3f}",
            prefix=prefix,
        )
        self.d_panel.redraw()

        # Fórmula simbólica
        expr = self._symbolic_formula()
        render_expression_latex(
            self.f_panel.ax, expr, fontsize=12, color=colors["fg"],
        )
        self.f_panel.redraw()

    @staticmethod
    def _scale_factor(D: np.ndarray) -> tuple[float, str]:
        vmax = float(np.max(np.abs(D)))
        if vmax == 0:
            return 1.0, ""
        exp = int(np.floor(np.log10(vmax)))
        if exp >= 9:
            return 1e9, "1e9"
        if exp >= 6:
            return 1e6, "1e6"
        if exp >= 3:
            return 1e3, "1e3"
        return 1.0, ""

    @staticmethod
    def _latex_prefix(scale_prefix: str) -> str:
        if not scale_prefix:
            return r"\mathbf{D}="
        if scale_prefix == "1e9":
            return r"\mathbf{D}=10^{9}\,"
        if scale_prefix == "1e6":
            return r"\mathbf{D}=10^{6}\,"
        if scale_prefix == "1e3":
            return r"\mathbf{D}=10^{3}\,"
        return r"\mathbf{D}="

    def _symbolic_formula(self) -> str:
        if self._case == ANALYSIS_PLANE_STRESS:
            return (
                r"\mathbf{D}=\dfrac{E}{1-\nu^{2}}"
                r"\begin{bmatrix} 1 & \nu & 0 \\ "
                r"\nu & 1 & 0 \\ "
                r"0 & 0 & \tfrac{1-\nu}{2}\end{bmatrix}"
            )
        return (
            r"\mathbf{D}=\dfrac{E}{(1+\nu)(1-2\nu)}"
            r"\begin{bmatrix} 1-\nu & \nu & 0 \\ "
            r"\nu & 1-\nu & 0 \\ "
            r"0 & 0 & \tfrac{1-2\nu}{2}\end{bmatrix}"
        )

    # ---------- teoría ----------
    def build_theory(self, doc: TheoryDoc, ctx: dict) -> None:
        doc.section("Relación constitutiva elástica-lineal")
        doc.para(
            r"Para un material isótropo, la tensión y la deformación se "
            r"relacionan como $\boldsymbol{\sigma}=\mathbf{D}\,"
            r"\boldsymbol{\varepsilon}$."
        )
        doc.subsection("Tensión plana")
        doc.para(
            r"Hipótesis: el espesor es pequeño frente a las dimensiones en el "
            r"plano y la carga actúa en el plano $(x,y)$. Se asume $\sigma_z="
            r"\tau_{xz}=\tau_{yz}=0$."
        )
        doc.equation(
            r"\mathbf{D}_{\text{TP}}=\dfrac{E}{1-\nu^{2}}"
            r"\begin{bmatrix}1 & \nu & 0\\ \nu & 1 & 0\\ 0 & 0 & \tfrac{1-\nu}{2}\end{bmatrix}"
        )
        doc.subsection("Deformación plana")
        doc.para(
            r"Hipótesis: la pieza es muy larga en $z$ y no puede deformarse en "
            r"esa dirección. Se asume $\varepsilon_z=\gamma_{xz}=\gamma_{yz}=0$."
        )
        doc.equation(
            r"\mathbf{D}_{\text{DP}}=\dfrac{E}{(1+\nu)(1-2\nu)}"
            r"\begin{bmatrix}1-\nu & \nu & 0\\ \nu & 1-\nu & 0\\ "
            r"0 & 0 & \tfrac{1-2\nu}{2}\end{bmatrix}"
        )
