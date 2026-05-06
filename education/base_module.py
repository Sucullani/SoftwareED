"""
Base classes para los módulos educativos de FEM.

Tres familias adaptadas a la naturaleza de cada módulo:

* GeometryModule  — exploración geométrica/funciones de forma (M0, M1, M2).
                    No requieren solver. Auto-detecta element_type/n_nodes
                    desde el project. Layout estándar.
* ProcessModule   — fase de proceso (M3, M4, M5, M6). Lee estado del project
                    (analysis_type, material, element_type) y lo expone como
                    badge informativo. Sin selectores redundantes con el menú.
* PostModule      — post-proceso (M7, M8). Auto-resuelve y cachea
                    self.solution, self.element_stresses, self.nodal_avg.
                    En caso de error expone self._solver_error y muestra
                    un panel de error en lugar de los controles/visualización.
                    M9 (sandbox) hereda pero opta por NOT_AUTO_SOLVE = True.

Layout estándar (puede ignorarse subclasificando build_visualization
para componer un layout custom):

    ┌──────────────────────────────────────────────────────────┐
    │ Título                  [badge]   [📖] [↻] [Cerrar]      │  header
    ├─────────────┬────────────────────────────────────────────┤
    │ Controles   │  Visualización                             │
    ├─────────────┴────────────────────────────────────────────┤
    │ [▶ ⏸ ■]   ──── progreso ────                             │  footer
    └──────────────────────────────────────────────────────────┘

Hooks que las subclases implementan (mismo contrato que la versión previa):
    build_controls(parent)        — controles izquierdos
    build_visualization(parent)   — panel principal
    build_theory(doc, ctx)        — opcional
    animate_step(t)               — opcional, requiere HAS_ANIMATION = True

Helpers nuevos disponibles en todas las subclases:
    self.element_type   — ELEMENT_Q4 o ELEMENT_Q9 (string canónico)
    self.n_nodes        — 4 o 9
    self.is_q9          — bool
    self.node_coords    — np.ndarray (N, 2) con coords del elemento
    self._pack_project_badge(parent, ...) — badge read-only del estado
    self._show_error(parent, msg)         — label rojo con scroll
"""

from __future__ import annotations

from typing import Optional

import tkinter as tk
import ttkbootstrap as ttk
import numpy as np

from education.components import TheoryViewer, StepAnimator
from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
)


# ────────────────────────────────────────────────────────────────────
#                          BASE COMÚN
# ────────────────────────────────────────────────────────────────────

