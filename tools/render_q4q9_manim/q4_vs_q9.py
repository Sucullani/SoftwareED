"""
Animacion educativa Manim: Q4 vs Q9 — Patch test de flexion pura.

Modelo: UN solo elemento por columna (Q4 izq, Q9 der), de lado
L=3.10, con la cinematica de flexion pura impuesta directamente
sobre los nodos via:

   u(x, y) =  κ · x · y          (bilineal en (x,y))
   v(x, y) = -κ · x² / 2          (cuadratico en x)

Q4 BILINEAL: solo 4 corners. Los 4 v_corner son iguales (todos
en |x| = HALF_SIDE) → la interpolacion bilineal de constantes da
v CONSTANTE dentro del elemento → toda la malla baja uniformemente
y top/bot quedan RECTOS, solo estirados/comprimidos en u.
Resultado: TRAPECIO INVERTIDO con bordes 100% rectos. Q4 NO puede
representar la curvatura de flexion pura — shear locking.

Q9 BICUADRATICO: 9 nodos (4 corners + 4 midedges + 1 centroide).
Los midnodes a (±HALF, 0) ven v = -κ·HALF²/2, los a (0, ±HALF) ven
v = 0. La biquadratica reproduce v(x) = -κ·x²/2 EXACTAMENTE.
Resultado: ARCO con bordes parabolicos exactos — flexion pura
capturada.

Decisiones de diseno (consolidadas tras feedback iterativo):

  · SIN flechas de momento M aplicado — EduFEM no soporta cargas
    de momento puntual, mostrarlas crearia expectativa falsa en el
    alumno de que el software las soporta. La cinematica se impone
    via desplazamientos nodales analiticos (label inferior dice
    "Flexion pura: u=κxy, v=-κx²/2" para fijar el experimento).

  · SIN gridlines internas — las isolineas de la shape function se
    leen visualmente como una "sub-malla" 4x4, creando la confusion
    de que el elemento esta subdividido en 16 sub-elementos. La
    diferencia Q4 vs Q9 se comunica suficiente con aristas + nodos:
       - Q4: 4 nodos, aristas RECTAS.
       - Q9: 9 nodos, aristas PARABOLICAS.

  · Los NODOS NO SE DEFORMAN — un nodo en FEM es un punto sin
    volumen. Pasarlos por apply_function los distorsiona como
    elipses (artifact de rendering, no correcto fisicamente). En
    cambio cada nodo se TRASLADA a su nueva posicion con un .shift
    individual (el circulo conserva forma).

  · Polygon con set_sheen(0.32, UP) → look metalico cenital.
    Sin gridlines, no hay interaccion problematica que generaba
    bandas en el render Q9 antes.

  · Nodos 3D mas grandes (radius 0.13 corners, 0.09 mids) con
    highlight y glint pronunciados → look de esferas metalicas
    iluminadas.

  · Ref outline dashed: rectangulo fantasma donde estaba el elemento
    en reposo. Sirve como ancla visual de la deformacion (Q4 queda
    DENTRO de la ref, Q9 sale FUERA en los corners — efecto educativo
    del fan-out cuadratico).

Salida: 900x600 px @ 22 fps, ~4.0 s.
"""

from manim import *
import numpy as np


# ─── Config global (matches tpvsdp.py) ─────────────────────────────────
config.background_color = "#212529"
config.frame_rate = 22
config.pixel_width = 900
config.pixel_height = 600
config.frame_width = 12.0
config.frame_height = 8.0


# ─── Paleta (sincronizada con config/settings.py + ElementTypeDialog) ─
C_SEPARATOR  = "#404040"
C_TEXT       = "#f1f3f5"
C_TEXT_MUTED = "#9aa5b1"

# Q4: gris steel (matches chip secondary del dialog)
C_Q4_FILL    = "#9aa5b1"
C_Q4_STROKE  = "#3f4754"
C_Q4_NODE    = "#e9ecef"
C_Q4_HEADER  = "#cdd2d8"
C_Q4_VERDICT = "#fb923c"          # naranja warning: no captura

# Q9: naranja PHASE_PROC (matches chip warning del dialog)
C_Q9_FILL    = "#fd7e14"
C_Q9_STROKE  = "#9c4a08"
C_Q9_NODE    = "#fff7e0"
C_Q9_HEADER  = "#fd7e14"
C_Q9_VERDICT = "#10b981"          # verde success: captura exacto

