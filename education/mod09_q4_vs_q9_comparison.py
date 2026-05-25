"""
Módulo 9 — Comparación Q4 vs Q9 (overlay, POST-PROCESO)

**Reescritura 2026-05**: migrado de Toplevel pesado a Overlay liviano
on-demand. La versión anterior pre-computaba 8 paneles (Q4×4 niveles +
Q9×4 niveles) en el `__init__`, lo que bloqueaba el UI durante varios
segundos antes de pintar nada — el módulo "no cargaba al iniciar".

Diseño actual:
    1. Hereda de `CanvasOverlayModule` (NO de `PostModule`/Toplevel).
    2. Layout compacto: 2 paneles Q4 vs Q9 lado a lado + log-log debajo
       + slider de nivel N=0..3 en el footer.
    3. **Cómputo on-demand**: al cambiar de nivel, dispara el solve solo
       si el resultado (kind, level) no está en cache. Usa `mesh.after`
       para ceder al UI antes de bloquear con el solver.
    4. Sandbox: `deepcopy(project)` al abrir; el original nunca se muta.

Pedagogía:
    El alumno recorre el refinamiento a su ritmo. Cada nivel cuesta
    visiblemente el doble que el anterior, pero el módulo arranca
    instantáneo con N=0 visible y el alumno *decide* cuándo invertir
    cómputo en cada incremento. La convergencia se va trazando en el
    log-log a medida que se computan los niveles.
"""

from __future__ import annotations

import copy
from typing import Optional

import tkinter as tk
import ttkbootstrap as ttk
import numpy as np

try:
    from PIL import ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.overlay_module import CanvasOverlayModule
from config.settings import EDU_FIG_BG, EDU_AXES_BG, EDU_FG, EDU_FG_MUTED
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from models.mesh_utils import (
    subdivide_q4_mesh, expand_q4_to_q9, shrink_q9_to_q4,
)
from gui.postprocessing.result_image_renderer import render_result_to_pil


_C_Q4 = "#4fa3ff"
_C_Q9 = "#43a047"

_MAX_LEVEL = 3
_PANEL_W = 280
_PANEL_H = 200