class BaseEducationalModule(ttk.Toplevel):
    """Ventana ttkbootstrap base. Subclasificar vía Geometry/Process/PostModule."""

    TITLE: str = "Módulo"
    HAS_ANIMATION: bool = False
    ANIMATION_DURATION_MS: int = 2500

    # Hints de tamaño por familia. Las subclases pueden pasar width/height
    # explícitos al super().__init__ para overridear.
    DEFAULT_WIDTH: int = 1280
    DEFAULT_HEIGHT: int = 820

    # Si True, se renderiza un badge con el estado del project (Q4/Q9, TP/DP)
    # en el header. Activado por defecto en ProcessModule y PostModule.
    SHOW_PROJECT_BADGE: bool = False
    BADGE_SHOW_ANALYSIS: bool = False
    BADGE_SHOW_MATERIAL: bool = False

    def __init__(self, parent, project, element_id,
                 width: Optional[int] = None,
                 height: Optional[int] = None):
        super().__init__(parent)
        self.project = project
        self.element_id = element_id
        self.element = (project.elements.get(element_id)
                         if project and element_id is not None else None)

        # Auto-detectar element_type / n_nodes / coords ANTES de build_*
        self._init_element_context()

        self.title(f"Módulo Educativo — {self.TITLE}")
        w = width or self.DEFAULT_WIDTH
        h = height or self.DEFAULT_HEIGHT
        self.geometry(f"{w}x{h}")
        self.minsize(1000, 680)

        self._build_layout()
        try:
            self.build_controls(self.controls_frame)
        except Exception as exc:
            self._show_error(self.controls_frame, f"Error en controles: {exc}")
        try:
            self.build_visualization(self.viz_frame)
        except Exception as exc:
            self._show_error(self.viz_frame, f"Error en visualización: {exc}")

        self.after(120, self._raise)

    # ────────────────── contexto de elemento ──────────────────
    def _init_element_context(self) -> None:
        """Setea self.element_type, self.n_nodes, self.is_q9, self.node_coords.

        Prioridad: tipo del elemento concreto → tipo global del project →
        Q4 default. Centraliza la detección que antes se duplicaba en
        cada módulo.
        """
        is_q9 = False
        if self.element is not None and getattr(self.element, "num_nodes", 0) == 9:
            is_q9 = True
        elif self.project is not None and \
                getattr(self.project, "element_type", None) == ELEMENT_Q9:
            is_q9 = True
        self.element_type = ELEMENT_Q9 if is_q9 else ELEMENT_Q4
        self.n_nodes = 9 if is_q9 else 4
        self.is_q9 = is_q9

        if self.element and self.project:
            try:
                self.node_coords = np.array([
                    [self.project.nodes[nid].x, self.project.nodes[nid].y]
                    for nid in self.element.node_ids
                ], dtype=float)
            except KeyError:
                self.node_coords = self._fallback_coords()
        else:
            self.node_coords = self._fallback_coords()

    def _fallback_coords(self) -> np.ndarray:
        """Coords demo cuando no hay elemento real (módulos abiertos sin proyecto)."""
        return np.array(
            [[0.0, 0.0], [2.0, 0.2], [2.2, 1.5], [0.1, 1.3]],
            dtype=float,
        )

    # ────────────────── layout ──────────────────
    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # ── HEADER ─────────────────────────────────────────────
        header = ttk.Frame(self, padding=(10, 6))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=0)
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text=self.TITLE,
                   font=("Segoe UI", 14, "bold"),
                   bootstyle="info", anchor="w",
                   ).grid(row=0, column=0, sticky="w")

        # Badge de contexto del project (solo si la subclase lo activa).
        if self.SHOW_PROJECT_BADGE:
            badge = self._build_project_badge(header)
            if badge is not None:
                badge.grid(row=0, column=1, sticky="w", padx=(12, 0))

        ttk.Button(header, text="📖 Teoría", bootstyle="info",
                    command=self.open_theory,
                    ).grid(row=0, column=2, padx=4)
        ttk.Button(header, text="↻", width=3, bootstyle="secondary-outline",
                    command=self.reset,
                    ).grid(row=0, column=3, padx=4)
        ttk.Button(header, text="Cerrar", bootstyle="danger-outline",
                    command=self.destroy,
                    ).grid(row=0, column=4, padx=(4, 0))

        # ── BODY: 2 columnas (controles | visualización) ────────
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

    # ────────────────── badge de contexto ──────────────────
    def _build_project_badge(self, parent) -> Optional[ttk.Label]:
        """Construye el badge informativo de estado del project.

        Subclases que quieran mostrarlo setean SHOW_PROJECT_BADGE = True
        y opcionalmente BADGE_SHOW_ANALYSIS / BADGE_SHOW_MATERIAL.
        """
        bits = []
        # Element type siempre
        et_short = "Q9" if self.is_q9 else "Q4"
        bits.append(f"📐 {et_short}")
        # Tipo de análisis (TP / DP)
        if self.BADGE_SHOW_ANALYSIS and self.project is not None:
            at = getattr(self.project, "analysis_type", None)
            if at == ANALYSIS_PLANE_STRESS:
                bits.append("⚙ Tensión Plana")
            elif at == ANALYSIS_PLANE_STRAIN:
                bits.append("⚙ Deformación Plana")
        # Material del elemento
        if self.BADGE_SHOW_MATERIAL and self.element is not None and \
                self.project is not None:
            mat = self.project.materials.get(
                getattr(self.element, "material_name", None)
            )
            if mat is not None:
                bits.append(f"🎨 {mat.name}")
        if not bits:
            return None
        return ttk.Label(parent, text="   ·   ".join(bits),
                          font=("Segoe UI", 9), bootstyle="info-inverse",
                          padding=(8, 3))

    def _pack_project_badge(self, parent) -> None:
        """Atajo para subclases que quieren replicar el badge dentro del
        panel de controles (no solo en el header)."""
        badge = self._build_project_badge(parent)
        if badge is not None:
            badge.pack(fill="x", pady=(0, 6))

    # ────────────────── hooks para subclases ──────────────────
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
            self._show_error(self.controls_frame, f"Error en controles: {exc}")
        try:
            self.build_visualization(self.viz_frame)
        except Exception as exc:
            self._show_error(self.viz_frame, f"Error en visualización: {exc}")

    # ────────────────── helpers ──────────────────
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
            "element_type": self.element_type,
            "n_nodes": self.n_nodes,
            "is_q9": self.is_q9,
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
    def _show_error(parent, msg: str) -> None:
        """Muestra un label rojo de error visible (no silenciado)."""
        lbl = ttk.Label(parent, text=msg, bootstyle="danger",
                         wraplength=300, justify="left")
        try:
            lbl.pack(padx=10, pady=10, anchor="w")
        except tk.TclError:
            lbl.grid(row=99, column=0, columnspan=4, padx=10, pady=10,
                      sticky="ew")

    # Compat con código viejo que llamara _error_label.
    _error_label = _show_error


# ────────────────────────────────────────────────────────────────────
#                       FAMILIA: GEOMETRÍA
# ────────────────────────────────────────────────────────────────────

