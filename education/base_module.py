"""
BaseEducationalModule: ventana base para los módulos educativos de FEM,
construida con ttkbootstrap sobre el mismo tema 'darkly' que la ventana
principal.

Layout (sin panel de fórmulas):
┌─────────────────────────────────────────────────────────┐
│ Título del módulo              [📖 Teoría] [↻] [Cerrar] │  header
├─────────────┬───────────────────────────────────────────┤
│ Controles y │         Visualización                     │
│ valores     │         (click sobre el elemento)         │
│ actuales    │                                           │
├─────────────┴───────────────────────────────────────────┤
│  [▶ Play] [⏸] [■]   ─── progreso ───                    │  footer
└─────────────────────────────────────────────────────────┘

Las subclases implementan:
    build_controls(parent), build_visualization(parent)
    build_theory(doc, ctx) -> None   # opcional
    animate_step(t)        -> None   # opcional, 0 ≤ t ≤ 1
"""

from __future__ import annotations

from typing import Optional

import tkinter as tk
import ttkbootstrap as ttk
import numpy as np

from education.components import TheoryViewer, StepAnimator


class BaseEducationalModule(ttk.Toplevel):
    """Ventana ttkbootstrap para un módulo educativo."""

    TITLE: str = "Módulo"
    HAS_ANIMATION: bool = False
    ANIMATION_DURATION_MS: int = 2500

    def __init__(self, parent, project, element_id,
                 width: int = 1280, height: int = 820):
        super().__init__(parent)
        self.project = project
        self.element_id = element_id
        self.element = project.elements.get(element_id) if project else None

        self.title(f"Módulo Educativo — {self.TITLE}")
        self.geometry(f"{width}x{height}")
        self.minsize(1000, 680)

        if self.element and project:
            self.node_coords = np.array([
                [project.nodes[nid].x, project.nodes[nid].y]
                for nid in self.element.node_ids
            ], dtype=float)
        else:
            self.node_coords = np.array(
                [[0.0, 0.0], [2.0, 0.2], [2.2, 1.5], [0.1, 1.3]],
                dtype=float,
            )

        self._build_layout()
        try:
            self.build_controls(self.controls_frame)
        except Exception as exc:
            self._error_label(self.controls_frame, f"Error en controles: {exc}")
        try:
            self.build_visualization(self.viz_frame)
        except Exception as exc:
            self._error_label(self.viz_frame, f"Error en visualización: {exc}")

        self.after(120, self._raise)

    # ---------- layout ----------
    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # ── HEADER ─────────────────────────────────────────────
        header = ttk.Frame(self, padding=(10, 6))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=self.TITLE,
                   font=("Segoe UI", 14, "bold"),
                   bootstyle="info", anchor="w",
                   ).grid(row=0, column=0, sticky="w")

        ttk.Button(header, text="📖 Teoría", bootstyle="info",
                    command=self.open_theory,
                    ).grid(row=0, column=1, padx=4)
        ttk.Button(header, text="↻", width=3, bootstyle="secondary-outline",
                    command=self.reset,
                    ).grid(row=0, column=2, padx=4)
        ttk.Button(header, text="Cerrar", bootstyle="danger-outline",
                    command=self.destroy,
                    ).grid(row=0, column=3, padx=(4, 0))

        # ── BODY: 2 columnas (controles | visualización) ────────
        # Columna de controles con scroll vertical
        controls_outer = ttk.Frame(self)
        controls_outer.grid(row=1, column=0, sticky="nsew",
                             padx=(8, 4), pady=6)
        controls_outer.rowconfigure(0, weight=1)
        controls_outer.columnconfigure(0, weight=1)

        self._ctrl_canvas = tk.Canvas(controls_outer, width=280,
                                       highlightthickness=0,
                                       background="#222233")
        self._ctrl_canvas.grid(row=0, column=0, sticky="nsew")
        self._ctrl_sb = ttk.Scrollbar(controls_outer, orient="vertical",
                                       command=self._ctrl_canvas.yview,
                                       bootstyle="round")
        self._ctrl_sb.grid(row=0, column=1, sticky="ns")
        self._ctrl_canvas.configure(yscrollcommand=self._ctrl_sb.set)

        self.controls_frame = ttk.Frame(self._ctrl_canvas, padding=(6, 6))
        self._ctrl_id = self._ctrl_canvas.create_window(
            (0, 0), window=self.controls_frame, anchor="nw"
        )
        self.controls_frame.bind(
            "<Configure>",
            lambda e: self._ctrl_canvas.configure(
                scrollregion=self._ctrl_canvas.bbox("all")
            ),
        )
        self._ctrl_canvas.bind(
            "<Configure>",
            lambda e: self._ctrl_canvas.itemconfigure(
                self._ctrl_id, width=e.width
            ),
        )

        # Visualización
        self.viz_frame = ttk.Frame(self, padding=(4, 4))
        self.viz_frame.grid(row=1, column=1, sticky="nsew",
                             padx=(4, 8), pady=6)
        self.viz_frame.rowconfigure(0, weight=1)
        self.viz_frame.columnconfigure(0, weight=1)

        # ── FOOTER ─────────────────────────────────────────────
        self.footer_frame = ttk.Frame(self, padding=(10, 6))
        self.footer_frame.grid(row=2, column=0, columnspan=2,
                                sticky="ew", padx=8, pady=(2, 8))
        if self.HAS_ANIMATION:
            self.animator = StepAnimator(
                self.footer_frame,
                step_fn=self._safe_animate_step,
                duration_ms=self.ANIMATION_DURATION_MS,
            )
            self.animator.pack(fill="x", padx=4, pady=2)
        else:
            self.animator = None
            ttk.Label(self.footer_frame, text="").pack(fill="x")

    # ---------- hooks para subclases ----------
    def build_controls(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="(sin controles)").pack(pady=10)

    def build_visualization(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="(visualización no implementada)"
                   ).pack(expand=True)

    def build_theory(self, doc, ctx: dict) -> None:
        doc.section("Teoría")
        doc.para("Este módulo no define un documento de teoría extendido todavía.")

    def animate_step(self, t: float) -> None:
        return None

    def reset(self) -> None:
        """Reconstruye controles y visualización."""
        for frame in (self.controls_frame, self.viz_frame):
            for child in frame.winfo_children():
                child.destroy()
        try:
            self.build_controls(self.controls_frame)
        except Exception as exc:
            self._error_label(self.controls_frame, f"Error en controles: {exc}")
        try:
            self.build_visualization(self.viz_frame)
        except Exception as exc:
            self._error_label(self.viz_frame, f"Error en visualización: {exc}")

    # ---------- helpers ----------
    def open_theory(self) -> None:
        ctx = self._theory_context()

        def builder(doc):
            try:
                self.build_theory(doc, ctx)
            except Exception as exc:
                doc.section("Error")
                doc.para(f"No se pudo construir la teoría: {exc}")

        TheoryViewer.open(
            self,
            title=f"Teoría — {self.TITLE}",
            doc_builder=builder,
            subtitle="EduFEM — Módulos educativos",
        )

    def _theory_context(self) -> dict:
        return {
            "element_type": (getattr(self.element, "element_type", "Q4")
                              if self.element else "Q4"),
            "node_coords": self.node_coords.copy(),
        }

    def _safe_animate_step(self, t: float) -> None:
        try:
            self.animate_step(t)
        except Exception:
            pass

    def _raise(self) -> None:
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    @staticmethod
    def _error_label(parent, msg: str) -> None:
        lbl = ttk.Label(parent, text=msg, bootstyle="danger",
                         wraplength=300, justify="left")
        try:
            lbl.pack(padx=10, pady=10)
        except tk.TclError:
            # parent ya está gestionado con grid
            lbl.grid(row=99, column=0, columnspan=3, padx=10, pady=10,
                      sticky="ew")
