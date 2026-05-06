"""
Módulo 3 — Matriz constitutiva D (TP / DP)

    σ = D · ε     con D = D(E, ν, caso plano)

REDISEÑADO: Modo Overlay sobre el MeshCanvas compartido.

Override explícito del usuario respecto a la propuesta UX original:

    "M3 utiliza también un overlay que no esté embebido en el panel
     lateral; no compares TP/DP ya que esto está en el menú principal."

Diseño actual:
    1. NO abre Toplevel ni vive embebido en proc_tab. Activa un overlay
       flotante (~440 px) sobre el MeshCanvas compartido.
    2. El elemento bajo análisis se ELIGE POR CLICK en el canvas — el
       overlay refleja la D del material asignado a ese elemento (highlight
       amarillo automático del MeshCanvas).
    3. Toggle Fórmula ↔ Valores (requerimiento del usuario): la fórmula
       simbólica D(E,ν, caso) en LaTeX, los valores la matriz 3×3 evaluada
       con la ν actual del dial.
    4. Dial físico de Poisson (ν ∈ [0, 0.499]). Mover el dial reescribe
       D en tiempo real. Cuando ν → 0.5 en DP, el dial se vuelve rojo y
       el overlay muestra la advertencia de volumetric locking.
    5. Sin botones para TP/DP. El caso plano se LEE del project (badge en
       el header del overlay) — para cambiarlo el usuario va a Modelo ▸
       Tipo de Análisis. Una sola fuente de verdad.
"""

from __future__ import annotations

from typing import Optional

import math
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.overlay_module import CanvasOverlayModule
from education.components import (
    FormulaValueToggle, render_matrix_latex,
)

from fem.constitutive import constitutive_matrix
from config.settings import (
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
)


# Defaults usados solo si el proyecto no tiene materiales asignados.
_DEMO_E = 210e9
_DEMO_NU = 0.30

# Tag del MeshCanvas para los dibujos M3 (highlight del elem seleccionado).
_TAG = "edu_m3"

# Colores del dial físico (estética CAD: arco oscuro + fill cromático).
_DIAL_TRACK   = "#3a3a55"
_DIAL_FILL_OK = "#0d6efd"
_DIAL_KNOB    = "#ffd54f"