class GeometryModule(BaseEducationalModule):
    """Módulos de exploración geométrica (M0, M1, M2).

    No requieren solver. Heredan los helpers de element_type/n_nodes
    de BaseEducationalModule. Layout estándar.
    """

    SHOW_PROJECT_BADGE = True
    BADGE_SHOW_ANALYSIS = False
    BADGE_SHOW_MATERIAL = False


# ────────────────────────────────────────────────────────────────────
#                        FAMILIA: PROCESO
# ────────────────────────────────────────────────────────────────────

class ProcessModule(BaseEducationalModule):
    """Módulos de la fase de proceso (M3, M4, M5, M6).

    Leen estado del project (analysis_type, material, element_type).
    Muestran badge en el header con TP/DP + Q4/Q9. NO incluyen selectores
    redundantes con el menú principal — la única fuente de verdad es el
    project.

    Subclases que necesitan el material del elemento (M3) ponen
    BADGE_SHOW_MATERIAL = True.
    """

    SHOW_PROJECT_BADGE = True
    BADGE_SHOW_ANALYSIS = True
    BADGE_SHOW_MATERIAL = False

    @property
    def analysis_type(self) -> str:
        """Caso plano (TP/DP) leído del project, con fallback a TP."""
        if self.project is not None:
            at = getattr(self.project, "analysis_type", None)
            if at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
                return at
        return ANALYSIS_PLANE_STRESS

    def get_material(self, element_id: Optional[int] = None):
        """Retorna el Material asignado al elemento (o al elemento actual).

        Fallback: primer material del project, o None si no hay materiales.
        """
        if self.project is None:
            return None
        eid = element_id if element_id is not None else self.element_id
        elem = self.project.elements.get(eid) if eid is not None else None
        if elem is not None:
            mat = self.project.materials.get(
                getattr(elem, "material_name", None)
            )
            if mat is not None:
                return mat
        mats = list(self.project.materials.values()) if self.project.materials else []
        return mats[0] if mats else None


# ────────────────────────────────────────────────────────────────────
#                       FAMILIA: POST-PROCESO
# ────────────────────────────────────────────────────────────────────

class PostModule(BaseEducationalModule):
    """Módulos de post-proceso (M7, M8, M9).

    Auto-resuelven al inicializar (UNA sola vez) y cachean:
        self.solution         — dict del solver (u, reactions, ...)
        self.element_stresses — por elemento
        self.nodal_avg        — promediado nodal
        self._solver_error    — str con la excepción si falló (None si ok)
        self.has_solution     — propiedad bool

    Si el solver falla, build_controls/build_visualization deben llamar
    self._maybe_show_solver_error(parent) al inicio: si retorna True,
    salir sin construir lo demás.

    Sandboxes que manejan sus propias copias del project (M9) setean
    AUTO_SOLVE = False y se encargan de su propio cómputo.
    """

    SHOW_PROJECT_BADGE = True
    BADGE_SHOW_ANALYSIS = True
    BADGE_SHOW_MATERIAL = False

    AUTO_SOLVE: bool = True

    def __init__(self, parent, project, element_id, **kwargs):
        # Inicializar atributos ANTES de super().__init__ para que estén
        # disponibles en build_controls / build_visualization.
        self._solver_error: Optional[str] = None
        self.solution: Optional[dict] = None
        self.element_stresses: Optional[dict] = None
        self.nodal_avg: Optional[dict] = None

        if self.AUTO_SOLVE and project is not None and project.elements:
            self._ensure_solved(project)

        super().__init__(parent, project, element_id, **kwargs)

    def _ensure_solved(self, project) -> bool:
        """Resuelve UNA vez y cachea stresses + nodal_avg.

        Reemplaza el patrón inconsistente de M7 (solve 2×) y M8 (solve sin
        guard). Si falla, setea self._solver_error y retorna False.
        """
        try:
            from fem.solver import solve_system
            from fem.stress import compute_all_stresses
            self.solution = solve_system(project)
            self.element_stresses, self.nodal_avg = compute_all_stresses(
                project, self.solution
            )
            return True
        except Exception as exc:
            self._solver_error = str(exc)
            self.solution = None
            self.element_stresses = None
            self.nodal_avg = None
            return False

    @property
    def has_solution(self) -> bool:
        """True si el solver corrió con éxito y hay datos para visualizar."""
        return (self._solver_error is None
                 and self.solution is not None
                 and self.nodal_avg is not None)

    def _maybe_show_solver_error(self, parent) -> bool:
        """Muestra el error del solver si lo hay. Retorna True si hubo error."""
        if self._solver_error:
            self._show_error(
                parent,
                f"⚠ El solver no pudo procesar el modelo:\n\n{self._solver_error}\n\n"
                "Volvé al pre-proceso para revisar las restricciones, "
                "el material y las cargas."
            )
            return True
        return False
