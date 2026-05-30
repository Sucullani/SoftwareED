"""
Módulo 3 — Matriz constitutiva D (TP / DP)

    σ = D · ε     con D = D(E, ν, caso plano)

Modo Overlay sobre el MeshCanvas compartido.

Override explícito del usuario respecto a la propuesta UX original:

    "M3 utiliza también un overlay que no esté embebido en el panel
     lateral; no compares TP/DP ya que esto está en el menú principal."

Diseño actual ("Espectro de Poisson", rediseño 2026-05):
    1. NO abre Toplevel ni vive embebido en proc_tab. Activa un overlay
       flotante (~480 px) sobre el MeshCanvas compartido.
    2. El elemento bajo análisis se ELIGE POR CLICK en el canvas — el
       overlay refleja la D del material asignado a ese elemento (highlight
       amarillo automático del MeshCanvas).
    3. Toggle Fórmula ↔ Valores (requerimiento del usuario): la fórmula
       simbólica D(E,ν, caso) en LaTeX, los valores la matriz 3×3 evaluada
       con la ν actual del espectro.
    4. UN SOLO control de ν: el "espectro de Poisson", una barra horizontal
       interactiva [0 .. 0.5] que fusiona — en un único widget — el antiguo
       dial circular, la regla de materiales de referencia, el botón Reset
       y el dropdown de presets. Cada material canónico (corcho ν≈0, acero
       ν≈0.3, caucho ν≈0.49) es un ancla clickeable; arrastrar barre el
       continuo; el ◆ dorado marca el ν del material real del elemento
       ("tu material") y tocarlo equivale al antiguo Reset. ν se muestra UNA
       sola vez (lectura bajo el espectro). En DP, la zona ν → 0.5 del track
       se sombrea en rojo (volumetric locking) y el overlay muestra el aviso.
    5. Sin botones para TP/DP. El caso plano se LEE del project — para
       cambiarlo el usuario va a Modelo ▸ Tipo de Análisis. Una sola fuente
       de verdad.

Sandbox explícito: mover el espectro NO muta el material del project — el
micro-rótulo lo aclara, reemplazando la semántica del ex-botón "Reset al ν
del material" (que sugería edición).
"""

from __future__ import annotations

from typing import Optional

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
    EDU_AXES_BG, EDU_FG, EDU_FG_MUTED, CANVAS_NODE_COLOR,
)


# Defaults usados solo si el proyecto no tiene materiales asignados.
_DEMO_E = 210e9
_DEMO_NU = 0.30

# Tag del MeshCanvas para los dibujos M3 (highlight del elem seleccionado).
_TAG = "edu_m3"

# Colores del espectro (mismo lenguaje cromático que el resto del overlay).
# TODO(hex): _TRACK_COLOR/_TRACK_FILL/_KNOB_COLOR/_HOME_COLOR siguen como
# literales del espectro (identidad visual aprobada). Migrar a config en un
# pase dedicado — _TRACK_FILL == PHASE_PRE_COLOR. Los text-colors del probe y
# del espectro ya usan EDU_FG / EDU_FG_MUTED de config.
_TRACK_COLOR = "#3a3a55"   # track base (sin llenar)
_TRACK_FILL  = "#0d6efd"   # porción 0..ν (estado OK)
_KNOB_COLOR  = "#ffd54f"   # perilla (amarillo highlight)
_HOME_COLOR  = "#ffd54f"   # marcador del ν del material real ("tu material")