class Q4vsQ9ComparisonModule(CanvasOverlayModule):
    """M9 overlay: comparación Q4 vs Q9 con refinamiento on-demand."""

    TITLE = "⑨  Q4 vs Q9  ·  refinamiento"
    PHASE = "post"
    OVERLAY_INITIAL_POS = (40, 40)
    OVERLAY_WIDTH = 640
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False

    def __init__(self, main_window, project, element_id):
        # Sandbox: deepcopy normalizada a Q4 base. Hacemos el shrink ANTES
        # de llamar al super() para que el cómputo on-demand siempre parta
        # de la malla Q4 macro original.
        self._base_project = copy.deepcopy(project) if project else None
        if self._base_project is not None:
            if any(e.num_nodes == 9
                   for e in self._base_project.elements.values()):
                shrink_q9_to_q4(self._base_project)
            self._base_project.file_path = None
            self._base_project.is_modified = False

        # Estado
        self._level = 0  # 0..3
        self._comp_key = "von_mises"
        # Cache de resultados: {(kind, level): {"project", "u_max"}}
        self._cache: dict = {}
        self._compute_pending: Optional[tuple] = None  # (kind, level) en curso

        # Widgets (placeholders; se inicializan en build_overlay)
        self._lbl_status: Optional[tk.Label] = None
        self._panel_q4: Optional[tk.Canvas] = None
        self._panel_q9: Optional[tk.Canvas] = None
        self._photo_q4: Optional["ImageTk.PhotoImage"] = None
        self._photo_q9: Optional["ImageTk.PhotoImage"] = None
        self._var_level: Optional[tk.IntVar] = None
        self._var_comp: Optional[tk.StringVar] = None
        self._fig: Optional[Figure] = None
        self._ax_conv = None
        self._canvas_mpl: Optional[FigureCanvasTkAgg] = None
        self._progressbar: Optional[ttk.Progressbar] = None
        self._progressbar_visible: bool = False

        super().__init__(main_window, project, element_id)

    # ── Construcción del overlay ───────────────────────────────────
    def build_overlay(self, body):
        if self._base_project is None or not self._base_project.elements:
            tk.Label(
                body,
                text="◎ Cargá un modelo con al menos un elemento.",
                bg=EDU_AXES_BG, fg=EDU_FG_MUTED, font=("Segoe UI", 10),
                wraplength=580,
            ).pack(fill="both", expand=True, padx=8, pady=8)
            return

        # Banner
        ttk.Label(
            body,
            text=("Refinamiento h del mismo problema en Q4 y Q9. "
                  "El log-log muestra la convergencia."),
            font=("Segoe UI", 9, "italic"), foreground=EDU_FG_MUTED,
            wraplength=600, justify="left",
        ).pack(fill="x", padx=4, pady=(0, 4))

        # Toolbar: selector de componente + slider de nivel
        bar = ttk.Frame(body)
        bar.pack(fill="x", pady=(0, 4))

        ttk.Label(bar, text="Componente:",
                   font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                   ).pack(side="left", padx=(0, 4))
        self._var_comp = tk.StringVar(value=self._comp_key)
        for key, label in (("von_mises", "VM"),
                            ("sigma_x",   "σx"),
                            ("sigma_y",   "σy"),
                            ("tau_xy",    "τxy")):
            ttk.Radiobutton(
                bar, text=label, value=key, variable=self._var_comp,
                bootstyle="success-outline-toolbutton",
                command=self._on_comp_change,
            ).pack(side="left", padx=1)

        ttk.Separator(bar, orient="vertical").pack(side="left",
                                                     fill="y", padx=8)
        ttk.Label(bar, text="N:",
                   font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                   ).pack(side="left", padx=(0, 4))
        self._var_level = tk.IntVar(value=self._level)
        for n in range(_MAX_LEVEL + 1):
            ttk.Radiobutton(
                bar, text=str(n), value=n, variable=self._var_level,
                bootstyle="success-outline-toolbutton",
                command=self._on_level_change,
            ).pack(side="left", padx=1)

        # Status + barra de progreso indeterminada. La barra se muestra
        # SOLO mientras hay un cómputo en vuelo (pack en _refresh_status,
        # pack_forget cuando termina). Pedagógicamente comunica "estoy
        # trabajando" sin necesitar estimar ETA del solver (que depende
        # del nivel N y la geometría).
        status_row = ttk.Frame(body)
        status_row.pack(fill="x", padx=4, pady=(0, 2))
        self._lbl_status = tk.Label(
            status_row, text="", bg=EDU_AXES_BG, fg="#ffd54f",
            font=("Consolas", 9), anchor="w",
        )
        self._lbl_status.pack(side="left", fill="x", expand=True)
        self._progressbar = ttk.Progressbar(
            status_row, mode="indeterminate", length=120,
            bootstyle="success-striped",
        )
        # NO se packea acá — se muestra/oculta dinámicamente en
        # _refresh_status según _compute_pending. Mantener una referencia
        # al frame parent para repackear cuando aparezca.
        self._progressbar_visible = False

        # Dos paneles lado a lado (Q4 / Q9) con encabezado de color por tipo
        panels = ttk.Frame(body)
        panels.pack(fill="x", pady=(0, 4))

        col_q4 = ttk.Frame(panels)
        col_q4.pack(side="left", expand=True, fill="both", padx=(0, 4))
        tk.Label(col_q4, text="Q4", bg=EDU_AXES_BG, fg=_C_Q4,
                  font=("Segoe UI Semibold", 10)).pack(anchor="w")
        self._panel_q4 = tk.Canvas(
            col_q4, width=_PANEL_W, height=_PANEL_H,
            bg=EDU_FIG_BG, highlightthickness=0,
        )
        self._panel_q4.pack()

        col_q9 = ttk.Frame(panels)
        col_q9.pack(side="left", expand=True, fill="both", padx=(4, 0))
        tk.Label(col_q9, text="Q9", bg=EDU_AXES_BG, fg=_C_Q9,
                  font=("Segoe UI Semibold", 10)).pack(anchor="w")
        self._panel_q9 = tk.Canvas(
            col_q9, width=_PANEL_W, height=_PANEL_H,
            bg=EDU_FIG_BG, highlightthickness=0,
        )
        self._panel_q9.pack()

        # Log-log de convergencia
        self._fig = Figure(figsize=(5.6, 2.4), dpi=100, facecolor=EDU_FIG_BG)
        self._ax_conv = self._fig.add_subplot(111)
        self._ax_conv.set_facecolor(EDU_AXES_BG)
        self._ax_conv.tick_params(colors=EDU_FG, labelsize=7)
        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=body)
        self._canvas_mpl.get_tk_widget().pack(fill="x", padx=4, pady=(2, 2))

        # Cross-reference decorativa (cierra la narrativa del pipeline; sin destino).
        self._pack_crossref(
            body, None,
            "👉 Q9 converge más rápido que Q4 al mismo número de DOF — "
            "el ratio de pendientes log-log lo evidencia.",
            wraplength=600,
        )

        # Disparar cómputo inicial del N=0 sin bloquear el alumno: el
        # overlay aparece inmediatamente con placeholders y el solver
        # corre en el próximo idle del event loop.
        self._schedule_compute("q4", 0)
        self._schedule_compute("q9", 0)

    # ── Callbacks de cambio de estado ──────────────────────────────
    def _on_level_change(self):
        try:
            self._level = int(self._var_level.get())
        except (tk.TclError, ValueError):
            return
        self._schedule_compute("q4", self._level)
        self._schedule_compute("q9", self._level)
        self._refresh_panels()
        self._refresh_convergence()
        self._refresh_status()

    def _on_comp_change(self):
        if self._var_comp is None:
            return
        self._comp_key = self._var_comp.get()
        self._refresh_panels()

    # ── Cómputo on-demand ──────────────────────────────────────────
    def _schedule_compute(self, kind: str, level: int):
        key = (kind, level)
        if key in self._cache:
            self._refresh_panels()
            self._refresh_convergence()
            self._refresh_status()
            return
        if self._compute_pending == key:
            return
        # Cedemos al event loop con un small after para que el spinner
        # de status pinte ANTES de bloquear con el solver.
        self._compute_pending = key
        self._refresh_status()
        try:
            self._mesh.after(50, lambda k=kind, lv=level: self._compute_one(k, lv))
        except tk.TclError:
            pass

    def _compute_one(self, kind: str, level: int):
        """Resuelve un (kind, level). Caro pero ya está cedido al UI."""
        try:
            proj = copy.deepcopy(self._base_project)
            for _ in range(level):
                subdivide_q4_mesh(proj, levels=1)
            if kind == "q9":
                expand_q4_to_q9(proj)
            result = solve_system(proj)
            stresses = compute_all_stresses(proj)
            u_max = float(np.max(np.abs(result["displacements"])))
            self._cache[(kind, level)] = {
                "project": proj,
                "stresses": stresses,
                "u_max": u_max,
                "n_dofs": int(result["displacements"].size),
            }
        except Exception:
            self._cache[(kind, level)] = None
        finally:
            if self._compute_pending == (kind, level):
                self._compute_pending = None
            try:
                self._refresh_panels()
                self._refresh_convergence()
                self._refresh_status()
            except tk.TclError:
                pass

    # ── Render ─────────────────────────────────────────────────────
    def _refresh_panels(self):
        self._render_panel(self._panel_q4, "q4", self._level, "_photo_q4")
        self._render_panel(self._panel_q9, "q9", self._level, "_photo_q9")

    def _render_panel(self, canvas: Optional[tk.Canvas], kind: str,
                       level: int, photo_attr: str):
        if canvas is None or not HAS_PIL:
            return
        canvas.delete("all")
        entry = self._cache.get((kind, level))
        if entry is None:
            if self._compute_pending == (kind, level):
                canvas.create_text(_PANEL_W / 2, _PANEL_H / 2,
                                    text="computando…",
                                    fill=EDU_FG_MUTED,
                                    font=("Consolas", 10))
            else:
                canvas.create_text(_PANEL_W / 2, _PANEL_H / 2,
                                    text="(sin computar)",
                                    fill=EDU_FG_MUTED,
                                    font=("Consolas", 10))
            return

        proj = entry["project"]
        node_values = self._extract_node_values(proj, entry["stresses"])
        if not node_values:
            canvas.create_text(_PANEL_W / 2, _PANEL_H / 2,
                                text="(sin datos)",
                                fill=EDU_FG_MUTED, font=("Consolas", 10))
            return
        vals = np.array(list(node_values.values()))
        vmin, vmax = float(np.min(vals)), float(np.max(vals))
        if vmax - vmin < 1e-12:
            vmin -= 1e-6; vmax += 1e-6
        img = render_result_to_pil(
            proj, node_values, vmin, vmax,
            width=_PANEL_W, height=_PANEL_H,
            wireframe=True,
        )
        if img is None:
            return
        photo = ImageTk.PhotoImage(img)
        setattr(self, photo_attr, photo)  # anti-GC
        canvas.create_image(0, 0, anchor="nw", image=photo)
        # Caption pequeño con el DOF count y u_max
        canvas.create_text(
            6, _PANEL_H - 14, anchor="w",
            text=f"N={level}  DOF={entry['n_dofs']}  |u|max={entry['u_max']:.3g}",
            fill="#ffffff", font=("Consolas", 8, "bold"),
        )

    def _extract_node_values(self, proj, stresses) -> dict:
        """Mapea project.nodes → escalar según self._comp_key."""
        if stresses is None:
            return {}
        comp = stresses.get(self._comp_key)
        if comp is None:
            return {}
        sorted_ids = sorted(proj.nodes.keys())
        return {nid: float(comp[i]) for i, nid in enumerate(sorted_ids)
                if i < len(comp)}

    def _refresh_convergence(self):
        if self._ax_conv is None:
            return
        ax = self._ax_conv
        ax.clear()
        ax.set_facecolor(EDU_AXES_BG)
        ax.tick_params(colors=EDU_FG, labelsize=7)

        for kind, color, label in (("q4", _C_Q4, "Q4"),
                                     ("q9", _C_Q9, "Q9")):
            xs, ys = [], []
            for lv in range(_MAX_LEVEL + 1):
                entry = self._cache.get((kind, lv))
                if entry is None:
                    continue
                xs.append(entry["n_dofs"])
                ys.append(entry["u_max"])
            if xs:
                ax.loglog(xs, ys, "-o", color=color, lw=1.6, label=label,
                          markersize=5)

        ax.set_xlabel("DOF", color=EDU_FG, fontsize=8)
        ax.set_ylabel("|u|_max", color=EDU_FG, fontsize=8)
        ax.grid(True, which="both", color="#444", lw=0.4, alpha=0.5)
        ax.legend(loc="best", fontsize=8, facecolor=EDU_AXES_BG,
                   edgecolor="none", labelcolor=EDU_FG)
        try:
            self._fig.tight_layout(pad=0.5)
            self._canvas_mpl.draw_idle()
        except tk.TclError:
            pass

    def _refresh_status(self):
        if self._lbl_status is None:
            return
        try:
            if self._compute_pending is not None:
                k, lv = self._compute_pending
                self._lbl_status.configure(
                    text=f"⏳ computando {k.upper()} N={lv}…",
                )
                self._show_progress(True)
            else:
                n_q4 = sum(1 for k, _ in self._cache.keys() if k == "q4"
                            and self._cache[(k, _)] is not None)
                n_q9 = sum(1 for k, _ in self._cache.keys() if k == "q9"
                            and self._cache[(k, _)] is not None)
                total = 2 * (_MAX_LEVEL + 1)
                done = n_q4 + n_q9
                bar = self._ascii_bar(done, total, width=16)
                self._lbl_status.configure(
                    text=f"{bar}  Q4: {n_q4}/{_MAX_LEVEL + 1}   "
                          f"Q9: {n_q9}/{_MAX_LEVEL + 1}   "
                          f"(N actual = {self._level})"
                )
                self._show_progress(False)
        except tk.TclError:
            pass

    def _show_progress(self, visible: bool) -> None:
        """Muestra/oculta la barra indeterminate sin re-crear el widget.

        Idempotente: si ya está en el estado pedido no hace nada (evita
        flicker cuando _refresh_status se invoca en cascada por varios
        _compute_one consecutivos)."""
        if self._progressbar is None:
            return
        if visible == self._progressbar_visible:
            return
        try:
            if visible:
                self._progressbar.pack(side="right", padx=(8, 0))
                self._progressbar.start(12)  # ms entre frames
            else:
                self._progressbar.stop()
                self._progressbar.pack_forget()
        except tk.TclError:
            return
        self._progressbar_visible = visible

    @staticmethod
    def _ascii_bar(done: int, total: int, width: int = 16) -> str:
        """Barra ASCII compacta para el contador de cache (sin animación,
        solo estado acumulado). `done` puede exceder `total` defensivamente."""
        if total <= 0:
            return "[" + " " * width + "]"
        ratio = max(0.0, min(1.0, done / total))
        filled = int(round(ratio * width))
        return "[" + "█" * filled + "·" * (width - filled) + "]"

    # ── Cleanup ────────────────────────────────────────────────────
    def on_closed(self):
        # Liberar referencias pesadas (cache de projects deepcopiados).
        self._cache.clear()
        self._base_project = None
