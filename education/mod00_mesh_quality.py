"""
Modulo 0 — Calidad geometrica de la malla (rediseno 2026-05, 3a pasada)

DECISION DE DISENO (dos metricas ortogonales, anotadas sobre el canvas):

    Dos metricas en sus RANGOS BIBLIOGRAFICOS de Verdict/Cubit (SAND2007-1751):

        JACOBIANO   SJ = min sin(theta_i)        in [-1, 1]   (rango completo)
        COMPACIDAD  Q  = sqrt(2)*L_min/D_max      in [ 0, 1]   (Verdict Stretch)

    Cada barra usa el mapeo cromatico rojo->amarillo->verde con el corte
    "aceptable" (rojo->amarillo) LITERAL de la bibliografia: Scaled Jacobian
    aceptable >= 0,50; Stretch aceptable >= 0,25 — distintos porque cada metrica
    tiene su propia tolerancia (cada barra los marca con una linea "acept.").
    El corte "bueno" (amarillo->verde: 0,80 SJ / 0,50 Stretch) es convencion de
    la UI. En el Jacobiano [-1, 1] el tramo INVALIDO [-1, 0] queda rojo solido
    (negativo = invertido) y el valido [0, 1] lleva el gradiente; NO se usa el
    coloreado bipolar gris-centro (rojo->gris->verde) que antes hacia ilegible
    la frontera de validez. El color del elemento en el X-ray es la PEOR clase
    por-metrica (no el min de valores crudos contra un umbral unico, que pintaba
    de rojo elementos aceptables cuyo Stretch caia en [0,25; 0,5)). La inversion
    (SJ <= 0) ademas levanta un banner de aviso y pinta el elemento entero rojo.

    Por que estas dos: conceptos ortogonales (forma angular + validez vs
    proporcion geometrica), rangos consistentes entre si, mismos numeros que
    el alumno ve en ANSYS/Cubit. Cobertura: inversion, distorsion angular,
    elongacion. NO detecta trapezoidalidad pura (modulo posterior de locking).

INTERACCION:
    1. Hover sobre un elemento del MeshCanvas -> las barras se actualizan al
       elemento bajo cursor y se anota su geometria sobre el canvas.
    2. Drag de un vertice (corner) del elemento bajo cursor -> distorsion EN
       VIVO. NO muta el project; vive en self._distortion. Durante el drag se
       refresca SOLO la capa edu_m0 (no un redraw() completo del canvas), para
       que el arrastre sea fluido y las aristas distorsionadas se vean nitidas.
    3. X-ray del canvas: cada elemento se pinta con un borde nitido del color
       de calidad (verde/amarillo/rojo segun min(Q_SJ, Q)) + relleno tenue.

ANOTACIONES SOBRE EL CANVAS (pedagogia clave — reemplazan la vieja derivacion
LaTeX en expanders, que duplicaba la teoria del Theory Hub y mostraba numeros
abstractos sin referente visual):
    - JACOBIANO: arco sobre el vertice del PEOR angulo (mas lejos de 90 grados)
      + etiqueta "theta = ...". El alumno ve CUAL esquina causa el numero.
    - COMPACIDAD: la arista mas corta (L_min, solida) y la diagonal mas larga
      (D_max, punteada) resaltadas + sus longitudes. La formula
      Q = sqrt(2)*L_min/D_max se vuelve lectura visual directa.
    Solo se anota el elemento bajo cursor (no satura). Las anotaciones usan
    coords distorsionadas, asi se mueven en vivo con el drag.

    El paso a paso simbolico completo (todos los elementos) vive en la Memoria
    de Calculo (Archivo > Exportar) y la teoria general en el Theory Hub
    (Ayuda > Teoria FEM); M0 no lo repite.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np
import tkinter as tk

from education.overlay_module import CanvasOverlayModule
from education.components.quality_bar import QualityBar, fmt_es
from education.components.gauss_glyph import lerp_hex

from fem.mesh_quality import (
    stretch_metric, scaled_jacobian_corners, internal_angles,
)
from config.settings import (
    EDU_FG_MUTED, EDU_FG, OVERLAY_BG, CANVAS_BG_COLOR,
    HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
    CANVAS_SELECTED_COLOR, CANVAS_NODE_COLOR, CANVAS_NODE_RADIUS,
    EDU_M0_ANGLE_COLOR, EDU_M0_LENGTH_COLOR,
)


# Tag del canvas — limpiado en cada redibujado de la capa.
_TAG = "edu_m0"
# Hit-test del drag de nodo (px de canvas).
_DRAG_HIT_PX = 14

# Umbrales POR-METRICA rojo->amarillo->verde (barras + X-ray). El corte
# "aceptable" (rojo->amarillo) es LITERAL de la bibliografia (Verdict/Cubit,
# SAND2007-1751): Scaled Jacobian aceptable >= 0,50; Stretch aceptable >= 0,25.
# El corte "bueno" (amarillo->verde) es convencion de la UI; en Stretch coincide
# con el "aceptable >= 0,5" del docstring de fem/mesh_quality (reconciliando
# ambas fuentes: 0,25 = minimo admisible Verdict, 0,5 = ya de buena calidad).
# Antes habia UN umbral unificado 0,5 que pintaba de rojo elementos cuyo Stretch
# caia en [0,25; 0,5) — aceptables segun Verdict pero "despreciados" en el X-ray.
_SJ_ACCEPT, _SJ_GOOD = 0.5, 0.8
_ST_ACCEPT, _ST_GOOD = 0.25, 0.5

# Color por clase de calidad: 0 = inadmisible, 1 = aceptable, 2 = bueno.
_TIER_COLOR = (HEALTH_ERROR_COLOR, HEALTH_WARNING_COLOR, HEALTH_OK_COLOR)


def _tier(value: float, t_accept: float, t_good: float) -> int:
    """Clasifica un valor de calidad: 0 inadmisible, 1 aceptable, 2 bueno."""
    if value < t_accept:
        return 0
    if value < t_good:
        return 1
    return 2

# Banner de Compacidad baja: elemento VALIDO (SJ>0) pero mal proporcionado
# (Stretch < aceptable). Caso que el Jacobiano NO detecta (p.ej. rectangulo
# 1x10: SJ=1 pero Stretch~0,14). Sin el valor de Stretch — lo muestra la barra
# (se evita la redundancia barra<->mensaje).
_CMP_LOW_MSG = ("⚠ Mal proporcionado — muy alargado o aplastado: es válido, "
                "pero degrada la precisión de las tensiones.")

# Anotaciones geometricas sobre el elemento bajo cursor.
_ARC_R_PX = 24            # radio del arco del peor angulo
_ANNOT_MIN_EDGE_PX = 26   # bajo este tamano en pantalla no se anota (satura)


def _infer_bg_safe(widget) -> str:
    try:
        from education.components.latex_image import _infer_bg
        return _infer_bg(widget)
    except Exception:
        return OVERLAY_BG


class MeshQualityModule(CanvasOverlayModule):
    """M0 — Overlay con X-ray del canvas + 2 barras (Jacobiano + Compacidad)."""

    TITLE = "Ⓜ  Calidad de la malla"
    PHASE = "pre"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 470
    OVERLAY_HEIGHT = None  # auto-fit segun contenido
    REQUIRES_ELEMENT = False

    def __init__(self, main_window, project, element_id):
        # Distorsion en vivo (drag del alumno). NO muta el project; vive
        # solo en este dict y se aplica al render del canvas y a las
        # metricas mostradas en el overlay.
        self._distortion: dict = {}
        self._dragging_node: Optional[int] = None
        self._drag_started_at: Optional[Tuple[float, float]] = None
        # ¿Estan visibles los banners (Jacobiano / Compacidad)? Para refit del
        # overlay solo en la transicion de visibilidad, no en cada frame.
        self._warning_shown: bool = False
        self._warning_cmp_shown: bool = False

        # Elemento mostrado actualmente. Logica:
        #   - hover_id  -> ultimo elemento bajo cursor
        #   - displayed -> hover_id si lo hay; sino, element_id de apertura
        # Esto permite que al cerrar el hover, las barras conserven el
        # ultimo dato util (no parpadean a vacio).
        self._hover_elem_id: Optional[int] = None
        self._last_displayed_id: Optional[int] = element_id

        # Widget refs (creados en build_overlay).
        self._lbl_header: Optional[tk.Label] = None
        self._lbl_warning: Optional[tk.Label] = None        # Jacobiano (SJ<=0)
        self._lbl_warning_cmp: Optional[tk.Label] = None     # Compacidad baja
        self._bar_jac: Optional[QualityBar] = None
        self._bar_cmp: Optional[QualityBar] = None
        # Hint de uso persistente (arrastrar un nodo no modifica la malla).
        self._lbl_hint: Optional[tk.Label] = None

        super().__init__(main_window, project, element_id)

    # ── Construccion del overlay flotante ─────────────────────────
    def build_overlay(self, body):
        bg = _infer_bg_safe(body)

        # Header — nombre del elemento mostrado (1 linea concisa).
        self._lbl_header = tk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            fg=EDU_FG, bg=bg, anchor="w",
        )
        self._lbl_header.pack(fill="x", pady=(0, 2))

        # Hint de uso (persistente, 1 linea muted): instruccion + tranquilidad.
        self._lbl_hint = tk.Label(
            body,
            text="✎ Arrastrá un nodo para distorsionar — no modifica tu malla.",
            font=("Segoe UI", 8, "italic"), fg=EDU_FG_MUTED, bg=bg,
            anchor="w", justify="left", wraplength=440,
        )
        self._lbl_hint.pack(fill="x", pady=(0, 2))

        # Warning de inversion (oculto hasta que SJ <= 0). Se pack-ea
        # bajo demanda en _refresh_overlay.
        self._lbl_warning = tk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            fg=HEALTH_ERROR_COLOR, bg=bg, anchor="w", justify="left",
            wraplength=440,
        )
        # NO pack inicial — se muestra solo cuando SJ <= 0.

        # Warning de Compacidad baja: elemento VALIDO pero mal proporcionado
        # (muy alargado/aplastado). Color ambar (warning), NO rojo: es usable,
        # solo degrada la calidad. Se pack-ea bajo la barra de Compacidad.
        self._lbl_warning_cmp = tk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            fg=HEALTH_WARNING_COLOR, bg=bg, anchor="w", justify="left",
            wraplength=440,
        )
        # NO pack inicial.

        # ═════ SECCION JACOBIANO ═════════════════════════════════════
        tk.Label(
            body, text="Jacobiano  ·  forma angular + validez",
            font=("Segoe UI", 9, "italic"), fg=EDU_FG_MUTED, bg=bg,
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        # Rango COMPLETO de Verdict para el Scaled Jacobian: [-1, 1] (negativo
        # = invertido). Coloreado por umbrales (NO el bipolar gris-centro): el
        # tramo invalido [-1, 0] queda rojo solido, y el valido [0, 1] lleva el
        # gradiente rojo->amarillo (aceptable Verdict 0,50) ->verde (0,80). La
        # linea "acept." marca el corte de aceptabilidad de la bibliografia.
        self._bar_jac = QualityBar(
            body,
            range_min=-1.0, range_max=1.0,
            ticks=(-1.0, -0.5, 0.0, 0.5, 1.0),
            thresholds=(_SJ_ACCEPT, _SJ_GOOD), accept_cutoff=_SJ_ACCEPT,
            bipolar=False, decimals=3,
        )
        self._bar_jac.pack(fill="x", pady=(2, 2))

        # ═════ SECCION COMPACIDAD ═══════════════════════════════════
        tk.Label(
            body, text="Compacidad  ·  proporción geométrica (Stretch)",
            font=("Segoe UI", 9, "italic"), fg=EDU_FG_MUTED, bg=bg,
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # Umbrales propios del Stretch: rojo->amarillo en 0,25 (aceptable
        # Verdict), amarillo->verde en 0,50.
        self._bar_cmp = QualityBar(
            body,
            range_min=0.0, range_max=1.0,
            ticks=(0.0, _ST_ACCEPT, _ST_GOOD, 1.0),
            thresholds=(_ST_ACCEPT, _ST_GOOD), accept_cutoff=_ST_ACCEPT,
            bipolar=False, decimals=3,
        )
        self._bar_cmp.pack(fill="x", pady=(2, 2))

        # Cross-reference al siguiente concepto del pipeline (enriquecido:
        # nombra la consecuencia fisica geometria -> B -> error en sigma).
        self._pack_crossref(
            body, "mod02",
            "👉 Más distorsión ⇒ B menos precisa ⇒ más error en σ. "
            "Una malla sana mantiene det J > 0 en cada Gauss. Ver ② Jacobiano.",
            wraplength=440,
        )

        self._refresh_overlay()

    # ── Ciclo de vida ──────────────────────────────────────────────
    def on_activated(self):
        # Malla base en modo "fantasma" (gris tenue): el X-ray de calidad
        # distorsionado pasa a ser la geometria protagonista, sin confundirse
        # con la malla base de colores normales al arrastrar.
        self._mesh.ghost_geometry = True
        # Hover de elementos (callback del MeshCanvas).
        self._mesh.on_hover_element = self._on_hover_element
        # Click consumer para el drag (consume click solo si pega en un
        # nodo corner del elemento bajo cursor).
        self._click_consumer = self._on_node_press_consume
        self._mesh.add_click_consumer(self._click_consumer)
        # Bindings aditivos para motion + release.
        c = self._mesh.canvas
        self._bid_move = c.bind("<B1-Motion>", self._on_node_drag, add="+")
        self._bid_rel = c.bind("<ButtonRelease-1>", self._on_node_release,
                                add="+")
        self._mesh.redraw()

    def on_closed(self):
        # Restaurar la malla base a su color normal (primero, por robustez).
        self._mesh.ghost_geometry = False
        self._mesh.on_hover_element = None
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass
        c = self._mesh.canvas
        for bid, evt in (
            (getattr(self, "_bid_move", None), "<B1-Motion>"),
            (getattr(self, "_bid_rel", None), "<ButtonRelease-1>"),
        ):
            if bid:
                try:
                    c.unbind(evt, bid)
                except Exception:
                    pass

    # ── Capa educativa: X-ray de cada elemento por calidad ─────────
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if not self.project or not self.project.elements:
            return

        disp_id = self._displayed_elem_id()

        for elem in self.project.elements.values():
            try:
                coords = self._coords_with_distortion(elem)
            except Exception:
                continue
            if coords is None or len(coords) < 4:
                continue

            color = self._color_for(coords)
            pts = []
            for c in coords[:4]:
                sx, sy = mesh.world_to_screen(c[0], c[1])
                pts.extend([sx, sy])
            is_disp = (disp_id == elem.id)
            # Relleno tintado hacia el fondo + stipple gray50 (SEMITRANSPARENTE
            # ~50%): la malla fantasma (gris tenue) asoma entre el tinte sin
            # perder el look de mapa de calor. gray75 (mas denso) tapaba
            # algunas lineas del fantasma. El elemento mostrado lleva un tinte
            # mas saturado + borde mas grueso para destacar (junto con sus
            # anotaciones); el resto, un tinte mas tenue. El borde es el color
            # de calidad PURO (nitido) = la geometria distorsionada, asi el
            # drag no "pierde" las aristas.
            fill_tint = lerp_hex(color, CANVAS_BG_COLOR,
                                 0.36 if is_disp else 0.58)
            mesh.canvas.create_polygon(
                *pts, fill=fill_tint, outline=color, stipple="gray50",
                width=2.4 if is_disp else 1.4, tags=_TAG,
            )

        # Nodos corner sobre la geometria DISTORSIONADA: la malla base esta en
        # fantasma (gris tenue, en su posicion original), asi que estos son los
        # nodos "reales" interactivos — los que se ven y se arrastran. Solo
        # corners (los mid/center Q9 no se mueven en M0). Deduplicados (un nodo
        # compartido por varios elementos se dibuja una sola vez).
        drawn_nodes: set = set()
        r = CANVAS_NODE_RADIUS
        for elem in self.project.elements.values():
            for nid in elem.node_ids[:4]:
                if nid in drawn_nodes:
                    continue
                drawn_nodes.add(nid)
                node = self.project.nodes.get(nid)
                if node is None:
                    continue
                dx, dy = self._distortion.get(nid, (0.0, 0.0))
                sx, sy = mesh.world_to_screen(node.x + dx, node.y + dy)
                mesh.canvas.create_oval(
                    sx - r, sy - r, sx + r, sy + r,
                    fill=CANVAS_NODE_COLOR, outline=CANVAS_BG_COLOR, width=1,
                    tags=_TAG,
                )

        # Anotaciones geometricas sobre el elemento mostrado (encima del
        # X-ray): arco del peor angulo + arista Lmin + diagonal Dmax.
        if disp_id is not None:
            disp = self.project.elements.get(disp_id)
            if disp is not None:
                try:
                    dcoords = self._coords_with_distortion(disp)
                    if dcoords is not None and len(dcoords) >= 4:
                        self._draw_quality_annotations(mesh, dcoords)
                except Exception:
                    pass

        # Anillo amarillo en el nodo que se esta arrastrando (encima de todo).
        if self._dragging_node is not None:
            node = self.project.nodes.get(self._dragging_node)
            if node is not None:
                dx, dy = self._distortion.get(self._dragging_node, (0.0, 0.0))
                sx, sy = mesh.world_to_screen(node.x + dx, node.y + dy)
                mesh.canvas.create_oval(
                    sx - 9, sy - 9, sx + 9, sy + 9,
                    outline=CANVAS_SELECTED_COLOR, width=2.2, tags=_TAG,
                )

    # ── Anotaciones geometricas (peor angulo, Lmin, Dmax) ──────────
    def _draw_quality_annotations(self, mesh, coords: np.ndarray) -> None:
        """Ancla cada metrica a la geometria concreta del elemento mostrado.

        Usa coords YA distorsionadas, asi el arco/aristas se mueven en vivo
        con el drag. Solo se llama para el elemento bajo cursor.
        """
        P = coords[:4]
        if P.shape[0] < 4:
            return
        canvas = mesh.canvas

        S = [mesh.world_to_screen(float(P[i][0]), float(P[i][1]))
             for i in range(4)]
        edge_px = [math.hypot(S[(i + 1) % 4][0] - S[i][0],
                              S[(i + 1) % 4][1] - S[i][1]) for i in range(4)]
        # Si el elemento es muy chico/alejado, no anotar (las barras siguen
        # informando; evita saturar el canvas).
        if min(edge_px) < _ANNOT_MIN_EDGE_PX:
            return

        # ── Compacidad: arista Lmin (solida) + diagonal Dmax (punteada) ──
        L = [float(np.linalg.norm(P[(i + 1) % 4] - P[i])) for i in range(4)]
        lmin_i = int(np.argmin(L))
        a, b = S[lmin_i], S[(lmin_i + 1) % 4]
        canvas.create_line(a[0], a[1], b[0], b[1],
                           fill=EDU_M0_LENGTH_COLOR, width=3, tags=_TAG)
        mesh._draw_label_with_bg(
            (a[0] + b[0]) / 2, (a[1] + b[1]) / 2,
            f"Lmín {fmt_es(L[lmin_i], 2)}", fg=EDU_M0_LENGTH_COLOR,
            anchor=tk.CENTER, font=("Segoe UI", 8), tags=(_TAG,),
        )

        D1 = float(np.linalg.norm(P[2] - P[0]))
        D2 = float(np.linalg.norm(P[3] - P[1]))
        if D1 >= D2:
            d0, d1, dval = S[0], S[2], D1
        else:
            d0, d1, dval = S[1], S[3], D2
        canvas.create_line(d0[0], d0[1], d1[0], d1[1],
                           fill=EDU_M0_LENGTH_COLOR, width=2, dash=(5, 3),
                           tags=_TAG)
        mesh._draw_label_with_bg(
            (d0[0] + d1[0]) / 2, (d0[1] + d1[1]) / 2,
            f"Dmáx {fmt_es(dval, 2)}", fg=EDU_M0_LENGTH_COLOR,
            anchor=tk.CENTER, font=("Segoe UI", 8), tags=(_TAG,),
        )

        # ── Jacobiano: arco en el peor angulo (mas lejos de 90 grados) ──
        angles = np.asarray(internal_angles(P))
        worst_i = int(np.argmax(np.abs(angles - 90.0)))
        theta = float(angles[worst_i])
        cx, cy = S[worst_i]
        sp = S[(worst_i - 1) % 4]   # vertice previo
        sn = S[(worst_i + 1) % 4]   # vertice siguiente
        # create_arc usa angulos en grados, sentido antihorario desde las 3 en
        # punto, con la convencion matematica de Y (por eso -dy: la Y de
        # pantalla esta
        # invertida — un vector pantalla (dx, dy) corresponde al angulo
        # atan2(-dy, dx)).
        a_prev = math.degrees(math.atan2(-(sp[1] - cy), sp[0] - cx))
        a_next = math.degrees(math.atan2(-(sn[1] - cy), sn[0] - cx))
        extent = a_next - a_prev
        # Normalizar a (-180, 180] => arco menor = angulo interior (convexo).
        while extent <= -180.0:
            extent += 360.0
        while extent > 180.0:
            extent -= 360.0
        # Radio acotado para que el arco no exceda las aristas adyacentes.
        r = min(_ARC_R_PX,
                0.4 * min(edge_px[(worst_i - 1) % 4], edge_px[worst_i]))
        canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=a_prev, extent=extent, style="arc",
            outline=EDU_M0_ANGLE_COLOR, width=2, tags=_TAG,
        )
        # Etiqueta theta en la bisectriz, un poco mas afuera del arco.
        bis = math.radians(a_prev + extent / 2.0)
        lx = cx + (r + 13) * math.cos(bis)
        ly = cy - (r + 13) * math.sin(bis)
        mesh._draw_label_with_bg(
            lx, ly, f"θ {fmt_es(theta, 1)}°", fg=EDU_M0_ANGLE_COLOR,
            anchor=tk.CENTER, font=("Segoe UI", 8), tags=(_TAG,),
        )

    def _refresh_layer_only(self) -> None:
        """Refresca SOLO la capa edu_m0 (sin redraw() completo del canvas).

        Hot path del drag: redraw() hace canvas.delete('all') + redibujado
        completo de toda la malla por evento de movimiento, lo que vuelve el
        arrastre lento. Como la geometria base (project.nodes) no cambia
        durante el drag, basta con redibujar nuestra capa (que dibuja la
        version distorsionada). draw_canvas_layer ya empieza por
        canvas.delete(_TAG), asi que no acumula items.
        """
        try:
            self.draw_canvas_layer(self._mesh)
        except Exception:
            pass

    # ── Coloreado por calidad combinada (Q_SJ + Stretch) ───────────
    def _color_for(self, coords: np.ndarray) -> str:
        if len(coords) < 4:
            return HEALTH_ERROR_COLOR
        try:
            sj = scaled_jacobian_corners(coords)
            st = stretch_metric(coords)
        except Exception:
            return HEALTH_ERROR_COLOR
        if sj <= 0:
            return HEALTH_ERROR_COLOR  # invertido o reflex (bandera dura)
        # Cada metrica se clasifica contra SU PROPIO umbral aceptable (Verdict);
        # el color del elemento es la PEOR clase. (Antes era min(sj, st) contra
        # un umbral unico 0,5, que pintaba de rojo un elemento aceptable cuyo
        # Stretch caia en [0,25; 0,5) — bug reportado: E3 con SJ=0,74 y
        # Stretch=0,40 quedaba rojo siendo aceptable.)
        tier = min(_tier(max(0.0, sj), _SJ_ACCEPT, _SJ_GOOD),
                   _tier(st, _ST_ACCEPT, _ST_GOOD))
        return _TIER_COLOR[tier]

    # ── Hover de elemento ──────────────────────────────────────────
    def _on_hover_element(self, elem_id, _sx, _sy):
        if elem_id == self._hover_elem_id:
            return
        self._hover_elem_id = elem_id
        if elem_id is not None:
            self._last_displayed_id = elem_id
        self._refresh_overlay()
        self._mesh.redraw()

    def _displayed_elem_id(self) -> Optional[int]:
        """Elemento "mostrado" en el overlay = hover_id o last_displayed.

        Permite que al alejar el cursor de la malla, las barras conserven
        el ultimo elemento valido en lugar de parpadear a vacio.
        """
        if self._hover_elem_id is not None:
            return self._hover_elem_id
        return self._last_displayed_id

    # ── Drag de nodo (distorsion no destructiva) ───────────────────
    def _on_node_press_consume(self, event) -> bool:
        if self.project is None:
            return False
        # Buscar el corner mas cercano a su posicion DISTORSIONADA entre TODOS
        # los elementos (no solo el "mostrado"). Bug corregido: tras invertir
        # un elemento no se podia volver a tomar el vertice invertido — el
        # elemento mostrado lo decide el hover sobre la geometria SIN
        # distorsion, que al invertir deja de coincidir con donde quedo el
        # vertice. Solo vertices macro (corners): en Q9 los mid/centroide no se
        # desplazan en M0 (las metricas usan coords[:4]); node_ids[:4] es no-op
        # en Q4. Se desempata a favor del elemento mostrado.
        disp_id = self._displayed_elem_id()
        elems = list(self.project.elements.values())
        if disp_id is not None and disp_id in self.project.elements:
            disp0 = self.project.elements[disp_id]
            elems = [disp0] + [e for e in elems if e.id != disp_id]

        candidate = None
        cand_elem = None
        best_d = float("inf")
        seen: set = set()
        for elem in elems:
            for nid in elem.node_ids[:4]:
                if nid in seen:
                    continue
                seen.add(nid)
                node = self.project.nodes.get(nid)
                if node is None:
                    continue
                dx, dy = self._distortion.get(nid, (0.0, 0.0))
                sx, sy = self._mesh.world_to_screen(node.x + dx, node.y + dy)
                d = math.hypot(sx - event.x, sy - event.y)
                if d < best_d:
                    best_d = d
                    candidate = nid
                    cand_elem = elem.id
        if candidate is None or best_d > _DRAG_HIT_PX:
            return False

        self._dragging_node = candidate
        # Si el corner agarrado no pertenece al elemento mostrado, pasar a
        # mostrar uno que lo contenga (barras + anotaciones siguen el drag).
        disp = (self.project.elements.get(disp_id)
                if disp_id is not None else None)
        if disp is None or candidate not in disp.node_ids[:4]:
            self._hover_elem_id = cand_elem
            self._last_displayed_id = cand_elem
            self._refresh_overlay()

        node = self.project.nodes[candidate]
        wx, wy = self._mesh.screen_to_world(event.x, event.y)
        # Offset de agarre RELATIVO A LA POSICION DISTORSIONADA actual: si el
        # vertice ya estaba movido, restamos su dx/dy para que no salte (pierda
        # su distorsion) al re-tomarlo.
        dx0, dy0 = self._distortion.get(candidate, (0.0, 0.0))
        self._drag_started_at = (wx - node.x - dx0, wy - node.y - dy0)
        return True

    def _on_node_drag(self, event):
        if self._dragging_node is None or self._drag_started_at is None:
            return
        node = self.project.nodes.get(self._dragging_node)
        if node is None:
            return
        wx, wy = self._mesh.screen_to_world(event.x, event.y)
        ox, oy = self._drag_started_at
        dx = wx - node.x - ox
        dy = wy - node.y - oy
        self._distortion[self._dragging_node] = (dx, dy)
        self._refresh_overlay()          # barras (widget, barato)
        self._refresh_layer_only()       # solo capa edu_m0 (drag fluido)

    def _on_node_release(self, _event):
        self._dragging_node = None
        self._drag_started_at = None
        # redraw() completo al soltar: resincroniza la malla base y borra el
        # anillo amarillo del drag (que la capa solo dibuja si _dragging_node
        # no es None — sin este redraw quedaba fantasma hasta el proximo
        # repintado incidental).
        self._mesh.redraw()

    # ── Coords con distorsion aplicada ────────────────────────────
    def _coords_with_distortion(self, elem) -> Optional[np.ndarray]:
        coords = []
        for nid in elem.node_ids:
            node = self.project.nodes.get(nid)
            if node is None:
                return None
            dx, dy = self._distortion.get(nid, (0.0, 0.0))
            coords.append((node.x + dx, node.y + dy))
        return np.array(coords, dtype=float)

    # ── Refresh del overlay flotante ──────────────────────────────
    def _refresh_overlay(self):
        elem_id = self._displayed_elem_id()
        elem = (self.project.elements.get(elem_id)
                if (self.project and elem_id is not None) else None)

        if elem is None:
            self._set_no_element_state()
            return

        try:
            coords = self._coords_with_distortion(elem)
            if coords is None or len(coords) < 4:
                self._set_no_element_state()
                return
        except Exception:
            self._set_no_element_state()
            return

        sj = scaled_jacobian_corners(coords)   # in [-1, 1] (signo = validez)
        st = stretch_metric(coords)            # in [0, 1]

        # Header
        hover_tag = ""
        if self._hover_elem_id is None and self._last_displayed_id is not None:
            hover_tag = "  (último visto)"
        if self._lbl_header is not None:
            self._lbl_header.configure(text=f"Elemento E{elem.id}{hover_tag}")

        # Banners por severidad, MUTUAMENTE EXCLUYENTES (para no intersectarse):
        #   - SJ <= 0  -> banner del JACOBIANO con la causa real. La validez se
        #     arregla primero, asi que tiene prioridad y suprime el de Compacidad
        #     (evita doble-marcar, p.ej., un elemento degenerado).
        #   - valido pero Stretch < aceptable -> banner de COMPACIDAD: caso que
        #     el Jacobiano NO detecta (rectangulo 1x10 con SJ=1 pero forma mala).
        if sj <= 0:
            jac_msg = self._diagnose_invalid(coords, elem.node_ids)
            cmp_msg = None
        else:
            jac_msg = None
            cmp_msg = _CMP_LOW_MSG if st < _ST_ACCEPT else None
        # Un solo refit combinado si CUALQUIERA cambio de visibilidad (no dos,
        # que parpadearian al pasar de invalido a valido-mal-proporcionado).
        changed = self._set_banner(self._lbl_warning, "_warning_shown",
                                   jac_msg, self._bar_jac)
        changed = self._set_banner(self._lbl_warning_cmp, "_warning_cmp_shown",
                                   cmp_msg, self._bar_cmp) or changed
        if changed:
            self.refit_overlay()

        # Barras: Jacobiano en su rango bibliografico [-1, 1] mostrando el
        # valor crudo (negativo = invertido); la inversion la refuerza el
        # banner. Compacidad en [0, 1].
        if self._bar_jac is not None:
            self._bar_jac.set_value(sj)
        if self._bar_cmp is not None:
            self._bar_cmp.set_value(st)

    @staticmethod
    def _diagnose_invalid(coords, node_ids) -> str:
        """Diagnostica POR QUE el elemento es invalido (SJ <= 0) y devuelve un
        mensaje en español con la causa REAL — NO repite el valor del Jacobiano
        (ya lo muestra la barra, se evita la redundancia).

        Usa el area con signo (shoelace; > 0 = antihorario) y el producto cruz
        por vertice (giro local). Casos:
          - area ~ 0          -> degenerado (nodos casi alineados / area nula)
          - area < 0          -> invertido (orden horario; debe ser antihorario)
          - area > 0 + 1 giro negativo  -> vertice concavo (angulo > 180°)
          - area > 0 + >=2 giros negativos -> geometria cruzada (auto-interseca)
        """
        P = np.asarray(coords, dtype=float)[:4]
        if P.shape[0] < 4:
            return "⚠ Elemento inválido — geometría incompleta."
        # Area con signo (shoelace).
        area = 0.5 * sum(
            float(P[i][0] * P[(i + 1) % 4][1] - P[(i + 1) % 4][0] * P[i][1])
            for i in range(4)
        )
        # Giro local en cada vertice (misma cruz que scaled_jacobian_corners).
        cs = []
        for i in range(4):
            a = P[i] - P[(i - 1) % 4]
            b = P[(i + 1) % 4] - P[i]
            cs.append(float(a[0] * b[1] - a[1] * b[0]))
        edge2 = max(
            float(np.dot(P[(i + 1) % 4] - P[i], P[(i + 1) % 4] - P[i]))
            for i in range(4)
        )
        eps = 1e-6 * edge2 if edge2 > 1e-12 else 1e-12

        if edge2 <= 1e-12 or abs(area) < eps:
            return ("⚠ Elemento degenerado — área casi nula "
                    "(nodos casi alineados).")
        if area < 0:
            return ("⚠ Elemento invertido — los nodos están en orden horario "
                    "(deben ir en sentido antihorario).")
        # area > 0 (antihorario) pero SJ <= 0: hay giro(s) negativo(s).
        neg = [i for i in range(4) if cs[i] < -eps]
        if len(neg) == 1:
            i = neg[0]
            nid = (node_ids[i] if node_ids is not None and i < len(node_ids)
                   else None)
            quien = f"el nodo N{nid}" if nid is not None else "un nodo"
            return (f"⚠ Vértice cóncavo — {quien} forma un ángulo interno "
                    f"mayor a 180°.")
        if len(neg) >= 2:
            return ("⚠ Geometría cruzada — el cuadrilátero se dobla sobre sí "
                    "mismo (aristas que se cruzan).")
        return "⚠ Elemento inválido — geometría degenerada."

    def _set_banner(self, label, flag_attr: str, msg: Optional[str],
                    after_widget) -> bool:
        """Muestra/oculta un banner (Jacobiano o Compacidad) con su texto ya
        diagnosticado, packeado DEBAJO de su barra (`after_widget`). Devuelve
        True si CAMBIO de visibilidad — el caller hace UN solo `refit_overlay`
        combinado (sin él, el banner empuja y recorta el contenido inferior;
        dos refits separados parpadearían). `msg=None` -> oculto. Solo toca el
        layout en la transición de visibilidad (no en cada frame del drag).
        """
        if label is None:
            return False
        show = msg is not None
        if show:
            label.configure(text=msg)
        if show == getattr(self, flag_attr):
            return False
        setattr(self, flag_attr, show)
        try:
            if show:
                try:
                    label.pack(fill="x", pady=(0, 2), after=after_widget)
                except Exception:
                    label.pack(fill="x", pady=(0, 2))
            else:
                label.pack_forget()
        except Exception:
            pass
        return True

    def _set_no_element_state(self):
        """Estado vacio: sin hover y sin elemento de apertura."""
        if self._lbl_header is not None:
            self._lbl_header.configure(
                text="(hover sobre un elemento para ver su calidad)",
            )
        # Ocultar ambos banners (Jacobiano + Compacidad) con un refit combinado.
        changed = self._set_banner(self._lbl_warning, "_warning_shown", None,
                                   self._bar_jac)
        changed = self._set_banner(self._lbl_warning_cmp, "_warning_cmp_shown",
                                   None, self._bar_cmp) or changed
        if changed:
            self.refit_overlay()
        if self._bar_jac is not None:
            self._bar_jac.set_value(None)
        if self._bar_cmp is not None:
            self._bar_cmp.set_value(None)