class ConstitutiveModule(CanvasOverlayModule):
    """M3 en modo Overlay: matriz D con toggle Fórmula/Valores + espectro ν.

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

    # ── Geometría del espectro (tk.Canvas horizontal) ──────────────
    SPEC_W = 440
    SPEC_H = 94
    SPEC_X0 = 26          # margen izq del track
    SPEC_X1 = 414         # margen der del track (SPEC_W - 26)
    SPEC_Y  = 52          # y del track
    SNAP_PX = 9           # tolerancia de snap a anclas (px)

    # Materiales canónicos de referencia (ν, nombre corto, color del chip).
    # Nombres CORTOS para evitar el solapamiento que tenían "polímero blando"
    # / "caucho (cuasi-inc.)" en la regla vieja. El detalle de incompresible
    # se muestra solo en la lectura bajo la perilla, no en el ancla.
    _MAT_REFS = (
        (0.00, "corcho",   "#80deea"),
        (0.20, "hormigón", "#90caf9"),
        (0.30, "acero",    "#a5d6a7"),
        (0.35, "aluminio", "#fff176"),
        (0.45, "polímero", "#ffb74d"),
        (0.49, "caucho",   "#ef9a9a"),
    )
    _CAUCHO_NOTE = "(cuasi-inc.)"
    # Ganancia visual FIJA del probe (adimensional). Bajo tracción uniaxial
    # σx, εx = σx/E es INDEPENDIENTE de ν → el ancho del probe es CONSTANTE en
    # ν; solo la altura se achata (εy = −ν·εx). El probe usa, contra el
    # cuadrado de referencia side×side:
    #   width  = side·(1 + S)      → FIJO (no depende de ν)
    #   height = side·(1 − S·ν)
    # El ratio de las deformaciones dibujadas es
    #   (Δh/h0)/(Δw/w0) = (−S·ν)/S = −ν  EXACTO (medible con regla),
    # y refleja la física correcta (ancho fijo). El bloque NO parte de un
    # cuadrado en ν=0 y eso es lo CORRECTO: σx siempre elonga (εx>0) una
    # cantidad fija. S magnifica solo la MAGNITUD (εx real = 1/E es ínfimo),
    # NO el ratio. Ver "Refactor 2026-05: M3 — probe".
    _PROBE_VIS_GAIN = 0.6

    def __init__(self, main_window, project, element_id):
        # Estado actual: E, ν, nombre del material en uso. Se RESUELVEN
        # al construir desde el elemento + materials del project. El espectro
        # de Poisson modifica self._nu para visualizar la sensibilidad,
        # pero NO muta el material en el project.
        self._E, self._nu_default, self._mat_name = self._resolve_material(
            project, element_id
        )
        self._nu = self._nu_default
        self._toggle: Optional[FormulaValueBlocksToggle] = None
        self._spectrum_canvas: Optional[tk.Canvas] = None
        self._poisson_canvas: Optional[tk.Canvas] = None
        self._lbl_sandbox: Optional[ttk.Label] = None
        self._lbl_warning: Optional[ttk.Label] = None
        # Widgets LatexMatrixImage (live-update via set_matrix)
        self._mat_formula: Optional[LatexMatrixImage] = None
        self._mat_values: Optional[LatexMatrixImage] = None
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

    def _sandbox_text(self) -> str:
        """Micro-rótulo sandbox (reemplaza la semántica del ex-botón Reset).
        Texto mínimo: el ◆, el material real y el rango ν ∈ [0, ½) se ven en
        el espectro — no se describen en prosa. "isótropo" sí va acá: fija el
        supuesto del modelo (D = D(E, ν) de 2 constantes) sin una línea
        aparte."""
        return ("🧪 Deslizá o tocá un material isótropo — no modifica la D "
                "de tu elemento.")

    # ── Construcción del overlay (compacto UX 2026) ───────────────
    def build_overlay(self, body):
        # Micro-rótulo sandbox (única explicación textual: el resto lo
        # cuentan el espectro interactivo + el probe físico).
        self._lbl_sandbox = ttk.Label(
            body, text=self._sandbox_text(),
            font=("Segoe UI", 8, "italic"), foreground=EDU_FG_MUTED,
            wraplength=440, justify="left",
        )
        self._lbl_sandbox.pack(anchor="w", pady=(0, 3))

        # ── Espectro de Poisson (control único de ν) ────────────────
        self._spectrum_canvas = tk.Canvas(
            body, width=self.SPEC_W, height=self.SPEC_H,
            bg=EDU_AXES_BG, highlightthickness=0, cursor="hand2",
        )
        self._spectrum_canvas.pack(fill="x", pady=(0, 0))
        self._spectrum_canvas.bind("<ButtonPress-1>", self._on_spectrum_press)
        self._spectrum_canvas.bind("<B1-Motion>", self._on_spectrum_drag)

        # (La nota "material isótropo / rango ν ∈ [0, ½)" se fundió en el
        # rótulo sandbox principal + el rango ya lo expresa el espectro —
        # sin línea separada, que era ruido. Ver _sandbox_text.)

        # Warning de locking (vacío salvo DP cerca de 0.5).
        self._lbl_warning = ttk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            foreground=HEALTH_ERROR_COLOR, wraplength=440, justify="left",
        )
        self._lbl_warning.pack(anchor="w", pady=(0, 2))

        # ── Probe físico del efecto Poisson (sin caption: la gráfica habla
        # sola — σx como causa, flechas de contracción ∝ ν como efecto, y el
        # ratio εy/εx = −ν como lectura). La regla de materiales ya NO vive
        # acá (la absorbió el espectro).
        probe_frame = ttk.Frame(body)
        probe_frame.pack(fill="x", pady=(0, 0))
        self._poisson_canvas = tk.Canvas(
            probe_frame, width=440, height=92,
            bg=EDU_AXES_BG, highlightthickness=0,
        )
        self._poisson_canvas.pack(fill="x")

        ttk.Separator(body).pack(fill="x", pady=(2, 3))

        # ── Toggle Fórmula ↔ Valores (Tk frames + LatexMatrixImage) ──
        # Mismo patron que M4: cada panel pobla widgets Tk, la matriz se
        # actualiza via set_matrix (sin re-render de axes).
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

        # Render inicial del espectro + probe + warning.
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
        # (El texto sandbox es estático; solo se mueve el ◆ del espectro, que
        # redibuja _refresh_nu_widgets.)
        self._nu = self._nu_default
        self._refresh_nu_widgets()
        self._refresh_d_widgets()
        self._mesh.redraw()

    # ── Espectro: mapeo x ↔ ν + snap a anclas ──────────────────────
    def _x_for_nu(self, nu: float) -> float:
        t = (nu - self.NU_MIN) / (self.NU_MAX - self.NU_MIN)
        return self.SPEC_X0 + t * (self.SPEC_X1 - self.SPEC_X0)

    def _nu_for_x(self, x: float) -> float:
        t = (x - self.SPEC_X0) / (self.SPEC_X1 - self.SPEC_X0)
        nu = self.NU_MIN + t * (self.NU_MAX - self.NU_MIN)
        return max(self.NU_MIN, min(self.NU_MAX, nu))

    def _snap_candidates(self):
        """Anclas a las que el puntero engancha: materiales + ν del material
        real del elemento (home)."""
        cands = [nu for nu, _, _ in self._MAT_REFS]
        cands.append(self._nu_default)
        return cands

    def _nu_for_pointer_x(self, x: float) -> float:
        nu_free = self._nu_for_x(x)
        best = None
        best_dx = self.SNAP_PX + 1.0
        for c in self._snap_candidates():
            dx = abs(self._x_for_nu(c) - x)
            if dx < best_dx:
                best_dx = dx
                best = c
        if best is not None and best_dx <= self.SNAP_PX:
            return best
        return nu_free

    def _on_spectrum_press(self, event):
        self._set_nu(self._nu_for_pointer_x(event.x))

    def _on_spectrum_drag(self, event):
        self._set_nu(self._nu_for_pointer_x(event.x))

    def _material_at(self, nu: float):
        """Nombre/color del material de referencia si ν coincide (snap), o
        (None, None) si está entre anclas."""
        for nu_ref, name, col in self._MAT_REFS:
            if abs(nu - nu_ref) < 1e-4:
                return name, col
        return None, None

    def _set_nu(self, nu: float):
        nu = max(self.NU_MIN, min(self.NU_MAX, float(nu)))
        if abs(nu - self._nu) < 1e-5:
            return
        self._nu = nu
        self._refresh_nu_widgets()
        self._refresh_d_widgets()

    # ── Refresh widgets reactivos ───────────────────────────────────
    def _refresh_nu_widgets(self):
        # Warning de volumetric locking (solo en DP cuando ν → 0.5).
        if self._lbl_warning is not None:
            warn = self._compute_locking_warning()
            self._lbl_warning.configure(
                text=warn["text"], foreground=warn["color"],
            )
        # Redibujar espectro + probe físico (ambos cambian con ν).
        self._draw_spectrum()
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

    def _state_fill_color(self) -> str:
        """Color de la porción llena del track / perilla según el régimen."""
        warn = self._compute_locking_warning()
        if warn["color"] == HEALTH_ERROR_COLOR:
            return HEALTH_ERROR_COLOR
        if warn["color"] == HEALTH_WARNING_COLOR:
            return HEALTH_WARNING_COLOR
        return _TRACK_FILL

    # ── Dibujo del espectro de Poisson ─────────────────────────────
    def _draw_spectrum(self):
        c = self._spectrum_canvas
        if c is None:
            return
        c.delete("all")
        x0, x1, y = self.SPEC_X0, self.SPEC_X1, self.SPEC_Y
        state_col = self._state_fill_color()

        # Zona de locking (solo DP): sombreado rojo tenue ν ∈ [0.48, 0.5]
        # DETRÁS del track. Unifica el "0.5 es peligroso" con el aviso textual.
        if self.analysis_case == ANALYSIS_PLANE_STRAIN:
            zx0 = self._x_for_nu(0.48)
            c.create_rectangle(
                zx0, y - 8, x1 + 4, y + 8,
                fill=HEALTH_ERROR_COLOR, outline="", stipple="gray25",
            )
            c.create_text(
                (zx0 + x1) / 2, y - 14, text="locking",
                fill=HEALTH_ERROR_COLOR, font=("Consolas", 7, "bold"),
            )

        # Track base + porción llena 0..ν (estética slider).
        c.create_line(x0, y, x1, y, fill=_TRACK_COLOR, width=6,
                      capstyle="round")
        kx = self._x_for_nu(self._nu)
        c.create_line(x0, y, kx, y, fill=state_col, width=6,
                      capstyle="round")

        # Marcadores de extremos del rango.
        c.create_text(x0 - 4, y + 13, text="0", fill=EDU_FG_MUTED,
                      font=("Consolas", 8), anchor="n")
        c.create_text(x1 + 4, y + 13, text="0.5", fill="#ef5350",
                      font=("Consolas", 8, "bold"), anchor="n")

        # Anclas de material: tick + label ESCALONADO (par arriba / impar
        # abajo) para de-saturar la zona ν alta (aluminio/polímero/caucho).
        active_name, _ = self._material_at(self._nu)
        for idx, (nu_ref, name, col) in enumerate(self._MAT_REFS):
            tx = self._x_for_nu(nu_ref)
            ly = 12 if idx % 2 == 0 else 30
            # Conector tenue label→tick.
            c.create_line(tx, ly + 6, tx, y - 5, fill=_TRACK_COLOR, width=1)
            # Tick del color del material.
            c.create_line(tx, y - 5, tx, y + 5, fill=col, width=1.6)
            is_active = (name == active_name)
            c.create_text(
                tx, ly, text=name, fill=col,
                font=("Consolas", 8, "bold" if is_active else "normal"),
                anchor="center",
            )

        # Marcador "home" (ν del material real del elemento). Tocarlo = Reset.
        hx = self._x_for_nu(self._nu_default)
        c.create_polygon(
            hx, y + 7, hx - 5, y + 15, hx + 5, y + 15,
            fill=_HOME_COLOR, outline="#ffffff", width=0.8,
        )

        # Perilla en la posición actual.
        c.create_oval(kx - 8, y - 8, kx + 8, y + 8,
                       fill=_KNOB_COLOR, outline="#ffffff", width=1.6)

        # Lectura ÚNICA de ν (centrada, robusta a clipping). Añade el nombre
        # del material solo cuando ν está enganchado a un ancla.
        txt = f"ν = {self._nu:.3f}"
        nm, _ = self._material_at(self._nu)
        if nm:
            txt += f"   ·   {nm}"
            if nm == "caucho":
                txt += f" {self._CAUCHO_NOTE}"
        c.create_text(
            self.SPEC_W / 2, y + 28, text=txt, fill=EDU_FG,
            font=("Consolas", 11, "bold"), anchor="center",
        )

    # ── Probe físico del efecto Poisson ─────────────────────────────
    def _draw_poisson_probe(self):
        """Material bajo tracción uniaxial: ancho FIJO, alto se achata con ν.

        Bajo tracción uniaxial (σx=1, σy=0, τxy=0) en TP:
            εx = 1/E (NO depende de ν),  εy = -ν/E,  γxy = 0  →  εy/εx = -ν

        Como εx es independiente de ν, el ANCHO del probe es CONSTANTE en ν
        (σx estira siempre lo mismo) y solo la ALTURA se contrae al crecer ν.
        Geometría, contra el cuadrado de referencia side×side:
            width  = side·(1 + S)     → FIJO
            height = side·(1 − S·ν)
        El ratio de las deformaciones DIBUJADAS es
            (Δh/h0)/(Δw/w0) = (−S·ν)/S = −ν  EXACTO
        medible con regla y coincidente con el label. El bloque NO es un
        cuadrado: es un rectángulo estirado horizontalmente (la elongación
        fija de σx) que se achata al subir ν. S magnifica la MAGNITUD (εx
        real = 1/E es ínfimo); el RATIO —lo que enseña D⁻¹— es fiel en la
        geometría y en el número. El cuadrado de referencia punteado es el
        estado SIN carga.

        Layout: el elemento va CENTRADO en el canvas (cx = ancho/2), con las
        flechas σx simétricas y la lectura εy/εx centrada debajo. Los 4 nodos
        de esquina lo identifican como un elemento finito (no un rectángulo
        genérico) y se mueven con la deformación.
        """
        c = self._poisson_canvas
        if c is None:
            return
        c.delete("all")

        W, H = 440, 92
        side = 60            # elemento más grande (antes 48)
        cx = W // 2          # centrado horizontalmente
        cy = 38              # snug: elemento arriba + ratio abajo, sin aire
        half = side // 2

        nu = self._nu
        S = self._PROBE_VIS_GAIN
        dx = half * (1.0 + S)        # ancho FIJO (εx no depende de ν)
        dy = half * (1.0 - S * nu)   # alto se achata ∝ ν

        # Cuadrado de referencia (sin carga) — ancla punteada contra la que se
        # lee la deformación. El bloque deformado SIEMPRE es más ancho (σx lo
        # estira una cantidad fija) y, al subir ν, más bajo.
        c.create_rectangle(
            cx - half, cy - half, cx + half, cy + half,
            outline=EDU_FG_MUTED, width=1.4, dash=(3, 3),
        )

        # Elemento deformado — UN solo color neutro (es GEOMETRÍA, no régimen:
        # el régimen de ν ya lo codifica el espectro de arriba; el rojo acá
        # contradiría que en TP un ν alto NO es patológico).
        c.create_rectangle(
            cx - dx, cy - dy, cx + dx, cy + dy,
            outline=CANVAS_NODE_COLOR, width=2.4,
            fill=CANVAS_NODE_COLOR, stipple="gray25",
        )

        # Nodos de esquina: lo leen como un ELEMENTO FINITO (no un rectángulo
        # genérico) y migran con la deformación.
        nr = 3.0
        for ex in (-dx, dx):
            for ey in (-dy, dy):
                c.create_oval(
                    cx + ex - nr, cy + ey - nr, cx + ex + nr, cy + ey + nr,
                    fill=CANVAS_NODE_COLOR, outline=EDU_AXES_BG,
                )

        # Flechas σx (la CAUSA): tracción uniaxial en los bordes verticales.
        arrow_len = 24
        for sx in (-1, +1):
            x_edge = cx + sx * dx
            c.create_line(
                x_edge + sx * 5, cy, x_edge + sx * (arrow_len + 5), cy,
                fill=EDU_FG, arrow=tk.LAST, width=2,
            )
            c.create_text(
                x_edge + sx * (arrow_len // 2 + 5), cy - 12, text="σx",
                fill=EDU_FG, font=("Consolas", 9, "bold"),
            )

        # Lectura del EFECTO: ratio εy/εx = −ν, CENTRADO debajo del elemento
        # (anclado a `half`, no a `dy`, para no saltar con la deformación). Sin
        # signo `+` forzado; `or 0.0` evita el −0.000 cosmético en ν=0.
        ratio = (-nu) or 0.0
        c.create_text(
            cx, cy + half + 14, text=f"εy/εx = {ratio:.3f}",
            fill=EDU_FG, font=("Consolas", 10, "bold"), anchor="center",
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
        `set_matrix` cuando ν cambia. SIN título 'ν = ...': la lectura de ν
        ya vive bajo el espectro y la matriz ES el valor (cero redundancia)."""
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
        self._mat_values.pack(anchor="center", pady=(6, 6))

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
