"""
Animacion educativa Manim: Tension Plana (TP) vs Deformacion Plana (DP).

Version 2 — comportamiento fisico real alineado con la definicion MEF plana:

  TP (Tension Plana):
    Cuerpo delgado en Z (espesor << dimensiones del plano XY). Las caras
    Z+ y Z- son superficies libres → sin traccion normal → σz=0. El
    cuerpo es libre de contraerse en Z bajo Poisson. Bajo traccion en X
    se elonga en X y se contrae en Y (Poisson en plano).

  DP (Deformacion Plana):
    Cuerpo largo en Z (longitud >> seccion transversal). Las secciones
    vecinas son identicas y por simetria/material confinan cualquier
    desplazamiento en Z → εz=0. Bajo presion hidrostatica la presa
    flecta levemente hacia downstream.

Decisiones de UX:
  · Las ecuaciones "σz = 0" y "εz = 0" PERMANECEN visibles todo el video
    (parte del layout estatico, igual que los titulos de columna). El
    usuario las puede leer a su ritmo, no desaparecen.
  · Sin texto explicativo dentro de la animacion — la justificacion
    textual va como caption del dialogo analysis_type_dialog.py.
  · Presa renderizada como prisma 3D extruido con caras semi-transparentes
    (top, lateral, back) + slice indicators para mostrar "todas las
    secciones son identicas".

Salida: 900x600 px @ 22 fps, ~8.6 segundos (~190 frames). Loop seamless:
el ultimo frame coincide con el primero (solo layout estatico visible).
"""

from manim import *
import numpy as np


# ─── Config global ─────────────────────────────────────────────────────
config.background_color = "#212529"
config.frame_rate = 22
config.pixel_width = 900
config.pixel_height = 600
config.frame_width = 12.0
config.frame_height = 8.0

# ─── Paleta (sincronizada con config/settings.py del proyecto) ─────────
C_STEEL       = "#9aa5b1"
C_STEEL_DARK  = "#5a6470"
C_RIVET       = "#3d4148"
C_CONCRETE    = "#a8a39a"
C_CONCRETE_DK = "#6b6760"
C_AGGREGATE   = "#7d7972"
C_WATER       = "#3b82f6"
C_WATER_DK    = "#1e4d8a"
C_GROUND      = "#92694e"
C_AXIS_X      = "#f87171"
C_AXIS_Y      = "#4ade80"
C_AXIS_Z      = "#6ba0d8"
C_LOAD        = "#fd7e14"
C_SENSOR      = "#4fc3f7"
C_BLOCKER     = "#ef4444"
C_TEXT        = "#f1f3f5"
C_EQUATION    = "#ffd166"
C_SEPARATOR   = "#404040"
C_YELLOW_TRY  = "#fbbf24"
C_HALO        = "#ffd166"

# Vector de profundidad para isometrica suave (25°)
ISO_ANGLE = 25 * DEGREES
ISO_VEC = np.array([np.cos(ISO_ANGLE), np.sin(ISO_ANGLE), 0.0])


def iso(depth: float) -> np.ndarray:
    """Offset 2D para una profundidad dada en isometrica."""
    return depth * ISO_VEC