# Reference dashed outline (donde estaba el elemento sin deformar)
C_REF        = "#475569"

# Rivet metalico (cabeza del remache) — color steel neutral igual
# que el TP plate de tpvsdp.py. NO cambia con Q4/Q9: los remaches
# reales son siempre de acero, la identidad Q4/Q9 viene del color
# del front face del elemento.
C_RIVET      = "#bdc6cf"


# ─── Constantes de geometria + flexion pura ────────────────────────────
HALF_SIDE = 1.55                  # semi-lado del elemento → lado total 3.10
KAPPA = 0.22                      # curvatura impuesta. Elegida para
                                  # deformacion VISIBLE pero no exagerada
                                  # (~0.53 de u en TR, ~0.26 de v drop en
                                  # sides).
N_SUB_EDGE = 16                   # subdivision por arista del polygon
                                  # para que Q9 curve smooth bajo
                                  # apply_function.


class Q4vsQ9(Scene):
    """Patch test de flexion pura — Q4 (no captura) vs Q9 (exacto)."""

    def construct(self):
        self._build_layout()
        q4 = self._build_element(side="left",  element_type="Q4")
        q9 = self._build_element(side="right", element_type="Q9")

        # Todo lo dinamico invisible al inicio (frame 0 = solo layout)
        for col in (q4, q9):
            col["deformable"].set_opacity(0)
            col["ref_outline"].set_opacity(0)
            for n in col["nodes"]:
                n.set_opacity(0)
            col["verdict"].set_opacity(0)

        # ─── 0.0..0.6s — Fade in elementos en reposo ──────────────────
        fade_in_targets = []
        for col in (q4, q9):
            fade_in_targets.append(col["deformable"].animate.set_opacity(1))
            fade_in_targets.append(
                col["ref_outline"].animate.set_opacity(0.55)
            )
            for n in col["nodes"]:
                fade_in_targets.append(n.animate.set_opacity(1))
            fade_in_targets.append(col["verdict"].animate.set_opacity(1))
        self.play(*fade_in_targets, run_time=0.6)

        # ─── 0.6..1.0s — Hold (alumno absorbe el estado en reposo) ───
        self.wait(0.4)

        # ─── 1.0..2.4s — Aplicar flexion pura (1.4s) ─────────────────
        # El polygon se deforma con apply_function (sus puntos
        # perimetrales se mueven segun u, v de la cinematica de
        # flexion pura interpolada por las shape functions del elemento).
        # Los NODOS se trasladan individualmente con .shift — cada uno a
        # su posicion nueva sin distorsionar su forma circular.
        bend_q4 = self._make_bend_q4(q4["center_x"])
        bend_q9 = self._make_bend_q9(q9["center_x"])

        node_anims = []
        for col, bend in [(q4, bend_q4), (q9, bend_q9)]:
            for node in col["nodes"]:
                old_center = node.get_center()
                new_center = bend(old_center)
                shift_vec = new_center - old_center
                node_anims.append(node.animate.shift(shift_vec))

        self.play(
            q4["deformable"].animate.apply_function(bend_q4),
            q9["deformable"].animate.apply_function(bend_q9),
            *node_anims,
            run_time=1.4,
            rate_func=smooth,
        )

        # ─── 2.4..3.5s — Hold deformado (1.1s) ────────────────────────
        # Tiempo suficiente para que el alumno absorba la diferencia:
        # Q4 = trapecio invertido bordes rectos, Q9 = arco bordes parabolicos.
        self.wait(1.1)

        # ─── 3.5..4.0s — Fade out para loop seamless ─────────────────
        # Frame final = frame inicial (solo layout estatico visible).
        fade_out_targets = []
        for col in (q4, q9):
            fade_out_targets.append(col["deformable"].animate.set_opacity(0))
            fade_out_targets.append(col["ref_outline"].animate.set_opacity(0))
            for n in col["nodes"]:
                fade_out_targets.append(n.animate.set_opacity(0))
            fade_out_targets.append(col["verdict"].animate.set_opacity(0))
        self.play(*fade_out_targets, run_time=0.5)

    # ─── Layout estatico: separadores + label de la formula ─────────
    def _build_layout(self):
        # SIN titulos "Q4 — 4 nodos" / "Q9 — 9 nodos" arriba — son
        # redundantes con los chips del ElementTypeDialog (que ya dicen
        # "Q4 · 8 GDL" y "Q9 · 18 GDL" con matching color por columna).
        # El video siempre se monta DENTRO del dialog, asi que el chip
        # provee toda la identificacion necesaria.
        sep_top  = Line([-6, 3.30, 0], [6, 3.30, 0],
                        color=C_SEPARATOR, stroke_width=1)
        sep_bot  = Line([-6, -3.00, 0], [6, -3.00, 0],
                        color=C_SEPARATOR, stroke_width=1)
        sep_vert = Line([0, 3.30, 0], [0, -3.00, 0],
                        color=C_SEPARATOR, stroke_width=1)

        # Label inferior con la cinematica impuesta (siempre visible).
        # Esto SI se queda — describe QUE experimento se hace, no
        # QUE elemento es (eso lo dice el chip).
        bend_label = MathTex(
            r"\text{Flexión pura: }",
            r"u = \kappa\,x\,y,\quad v = -\tfrac{1}{2}\kappa\,x^{2}",
            color=C_TEXT_MUTED,
        ).scale(0.45)
        bend_label.move_to(np.array([0.0, -3.30, 0]))

        self.add(sep_top, sep_bot, sep_vert, bend_label)

    # ─── Construccion de un elemento (Q4 o Q9) ──────────────────────
    def _build_element(self, side: str, element_type: str) -> dict:
        """Construye un elemento estilizado como CHAPA INDUSTRIAL METALICA
        (paralelo al lenguaje visual del TP plate de tpvsdp.py):
           - Front face con sheen cenital fuerte (0.45 UP) → metalica.
           - Linea especular brillante en arista superior (sol catching).
           - Linea de oclusion ambiental en arista inferior (sombra).
           - Nodos como RIVETS de 5 capas (shadow + washer + head +
             highlight + glint) — pieza atornillada con volumen 3D real.
        Bajo apply_function el front face + spec/AO bend; los rivets
        SOLO se trasladan (preservan forma circular)."""
        cx = -3.0 if side == "left" else 3.0
        x_l = cx - HALF_SIDE
        x_r = cx + HALF_SIDE
        y_b = -HALF_SIDE
        y_t = +HALF_SIDE

        if element_type == "Q4":
            fill_c, stroke_c = C_Q4_FILL, C_Q4_STROKE
            verdict_color = C_Q4_VERDICT
            verdict_text = "✗  bordes rectos  ·  trapecio invertido"
        else:
            fill_c, stroke_c = C_Q9_FILL, C_Q9_STROKE
            verdict_color = C_Q9_VERDICT
            verdict_text = "✓  bordes parabólicos  ·  flexión exacta"

        # ── Front face: polygon con aristas subdivididas + sheen fuerte ──
        # Todas las aristas subdivididas para que la biquadratica Q9
        # pueda curvarlas bajo apply_function. Sheen 0.45 UP igual que
        # la chapa TP — luz cenital fuerte → claro arriba, oscuro abajo.
        border_pts = []
        for k in range(N_SUB_EDGE):
            t = k / N_SUB_EDGE
            border_pts.append(np.array([x_l + t * (x_r - x_l), y_b, 0]))
        for k in range(N_SUB_EDGE):
            t = k / N_SUB_EDGE
            border_pts.append(np.array([x_r, y_b + t * (y_t - y_b), 0]))
        for k in range(N_SUB_EDGE):
            t = k / N_SUB_EDGE
            border_pts.append(np.array([x_r - t * (x_r - x_l), y_t, 0]))
        for k in range(N_SUB_EDGE):
            t = k / N_SUB_EDGE
            border_pts.append(np.array([x_l, y_t - t * (y_t - y_b), 0]))
        polygon = Polygon(
            *border_pts,
            color=stroke_c, fill_color=fill_c,
            fill_opacity=0.95, stroke_width=2.6,
        )
        polygon.set_sheen_direction(UP)
        polygon.set_sheen(0.45, UP)

        # ── Linea especular en arista superior (sol catching cenital) ──
        # Como Line segments individuales (no VMobject subdividido) para
        # que apply_function las curve sin generar streaks/artifacts.
        spec_top = VGroup()
        margin = 0.05
        for k in range(N_SUB_EDGE):
            xa = x_l + margin + (k / N_SUB_EDGE) * (x_r - x_l - 2 * margin)
            xb = x_l + margin + ((k + 1) / N_SUB_EDGE) * (x_r - x_l - 2 * margin)
            spec_top.add(Line(
                np.array([xa, y_t - 0.012, 0]),
                np.array([xb, y_t - 0.012, 0]),
                color="#f1f3f5", stroke_width=2.4, stroke_opacity=0.70,
            ))

        # ── Linea de oclusion ambiental en arista inferior (sombra) ──
        ao_bot = VGroup()
        for k in range(N_SUB_EDGE):
            xa = x_l + margin + (k / N_SUB_EDGE) * (x_r - x_l - 2 * margin)
            xb = x_l + margin + ((k + 1) / N_SUB_EDGE) * (x_r - x_l - 2 * margin)
            ao_bot.add(Line(
                np.array([xa, y_b + 0.012, 0]),
                np.array([xb, y_b + 0.012, 0]),
                color="#0a0c0f", stroke_width=2.4, stroke_opacity=0.55,
            ))

        # ── Outline de referencia (rectangulo dashed sin deformar) ──
        # Sirve como ancla visual: el alumno ve que Q4 queda DENTRO
        # de la ref (trapecio mas chico) y Q9 sale FUERA en corners
        # (fan-out cuadratico). Refuerza visualmente el contraste.
        ref_outline = DashedVMobject(
            Polygon(
                np.array([x_l, y_b, 0]),
                np.array([x_r, y_b, 0]),
                np.array([x_r, y_t, 0]),
                np.array([x_l, y_t, 0]),
                color=C_REF, stroke_width=1.2,
            ),
            num_dashes=32, dashed_ratio=0.5,
        ).set_stroke(C_REF, width=1.2, opacity=0.55)
        for sm in ref_outline.submobjects:
            sm.set_fill(opacity=0)

        # ── Nodos = RIVETS industriales (5 capas) — translatables ──
        # Q4: 4 corners. Q9: 4 corners + 4 midedges + 1 centroide.
        # Cada rivet es un VGroup que se mueve como bloque rigido
        # bajo .shift (preserva forma circular, no se deforma).
        nodes = VGroup()
        if element_type == "Q4":
            for x in (x_l, x_r):
                for y in (y_b, y_t):
                    nodes.add(self._make_industrial_rivet(
                        np.array([x, y, 0]), head_radius=0.115,
                    ))
        else:  # Q9 — 3x3 grid
            for x in (x_l, cx, x_r):
                for y in (y_b, 0.0, y_t):
                    is_corner = (x in (x_l, x_r)) and (y in (y_b, y_t))
                    nodes.add(self._make_industrial_rivet(
                        np.array([x, y, 0]),
                        head_radius=0.115 if is_corner else 0.080,
                    ))

        # ── Verdict label (color semantico bajo el elemento) ──
        verdict = Text(verdict_text, color=verdict_color,
                       weight=NORMAL).scale(0.34)
        verdict.move_to(np.array([cx, -2.55, 0]))

        # ── Ensamblar grupos ──
        # deformable: front face + spec/AO lines. Bajo apply_function
        # el polygon se deforma y las spec/AO lines lo acompañan en su
        # nuevo borde superior/inferior.
        deformable = VGroup(polygon, spec_top, ao_bot)

        return {
            "deformable":  deformable,   # apply_function aqui
            "ref_outline": ref_outline,  # estatico
            "nodes":       nodes,        # translatables (cada uno con .shift)
            "verdict":     verdict,      # estatico
            "center_x":    cx,
        }

    # ─── Helper: rivet industrial 5-capas (estilo TP plate) ─────────
    @staticmethod
    def _make_industrial_rivet(pos: np.ndarray, head_radius: float):
        """Rivet de 5 capas igual que en tpvsdp.py:
        shadow + washer ring + head + highlight + glint.
        Color de la cabeza siempre METALICO (C_RIVET steel) — no
        cambia con Q4/Q9, la identidad cromatica viene del front face
        del elemento (gris vs naranja). Esto simula remaches reales
        que son siempre de acero independiente del material del panel."""
        # Drop shadow offset abajo-derecha (simula luz cenital)
        shadow = Circle(
            radius=head_radius * 1.10, color="#0a0c0f", fill_color="#0a0c0f",
            fill_opacity=0.55, stroke_width=0,
        ).move_to(pos + np.array([0.022, -0.022, 0]))
        # Washer ring (arandela oscura debajo del rivet)
        washer = Annulus(
            inner_radius=head_radius * 1.00,
            outer_radius=head_radius * 1.45,
            color="#1a1d22", fill_color="#1a1d22",
            fill_opacity=0.78, stroke_width=0,
        ).move_to(pos)
        # Cabeza del rivet (boton hemisferico metalico)
        head = Circle(
            radius=head_radius, color="#3a3d42", fill_color=C_RIVET,
            fill_opacity=1.0, stroke_width=0.5, stroke_opacity=0.8,
        ).move_to(pos)
        # Highlight cenital (curva clara arriba-izq)
        highlight = Dot(
            radius=head_radius * 0.42, color="#dee2e6", fill_opacity=0.55,
        ).move_to(pos + np.array([-head_radius * 0.32, head_radius * 0.32, 0]))
        # Glint puntual (reflejo brillante en la cima de la "esfera")
        glint = Dot(
            radius=head_radius * 0.18, color=WHITE, fill_opacity=0.90,
        ).move_to(pos + np.array([-head_radius * 0.40, head_radius * 0.40, 0]))
        return VGroup(shadow, washer, head, highlight, glint)

    # ─── Bend functions (cinematica de flexion pura) ─────────────────
    @staticmethod
    def _make_bend_q4(cx: float):
        """Q4 BILINEAL: 4 corners. Los v_corner son todos iguales
        (mismo x² en |x|=HALF), asi que la interpolacion bilineal
        degrada v(x) a CONSTANTE → no captura curvatura. u sigue siendo
        bilineal exacta porque κxy es de la base bilineal."""
        v_uniform = -KAPPA * HALF_SIDE * HALF_SIDE / 2.0
        def bend(point):
            x, y, z = point
            xr = x - cx
            u = KAPPA * xr * y                # bilineal exacta
            v = v_uniform                     # CONSTANTE
            return np.array([x + u, y + v, z])
        return bend

    @staticmethod
    def _make_bend_q9(cx: float):
        """Q9 BICUADRATICO: 9 nodos. La biquadratica reproduce
        v(x) = -κx²/2 EXACTAMENTE (cuadratica en x esta en la base).
        u bilineal tambien capturada exactamente. Arco perfecto."""
        def bend(point):
            x, y, z = point
            xr = x - cx
            u = KAPPA * xr * y                # bilineal exacta
            v = -KAPPA * xr * xr / 2.0        # cuadratica exacta
            return np.array([x + u, y + v, z])
        return bend

    # ─── Helper: nodo 3D estilo esfera metalica ─────────────────────
    @staticmethod
    def _make_3d_node(pos: np.ndarray, radius: float,
                       body_color: str, stroke_color: str,
                       with_glint: bool = True):
        """Nodo con apariencia 3D: cuerpo (con sheen cenital del nodo
        propio) + highlight curvo + glint puntual. Los 3 elementos
        forman un VGroup que se traslada como UN bloque rigido
        (preserva la forma esferica)."""
        body = Circle(
            radius=radius, color=stroke_color, fill_color=body_color,
            fill_opacity=1, stroke_width=1.4,
        ).move_to(pos)
        # Sheen cenital propio del nodo (simula reflejo sobre esfera)
        body.set_sheen_direction(np.array([-0.3, 0.7, 0]))
        body.set_sheen(0.40, np.array([-0.3, 0.7, 0]))
        # Highlight cenital (curva clara arriba-izq)
        highlight = Dot(
            radius=radius * 0.42, color=WHITE, fill_opacity=0.50,
        ).move_to(pos + np.array([-radius * 0.28, radius * 0.28, 0]))
        if not with_glint:
            return VGroup(body, highlight)
        # Glint puntual (reflejo brillante en la cima de la "esfera")
        glint = Dot(
            radius=radius * 0.20, color=WHITE, fill_opacity=0.95,
        ).move_to(pos + np.array([-radius * 0.34, radius * 0.34, 0]))
        return VGroup(body, highlight, glint)
