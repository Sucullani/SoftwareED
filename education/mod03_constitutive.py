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
    FormulaValueBlocksToggle, LatexMatrixImage,
)

from fem.constitutive import constitutive_matrix
from config.settings import (
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
    EDU_AXES_BG,
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
        self._toggle: Optional[FormulaValueBlocksToggle] = None
        self._dial_canvas: Optional[tk.Canvas] = None
        self._entry_nu: Optional[ttk.Entry] = None
        self._var_nu: Optional[tk.StringVar] = None
        self._poisson_canvas: Optional[tk.Canvas] = None
        self._lbl_warning: Optional[ttk.Label] = None
        # Widgets LatexMatrixImage (live-update via set_matrix)
        self._mat_formula: Optional[LatexMatrixImage] = None
        self._mat_values: Optional[LatexMatrixImage] = None
        self._lbl_values_title: Optional[tk.Label] = None
        # Caso plano del ultimo render del panel de formula — para detectar
        # cambio TP<->DP y rebuild de la matriz simbolica (cells distintas).
        self._formula_case_rendered: Optional[str] = None
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

    # ── Construcción del overlay (compacto UX 2026) ───────────────
    def build_overlay(self, body):
        # Sin badge "caso vigente" (el alumno ya lo definió en Modelo).
        # Sin label de material / E (igual). Sin instrucción "click en
        # otro elemento" — el panel de módulos ya muestra qué elemento
        # opera. La cinética del dial + el toggle f/v cuentan la historia.

        # ── Dial de Poisson ────────────────────────────────────────
        ttk.Label(
            body, text="ν  (Poisson)",
            font=("Segoe UI", 10, "bold"),
            foreground="#dcdcdc",
        ).pack(anchor="w")

        dial_frame = ttk.Frame(body)
        dial_frame.pack(fill="x", pady=(2, 6))

        self._dial_canvas = tk.Canvas(
            dial_frame, width=120, height=120,
            bg=EDU_AXES_BG, highlightthickness=0,
            cursor="hand2",
        )
        self._dial_canvas.pack(side="left", padx=(0, 10))

        # Entry numérico al lado del dial: el dial da la metáfora física
        # (rango [0, 0.5] visible de un vistazo + valor centrado), el Entry
        # permite tipear un valor exacto con teclado. Una sola lectura
        # ("0.250" centrado en el dial) + un solo input (Entry). Sin slider
        # ni label numérico redundantes.
        side_col = ttk.Frame(dial_frame)
        side_col.pack(side="left", fill="x", expand=True)

        entry_row = ttk.Frame(side_col)
        entry_row.pack(anchor="w", pady=(12, 0))
        ttk.Label(
            entry_row, text="ν =", font=("Consolas", 11, "bold"),
            foreground="#9e9e9e",
        ).pack(side="left", padx=(0, 4))
        self._var_nu = tk.StringVar(value=f"{self._nu:.4f}")
        self._entry_nu = ttk.Entry(
            entry_row, textvariable=self._var_nu, width=8,
            font=("Consolas", 11, "bold"), justify="center",
        )
        self._entry_nu.pack(side="left")
        # Commit en Enter o al salir del foco; mientras tipea no dispara
        # (evita oscilaciones del dial a cada tecla).
        self._entry_nu.bind("<Return>",   lambda _e: self._on_nu_entry_commit())
        self._entry_nu.bind("<KP_Enter>", lambda _e: self._on_nu_entry_commit())
        self._entry_nu.bind("<FocusOut>", lambda _e: self._on_nu_entry_commit())

        # Drag interactivo en el dial: click + arrastrar para barrer ν
        self._dial_canvas.bind("<ButtonPress-1>", self._on_dial_press)
        self._dial_canvas.bind("<B1-Motion>", self._on_dial_drag)

        # Botón "Reset al ν del material"
        ttk.Button(
            side_col, text="↺ Reset al ν del material",
            bootstyle="secondary-outline-toolbutton",
            command=self._reset_nu_to_material,
        ).pack(anchor="w", pady=(6, 0))

        # Warning de locking (vacío inicialmente)
        self._lbl_warning = ttk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            foreground=HEALTH_ERROR_COLOR, wraplength=440, justify="left",
        )
        self._lbl_warning.pack(anchor="w", pady=(0, 4))

        # ── Probe físico: ν NO es un número abstracto, es la contracción
        # lateral del material bajo tracción uniaxial. El alumno aplica
        # mentalmente σx=1 y ve cómo el cuadrado se DEFORMA en tiempo
        # real al mover el dial. Conecta la matriz D con el fenómeno
        # físico (efecto Poisson) que da nombre a la constante. Materiales
        # de referencia coloreados (corcho ν≈0, acero ν≈0.3, caucho ν≈0.49)
        # anclan el rango numérico a la intuición.
        probe_frame = ttk.Frame(body)
        probe_frame.pack(fill="x", pady=(0, 2))
        ttk.Label(
            probe_frame,
            text="Efecto Poisson — respuesta a tracción uniaxial  σx = 1:",
            font=("Segoe UI", 8, "italic"), foreground="#9e9e9e",
        ).pack(anchor="w")
        self._poisson_canvas = tk.Canvas(
            probe_frame, width=440, height=110,
            bg=EDU_AXES_BG, highlightthickness=0,
        )
        self._poisson_canvas.pack(fill="x")

        ttk.Separator(body).pack(fill="x", pady=(2, 4))

        # ── Toggle Fórmula ↔ Valores (Tk frames + LatexMatrixImage) ──
        # Mismo patron que M4: cada panel pobla widgets Tk, la matriz se
        # actualiza via set_matrix (sin re-render de axes). Render
        # matplotlib-nativo via mathtext mathmode dentro del widget.
        self._toggle = FormulaValueBlocksToggle(
            body,
            build_formula=self._build_formula_panel,
            build_values=self._build_values_panel,
            initial=FormulaValueBlocksToggle.MODE_VALUES,
        )
        self._toggle.pack(fill="both", expand=True)

        # Cross-reference clickeable: D entra en el integrando de k_e.
        self._pack_crossref(
            body, "mod05",
            "👉 Esta D entra en  k_e = ∫ BᵀDB |det J| t  (ver ⑤ Matriz K_e).",
            wraplength=440,
        )

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
        # Resetear al ν del nuevo material — es lo que ese material es.
        self._nu = self._nu_default
        self._refresh_nu_widgets()
        self._refresh_d_widgets()
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

    def _on_nu_entry_commit(self):
        """Commit del Entry: parsea, clampa, propaga al dial. Si el texto
        no es numérico, revierte al último valor válido sin disparar."""
        raw = self._var_nu.get().strip().replace(",", ".")
        try:
            v = float(raw)
        except (ValueError, tk.TclError):
            # Revert al valor actual válido (formato canónico).
            try:
                self._var_nu.set(f"{self._nu:.4f}")
            except tk.TclError:
                pass
            return
        self._set_nu(v)

    def _set_nu(self, nu: float):
        nu = max(self.NU_MIN, min(self.NU_MAX, float(nu)))
        if abs(nu - self._nu) < 1e-5:
            return
        self._nu = nu
        self._refresh_nu_widgets()
        self._refresh_d_widgets()

    def _reset_nu_to_material(self):
        self._set_nu(self._nu_default)

    # ── Refresh widgets reactivos ───────────────────────────────────
    def _refresh_nu_widgets(self):
        # Escribir el StringVar del Entry (única fuente textual de ν).
        # No disparamos callback porque el bind es a <Return>/<FocusOut>,
        # no a un trace del StringVar.
        if self._var_nu is not None:
            try:
                self._var_nu.set(f"{self._nu:.4f}")
            except tk.TclError:
                pass
        # Warning de volumetric locking (solo en DP cuando ν → 0.5)
        if self._lbl_warning is not None:
            warn = self._compute_locking_warning()
            self._lbl_warning.configure(
                text=warn["text"], foreground=warn["color"],
            )
        # Redibujar dial + probe físico (ambos cambian con ν)
        self._draw_dial()
        self._draw_poisson_probe()

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

    # ── Probe físico del efecto Poisson ─────────────────────────────
    # Materiales canónicos de referencia (ν, nombre, color del chip).
    # El alumno reconoce el material por la posición del ν en el dial
    # y por el COMPORTAMIENTO visible del cuadrado deformado.
    _MAT_REFS = (
        (0.00, "corcho",            "#80deea"),
        (0.20, "hormigón",          "#90caf9"),
        (0.30, "acero",             "#a5d6a7"),
        (0.35, "aluminio",          "#fff176"),
        (0.45, "polímero blando",   "#ffb74d"),
        (0.49, "caucho (cuasi-inc)","#ef9a9a"),
    )
    _PROBE_VIS_SCALE = 4.0   # exageración visual de la deformación

    def _draw_poisson_probe(self):
        """Cuadrado de material que se deforma según ν bajo σx=1 (TP).

        Para tensión plana con σx=1, σy=0, τxy=0:
            ε = D⁻¹ σ  →  εx = 1/E,  εy = -ν/E,  γxy = 0

        Lo que importa pedagógicamente es el RATIO εy/εx = -ν — el alumno
        ve directamente "cuánto se contrae el material lateralmente por
        cada unidad de estiramiento". Para ν=0 no hay contracción
        (corcho); para ν=0.49 la contracción es casi total (caucho).
        """
        c = self._poisson_canvas
        if c is None:
            return
        c.delete("all")

        W, H = 440, 110
        side = 64
        # Centro del cuadrado: corrido a la izquierda para dejar espacio
        # a las flechas σ y a la escala lateral de materiales.
        cx = 150
        cy = H // 2 - 6

        # Cuadrado de referencia (sin deformar) — punteado gris.
        half = side // 2
        c.create_rectangle(
            cx - half, cy - half, cx + half, cy + half,
            outline="#5a5a6e", width=1, dash=(2, 3),
        )

        nu = self._nu
        # Estiramiento normalizado a "1 unidad de ε" y exagerado por
        # _PROBE_VIS_SCALE para que el efecto sea visible en pantalla
        # con un dial de baja sensibilidad (ν~0.25 produciría 3 px sin
        # exagerar). El RATIO entre εx y εy se preserva — es lo único
        # que importa para enseñar Poisson.
        s = self._PROBE_VIS_SCALE
        dx = half * (1.0 + 0.25 * s)             # estiramiento horizontal fijo
        dy = half * (1.0 - 0.25 * s * nu)        # contracción vertical ∝ ν

        # Color del cuadrado deformado según el régimen de Poisson.
        # Mapping ergonómico: cuanto más se contrae, más cálido el color.
        if nu >= 0.475:
            col_fill = "#ef5350"
        elif nu >= 0.40:
            col_fill = "#ffb74d"
        elif nu >= 0.20:
            col_fill = "#4fc3f7"
        else:
            col_fill = "#80deea"

        c.create_rectangle(
            cx - dx, cy - dy, cx + dx, cy + dy,
            outline=col_fill, width=2.4, fill=col_fill, stipple="gray25",
        )

        # Flechas de tracción σx aplicadas en los bordes verticales del
        # cuadrado DEFORMADO (siguen al cuadrado al estirarse).
        arrow_len = 26
        c.create_line(
            cx - dx - arrow_len - 4, cy, cx - dx - 4, cy,
            fill="#ffffff", arrow=tk.LAST, width=2,
        )
        c.create_line(
            cx + dx + 4, cy, cx + dx + arrow_len + 4, cy,
            fill="#ffffff", arrow=tk.LAST, width=2,
        )
        c.create_text(
            cx - dx - arrow_len // 2 - 4, cy - 12,
            text="σx", fill="#ffffff",
            font=("Consolas", 9, "bold"),
        )
        c.create_text(
            cx + dx + arrow_len // 2 + 4, cy - 12,
            text="σx", fill="#ffffff",
            font=("Consolas", 9, "bold"),
        )

        # Indicador de contracción lateral: brackets ↑↓ junto al lado
        # derecho del cuadrado mostrando la altura final < original.
        # Es la lectura clave: el alumno mide visualmente "cuánto se
        # contrajo" y lo asocia con el valor de ν.
        bracket_x = cx + dx + arrow_len + 18
        c.create_line(
            bracket_x, cy - dy, bracket_x, cy + dy,
            fill="#dcdcdc", width=1.6,
        )
        c.create_line(
            bracket_x - 4, cy - dy, bracket_x + 4, cy - dy,
            fill="#dcdcdc", width=1.6,
        )
        c.create_line(
            bracket_x - 4, cy + dy, bracket_x + 4, cy + dy,
            fill="#dcdcdc", width=1.6,
        )
        # Ratio explícito (la fórmula clave)
        c.create_text(
            bracket_x + 10, cy,
            text=f"εy/εx\n= {-nu:+.3f}",
            fill="#dcdcdc", font=("Consolas", 9, "bold"),
            anchor="w", justify="left",
        )

        # Mini-escala de materiales canónicos: una regla en la base del
        # canvas con tics en los ν de referencia + marker triangular del
        # ν actual deslizándose. Anclajes mnemónicos (corcho, acero,
        # caucho) que estabilizan el aprendizaje del rango.
        rule_y = H - 12
        rule_x0 = 16
        rule_x1 = W - 16
        c.create_line(
            rule_x0, rule_y, rule_x1, rule_y,
            fill="#5a5a6e", width=1.2,
        )
        # Tics de los materiales de referencia
        for nu_ref, name, col_ref in self._MAT_REFS:
            t = nu_ref / self.NU_MAX
            tx = rule_x0 + t * (rule_x1 - rule_x0)
            c.create_line(
                tx, rule_y - 3, tx, rule_y + 3,
                fill=col_ref, width=1.6,
            )
            c.create_text(
                tx, rule_y - 9,
                text=name, fill=col_ref,
                font=("Consolas", 7), anchor="s",
            )
        # Marker triangular del ν actual sobre la regla.
        t_now = nu / self.NU_MAX
        mx = rule_x0 + t_now * (rule_x1 - rule_x0)
        c.create_polygon(
            mx, rule_y + 1,
            mx - 5, rule_y + 9,
            mx + 5, rule_y + 9,
            fill=col_fill, outline="#ffffff", width=1,
        )

    # ── Builders del toggle (Tk widgets, no axes compartido) ───────
    @staticmethod
    def _d_formula_cells_and_prefix(case: str):
        r"""Cells `\dfrac{...}{...}` y prefijo escalar para la fórmula
        simbólica de D según el caso plano. Centralizado para que el
        builder inicial y el rebuild on case-change usen la misma
        verdad."""
        if case == ANALYSIS_PLANE_STRESS:
            cells = [
                ["1",      r"\nu",  "0"],
                [r"\nu",   "1",     "0"],
                ["0",      "0",     r"\dfrac{1-\nu}{2}"],
            ]
            prefix = r"\mathbf{D}_{TP}=\dfrac{E}{1-\nu^{2}}\,"
        else:
            cells = [
                [r"1-\nu", r"\nu",   "0"],
                [r"\nu",   r"1-\nu", "0"],
                ["0",      "0",      r"\dfrac{1-2\nu}{2}"],
            ]
            prefix = r"\mathbf{D}_{DP}=\dfrac{E}{(1+\nu)(1-2\nu)}\,"
        return cells, prefix

    def _build_formula_panel(self, frame) -> None:
        """Panel de la fórmula simbólica D(E, ν, caso) como LatexMatrixImage."""
        case = self.analysis_case
        cells, prefix = self._d_formula_cells_and_prefix(case)
        self._mat_formula = LatexMatrixImage(
            frame, matrix=cells, fmt="{}", fontsize=15,
            prefix=prefix, cache_values=True,
        )
        self._mat_formula.pack(anchor="center", pady=(6, 6))
        self._formula_case_rendered = case

    def _build_values_panel(self, frame) -> None:
        """Panel de valores numéricos de D — matriz live-update via
        `set_matrix` cuando ν cambia."""
        from config.settings import EDU_AXES_BG
        self._lbl_values_title = tk.Label(
            frame, text=f"ν = {self._nu:.3f}", bg=EDU_AXES_BG, fg="#dcdcdc",
            font=("Consolas", 9, "bold"), anchor="center",
        )
        self._lbl_values_title.pack(fill="x", pady=(2, 2))
        try:
            D = constitutive_matrix(self._E, self._nu, self.analysis_case)
        except Exception:
            D = np.zeros((3, 3))
        scale, prefix_sci = self._scale_factor(D)
        Dn = D / scale
        prefix = self._latex_prefix(prefix_sci)
        self._mat_values = LatexMatrixImage(
            frame, matrix=Dn, fmt="{:.3f}", fontsize=15,
            prefix=prefix, cache_values=False,
        )
        self._mat_values.pack(anchor="center", pady=(0, 6))

    def _refresh_d_widgets(self) -> None:
        """Re-renderiza valores (siempre, cambia con ν) y fórmula (solo
        si cambió el caso TP↔DP)."""
        case = self.analysis_case
        # Valores: la matriz cambia con cada ν o cambio de material.
        if self._mat_values is not None:
            try:
                D = constitutive_matrix(self._E, self._nu, case)
                scale, prefix_sci = self._scale_factor(D)
                Dn = D / scale
                prefix = self._latex_prefix(prefix_sci)
                self._mat_values.set_matrix(Dn, prefix=prefix)
            except Exception:
                pass
        if self._lbl_values_title is not None:
            try:
                self._lbl_values_title.configure(text=f"ν = {self._nu:.3f}")
            except tk.TclError:
                pass
        # Fórmula: solo si cambió TP↔DP (re-mount de cells distintas).
        if self._mat_formula is not None and case != self._formula_case_rendered:
            try:
                cells, prefix = self._d_formula_cells_and_prefix(case)
                self._mat_formula.set_matrix(cells, prefix=prefix)
                self._formula_case_rendered = case
            except Exception:
                pass

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