class TPvsDP(Scene):
    """Animacion comparativa TP/DP de 6 segundos, loop seamless."""

    # Switch entre tres opciones de estructura TP. Solo "plate" es la
    # version activa actualmente; "beam" y "dogbone" son backups de
    # iteraciones previas que se conservaron por pedido del usuario.
    #   "plate"   → chapa industrial con remaches mejorados (washer +
    #               shadow + highlight) + stencil "AISI 1020" + manchas
    #               de oxidacion. Estetica de panel atornillado real.
    #   "beam"    → viga peraltada simplemente apoyada con carga
    #               distribuida (deep beam, ejemplo canónico FEM).
    #   "dogbone" → probeta de traccion ASTM E8 (intento previo).
    TP_MODE = "plate"

    def construct(self):
        self._build_layout()
        tp_builder = {
            "plate": self._build_tp_plate,
            "beam": self._build_tp_beam,
            "dogbone": self._build_tp_dogbone,
        }[self.TP_MODE]
        tp = tp_builder()
        dp = self._build_dp()

        # Estructuras invisibles al inicio (asi frame 0 = frame final).
        tp["geometry"].set_opacity(0)
        dp["geometry"].set_opacity(0)

        # ─── 0.0..0.7s — Aparicion ───────────────────────────────────
        self.play(
            tp["geometry"].animate.set_opacity(1),
            dp["geometry"].animate.set_opacity(1),
            run_time=0.7,
        )

        # ─── 0.7..1.5s — Aplicacion de cargas ─────────────────────────
        self.play(
            *[GrowArrow(a) for a in tp["loads"]],
            *[GrowArrow(a) for a in dp["loads"]],
            run_time=0.8,
        )

        # Mover las flechas hidrostaticas DENTRO de dam_solid_group para
        # que el bend cubico las afecte tambien — los puntos de las
        # flechas se desplazan por shift(y), igual que la cara upstream,
        # asi se mueven junto con la presa (origen en el agua, extremo
        # en la cara upstream — ambos a la misma altura y, mismo shift).
        for a in dp["loads"]:
            dp["dam_solid_group"].add(a)

        # ─── 1.5..2.1s — Deformacion fisica real ──────────────────────
        # TP: elongacion en X + contraccion Poisson en Y (εy = -ν·εx con
        #     ν ≈ 0.3 propio de acero estructural).
        # DP: la presa flecta como una VIGA EMPOTRADA con carga distribuida
        # TRIANGULAR (presion hidrostatica w(y) ∝ H - y, maxima en base).
        # Integrando EI·δ'''' = w 4 veces con BCs de voladizo, el perfil
        # de deflexion normalizado es:
        #     δ(h)/δmax = h² · (10 - 10h + 5h² - h³) / 4
        # - base (h=0): δ=0 (empotramiento)
        # - corona (h=1): δ=δmax (flecha libre)
        # - middle (h=0.5): δ≈0.383·δmax (mas curvatura cerca de la base,
        #   donde la presion es maxima — visualmente distinguible del
        #   perfil de carga puntual h²(3-h)/2 que daria 0.31).
        # Las flechas hidrostaticas se mueven junto con la presa (ya
        # estan dentro del dam_solid_group).
        dp_base_y = dp["dam_base_y"]
        dp_crown_y = dp["dam_crown_y"]
        MAX_SHIFT = 0.25

        def dam_bend(point):
            x, y, z = point
            h = (y - dp_base_y) / (dp_crown_y - dp_base_y)
            h = max(0.0, h)
            shape = h * h * (10.0 - 10.0 * h + 5.0 * h * h - h * h * h) / 4.0
            shift = MAX_SHIFT * shape
            return np.array([x + shift, y, z])

        # ── Deformacion TP (depende del modo) ──
        if self.TP_MODE == "beam":
            # Viga peraltada: pandeo descendente con perfil de simply
            # supported bajo carga uniforme. Los apoyos NO se mueven
            # (estan fuera de plate_group).
            tp_anims = [
                tp["plate_group"].animate.apply_function(tp["beam_bend"]),
            ]
        else:
            # Placa traccionada: stretch en X + contraccion Poisson en Y.
            # Las pinzas TP se desplazan con el borde de la chapa: 1.05x
            # en ancho W → cada borde se mueve W * 0.025 hacia afuera.
            # El stretch en Y = 0.985 corresponde a Poisson de acero
            # (ν ≈ 0.3): εx = 0.05 → εy = -ν·εx = -0.015 → 0.985.
            plate_shift = tp["plate_width"] * 0.025  # = 0.0625 para W=2.5
            tp_anims = [
                tp["plate_group"].animate.stretch(1.05, dim=0)
                                         .stretch(0.985, dim=1),
                tp["left_pull"].animate.shift(LEFT * plate_shift),
                tp["right_pull"].animate.shift(RIGHT * plate_shift),
            ]

        self.play(
            *tp_anims,
            dp["dam_solid_group"].animate.apply_function(dam_bend),
            run_time=0.6,
        )

        # ─── 2.1..2.6s — Mini elementos finitos emergen de las rebanadas ─
        # Patron: cada rebanada tiene UNA particula ESTATICA que permanece
        # en el modelo (visible durante todo el video) + un COURIER (copia)
        # que vuela al centro y se transforma en el stress element.
        # Asi el alumno siempre ve "de donde viene este analisis" — la
        # particula estatica marca la posicion en el modelo, el courier
        # representa la extraccion al espacio analitico 2D.
        # Para TP-beam, el centro descendio MAX_SAG bajo la carga
        # distribuida → corregir con beam_bend. Para TP-plate/dogbone
        # el stretch mantiene el centro fijo, asi que se usa tal cual.
        tp_slice = (tp["beam_bend"](tp["plate_center"])
                    if self.TP_MODE == "beam" else tp["plate_center"])
        # Para DP: corregir slice_center por la deformacion del dam (la
        # presa flecto bajo presion hidrostatica, el centro de la rebanada
        # se desplazo hacia downstream).
        dp_slice = dam_bend(dp["slice_center"])
        element_center = np.array([0.0, 0.0, 0])

        # Tamano final del elemento de esfuerzo central
        TARGET_SIZE = 1.50
        PARTICLE_SIZE = 0.34  # tamano de las particulas estaticas + couriers
        growth_factor = TARGET_SIZE / PARTICLE_SIZE  # ≈ 4.41

        # Colores: amarillo vibrante con stroke OSCURO (no cream).
        # El stroke oscuro fuerza contraste contra cualquier fondo —
        # crema se mimetizaba con la chapa gris claro y la particula TP
        # quedaba practicamente invisible.
        PARTICLE_FILL   = C_YELLOW_TRY   # "#fbbf24" amber vibrante
        PARTICLE_STROKE = "#1a1d22"      # casi-negro (maximo contraste)

        def make_particle(pos):
            """Helper para construir cada particula con identicos atributos
            — evita usar .copy() que en algunos cases compartia estado
            sutil entre particulas y causaba comportamientos asimetricos."""
            sq = Square(side_length=PARTICLE_SIZE)
            sq.move_to(pos)
            sq.set_fill(PARTICLE_FILL, opacity=1.0)
            sq.set_stroke(PARTICLE_STROKE, width=5)
            sq.set_opacity(0)
            return sq

        # ── Particulas ESTATICAS (permanecen en el modelo) ──
        particle_tp = make_particle(tp_slice)
        particle_dp = make_particle(dp_slice)

        # ── COURIERS (vuelan al centro). Creados explicitamente para
        # garantizar atributos identicos sin riesgo de estado compartido.
        courier_tp = make_particle(tp_slice)
        courier_dp = make_particle(dp_slice)

        # Trazas que siguen a los couriers durante el vuelo (no a las
        # estaticas — esas no se mueven, no generarian traza).
        trail_tp = TracedPath(
            courier_tp.get_center,
            stroke_color=C_YELLOW_TRY,
            stroke_width=3.0, stroke_opacity=0.85,
        )
        trail_dp = TracedPath(
            courier_dp.get_center,
            stroke_color=C_YELLOW_TRY,
            stroke_width=3.0, stroke_opacity=0.85,
        )
        # Z-order EXPLICITO via z_index — fuerza que las particulas se
        # rendericen por encima de todo, incluso de las pinzas (que tienen
        # fill_opacity=1 y son opacas). Sin esto, el courier TP queda
        # oculto cuando pasa por el cuerpo de la pinza derecha durante el
        # vuelo: Manim re-agrega los children del VGroup geometry al final
        # de scene.mobjects durante las animaciones, pisando el orden
        # natural de adicion.
        for obj in (trail_tp, trail_dp):
            obj.set_z_index(99)
        for obj in (particle_tp, particle_dp, courier_tp, courier_dp):
            obj.set_z_index(100)
        self.add(trail_tp, trail_dp,
                 particle_tp, particle_dp,
                 courier_tp, courier_dp)

        # Emergen TODAS las particulas (estaticas + couriers) — al inicio
        # las dos overlapean en cada slice y se ven como una sola.
        self.play(
            particle_tp.animate.set_opacity(1),
            particle_dp.animate.set_opacity(1),
            courier_tp.animate.set_opacity(1),
            courier_dp.animate.set_opacity(1),
            run_time=0.5,
        )

        # ─── Vuelo (1.7s) — solo couriers se mueven, estaticas se quedan ─
        # Atenuamos las estructuras + cargas al 18% para que el vuelo
        # destaque. Las particulas estaticas tampoco se atenuan: al estar
        # FUERA del geometry group, mantienen brillo completo → marcan
        # claramente la rebanada en cada modelo.
        self.play(
            courier_tp.animate.move_to(element_center),
            courier_dp.animate.move_to(element_center),
            tp["geometry"].animate.set_opacity(0.18),
            dp["geometry"].animate.set_opacity(0.18),
            *[a.animate.set_opacity(0.18) for a in tp["loads"]],
            run_time=1.7,
        )

        # En el centro hay dos couriers identicos superpuestos. Eliminamos
        # uno y usamos el otro como base del stress element central.
        self.remove(courier_dp)
        # Crecimiento + transicion al look analitico (gris). El courier
        # crece y se "enfria" del amarillo al gris simultaneamente.
        self.play(
            courier_tp.animate
                .scale(growth_factor)
                .set_fill("#5a6470", opacity=0.88)
                .set_stroke(C_TEXT, width=2.5),
            run_time=0.5,
        )
        elem = self._make_standard_stress_element(element_center)
        # particle_tp es ahora el cuadrado central — no necesitamos
        # crear uno nuevo. Solo reusamos las flechas/labels de `elem`.

        # ─── σx, σy aparecen en las 4 caras (normales — cyan) ────────
        # SIMULTANEAMENTE las trazas del vuelo se desvanecen: el alumno
        # ya vio el camino, ahora la atencion debe centrarse en el stress
        # element. Las particulas estaticas (particle_tp/dp) SIGUEN
        # visibles en sus modelos — marcan "este analisis viene de aqui".
        # Las 4 caras muestran el equilibrio de fuerzas (pares opuestos).
        self.add(elem["sigma_y"], elem["sigma_x"],
                 elem["sigma_y_bot"], elem["sigma_x_left"],
                 elem["label_sy"], elem["label_sx"])
        self.play(
            FadeOut(trail_tp),
            FadeOut(trail_dp),
            GrowArrow(elem["sigma_y"]),
            GrowArrow(elem["sigma_x"]),
            GrowArrow(elem["sigma_y_bot"]),
            GrowArrow(elem["sigma_x_left"]),
            Write(elem["label_sy"]),
            Write(elem["label_sx"]),
            run_time=0.8,
        )

        # ─── 4.5..4.9s — Pausa para absorber σ antes de τ ────────────
        self.wait(0.4)

        # ─── 4.9..5.5s — τxy aparecen en las 4 caras (cortantes — lavanda) ─
        # Par CCW de tangenciales: top→der, right→arriba, bot→izq, left→abajo.
        # La simetria σ_xy = σ_yx queda visible en los pares ortogonales.
        self.add(elem["tau_top"], elem["tau_right"],
                 elem["tau_bot"], elem["tau_left"],
                 elem["label_tau_top"], elem["label_tau_right"])
        self.play(
            GrowArrow(elem["tau_top"]),
            GrowArrow(elem["tau_right"]),
            GrowArrow(elem["tau_bot"]),
            GrowArrow(elem["tau_left"]),
            Write(elem["label_tau_top"]),
            Write(elem["label_tau_right"]),
            run_time=0.6,
        )

        # ─── HOLD (1.6 s) para lectura del elemento ───────────────────
        # Con 8 brazos (4 σ + 4 τ) + 4 labels, el alumno necesita mas
        # tiempo que con la version original de 4 brazos. 1.6s deja
        # respiro para reconocer simetria + equilibrio antes del fade.
        self.wait(1.6)

        # ─── Fade-out para loop seamless ─────────────────────────────
        # Se desvanecen: el courier convertido en stress element central,
        # las DOS particulas estaticas (en cada modelo), y todas las
        # flechas/labels. Los trails ya se desvanecieron antes (en el
        # play de σ arrows).
        self.play(
            FadeOut(courier_tp),       # central stress element
            FadeOut(particle_tp),      # estatica en TP slice
            FadeOut(particle_dp),      # estatica en DP slice
            FadeOut(elem["sigma_y"]),
            FadeOut(elem["sigma_x"]),
            FadeOut(elem["sigma_y_bot"]),
            FadeOut(elem["sigma_x_left"]),
            FadeOut(elem["tau_top"]),
            FadeOut(elem["tau_right"]),
            FadeOut(elem["tau_bot"]),
            FadeOut(elem["tau_left"]),
            FadeOut(elem["label_sy"]),
            FadeOut(elem["label_sx"]),
            FadeOut(elem["label_tau_top"]),
            FadeOut(elem["label_tau_right"]),
            tp["geometry"].animate.set_opacity(0),
            dp["geometry"].animate.set_opacity(0),
            *[FadeOut(a) for a in tp["loads"]],
            *[FadeOut(a) for a in dp["loads"]],
            run_time=0.5,
        )

    # ─── Layout: bandas + separadores + ECUACIONES estaticas ───────
    def _build_layout(self):
        # SIN titulos "TENSIÓN PLANA" / "DEFORMACIÓN PLANA" arriba —
        # son redundantes con los chips del AnalysisTypeDialog (que
        # dicen exactamente lo mismo). Ademas la geometria de cada
        # columna (placa con remaches vs presa) es visualmente
        # inequivoca, no hace falta titulo de texto para distinguir.

        # Ecuaciones de hipotesis (banda inferior, SIEMPRE visibles).
        # Estas SI se quedan — describen la HIPOTESIS FISICA del caso,
        # no la identidad del caso (lo cual ya hace el chip). El alumno
        # debe poder leer "σz=0 vs εz=0" en cualquier momento del loop.
        eq_tp = MathTex(r"\sigma_z = 0", color=C_EQUATION).scale(1.15)
        eq_tp.move_to([-3, -3.55, 0])
        eq_dp = MathTex(r"\varepsilon_z = 0", color=C_EQUATION).scale(1.15)
        eq_dp.move_to([3, -3.55, 0])

        # Separadores sutiles. Sep_top movido a y=3.50 para ocupar el
        # espacio liberado por los titulos eliminados (mas superficie
        # visual para las geometrias).
        sep_top  = Line([-6,  3.50, 0], [6,  3.50, 0], color=C_SEPARATOR, stroke_width=1)
        sep_bot  = Line([-6, -3.15, 0], [6, -3.15, 0], color=C_SEPARATOR, stroke_width=1)
        sep_vert = Line([0,   3.50, 0], [0, -3.15, 0], color=C_SEPARATOR, stroke_width=1)

        # Sistema XYZ UNIVERSAL (un solo icono compartido por ambos
        # modelos — ambos usan el mismo frame global). Ubicado en la
        # banda inferior, centrado sobre el separador vertical entre
        # las dos ecuaciones σz=0 y εz=0. Pequeno para no competir
        # visualmente con las ecuaciones.
        axes_universal = self._make_axes(
            np.array([0, -3.62, 0]), sz=0.26, label_scale=0.16,
        )

        self.add(eq_tp, eq_dp,
                 sep_top, sep_bot, sep_vert, axes_universal)

    # ─── TP (ACTIVO): chapa industrial atornillada ────────────────────
    def _build_tp_plate(self):
        """Chapa metalica rectangular (panel industrial atornillado)
        traccionada por pinzas. Realismo visual basado en iluminacion:
          - Gradiente fuerte en cara frontal (sheen UP = 0.45, claro
            arriba, oscuro abajo — luz cenital frontal).
          - Linea especular brillante en arista superior (sol catching).
          - Linea de oclusion ambiental en arista inferior (sombra).
          - Overlay de sombra sobre cara lateral derecha (cara apartada
            de la luz, propia de proyeccion isometrica 25°).
          - Sombra inferior por debajo del back/bottom edge.
          - Remaches con 5 capas (shadow + washer ring + head +
            highlight + glint) — pieza atornillada con volumen 3D real.
          - Junta horizontal sutil entre dos chapas.

        Geometria estandar: W=2.5, H=1.55, T=0.15.
        """
        center = np.array([-3.0, -0.1, 0])
        W, H, T = 2.5, 1.55, 0.15

        # ── Cara frontal con gradiente cenital fuerte ──
        front = Polygon(
            center + [-W/2, -H/2, 0],
            center + [ W/2, -H/2, 0],
            center + [ W/2,  H/2, 0],
            center + [-W/2,  H/2, 0],
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=1.0, stroke_width=1.8,
        )
        front.set_sheen_direction(UP)
        front.set_sheen(0.45, UP)  # antes 0.25, mas dramatico

        bo = iso(T)
        top = Polygon(
            center + [-W/2, H/2, 0],
            center + [ W/2, H/2, 0],
            center + [ W/2, H/2, 0] + bo,
            center + [-W/2, H/2, 0] + bo,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.92, stroke_width=1.4,  # mas opaca (catches light)
        )
        top.set_sheen(0.30, UP)

        right_face = Polygon(
            center + [W/2, -H/2, 0],
            center + [W/2,  H/2, 0],
            center + [W/2,  H/2, 0] + bo,
            center + [W/2, -H/2, 0] + bo,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.65, stroke_width=1.4,
        )
        # Overlay de sombra sobre la cara derecha (esta cara se aleja
        # del observador en iso 25° → recibe menos luz)
        right_shadow = Polygon(
            center + [W/2, -H/2, 0],
            center + [W/2,  H/2, 0],
            center + [W/2,  H/2, 0] + bo,
            center + [W/2, -H/2, 0] + bo,
            fill_color="#0a0c0f", fill_opacity=0.32, stroke_width=0,
        )

        back = Polygon(
            center + [-W/2, -H/2, 0] + bo,
            center + [ W/2, -H/2, 0] + bo,
            center + [ W/2,  H/2, 0] + bo,
            center + [-W/2,  H/2, 0] + bo,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.20, stroke_width=1, stroke_opacity=0.4,
        )

        # ── Junta horizontal (costura entre dos chapas atornilladas) ──
        joint = Line(
            center + [-W/2 + 0.10, 0, 0],
            center + [ W/2 - 0.10, 0, 0],
            color="#2a2d33", stroke_width=1.2, stroke_opacity=0.55,
        )
        joint_highlight = Line(
            center + [-W/2 + 0.10, 0.008, 0],
            center + [ W/2 - 0.10, 0.008, 0],
            color="#9aa5b1", stroke_width=0.5, stroke_opacity=0.35,
        )

        # ── Linea especular en arista superior (luz cenital catching) ──
        top_specular = Line(
            center + [-W/2 + 0.04, H/2 - 0.008, 0],
            center + [ W/2 - 0.04, H/2 - 0.008, 0],
            color="#f1f3f5", stroke_width=2.4, stroke_opacity=0.65,
        )

        # ── Linea de oclusion ambiental en arista inferior ──
        bottom_ao = Line(
            center + [-W/2 + 0.04, -H/2 + 0.008, 0],
            center + [ W/2 - 0.04, -H/2 + 0.008, 0],
            color="#0a0c0f", stroke_width=2.4, stroke_opacity=0.55,
        )

        # (Sombra arrojada inferior eliminada: se veia como rectangulo
        # opaco abajo de la chapa, no como sombra suave. Sin un
        # gradiente radial verdadero, no aporta realismo.)

        # ── REMACHES con 5 capas para sensacion 3D real ──
        # Tamaño reducido ~26% respecto a la version anterior
        # (radius 0.054 → 0.040): los remaches a 7% de H se veian
        # decorativos; ahora a ~5% de H quedan claramente identificables
        # sin dominar visualmente la chapa. Proporcion mas cercana a
        # paneles industriales reales (2-3% en realidad).
        def _make_industrial_rivet(pos):
            """Remache con sombra + washer ring + cabeza + highlight."""
            # Drop shadow (offset abajo-derecha, simula luz cenital)
            shadow = Circle(
                radius=0.044, color="#0a0c0f", fill_color="#0a0c0f",
                fill_opacity=0.55, stroke_width=0,
            ).move_to(pos + np.array([0.010, -0.010, 0]))
            # Washer ring (arandela oscura debajo del remache)
            washer = Annulus(
                inner_radius=0.040, outer_radius=0.060,
                color="#1a1d22", fill_color="#1a1d22",
                fill_opacity=0.78, stroke_width=0,
            ).move_to(pos)
            # Cabeza del remache (boton hemisferico)
            head = Circle(
                radius=0.040, color=C_RIVET, fill_color=C_RIVET,
                fill_opacity=1, stroke_width=0.4, stroke_opacity=0.8,
            ).move_to(pos)
            # Highlight (curva clara arriba-izquierda)
            highlight = Dot(
                radius=0.017, color="#dee2e6", fill_opacity=0.55,
            ).move_to(pos + np.array([-0.014, 0.014, 0]))
            # Glint puntual (reflejo brillante)
            glint = Dot(
                radius=0.0075, color=WHITE, fill_opacity=0.90,
            ).move_to(pos + np.array([-0.017, 0.017, 0]))
            return VGroup(shadow, washer, head, highlight, glint)

        rivets = VGroup()
        edge_margin = 0.16
        # 5 remaches en fila superior + 5 en fila inferior
        for dy_sign in (-1, 1):
            y_pos = dy_sign * (H/2 - edge_margin)
            for i in range(5):
                t = i / 4
                x_pos = -W/2 + edge_margin + t * (W - 2 * edge_margin)
                rivets.add(_make_industrial_rivet(
                    center + [x_pos, y_pos, 0]
                ))
        # 1 remache al centro de cada lado (refuerza el panel)
        for dx_sign in (-1, 1):
            x_pos = dx_sign * (W/2 - edge_margin)
            rivets.add(_make_industrial_rivet(
                center + [x_pos, 0, 0]
            ))

        # Reflejo brillante sutil en la cara superior (luz cenital)
        highlight_pts = [
            center + [-W/2 + 0.18, H/2 + 0.005, 0],
            center + [-W/2 + 0.18 + W * 0.55, H/2 + 0.005, 0],
            center + [-W/2 + 0.18 + W * 0.55, H/2 + 0.005, 0] + bo * 0.35,
            center + [-W/2 + 0.18, H/2 + 0.005, 0] + bo * 0.35,
        ]
        top_highlight = Polygon(
            *highlight_pts,
            color="#dee2e6", fill_color="#dee2e6",
            fill_opacity=0.40, stroke_width=0,
        )

        # Z-order: back faces (deepest) → right_face + shadow overlay
        # → top + highlight → front → joint y especulares → rivets
        # (encima de todo).
        plate_group = VGroup(
            back, right_face, right_shadow, top, top_highlight,
            front, joint, joint_highlight,
            top_specular, bottom_ao, rivets,
        )

        # ── Estructura comun (pinzas + cargas) ──
        geometry = VGroup(plate_group)

        pinch_left = self._make_pinch(center + [-W/2 - 0.24, 0, 0],
                                       facing_right=True)
        pinch_right = self._make_pinch(center + [W/2 + 0.24, 0, 0],
                                        facing_right=False)
        ARROW_LEN = 0.55
        load_left = VGroup(
            Arrow(center + [-W/2 - 1.04, 0.32, 0],
                  center + [-W/2 - 1.04 - ARROW_LEN, 0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
            Arrow(center + [-W/2 - 1.04, -0.32, 0],
                  center + [-W/2 - 1.04 - ARROW_LEN, -0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
        )
        load_right = VGroup(
            Arrow(center + [W/2 + 1.04, 0.32, 0],
                  center + [W/2 + 1.04 + ARROW_LEN, 0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
            Arrow(center + [W/2 + 1.04, -0.32, 0],
                  center + [W/2 + 1.04 + ARROW_LEN, -0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
        )
        loads = [*load_left, *load_right]
        self.add(pinch_left, pinch_right)
        geometry.add(pinch_left, pinch_right)

        left_pull = VGroup(pinch_left, *load_left)
        right_pull = VGroup(pinch_right, *load_right)

        return {
            "geometry": geometry,
            "plate_group": plate_group,
            "plate_center": center,
            "plate_width": W,
            "loads": loads,
            "left_pull": left_pull,
            "right_pull": right_pull,
        }

    # ─── TP (BACKUP 1): viga peraltada simplemente apoyada ────────────
    def _build_tp_beam(self):
        """Viga peraltada (deep beam) simplemente apoyada con carga
        distribuida vertical uniforme. Ejemplo canonico de tension plana
        para FEM: espesor T << altura h << span L (T<<h y h<L, ratio L/h
        chico → shear lag importante → no es Euler-Bernoulli, requiere
        analisis 2D plane stress).

        Geometria:
          - Span L = 2.6, altura h = 1.2 (L/h ≈ 2.17, claramente
            peraltada — Cook capitulo 6, Bathe seccion 5.6).
          - Espesor T = 0.05 → iso shift ~0.045 unidades, casi
            imperceptible visualmente → comunica 'delgado en Z'.

        Apoyos: pasador (pin) en bottom-left, rodillo en bottom-right.
        Simbolos estandar de Resmat (triangulo + base + hatching diagonal
        a -45°; el rodillo agrega un circulo entre triangulo y base).

        Carga: 8 flechas distribuidas verticales hacia abajo en el borde
        superior, equispaciadas.

        Deformacion: pandeo descendente con perfil exacto de viga
        simplemente apoyada bajo carga uniforme:
          δ(s)/δmax = (16/5) · s(1-s)(1 + s - s²)   con s = x/L
          - δ(0) = δ(1) = 0 (apoyos)
          - δ(0.5) = δmax (mid-span)
          - perfil exacto de wx(L³-2Lx²+x³)/(24EI) normalizado.

        Subdivision: front/back/top polygons subdividen sus aristas
        horizontales en N=18 segmentos para que apply_function curve la
        silueta (con solo 4 vertices el pandeo seria invisible: como
        δ=0 en ambos extremos, los corners no se moverian y la
        rectangulo no cambiaria). Lo mismo para las hairlines de
        textura (VMobject con 24 puntos).
        """
        center = np.array([-3.0, -0.1, 0])
        L = 2.6
        h = 1.2
        T = 0.05  # casi sin profundidad → 'obviamente delgado en Z'
        N_SUB = 18  # subdivisiones de aristas horizontales

        bl = center + np.array([-L/2, -h/2, 0])
        br = center + np.array([ L/2, -h/2, 0])
        tr = center + np.array([ L/2,  h/2, 0])
        tl = center + np.array([-L/2,  h/2, 0])
        bo = iso(T)

        def _subdivided_rect(p_bl, p_br, p_tr, p_tl, n, **kw):
            """Polygon con aristas horizontales subdivididas en n
            segmentos (las verticales quedan rectas, 1 segmento)."""
            pts = []
            for i in range(n):
                t = i / n
                pts.append(p_bl + t * (p_br - p_bl))
            pts.append(p_br)
            pts.append(p_tr)
            for i in range(1, n):
                t = i / n
                pts.append(p_tr + t * (p_tl - p_tr))
            pts.append(p_tl)
            return Polygon(*pts, **kw)

        # Cara frontal — subdividida para curvarse con apply_function
        front = _subdivided_rect(
            bl, br, tr, tl, N_SUB,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=1.0, stroke_width=1.8,
        )
        front.set_sheen_direction(UP)
        front.set_sheen(0.20, UP)

        # Cara trasera (iso shift pequeño)
        back = _subdivided_rect(
            bl + bo, br + bo, tr + bo, tl + bo, N_SUB,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.25, stroke_width=1, stroke_opacity=0.5,
        )

        # Cara superior (parallelogram en iso) — subdividida en ambas
        # aristas horizontales (la del frente tl→tr y la del back
        # tr+bo→tl+bo). Nota: en este Polygon, p_bl=tl, p_br=tr,
        # p_tr=tr+bo, p_tl=tl+bo (el "fondo" del top face es la arista
        # del beam top, el "techo" del top face es el back-top).
        top = _subdivided_rect(
            tl, tr, tr + bo, tl + bo, N_SUB,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.85, stroke_width=1.4,
        )

        # Cara lateral derecha (en x=L/2, s=1 → sag=0, no necesita
        # subdividirse: queda rectangulo aun despues del bend).
        right_face = Polygon(
            br, tr, tr + bo, br + bo,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.7, stroke_width=1.4,
        )

        # ── Textura: 2 hairlines horizontales (acero laminado).
        # Como VMobject de 25 puntos para que se curven con el beam. ──
        def _horizontal_curve(x0, x1, y, n=24, **kw):
            pts = [[x0 + (i / n) * (x1 - x0), y, 0]
                   for i in range(n + 1)]
            v = VMobject()
            v.set_points_as_corners(pts)
            v.set_stroke(**kw)
            return v

        brush = VGroup()
        for hy_frac in (-0.28, 0.22):
            hy = center[1] + hy_frac * h
            brush.add(_horizontal_curve(
                bl[0] + 0.15, br[0] - 0.15, hy,
                n=24, color=C_STEEL_DARK, width=0.7, opacity=0.28,
            ))

        beam_group = VGroup(back, right_face, top, front, brush)

        # ── Apoyos (fuera de beam_group → NO se deforman) ──
        pin = self._make_pin_support(bl)
        roller = self._make_roller_support(br)

        # ── Carga distribuida vertical (8 flechas hacia abajo) ──
        n_loads = 8
        load_y_top = tl[1] + 0.42
        load_y_bottom = tl[1] + 0.06
        loads = []
        margin = L * 0.04
        for i in range(n_loads):
            t = (i + 0.5) / n_loads
            lx = bl[0] + margin + t * (L - 2 * margin)
            arrow = Arrow(
                [lx, load_y_top, 0],
                [lx, load_y_bottom, 0],
                color=C_LOAD, buff=0, stroke_width=4,
                max_tip_length_to_length_ratio=0.30,
            )
            loads.append(arrow)

        geometry = VGroup(beam_group, pin, roller)

        # ── Sag function (closure sobre L y beam_left_x) ──
        beam_left_x = bl[0]
        MAX_SAG = 0.13  # ~11% de h, visible sin caricaturizar

        def beam_bend(point):
            x, y, z = point
            s = (x - beam_left_x) / L
            s = max(0.0, min(1.0, s))
            profile = (16.0/5.0) * s * (1.0 - s) * (1.0 + s - s * s)
            sag = MAX_SAG * profile
            return np.array([x, y - sag, z])

        return {
            "geometry": geometry,
            "plate_group": beam_group,    # compat con construct
            "plate_center": center,        # slice center (geom center)
            "plate_width": L,              # no usado en modo beam
            "loads": loads,
            "left_pull": VGroup(),         # no aplica
            "right_pull": VGroup(),        # no aplica
            "beam_bend": beam_bend,        # usado por construct para slice
        }

    # ── Apoyos: simbolos estandar de Resmat (pin + roller) ───────────
    def _make_pin_support(self, top_pt: np.ndarray) -> VGroup:
        """Pin (pasador): triangulo apoyado en el nodo + base con
        hatching diagonal a -45°. Restringe x e y."""
        s = 0.20
        p_left = top_pt + np.array([-s, -s * 1.6, 0])
        p_right = top_pt + np.array([+s, -s * 1.6, 0])
        triangle = Polygon(
            top_pt, p_left, p_right,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=1, stroke_width=1.5,
        )
        base = Line(
            p_left + np.array([-0.10, 0, 0]),
            p_right + np.array([+0.10, 0, 0]),
            color=C_STEEL_DARK, stroke_width=2,
        )
        hatching = self._make_support_hatching(
            p_left[0] - 0.10, p_right[0] + 0.10, p_left[1],
        )
        return VGroup(triangle, base, hatching)

    def _make_roller_support(self, top_pt: np.ndarray) -> VGroup:
        """Rodillo: triangulo + circulo (rodillo) entre triangulo y base
        + base con hatching. Restringe solo y (deja libre x)."""
        s = 0.20
        p_left = top_pt + np.array([-s, -s * 1.4, 0])
        p_right = top_pt + np.array([+s, -s * 1.4, 0])
        triangle = Polygon(
            top_pt, p_left, p_right,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=1, stroke_width=1.5,
        )
        r_radius = 0.055
        roller_y = p_left[1] - r_radius - 0.01
        roller_center = np.array(
            [(p_left[0] + p_right[0]) / 2, roller_y, 0]
        )
        circle = Circle(
            radius=r_radius, color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=1, stroke_width=1.5,
        ).move_to(roller_center)
        base_y = roller_y - r_radius - 0.01
        base = Line(
            np.array([p_left[0] - 0.10, base_y, 0]),
            np.array([p_right[0] + 0.10, base_y, 0]),
            color=C_STEEL_DARK, stroke_width=2,
        )
        hatching = self._make_support_hatching(
            p_left[0] - 0.10, p_right[0] + 0.10, base_y,
        )
        return VGroup(triangle, circle, base, hatching)

    def _make_support_hatching(self, x_start: float, x_end: float,
                                y: float) -> VGroup:
        """Hatching diagonal a -45° debajo de la linea base de un apoyo
        (convencion universal de dibujo tecnico para suelo/fundacion)."""
        g = VGroup()
        count = 7
        for i in range(count):
            t = i / (count - 1)
            hx = x_start + t * (x_end - x_start)
            g.add(Line(
                np.array([hx, y, 0]),
                np.array([hx + 0.11, y - 0.11, 0]),
                color=C_STEEL_DARK, stroke_width=1, stroke_opacity=0.85,
            ))
        return g

    # ─── TP (LEGACY 2): probeta de traccion dog-bone (ASTM E8) ────────
    # Backup del intento que el usuario no aprobo (la dog-bone era una
    # probeta de laboratorio, no comunicaba "delgada en Z").
    # Acceder via TP_MODE = "dogbone".
    def _build_tp_dogbone(self):
        center = np.array([-3.0, -0.1, 0])
        # Probeta de traccion estandarizada. Extremos anchos (H_grip)
        # donde las pinzas agarran; seccion central angosta (H_gauge,
        # "gauge length") donde se mide la deformacion y donde la
        # contraccion de Poisson es perceptible visualmente. Las
        # transiciones conicas (taper) son las que delatan "esto es
        # una probeta diseñada, no un retazo".
        W, T = 2.5, 0.15
        H_grip = 1.55
        H_gauge = 0.78
        grip_len = 0.42
        taper_len = 0.32

        # 12 vertices CCW desde bottom-left
        #  0: BL outer   |  1: BL inner grip   |  2: BL gauge corner
        #  3: BR gauge   |  4: BR inner grip   |  5: BR outer
        #  6: TR outer   |  7: TR inner grip   |  8: TR gauge corner
        #  9: TL gauge   | 10: TL inner grip   | 11: TL outer
        fc_local = [
            np.array([-W/2,                          -H_grip/2,  0]),
            np.array([-W/2 + grip_len,               -H_grip/2,  0]),
            np.array([-W/2 + grip_len + taper_len,   -H_gauge/2, 0]),
            np.array([ W/2 - grip_len - taper_len,   -H_gauge/2, 0]),
            np.array([ W/2 - grip_len,               -H_grip/2,  0]),
            np.array([ W/2,                          -H_grip/2,  0]),
            np.array([ W/2,                           H_grip/2,  0]),
            np.array([ W/2 - grip_len,                H_grip/2,  0]),
            np.array([ W/2 - grip_len - taper_len,    H_gauge/2, 0]),
            np.array([-W/2 + grip_len + taper_len,    H_gauge/2, 0]),
            np.array([-W/2 + grip_len,                H_grip/2,  0]),
            np.array([-W/2,                           H_grip/2,  0]),
        ]
        front_pts = [center + p for p in fc_local]

        # Cara frontal (dog-bone, gradiente cenital)
        front = Polygon(
            *front_pts,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=1.0, stroke_width=1.8,
        )
        front.set_sheen_direction(UP)
        front.set_sheen(0.25, UP)

        bo = iso(T)

        # Cara trasera: misma silueta, desplazada en iso(T)
        back_pts = [p + bo for p in front_pts]
        back = Polygon(
            *back_pts,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.25, stroke_width=1, stroke_opacity=0.5,
        )

        # Cara superior: tira siguiendo el borde superior polilineal de
        # la dog-bone (vertices 6→7→8→9→10→11 front + reverso back).
        top_pts = (front_pts[6:12]
                   + [p + bo for p in front_pts[11:5:-1]])
        top = Polygon(
            *top_pts,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.85, stroke_width=1.4,
        )

        # Cara lateral derecha (rectangular, en el extremo de mordaza)
        right = Polygon(
            front_pts[5], front_pts[6],
            front_pts[6] + bo, front_pts[5] + bo,
            color=C_STEEL_DARK, fill_color=C_STEEL,
            fill_opacity=0.7, stroke_width=1.4,
        )

        # Reflejo brillante sutil en la zona gauge (parte plana del borde
        # superior — la transicion conica seria un highlight irregular)
        hl_xl = center[0] - (W/2 - grip_len - taper_len) + 0.05
        hl_xr = center[0] + (W/2 - grip_len - taper_len) - 0.05
        hl_y = center[1] + H_gauge/2 + 0.005
        top_highlight = Polygon(
            np.array([hl_xl, hl_y, 0]),
            np.array([hl_xr, hl_y, 0]),
            np.array([hl_xr, hl_y, 0]) + bo * 0.4,
            np.array([hl_xl, hl_y, 0]) + bo * 0.4,
            color="#dee2e6", fill_color="#dee2e6",
            fill_opacity=0.40, stroke_width=0,
        )

        # ── Detalles de superficie en la zona gauge ──
        # Sello "ST-37" (grado de acero estructural clasico) — comunica
        # "probeta normalizada de un material especifico" sin necesidad
        # de cartel externo. Pequeño y sutil para no competir con el
        # comportamiento visual.
        stamp = Text("ST-37", font="Consolas", weight=BOLD,
                     color=C_STEEL_DARK).scale(0.18)
        stamp.move_to(center + [-(W/2 - grip_len - taper_len) * 0.35,
                                H_gauge/2 - 0.18, 0])
        stamp.set_opacity(0.55)

        # 2 hairlines horizontales de acero laminado/bruñido en la zona
        # gauge. Muy sutiles — solo dan textura, no estructura.
        gauge_xl = center[0] - (W/2 - grip_len - taper_len) + 0.10
        gauge_xr = center[0] + (W/2 - grip_len - taper_len) - 0.10
        brush = VGroup()
        for hy_frac in (-0.30, 0.18):
            hy = center[1] + hy_frac * H_gauge
            brush.add(Line(
                [gauge_xl, hy, 0], [gauge_xr, hy, 0],
                color=C_STEEL_DARK, stroke_width=0.8, stroke_opacity=0.30,
            ))

        plate_group = VGroup(back, right, top, top_highlight,
                             front, brush, stamp)

        # Ejes XYZ: ahora son universales (uno solo, centrado abajo) en
        # vez de un set por columna. Se construyen en _build_layout.
        geometry = VGroup(plate_group)

        # ── Cargas: pinzas industriales TOCANDO la chapa ──
        # Los dientes emergen a sign*0.24 del anchor → para que la punta
        # de los dientes coincida con el borde de la chapa (±W/2):
        #   anchor.x = ±(W/2 + 0.24)
        pinch_left = self._make_pinch(center + [-W/2 - 0.24, 0, 0],
                                       facing_right=True)
        pinch_right = self._make_pinch(center + [W/2 + 0.24, 0, 0],
                                        facing_right=False)

        # Flechas DETRAS del mango de cada pinza, apuntando hacia afuera
        # (direccion de la traccion). Sin las pinzas tocando la placa no
        # queda espacio entre placa y pinza para flechas — entonces salen
        # del mango trasero como vectores de la fuerza aplicada.
        # Mango trasero: anchor.x ± (body_w + 0.30) = ±(W/2 + 1.04).
        ARROW_LEN = 0.55
        load_left = VGroup(
            Arrow(center + [-W/2 - 1.04, 0.32, 0],
                  center + [-W/2 - 1.04 - ARROW_LEN, 0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
            Arrow(center + [-W/2 - 1.04, -0.32, 0],
                  center + [-W/2 - 1.04 - ARROW_LEN, -0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
        )
        load_right = VGroup(
            Arrow(center + [W/2 + 1.04, 0.32, 0],
                  center + [W/2 + 1.04 + ARROW_LEN, 0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
            Arrow(center + [W/2 + 1.04, -0.32, 0],
                  center + [W/2 + 1.04 + ARROW_LEN, -0.32, 0],
                  color=C_LOAD, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.3),
        )
        loads = [*load_left, *load_right]
        self.add(pinch_left, pinch_right)
        geometry.add(pinch_left, pinch_right)

        # ── Grupos de "tiron" para sincronizar pinza + flechas con la
        # elongacion de la chapa: al estirar 1.05x, los bordes de la
        # chapa se desplazan ±0.0625; estos grupos reciben el mismo
        # shift en construct() para mantener el agarre fisico.
        left_pull = VGroup(pinch_left, *load_left)
        right_pull = VGroup(pinch_right, *load_right)

        return {
            "geometry": geometry,
            "plate_group": plate_group,
            "plate_center": center,
            "plate_width": W,
            "loads": loads,
            "left_pull": left_pull,
            "right_pull": right_pull,
        }

    def _make_pinch(self, anchor: np.ndarray, facing_right: bool) -> VGroup:
        """Gripper industrial estilizado con iluminacion realista.
        Composicion (atras → adelante):
          1. Sombra proyectada bajo el cuerpo (cast shadow).
          2. Mango trasero (barra actuadora) con su propio sheen.
          3. Cuerpo metalico amplio (trapecio) con gradiente fuerte.
          4. Specular en arista superior + AO en arista inferior.
          5. Hatching anti-deslizante en la cara de agarre.
          6. Dientes con shadow drop individual.
          7. Pivote/bolt visible en la articulacion mango-cuerpo
             (revela "herramienta articulada", no monolitica).
          8. Highlight cenital en el centro del cuerpo (catch luz).
        """
        sign = 1 if facing_right else -1
        body_w = 0.50
        body_h = 0.85

        # Sombra arrojada del cuerpo (offset abajo-adelante)
        shadow_offset = np.array([sign * 0.025, -0.025, 0])
        body_shadow = Polygon(
            anchor + [-sign * body_w, body_h / 2, 0] + shadow_offset,
            anchor + [ sign * 0.10, body_h / 2 - 0.12, 0] + shadow_offset,
            anchor + [ sign * 0.10, -body_h / 2 + 0.12, 0] + shadow_offset,
            anchor + [-sign * body_w, -body_h / 2, 0] + shadow_offset,
            fill_color="#0a0c0f", fill_opacity=0.45, stroke_width=0,
        )

        # Cuerpo principal — trapecio con gradiente fuerte
        body = Polygon(
            anchor + [-sign * body_w, body_h / 2, 0],
            anchor + [ sign * 0.10, body_h / 2 - 0.12, 0],
            anchor + [ sign * 0.10, -body_h / 2 + 0.12, 0],
            anchor + [-sign * body_w, -body_h / 2, 0],
            color="#3d4148", fill_color="#5a6470",
            fill_opacity=1, stroke_width=1.8,
        )
        body.set_sheen_direction(UP)
        body.set_sheen(0.38, UP)  # antes 0.18, mas dramatico

        # Specular en arista superior (sol cenital catching)
        spec_top = Line(
            anchor + [-sign * (body_w - 0.04), body_h / 2 - 0.006, 0],
            anchor + [ sign * 0.08, body_h / 2 - 0.12 - 0.006, 0],
            color="#f1f3f5", stroke_width=2.0, stroke_opacity=0.65,
        )

        # AO en arista inferior (sombra ambiental)
        ao_bot = Line(
            anchor + [-sign * (body_w - 0.04), -body_h / 2 + 0.006, 0],
            anchor + [ sign * 0.08, -body_h / 2 + 0.12 + 0.006, 0],
            color="#0a0c0f", stroke_width=2.0, stroke_opacity=0.55,
        )

        # Highlight cenital horizontal sobre el centro del cuerpo
        # (reflejo del sol en la curvatura superior)
        center_highlight = Polygon(
            anchor + [-sign * (body_w - 0.08), body_h * 0.28, 0],
            anchor + [ sign * 0.05, body_h * 0.22, 0],
            anchor + [ sign * 0.05, body_h * 0.32, 0],
            anchor + [-sign * (body_w - 0.08), body_h * 0.38, 0],
            fill_color="#c5cad1", fill_opacity=0.32, stroke_width=0,
        )

        # Hatching anti-deslizante en la cara de agarre
        hatching = VGroup()
        for hy in np.linspace(-body_h / 2 + 0.18, body_h / 2 - 0.18, 5):
            line = Line(
                anchor + [-sign * (body_w - 0.10), hy, 0],
                anchor + [ sign * 0.05, hy, 0],
                color="#2a2d33", stroke_width=1.3, stroke_opacity=0.55,
            )
            hatching.add(line)

        # Dientes con shadow drop individual
        teeth = VGroup()
        for dy in (-0.28, -0.14, 0.0, 0.14, 0.28):
            # Sombra del diente (offset hacia atras del cuerpo)
            t_shadow = Polygon(
                anchor + [ sign * 0.10, dy + 0.06, 0] +
                    np.array([-sign * 0.008, -0.012, 0]),
                anchor + [ sign * 0.24, dy, 0] +
                    np.array([-sign * 0.008, -0.012, 0]),
                anchor + [ sign * 0.10, dy - 0.06, 0] +
                    np.array([-sign * 0.008, -0.012, 0]),
                fill_color="#0a0c0f", fill_opacity=0.55, stroke_width=0,
            )
            # Diente principal
            t_body = Polygon(
                anchor + [ sign * 0.10, dy + 0.06, 0],
                anchor + [ sign * 0.24, dy, 0],
                anchor + [ sign * 0.10, dy - 0.06, 0],
                color="#2a2d33", fill_color="#3d4148",
                fill_opacity=1, stroke_width=0,
            )
            # Highlight en la punta del diente (reflejo)
            t_glint = Dot(
                radius=0.008, color="#dee2e6", fill_opacity=0.7,
            ).move_to(anchor + [ sign * 0.21, dy + 0.012, 0])
            teeth.add(t_shadow, t_body, t_glint)

        # Mango/actuador trasero con gradiente
        handle = Polygon(
            anchor + [-sign * body_w, 0.13, 0],
            anchor + [-sign * (body_w + 0.30), 0.07, 0],
            anchor + [-sign * (body_w + 0.30), -0.07, 0],
            anchor + [-sign * body_w, -0.13, 0],
            color="#2a2d33", fill_color="#3d4148",
            fill_opacity=1, stroke_width=1,
        )
        handle.set_sheen_direction(UP)
        handle.set_sheen(0.28, UP)

        # Pivote/bolt visible en la articulacion mango-cuerpo
        # (revela herramienta articulada — no es un block monolitico)
        pivot_pos = anchor + np.array([-sign * (body_w - 0.06), 0, 0])
        pivot_socket = Circle(
            radius=0.062, color="#0a0c0f", fill_color="#0a0c0f",
            fill_opacity=0.7, stroke_width=0,
        ).move_to(pivot_pos)
        pivot_head = Circle(
            radius=0.045, color="#1a1d22", fill_color="#5a6470",
            fill_opacity=1, stroke_width=0.6, stroke_opacity=0.9,
        ).move_to(pivot_pos)
        # Cruz central del bolt (cabeza Phillips/Allen sugerida)
        pivot_slot_h = Line(
            pivot_pos + np.array([-0.022, 0, 0]),
            pivot_pos + np.array([+0.022, 0, 0]),
            color="#1a1d22", stroke_width=1.4, stroke_opacity=0.9,
        )
        pivot_slot_v = Line(
            pivot_pos + np.array([0, -0.022, 0]),
            pivot_pos + np.array([0, +0.022, 0]),
            color="#1a1d22", stroke_width=1.4, stroke_opacity=0.9,
        )
        pivot_glint = Dot(
            radius=0.011, color=WHITE, fill_opacity=0.8,
        ).move_to(pivot_pos + np.array([-0.014, 0.014, 0]))
        pivot = VGroup(pivot_socket, pivot_head,
                       pivot_slot_h, pivot_slot_v, pivot_glint)

        return VGroup(
            body_shadow, handle, body, center_highlight,
            spec_top, ao_bot, hatching, teeth, pivot,
        )

    # ─── DP: presa 3D extruida con caras transparentes ────────────────
    def _build_dp(self):
        cx = 3.0
        base_y, crown_y = -2.0, 1.4
        # Perfil real de presa de gravedad (5 vertices, pentagonal):
        # cara upstream VERTICAL (1.95), cara downstream con QUIEBRE
        # tipico (parte superior steeper, parte inferior mas inclinada
        # → mayor masa al pie para resistir vuelco).
        knee_y = base_y + 1.6  # = -0.4 (transicion entre las dos pendientes)
        front_corners = [
            np.array([cx - 1.05, base_y, 0]),    # 0: base izq (upstream foot)
            np.array([cx + 1.50, base_y, 0]),    # 1: base der (downstream foot)
            np.array([cx + 0.10, knee_y, 0]),    # 2: quiebre downstream
            np.array([cx - 0.40, crown_y, 0]),   # 3: corona der
            np.array([cx - 1.05, crown_y, 0]),   # 4: corona izq (top vertical face)
        ]

        # Profundidad TOTAL del cuerpo (largo del valle en Z).
        # 2.6 unidades → claramente "Z >> seccion transversal".
        TOTAL_DEPTH = 2.6
        depth_vec = iso(TOTAL_DEPTH)
        back_corners = [p + depth_vec for p in front_corners]

        # ── Caras del prisma 3D extruido ──
        # Z-order (atras hacia adelante): back, top, side, front
        # (sin slice_indicators ni wire_edges — confundian como "ghosts
        # del estado pre-deformacion")

        # Cara TRASERA (muy transparente — solo silueta del fondo)
        back_face = Polygon(
            *back_corners,
            color=C_CONCRETE_DK, fill_color=C_CONCRETE,
            fill_opacity=0.12, stroke_width=1, stroke_opacity=0.28,
        )

        # Cara SUPERIOR (corona — atenuada). Va entre front[3]=corona der
        # y front[4]=corona izq, con back correspondientes.
        top_face = Polygon(
            front_corners[3], front_corners[4],
            back_corners[4], back_corners[3],
            color=C_CONCRETE_DK, fill_color=C_CONCRETE,
            fill_opacity=0.32, stroke_width=1.2, stroke_opacity=0.45,
        )

        # Cara LATERAL DERECHA: dos sub-caras por el quiebre del perfil.
        # Lower: base_der (1) → quiebre (2)
        # Upper: quiebre (2) → corona der (3)
        right_face_lower = Polygon(
            front_corners[1], front_corners[2],
            back_corners[2], back_corners[1],
            color=C_CONCRETE_DK, fill_color=C_CONCRETE,
            fill_opacity=0.25, stroke_width=1.2, stroke_opacity=0.40,
        )
        right_face_upper = Polygon(
            front_corners[2], front_corners[3],
            back_corners[3], back_corners[2],
            color=C_CONCRETE_DK, fill_color=C_CONCRETE,
            fill_opacity=0.27, stroke_width=1.2, stroke_opacity=0.42,
        )
        right_face = VGroup(right_face_lower, right_face_upper)

        # Cara FRONTAL — LA REBANADA del modelo FEM. Se mantiene como
        # cuerpo de concreto regular (con su gradiente) PERO se le
        # superpone un outline rojo brillante (slice_outline) para
        # marcarla explicitamente como la seccion 2D extraida del
        # modelo 3D — convencion de dibujo tecnico (la rebanada
        # destacada es la que se analiza en plane strain).
        dam_main = Polygon(
            *front_corners,
            color=C_CONCRETE_DK, fill_color=C_CONCRETE,
            fill_opacity=1.0, stroke_width=1.8,
        )
        # Gradiente vertical fuerte (claro arriba donde da el sol,
        # oscuro abajo donde queda en sombra propia)
        dam_main.set_sheen_direction(DOWN)
        dam_main.set_sheen(-0.38, DOWN)  # antes -0.20, mas dramatico

        # ── Iluminacion adicional de la presa ──
        # Linea especular en la corona (sol catching el borde superior)
        corona_specular = Line(
            np.array([front_corners[4][0] + 0.04, crown_y - 0.008, 0]),
            np.array([front_corners[3][0] - 0.04, crown_y - 0.008, 0]),
            color="#f5f5f4", stroke_width=2.3, stroke_opacity=0.75,
        )

        # Specular sutil en la cara upstream vertical (luz lateral
        # rebotando — la cara mirando al agua recibe luz reflejada)
        upstream_specular = Line(
            np.array([front_corners[0][0] + 0.005, base_y + 0.20, 0]),
            np.array([front_corners[0][0] + 0.005, crown_y - 0.10, 0]),
            color="#e7e5e4", stroke_width=1.5, stroke_opacity=0.40,
        )

        # ── REBANADA con ANCHO en Z (longitud de la presa) ──
        # Cada arista (top, downstream upper, downstream lower) se dibuja
        # como PAR de lineas paralelas: una en la cara frontal del slab
        # y otra iso-shifted por SLICE_WIDTH (la "longitud" del slab en
        # direccion Z). 6 lineas totales, comunican visualmente "esta
        # seccion tiene un ancho en Z" sin necesidad de fill ni poligonos
        # cerrados. Sin upstream face (oculta por agua), sin base (sobre
        # terreno). Se anade a slice_detail_group → deforma con la presa.
        SLICE_WIDTH = 0.32
        edge_pairs = [
            (front_corners[4], front_corners[3]),  # top: corona izq → corona der
            (front_corners[3], front_corners[2]),  # downstream upper: corona → knee
            (front_corners[2], front_corners[1]),  # downstream lower: knee → base
        ]
        slice_outline = VGroup()
        for p_start, p_end in edge_pairs:
            # Linea en la cara frontal del slab
            slice_outline.add(
                Line(p_start, p_end,
                     color=C_BLOCKER, stroke_width=4.5, stroke_opacity=0.95)
            )
            # Linea en la cara trasera del slab (iso-shifted por SLICE_WIDTH)
            slice_outline.add(
                Line(p_start + iso(SLICE_WIDTH), p_end + iso(SLICE_WIDTH),
                     color=C_BLOCKER, stroke_width=4.5, stroke_opacity=0.85)
            )

        # ── Helpers para el perfil pentagonal ──
        # La cara upstream es VERTICAL (x constante), la cara downstream
        # tiene un quiebre en knee_y.
        upstream_x = front_corners[0][0]  # = front_corners[4][0] (vertical)

        def downstream_x_at(y: float) -> float:
            """Devuelve la x de la cara downstream a la altura y."""
            if y <= knee_y:
                # Tramo inferior: base_der (1) → quiebre (2)
                t = (y - base_y) / (knee_y - base_y)
                return (front_corners[1][0] * (1 - t)
                        + front_corners[2][0] * t)
            # Tramo superior: quiebre (2) → corona der (3)
            t = (y - knee_y) / (crown_y - knee_y)
            return (front_corners[2][0] * (1 - t)
                    + front_corners[3][0] * t)

        # ── Detalles de realismo en la cara frontal ──

        # Juntas de construccion: 3 lineas horizontales
        construction_joints = VGroup()
        for jy_frac in [0.28, 0.52, 0.76]:
            jy = base_y + jy_frac * (crown_y - base_y)
            joint = Line(
                [upstream_x + 0.02, jy, 0],
                [downstream_x_at(jy) - 0.02, jy, 0],
                color=C_CONCRETE_DK, stroke_width=1.0, stroke_opacity=0.55,
            )
            construction_joints.add(joint)

        # Manchas verticales de filtracion (weathering streaks).
        # Se dibujan paralelas a la cara upstream (vertical).
        weathering = VGroup()
        for streak_x_frac in [0.30, 0.55, 0.80]:
            # Punto superior (cerca de corona)
            x_top_min = upstream_x + 0.10
            x_top_max = downstream_x_at(crown_y - 0.05) - 0.10
            x_pos = x_top_min + streak_x_frac * (x_top_max - x_top_min)
            # La mancha cae vertical desde la corona
            y_top = crown_y - 0.08
            # La mancha termina cuando topa con el agua (linea de mojado)
            y_bot = 0.85 + 0.05  # justo sobre water_top
            streak = Line(
                [x_pos, y_top, 0], [x_pos, y_bot, 0],
                color="#787470", stroke_width=1.8, stroke_opacity=0.28,
            )
            weathering.add(streak)

        # Linea de mojado (waterline mark)
        water_top = 0.85
        wm_xl = upstream_x
        wm_xr = downstream_x_at(water_top)
        wetline = Line(
            [wm_xl + 0.02, water_top, 0],
            [wm_xr - 0.02, water_top, 0],
            color="#5a544c", stroke_width=2.2, stroke_opacity=0.55,
        )

        # Textura de aggregate (solo cara frontal — donde es solida).
        # Respeta el perfil pentagonal via downstream_x_at + upstream_x.
        # Iluminacion: ~12% de los granos son "cuarzo" (mas brillante y
        # con halo claro) → simula reflejos puntuales de minerales que
        # catch la luz cenital cuando el alumno mira de cerca.
        rng = np.random.default_rng(seed=42)
        aggregate = VGroup()
        for _ in range(42):
            ty = rng.uniform(base_y + 0.15, crown_y - 0.15)
            xl = upstream_x + 0.10
            xr = downstream_x_at(ty) - 0.10
            if xr <= xl:
                continue
            tx = rng.uniform(xl, xr)
            is_quartz = rng.random() < 0.13
            if is_quartz:
                agg_color = "#e7e5e4"
                agg_radius = rng.uniform(0.022, 0.030)
                opacity = 0.92
            else:
                agg_color = rng.choice([C_AGGREGATE, "#928d85", "#6b6760"])
                agg_radius = rng.uniform(0.018, 0.028)
                opacity = 0.7
            pt = Dot(radius=agg_radius, color=agg_color,
                     fill_opacity=opacity)
            pt.move_to([tx, ty, 0])
            aggregate.add(pt)
            # Halo blanco alrededor del cuarzo (suma volumen)
            if is_quartz:
                halo = Dot(radius=agg_radius * 0.40, color=WHITE,
                           fill_opacity=0.85)
                halo.move_to([tx - agg_radius * 0.20,
                              ty + agg_radius * 0.20, 0])
                aggregate.add(halo)

        # ── Agua a la izquierda (extruida en Z, gradiente vertical) ──
        # water_top YA definida arriba (cerca de wetline).
        # IMPORTANTE: el agua NO rota con la presa (las superficies de
        # agua quedan horizontales por gravedad). Pero la presa se inclina
        # bajo la presion hidrostatica → su cara upstream se desplaza
        # hacia la derecha. Para que no aparezca un gap visible entre el
        # agua y la presa inclinada, extendemos el borde derecho del
        # agua 0.25 unidades hacia adentro de la presa. El dam_main esta
        # dibujado DESPUES del agua en z-order → cubre la extension.
        # Con cara upstream vertical: contacto agua-presa es una linea
        # vertical a x = upstream_x para todo el rango water [base_y, water_top].
        x_dam_at_water_front = upstream_x
        water_left_x = cx - 2.55
        OVERLAP = 0.25  # extension del agua hacia dentro de la presa

        water_front_pts = [
            np.array([water_left_x, base_y, 0]),
            np.array([upstream_x + OVERLAP, base_y, 0]),
            np.array([upstream_x + OVERLAP, water_top, 0]),
            np.array([water_left_x, water_top, 0]),
        ]
        water_back_pts = [p + depth_vec for p in water_front_pts]

        # Lateral izq del agua (extension hacia atras en Z)
        water_left_side = Polygon(
            water_front_pts[0], water_front_pts[3],
            water_back_pts[3], water_back_pts[0],
            color=C_WATER_DK, fill_color=C_WATER_DK,
            fill_opacity=0.30, stroke_width=0,
        )
        # Superficie del agua (top face, 3D)
        water_surface_face = Polygon(
            water_front_pts[3], water_front_pts[2],
            water_back_pts[2], water_back_pts[3],
            color=C_WATER, fill_color=C_WATER,
            fill_opacity=0.42, stroke_width=0,
        )
        # Frente del agua: dos capas para gradiente (oscuro abajo,
        # azul claro arriba). Simula columna de agua con profundidad.
        water_front_dark = Polygon(
            *water_front_pts,
            color=C_WATER_DK, fill_color=C_WATER_DK,
            fill_opacity=0.55, stroke_width=0,
        )
        # Capa clara arriba: rectangulo cubriendo la mitad superior
        water_mid_y = (base_y + water_top) / 2
        water_front_light = Polygon(
            [water_left_x, water_mid_y, 0],
            [upstream_x + OVERLAP, water_mid_y, 0],
            [upstream_x + OVERLAP, water_top, 0],
            [water_left_x, water_top, 0],
            color=C_WATER, fill_color=C_WATER,
            fill_opacity=0.32, stroke_width=0,
        )
        # Onda en la superficie frontal (mas marcada). Termina en el
        # borde extendido — la onda se "esconde" detras del dam_main
        # cuando la presa flecta hacia downstream.
        wave_pts = []
        glint_pts = []  # subset central donde refleja el sol
        nx = 22
        for i in range(nx + 1):
            t = i / nx
            x = (water_left_x
                 + t * (x_dam_at_water_front + OVERLAP - water_left_x))
            y = water_top + 0.030 * np.sin(t * 10 * np.pi)
            wave_pts.append([x, y, 0])
            if 0.30 <= t <= 0.65:
                glint_pts.append([x, y + 0.006, 0])
        water_surface_line = VMobject()
        water_surface_line.set_points_as_corners(wave_pts)
        water_surface_line.set_stroke(WHITE, width=1.3, opacity=0.6)

        # ── Glint solar sobre la superficie (banda central brillante) ──
        # Banda de reflejo blanco-amarillenta sobre las olas en la zona
        # central, simulando reflejo del sol cenital en la lamina de
        # agua. Termina mas chica en los bordes (peak central).
        water_glint = VMobject()
        if len(glint_pts) >= 2:
            water_glint.set_points_as_corners(glint_pts)
            water_glint.set_stroke("#fef9c3", width=2.8, opacity=0.65)

        # ── Terreno: simbolo estandar de "tierra/empotramiento" ──
        # Linea horizontal solida + hatching diagonal a -45° debajo.
        # Convencion universal en dibujo tecnico para suelo/fundacion.
        x_left_ground = water_left_x - 0.30
        x_right_ground = cx + 2.40

        ground_line = Line(
            [x_left_ground, base_y, 0],
            [x_right_ground, base_y, 0],
            color=C_GROUND, stroke_width=2.5,
        )
        hatching_lines = VGroup()
        hatch_step = 0.22
        hatch_len = 0.22
        hx = x_left_ground
        while hx < x_right_ground:
            h_line = Line(
                [hx, base_y, 0],
                [hx + hatch_len * 0.707, base_y - hatch_len * 0.707, 0],
                color=C_GROUND, stroke_width=1.5, stroke_opacity=0.85,
            )
            hatching_lines.add(h_line)
            hx += hatch_step
        ground = VGroup(ground_line, hatching_lines)
        # ground_back: eliminado (sin extension Z del terreno)

        # Ejes XYZ: ahora son universales (uno solo, centrado abajo) en
        # vez de un set por columna. Se construyen en _build_layout.

        # Grupo deformable (recibe shear bajo presion hidrostatica)
        dam_solid_group = VGroup(
            back_face, top_face, right_face,
        )
        slice_detail_group = VGroup(
            dam_main, aggregate,
            construction_joints, weathering, wetline,
            corona_specular, upstream_specular,
            slice_outline,
        )

        # ── Cargas hidrostaticas: 6 flechas en distribucion triangular ──
        # Sin envelope con fill (se sobreponia al cuerpo). Solo flechas,
        # gruesas y largas, distribucion p(y) = rho * g * (water_top - y).
        # frac=1 (corona): presion ~0, sin flecha. frac→0 (base): maxima.
        # La cobertura llega hasta frac=0.015 (≈ base) para que el alumno
        # no perciba un "hueco" en el fondo de la presa.
        ARROW_MAX_LEN = 1.20
        ARROW_MIN_LEN = 0.40
        loads = []
        for frac in [0.85, 0.68, 0.52, 0.36, 0.20, 0.05]:
            y_arrow = base_y + frac * (crown_y - base_y)
            length = ARROW_MIN_LEN + (ARROW_MAX_LEN - ARROW_MIN_LEN) * (1 - frac)
            arrow = Arrow(
                [upstream_x - length - 0.05, y_arrow, 0],
                [upstream_x - 0.05, y_arrow, 0],
                color=C_LOAD, buff=0, stroke_width=5.5,
                max_tip_length_to_length_ratio=0.25,
            )
            loads.append(arrow)

        # ── Sin try_arrows ni barriers ──
        # La "acotacion" del demo Z-blocking se elimino (causaba lectura
        # de dimensionado tecnico, no de fenomeno fisico). En su lugar
        # el video termina con una extraccion del elemento de esfuerzo
        # 2D, manejada desde construct().

        # ── Ensamblaje final ──
        # Lo siguiente recibe SHEAR (apply_function en construct):
        # - extrusion 3D del cuerpo (back/top/side transparentes)
        # - rebanada frontal SOLIDA (la "seccion 2D del FEM")
        # NO se mueve (queda fijo en el sistema de referencia):
        # - agua (superficie horizontal por gravedad)
        # - cargas hidrostaticas
        # - fundacion
        static_water = VGroup(
            water_left_side, water_surface_face,
            water_front_dark, water_front_light,
            water_surface_line, water_glint,
        )
        dam_solid_group.add(slice_detail_group)

        # Punto de apoyo: base de la presa (la flecha sera shear, no
        # rotacion — el shear hace que la corona se desplace y la base
        # quede fija, como una viga empotrada bajo presion hidrostatica).
        dam_base_y = base_y
        dam_crown_y = crown_y

        dam_assembly = VGroup(
            ground,                     # Fundacion: linea + hatching 45°
            static_water,               # Agua: NO se mueve
            dam_solid_group,            # Presa: FLECTA con perfil cubico
        )
        geometry = VGroup(dam_assembly)
        # Cargas (flechas): NO se hace self.add() aqui — el GrowArrow
        # las agrega a la escena cuando corresponde. Si las agregamos
        # aca, quedan visibles a tamaño completo desde el frame 0
        # (las loads NO estan dentro de dp["geometry"], asi que el
        # set_opacity(0) inicial no las afecta). Despues del GrowArrow
        # se mueven dentro de dam_solid_group para que el bend cubico
        # tambien las afecte y se muevan con la presa.

        # Centro de la cara frontal — origen visual del 2D stress element
        slice_center = np.mean(front_corners, axis=0)

        return {
            "geometry": geometry,
            "dam_solid_group": dam_solid_group,
            "slice_center": slice_center,
            "dam_base_y": dam_base_y,
            "dam_crown_y": dam_crown_y,
            "loads": loads,
        }

    # ─── Ejes X/Y/Z compactos ─────────────────────────────────────────
    def _make_axes(self, origin: np.ndarray, sz: float = 0.42,
                   label_scale: float = 0.20) -> VGroup:
        x = Arrow(origin, origin + RIGHT * sz,
                  color=C_AXIS_X, buff=0, stroke_width=2.5,
                  max_tip_length_to_length_ratio=0.35)
        y = Arrow(origin, origin + UP * sz,
                  color=C_AXIS_Y, buff=0, stroke_width=2.5,
                  max_tip_length_to_length_ratio=0.35)
        z = Arrow(origin, origin + iso(sz * 1.3),
                  color=C_AXIS_Z, buff=0, stroke_width=2.5,
                  max_tip_length_to_length_ratio=0.35)
        lx = Text("X", color=C_AXIS_X, weight=BOLD).scale(label_scale)
        lx.next_to(x.get_end(), RIGHT, buff=0.05)
        ly = Text("Y", color=C_AXIS_Y, weight=BOLD).scale(label_scale)
        ly.next_to(y.get_end(), UP, buff=0.05)
        lz = Text("Z", color=C_AXIS_Z, weight=BOLD).scale(label_scale)
        lz.next_to(z.get_end(), UR, buff=0.02)
        return VGroup(x, y, z, lx, ly, lz)

    # ─── Elemento de esfuerzo 2D estandar (notacion de libro) ─────────
    def _make_standard_stress_element(self, center: np.ndarray) -> dict:
        """Elemento 2D con notacion textbook completa (4 caras):

        Cada cara tiene su par σ (normal, hacia afuera) + τ (tangencial).
        Convencion positiva estandar de mecanica de materiales — τ_xy
        positivo corresponde al sentido CCW del par sobre el elemento:
          - Cara TOP    : σy ↑    , τxy →
          - Cara RIGHT  : σx →    , τxy ↑
          - Cara BOTTOM : σy ↓    , τxy ←   (equilibrio con cara top)
          - Cara LEFT   : σx ←    , τxy ↓   (equilibrio con cara right)
        Los pares cara-opuesta se cancelan en suma (equilibrio de
        fuerzas) y los pares de τ ortogonales son iguales (simetria
        del tensor σ_xy = σ_yx). Solo se etiquetan los simbolos una
        vez por tipo para evitar saturacion visual.

        Color del shear: lavanda `#c084fc` — distinto del ambar de las
        particulas (`#fbbf24`), del cyan de σ (`C_SENSOR`) y del naranja
        de las cargas (`C_LOAD`).
        """
        SIZE = 1.50
        half = SIZE / 2
        NORMAL_COLOR = C_SENSOR
        SHEAR_COLOR  = "#c084fc"  # lavanda — vease docstring

        sq = Square(side_length=SIZE).move_to(center)
        sq.set_fill("#5a6470", opacity=0.88)
        sq.set_stroke(C_TEXT, width=2.5)

        NORMAL_LEN = 0.70
        SHEAR_LEN  = 0.55
        gap = 0.06       # separacion entre flecha σ y la arista
        tan_gap = 0.05   # offset de τ hacia afuera de la arista

        # ── σ (4 caras): normales hacia afuera ──
        sigma_y = Arrow(
            center + UP * (half + gap),
            center + UP * (half + gap + NORMAL_LEN),
            color=NORMAL_COLOR, buff=0, stroke_width=5.5,
            max_tip_length_to_length_ratio=0.25,
        )
        sigma_x = Arrow(
            center + RIGHT * (half + gap),
            center + RIGHT * (half + gap + NORMAL_LEN),
            color=NORMAL_COLOR, buff=0, stroke_width=5.5,
            max_tip_length_to_length_ratio=0.25,
        )
        sigma_y_bot = Arrow(
            center + DOWN * (half + gap),
            center + DOWN * (half + gap + NORMAL_LEN),
            color=NORMAL_COLOR, buff=0, stroke_width=5.5,
            max_tip_length_to_length_ratio=0.25,
        )
        sigma_x_left = Arrow(
            center + LEFT * (half + gap),
            center + LEFT * (half + gap + NORMAL_LEN),
            color=NORMAL_COLOR, buff=0, stroke_width=5.5,
            max_tip_length_to_length_ratio=0.25,
        )

        # ── τ (4 caras): par CCW (top→der, right→arriba, bot→izq, left→abajo) ──
        tau_top = Arrow(
            center + LEFT * (SHEAR_LEN / 2) + UP * (half + tan_gap),
            center + RIGHT * (SHEAR_LEN / 2) + UP * (half + tan_gap),
            color=SHEAR_COLOR, buff=0, stroke_width=5,
            max_tip_length_to_length_ratio=0.28,
        )
        tau_right = Arrow(
            center + RIGHT * (half + tan_gap) + DOWN * (SHEAR_LEN / 2),
            center + RIGHT * (half + tan_gap) + UP * (SHEAR_LEN / 2),
            color=SHEAR_COLOR, buff=0, stroke_width=5,
            max_tip_length_to_length_ratio=0.28,
        )
        tau_bot = Arrow(
            center + RIGHT * (SHEAR_LEN / 2) + DOWN * (half + tan_gap),
            center + LEFT * (SHEAR_LEN / 2) + DOWN * (half + tan_gap),
            color=SHEAR_COLOR, buff=0, stroke_width=5,
            max_tip_length_to_length_ratio=0.28,
        )
        tau_left = Arrow(
            center + LEFT * (half + tan_gap) + UP * (SHEAR_LEN / 2),
            center + LEFT * (half + tan_gap) + DOWN * (SHEAR_LEN / 2),
            color=SHEAR_COLOR, buff=0, stroke_width=5,
            max_tip_length_to_length_ratio=0.28,
        )

        # LABELS — solo un rotulo por tipo (σx, σy, τxy) en la cara
        # canonica (top/right) para no saturar el cuadrado con 8 textos.
        label_sy = MathTex(r"\sigma_y", color=NORMAL_COLOR).scale(0.78)
        label_sy.next_to(sigma_y, UP, buff=0.10)
        label_sx = MathTex(r"\sigma_x", color=NORMAL_COLOR).scale(0.78)
        label_sx.next_to(sigma_x, RIGHT, buff=0.10)
        label_tau_top = MathTex(r"\tau_{xy}", color=SHEAR_COLOR).scale(0.62)
        label_tau_top.next_to(tau_top.get_end(), UP, buff=0.10)
        label_tau_right = MathTex(r"\tau_{xy}", color=SHEAR_COLOR).scale(0.62)
        label_tau_right.next_to(tau_right.get_end(), RIGHT, buff=0.10)

        return {
            "square": sq,
            "sigma_y": sigma_y,
            "sigma_x": sigma_x,
            "sigma_y_bot": sigma_y_bot,
            "sigma_x_left": sigma_x_left,
            "tau_top": tau_top,
            "tau_right": tau_right,
            "tau_bot": tau_bot,
            "tau_left": tau_left,
            "label_sy": label_sy,
            "label_sx": label_sx,
            "label_tau_top": label_tau_top,
            "label_tau_right": label_tau_right,
        }