class ConstitutiveModule(CanvasOverlayModule):
    """M3 en modo Overlay: matriz D con toggle Fórmula/Valores + dial ν.

    NO contiene comparación TP/DP — el caso plano viene del project.
    """

    TITLE = "③  Matriz constitutiva D  (σ = D · ε)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 480
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = True

    NU_MIN = 0.00
    NU_MAX = 0.499   # Asintota numerica en DP — no llegamos a 0.5 exacto

    def __init__(self, main_window, project, element_id):
        # Estado actual: E, ν, nombre del material en uso. Se RESUELVEN
        # al construir desde el elemento + materials del project. El dial
        # de Poisson modifica self._nu para visualizar la sensibilidad,
        # pero NO muta el material en el project.
        self._E, self._nu_default, self._mat_name = self._resolve_material(
            project, element_id
        )
        self._nu = self._nu_default
        self._toggle: Optional[FormulaValueToggle] = None
        self._dial_canvas: Optional[tk.Canvas] = None
        self._lbl_material: Optional[ttk.Label] = None
        self._lbl_warning: Optional[ttk.Label] = None
        self._badge_lbl: Optional[ttk.Label] = None
        super().__init__(main_window, project, element_id)

    # ── Resolución de material ─────────────────────────────────────
    @staticmethod
    def _resolve_material(project, element_id):
        if project is None:
            return _DEMO_E, _DEMO_NU, "demo (sin proyecto)"
        elem = (project.elements.get(element_id)
                if element_id is not None else None)
        if elem is not None:
            mat = project.materials.get(getattr(elem, "material_name", None))
            if mat is not None:
                return float(mat.E), float(mat.nu), mat.name
        mats = (list(project.materials.values())
                if project.materials else [])
        if mats:
            return float(mats[0].E), float(mats[0].nu), \
                   f"{mats[0].name} (fallback)"
        return _DEMO_E, _DEMO_NU, "demo (sin materiales)"

    # ── Análisis vigente leído del project (sin selector local) ────
    @property
    def analysis_case(self) -> str:
        if self.project is not None:
            at = getattr(self.project, "analysis_type", None)
            if at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
                return at
        return ANALYSIS_PLANE_STRESS

    def _case_label(self) -> str:
        return ("Tensión Plana" if self.analysis_case == ANALYSIS_PLANE_STRESS
                else "Deformación Plana")

    # ── Construcción del overlay ───────────────────────────────────
    def build_overlay(self, body):
        # Banner: caso plano vigente (read-only). Cambiarlo es Modelo ▸
        # Tipo de Análisis — el overlay sólo refleja.
        banner = ttk.Frame(body)
        banner.pack(fill="x", pady=(0, 6))
        self._badge_lbl = ttk.Label(
            banner,
            text=f"Caso vigente: {self._case_label()}    ·    "
                  f"(cambiarlo: Modelo ▸ Tipo de Análisis)",
            font=("Segoe UI", 9, "bold"),
            foreground="#90caf9",
        )
        self._badge_lbl.pack(anchor="w")

        # Material del elemento bajo análisis (read-only)
        self._lbl_material = ttk.Label(
            body, text="", font=("Consolas", 9),
            foreground="#cfd2d8", justify="left",
        )
        self._lbl_material.pack(anchor="w", pady=(0, 4))
        self._refresh_material_label()

        ttk.Label(
            body,
            text="Click en otro elemento del canvas → cambia el material.",
            font=("Segoe UI", 8), foreground="#9e9e9e",
        ).pack(anchor="w", pady=(0, 6))

        ttk.Separator(body).pack(fill="x", pady=(0, 6))

        # ── Dial de Poisson (control físico cinético) ───────────────
        ttk.Label(
            body, text="ν  (Poisson)",
            font=("Segoe UI", 10, "bold"),
            foreground="#dcdcdc",
        ).pack(anchor="w")

        dial_frame = ttk.Frame(body)
        dial_frame.pack(fill="x", pady=(2, 6))

        self._dial_canvas = tk.Canvas(
            dial_frame, width=120, height=120,
            bg="#222233", highlightthickness=0,
        )
        self._dial_canvas.pack(side="left", padx=(0, 10))

        # Slider lineal abajo del dial: redundancia útil para precisión.
        slider_col = ttk.Frame(dial_frame)
        slider_col.pack(side="left", fill="x", expand=True)

        self._var_nu = tk.DoubleVar(value=self._nu)
        ttk.Scale(
            slider_col, from_=self.NU_MIN, to=self.NU_MAX,
            orient="horizontal", variable=self._var_nu,
            command=lambda _v: self._on_nu_changed(),
        ).pack(fill="x")
        self._lbl_nu = ttk.Label(
            slider_col, text="", font=("Consolas", 11, "bold"),
            foreground="#ffd54f",
        )
        self._lbl_nu.pack(anchor="w", pady=(2, 0))

        # Drag interactivo en el dial: click + arrastrar para barrer ν
        self._dial_canvas.bind("<ButtonPress-1>", self._on_dial_press)
        self._dial_canvas.bind("<B1-Motion>", self._on_dial_drag)

        # Botón "Reset al ν del material"
        ttk.Button(
            slider_col, text="↺ Reset al ν del material",
            bootstyle="secondary-outline-toolbutton",
            command=self._reset_nu_to_material,
        ).pack(anchor="w", pady=(4, 0))

        # Warning de locking (vacío inicialmente)
        self._lbl_warning = ttk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            foreground=HEALTH_ERROR_COLOR, wraplength=440, justify="left",
        )
        self._lbl_warning.pack(anchor="w", pady=(0, 4))

        ttk.Separator(body).pack(fill="x", pady=(2, 4))

        # ── Toggle Fórmula ↔ Valores (requerimiento del usuario) ──
        self._toggle = FormulaValueToggle(
            body,
            render_formula=self._render_d_formula,
            render_values=self._render_d_values,
            initial=FormulaValueToggle.MODE_VALUES,
            figsize=(5.4, 2.6),
            dpi=100,
        )
        self._toggle.pack(fill="both", expand=True)

        # Update inicial del dial y del label de ν
        self._refresh_nu_widgets()

    # ── Capa educativa: highlight del elemento seleccionado ────────
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if self.element is None or self.project is None:
            return
        # Dibujar contorno amarillo grueso sobre el elemento bajo análisis.
        # Reusa los corners macro (Q4/Q9 trato igual).
        try:
            corners = self.element.node_ids[:4]
            pts = []
            for nid in corners:
                node = self.project.nodes.get(nid)
                if node is None:
                    return
                sx, sy = mesh.world_to_screen(node.x, node.y)
                pts.extend([sx, sy])
            if len(pts) < 8:
                return
            mesh.canvas.create_polygon(
                *pts,
                outline="#ffd54f", fill="", width=3.0, tags=_TAG,
            )
            # Label "D-> En" centrado al interior
            cx = sum(pts[::2]) / 4
            cy = sum(pts[1::2]) / 4
            mesh.canvas.create_text(
                cx, cy - 16, text=f"D ▸ E{self.element_id}",
                fill="#ffd54f", font=("Consolas", 10, "bold"),
                tags=_TAG,
            )
        except Exception:
            pass

    # ── Click en otro elemento → cambiar material ──────────────────
    def on_element_selected(self, elem_id):
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = (self.project.elements.get(elem_id)
                         if self.project else None)
        self._E, self._nu_default, self._mat_name = self._resolve_material(
            self.project, elem_id
        )
        # Si el alumno había desplazado el dial, conservamos el offset
        # respecto al ν del material previo: lo más pedagógico es resetear
        # al ν del nuevo material (es lo que ese material realmente es).
        self._nu = self._nu_default
        self._refresh_material_label()
        self._refresh_nu_widgets()
        self._toggle.refresh()
        self._mesh.redraw()

    # ── Dial: lógica de ángulo ↔ ν ─────────────────────────────────
    # El dial barre 270° (de 135° a -135° en sentido horario, pasando por
    # 0° arriba). ν=0 → ángulo bajo izq, ν=NU_MAX → ángulo bajo der.
    DIAL_CX = 60
    DIAL_CY = 64
    DIAL_R  = 44

    def _angle_for_nu(self, nu: float) -> float:
        """Ángulo en grados (matplotlib-style: 0=este, 90=norte) para un ν."""
        t = (nu - self.NU_MIN) / (self.NU_MAX - self.NU_MIN)
        # 225° (abajo-izq) → -45° (abajo-der), barriendo 270° por arriba.
        return 225.0 - 270.0 * t

    def _nu_for_pointer(self, x: float, y: float) -> float:
        dx = x - self.DIAL_CX
        dy = -(y - self.DIAL_CY)  # tk-y va hacia abajo, invertimos
        ang = math.degrees(math.atan2(dy, dx))  # -180..180
        # Mapear cualquier ángulo al rango válido [225, -45] en sentido CW.
        # Normalizamos a 0..360 para facilitar comparación.
        ang_360 = (ang + 360) % 360
        # Rango angular activo: 225° (= 225) → 360° → 90° (= -45° + 360 - 90)
        # Más fácil: definimos start=225, sweep=270 en sentido horario.
        start = 225.0
        sweep = 270.0
        # delta CW desde start
        delta_cw = (start - ang_360) % 360
        if delta_cw > sweep:
            # Click fuera del arco activo: clampear al extremo más cercano.
            return self.NU_MAX if delta_cw < (360 - (sweep / 2 + 45)) \
                                else self.NU_MIN
        t = delta_cw / sweep
        return self.NU_MIN + t * (self.NU_MAX - self.NU_MIN)

    def _on_dial_press(self, event):
        nu = self._nu_for_pointer(event.x, event.y)
        self._set_nu(nu)

    def _on_dial_drag(self, event):
        nu = self._nu_for_pointer(event.x, event.y)
        self._set_nu(nu)

    def _on_nu_changed(self):
        try:
            self._set_nu(float(self._var_nu.get()))
        except (tk.TclError, ValueError):
            pass

    def _set_nu(self, nu: float):
        nu = max(self.NU_MIN, min(self.NU_MAX, float(nu)))
        if abs(nu - self._nu) < 1e-5:
            return
        self._nu = nu
        # Actualizar slider sin disparar callback en bucle
        try:
            self._var_nu.set(self._nu)
        except tk.TclError:
            pass
        self._refresh_nu_widgets()
        if self._toggle is not None:
            self._toggle.refresh()

    def _reset_nu_to_material(self):
        self._set_nu(self._nu_default)

    # ── Refresh widgets reactivos ───────────────────────────────────
    def _refresh_nu_widgets(self):
        # Label numérico bajo el slider
        if self._lbl_nu is not None:
            self._lbl_nu.configure(text=f"ν = {self._nu:.4f}")
        # Warning de volumetric locking (solo en DP cuando ν → 0.5)
        if self._lbl_warning is not None:
            warn = self._compute_locking_warning()
            self._lbl_warning.configure(
                text=warn["text"], foreground=warn["color"],
            )
        # Redibujar dial
        self._draw_dial()

    def _compute_locking_warning(self) -> dict:
        """Retorna {text, color} según la cercanía a la singularidad.

        En DP, D depende de 1/((1+ν)(1-2ν)). Cuando ν→0.5 el módulo
        volumétrico se va a infinito (volumetric locking). En TP no hay
        singularidad pero ν > 0.49 es físicamente extraño igual.
        """
        if self.analysis_case == ANALYSIS_PLANE_STRAIN:
            if self._nu >= 0.495:
                return {
                    "text": ("⚠ Locking volumétrico: en DP, ν → 0.5 hace que "
                              "1/(1−2ν) → ∞. La matriz D explota — los "
                              "elementos no pueden representar materiales "
                              "incompresibles sin formulación especial."),
                    "color": HEALTH_ERROR_COLOR,
                }
            if self._nu >= 0.48:
                return {
                    "text": ("⚠ Cerca de la singularidad de DP (ν → 0.5). "
                              "Los términos diagonales de D crecen rápidamente."),
                    "color": HEALTH_WARNING_COLOR,
                }
        return {"text": "", "color": HEALTH_OK_COLOR}

    def _draw_dial(self):
        c = self._dial_canvas
        if c is None:
            return
        c.delete("all")
        cx, cy, r = self.DIAL_CX, self.DIAL_CY, self.DIAL_R

        # Track (arco completo de 270°)
        bbox = (cx - r, cy - r, cx + r, cy + r)
        c.create_arc(*bbox, start=-45, extent=-270, style="arc",
                     outline=_DIAL_TRACK, width=10)

        # Fill (parte cubierta por ν actual). Color depende del warning.
        warn = self._compute_locking_warning()
        if warn["color"] == HEALTH_ERROR_COLOR:
            fill_color = HEALTH_ERROR_COLOR
        elif warn["color"] == HEALTH_WARNING_COLOR:
            fill_color = HEALTH_WARNING_COLOR
        else:
            fill_color = _DIAL_FILL_OK

        # Tk arc: start counterclockwise from east (0°) hacia 90° = norte.
        # Queremos llenar desde 225° (abajo-izq) hacia el ángulo actual,
        # en sentido horario. Tk usa extent NEGATIVO para CW.
        t = (self._nu - self.NU_MIN) / (self.NU_MAX - self.NU_MIN)
        sweep_now = -270.0 * t
        if abs(sweep_now) > 0.5:
            c.create_arc(*bbox, start=225, extent=sweep_now,
                         style="arc", outline=fill_color, width=10)

        # Knob (pequeño círculo amarillo en la posición actual)
        ang = math.radians(self._angle_for_nu(self._nu))
        kx = cx + r * math.cos(ang)
        ky = cy - r * math.sin(ang)  # invert y
        c.create_oval(kx - 7, ky - 7, kx + 7, ky + 7,
                       fill=_DIAL_KNOB, outline="#fff", width=1.5)

        # Label central
        c.create_text(cx, cy - 4, text=f"{self._nu:.3f}",
                       fill="#dcdcdc",
                       font=("Consolas", 14, "bold"))
        c.create_text(cx, cy + 14, text="ν",
                       fill="#9e9e9e",
                       font=("Segoe UI", 10, "italic"))

        # Marcadores de los extremos
        c.create_text(cx - r - 6, cy + r + 2, text="0",
                       fill="#9e9e9e", font=("Consolas", 8))
        c.create_text(cx + r + 6, cy + r + 2, text="0.5",
                       fill="#ef5350", font=("Consolas", 8, "bold"))

    def _refresh_material_label(self):
        if self._lbl_material is None:
            return
        eid = self.element_id if self.element_id is not None else "—"
        self._lbl_material.configure(
            text=(f"Elemento E{eid}  ·  Material '{self._mat_name}'\n"
                   f"E = {self._E:.3e} Pa")
        )

    # ── Render del toggle ───────────────────────────────────────────
    def _render_d_formula(self, ax):
        # Renderizamos la matriz simbolica como matriz de strings, con
        # prefijo mathtext que contiene el factor escalar (E/(1-nu^2) etc.).
        # render_matrix_latex acepta cells de tipo str y los renderiza
        # con fuente monospace + corchetes. mathtext NO soporta bmatrix
        # asi que el rendering manual es la unica via robusta.
        if self.analysis_case == ANALYSIS_PLANE_STRESS:
            cells = [
                ["1",  "ν",  "0"],
                ["ν",  "1",  "0"],
                ["0",  "0",  "(1-ν)/2"],
            ]
            prefix = r"\mathbf{D}_{TP}=\dfrac{E}{1-\nu^{2}}\,"
        else:
            cells = [
                ["1-ν", "ν",   "0"],
                ["ν",   "1-ν", "0"],
                ["0",   "0",   "(1-2ν)/2"],
            ]
            prefix = r"\mathbf{D}_{DP}=\dfrac{E}{(1+\nu)(1-2\nu)}\,"
        render_matrix_latex(
            ax, cells, fontsize=12, color="#dcdcdc", prefix=prefix,
        )

    def _render_d_values(self, ax):
        try:
            D = constitutive_matrix(self._E, self._nu, self.analysis_case)
        except Exception as exc:
            ax.text(0.5, 0.5, f"Error: {exc}",
                     ha="center", va="center",
                     color="#e74c3c", fontsize=10,
                     transform=ax.transAxes)
            return
        scale, prefix_sci = self._scale_factor(D)
        Dn = D / scale
        prefix = self._latex_prefix(prefix_sci)
        title = (f"{self._case_label()}  ·  "
                  f"E = {self._E:.2e} Pa  ·  ν = {self._nu:.3f}")
        render_matrix_latex(
            ax, Dn, fmt="{:+.3f}", fontsize=12, color="#dcdcdc",
            title=title, prefix=prefix,
        )

    @staticmethod
    def _scale_factor(D: np.ndarray):
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
