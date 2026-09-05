# -*- coding: utf-8 -*-
"""
Concepto #5 de logo para EduFEM: "BIRRETE-MALLA".

Un birrete academico de graduacion (mortarboard) cuyo TABLERO superior
(la tapa cuadrada en perspectiva isometrica) ES una malla de elementos
finitos 2x2 (estilo Q4) con nodos en las intersecciones. La borla cuelga
en amarillo de acento. Fundimos "Edu" (graduacion) con "FEM" (malla).

Solo Pillow + math. Determinista. Supersampling 1024 -> LANCZOS.
"""
import os
import math
from PIL import Image, ImageDraw

# ----------------------------------------------------------------------------
# Paleta de marca (hex EXACTOS)
# ----------------------------------------------------------------------------
AZUL        = (0x0d, 0x6e, 0xfd)   # fase pre / modelado
NARANJA     = (0xfd, 0x7e, 0x14)   # fase proceso
VERDE       = (0x19, 0x87, 0x54)   # fase post
NODO_CORNER = (0x4f, 0xc3, 0xf7)   # nodo vertice
NODO_MID    = (0x6f, 0xb8, 0xff)   # nodo medio
NODO_CENTER = (0xb8, 0x6f, 0xff)   # nodo centroide violeta
MALLA_VERDE = (0x81, 0xc7, 0x84)   # elemento / malla
ACENTO      = (0xff, 0xeb, 0x3b)   # seleccion / borla
BG_TOP      = (0x2e, 0x33, 0x3b)
BG_BOT      = (0x18, 0x1b, 0x1f)
BORDE       = (0x48, 0x50, 0x5a)
BLANCO      = (0xf2, 0xf4, 0xf7)

SS = 1024  # lienzo de supersampling


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def jet(t):
    """Colormap JET firma de resultados (rojo=max, verde=medio, azul=min)."""
    t = max(0.0, min(1.0, t))
    r = max(0.0, min(1.0, 1.5 - abs(4 * t - 3)))
    g = max(0.0, min(1.0, 1.5 - abs(4 * t - 2)))
    b = max(0.0, min(1.0, 1.5 - abs(4 * t - 1)))
    return (int(r * 255), int(g * 255), int(b * 255))


def rounded_tile(size, radius_frac=0.225):
    """Baldosa oscura con gradiente vertical + borde, estilo app icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # gradiente vertical en un buffer cuadrado
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        grad.putpixel((0, y), lerp(BG_TOP, BG_BOT, y / (size - 1)))
    grad = grad.resize((size, size))
    grad = grad.convert("RGBA")

    # mascara redondeada
    radius = int(size * radius_frac)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)

    # borde sutil
    d = ImageDraw.Draw(img)
    bw = max(2, int(size * 0.012))
    d.rounded_rectangle(
        [bw // 2, bw // 2, size - 1 - bw // 2, size - 1 - bw // 2],
        radius=radius, outline=BORDE + (255,), width=bw,
    )
    return img


def fill_quad(draw, pts, color):
    draw.polygon(pts, fill=color)


def line_quad_edges(draw, pts, color, width):
    n = len(pts)
    for i in range(n):
        draw.line([pts[i], pts[(i + 1) % n]], fill=color, width=width, joint="curve")


# ----------------------------------------------------------------------------
# Construccion del birrete
# ----------------------------------------------------------------------------
def build_logo(size, small=False):
    img = rounded_tile(size)
    d = ImageDraw.Draw(img, "RGBA")

    cx = size * 0.50
    # El birrete se centra ligeramente arriba para dejar caer la borla.
    cy_board = size * 0.40   # centro del tablero (mortarboard)

    # --- Tablero superior: rombo isometrico (cuadrado en perspectiva) ---
    # half-anchos del rombo
    hw = size * 0.345        # mitad ancho horizontal
    hh = size * 0.180        # mitad alto vertical (perspectiva aplastada)

    top    = (cx,        cy_board - hh)
    right  = (cx + hw,   cy_board)
    bottom = (cx,        cy_board + hh)
    left   = (cx - hw,   cy_board)
    board = [top, right, bottom, left]

    # ------------------------------------------------------------------
    # Casquete del birrete (skull cap) — DIBUJADO PRIMERO (queda detras
    # del tablero, conectado bajo el rombo). Trapecio + base curva, azul.
    # ------------------------------------------------------------------
    cap_w_top = hw * 0.62
    cap_w_bot = hw * 0.52
    cap_top_y = cy_board + hh * 0.05          # arranca bajo el centro del rombo
    cap_h = size * 0.165
    cap_top_l = (cx - cap_w_top, cap_top_y)
    cap_top_r = (cx + cap_w_top, cap_top_y)
    cap_bot_r = (cx + cap_w_bot, cap_top_y + cap_h)
    cap_bot_l = (cx - cap_w_bot, cap_top_y + cap_h)
    cap = [cap_top_l, cap_top_r, cap_bot_r, cap_bot_l]
    azul_osc = lerp(AZUL, BG_BOT, 0.30)
    d.polygon(cap, fill=azul_osc + (255,))
    # franja iluminada izquierda (volumen)
    cap_lit = [cap_top_l,
               (cx, cap_top_y),
               (cx, cap_top_y + cap_h),
               cap_bot_l]
    d.polygon(cap_lit, fill=AZUL + (255,))
    # base curva del casquete
    d.ellipse([cap_bot_l[0], cap_top_y + cap_h - cap_h * 0.28,
               cap_bot_r[0], cap_top_y + cap_h + cap_h * 0.28],
              fill=azul_osc + (255,))

    # --- Sombra suave del tablero (offset hacia abajo) ---
    sh = int(size * 0.020)
    shadow = [(p[0], p[1] + sh) for p in board]
    d.polygon(shadow, fill=(0, 0, 0, 110))

    # --- Relleno base del tablero ---
    d.polygon(board, fill=(0x20, 0x25, 0x2c, 255))

    # ------------------------------------------------------------------
    # MALLA de elementos finitos sobre el tablero (rejilla 2x2 -> Q4 + N9)
    # Parametrizamos el rombo con coords bilineales (s,t) en [0,1]^2:
    #   P(s,t) = (1-s)(1-t)·left' + ... usando las 4 esquinas del rombo.
    # Para que sea una grilla en perspectiva usamos las diagonales:
    #   esquina LL = left, LR = top, UR = right, UL = bottom (rotado)
    # ------------------------------------------------------------------
    # Esquinas logicas del cuadrado (en orden) -> rombo
    A = left     # (0,0)
    B = top      # (1,0)
    C = right    # (1,1)
    D = bottom   # (0,1)

    def bilin(s, t):
        x = ((1 - s) * (1 - t) * A[0] + s * (1 - t) * B[0]
             + s * t * C[0] + (1 - s) * t * D[0])
        y = ((1 - s) * (1 - t) * A[1] + s * (1 - t) * B[1]
             + s * t * C[1] + (1 - s) * t * D[1])
        return (x, y)

    N = 2  # 2x2 elementos -> firma Q9 (corner/mid/center)
    # Rellenar cada celda con un tinte JET para evocar resultados FEM.
    # Recorrido en abanico (azul -> verde -> naranja -> rojo) por celda,
    # asi las 4 celdas quedan claramente distintas y vivas.
    cell_t = {(0, 0): 0.12, (1, 0): 0.40, (0, 1): 0.62, (1, 1): 0.88}
    for i in range(N):
        for j in range(N):
            s0, s1 = i / N, (i + 1) / N
            t0, t1 = j / N, (j + 1) / N
            cell = [bilin(s0, t0), bilin(s1, t0), bilin(s1, t1), bilin(s0, t1)]
            base = lerp(MALLA_VERDE, jet(cell_t[(i, j)]), 0.55)
            tint = lerp((0x26, 0x2b, 0x33), base, 0.60)
            d.polygon(cell, fill=tint + (255,))

    # Lineas de la malla (grilla s y t)
    lw_mesh = max(2, int(size * 0.012))
    for k in range(N + 1):
        u = k / N
        # lineas constantes en s
        pts_s = [bilin(u, t / 16.0) for t in range(17)]
        d.line(pts_s, fill=MALLA_VERDE + (255,), width=lw_mesh, joint="curve")
        # lineas constantes en t
        pts_t = [bilin(s / 16.0, u) for s in range(17)]
        d.line(pts_t, fill=MALLA_VERDE + (255,), width=lw_mesh, joint="curve")

    # Contorno fuerte del tablero (silueta reconocible)
    lw_out = max(3, int(size * 0.020))
    line_quad_edges(d, board, BLANCO + (255,), lw_out)

    # --- Nodos en las intersecciones (estilo Q9) ---
    r_corner = max(2, int(size * 0.022))
    r_mid    = max(2, int(size * 0.017))
    for i in range(N + 1):
        for j in range(N + 1):
            s, t = i / N, j / N
            px, py = bilin(s, t)
            is_center = (i == N // 2 and j == N // 2 and N % 2 == 0)
            is_corner = (i in (0, N) and j in (0, N))
            if is_center:
                col, r = NODO_CENTER, r_corner
            elif is_corner:
                col, r = NODO_CORNER, r_corner
            else:
                col, r = NODO_MID, r_mid
            d.ellipse([px - r, py - r, px + r, py + r], fill=col + (255,),
                      outline=(0x14, 0x17, 0x1b, 255), width=max(1, r // 4))

    # ------------------------------------------------------------------
    # Boton central del tablero + borla (tassel) en amarillo de acento
    # ------------------------------------------------------------------
    btn_r = max(3, int(size * 0.030))
    d.ellipse([cx - btn_r, cy_board - btn_r, cx + btn_r, cy_board + btn_r],
              fill=ACENTO + (255,), outline=(0x14, 0x17, 0x1b, 255),
              width=max(1, btn_r // 4))

    # cordon de la borla: del boton al borde del rombo y cae por el lado derecho
    edge = right  # punto por donde cuelga
    cord_w = max(2, int(size * 0.016))
    # tramo sobre el tablero
    d.line([(cx, cy_board), edge], fill=ACENTO + (255,), width=cord_w, joint="curve")
    # caida vertical de la borla
    fall_x = edge[0] - size * 0.01
    fall_y0 = edge[1]
    fall_y1 = cy_board + size * 0.30
    d.line([(edge[0], fall_y0), (fall_x, fall_y1)], fill=ACENTO + (255,),
           width=cord_w, joint="curve")
    # mechon (flecos) de la borla
    tw = max(2, int(size * 0.014))
    for off in (-1, 0, 1):
        x = fall_x + off * size * 0.022
        d.line([(fall_x, fall_y1 - size * 0.005),
                (x, fall_y1 + size * 0.055)], fill=ACENTO + (255,), width=tw,
               joint="curve")
    # nudo de la borla
    knot_r = max(2, int(size * 0.020))
    d.ellipse([fall_x - knot_r, fall_y1 - knot_r,
               fall_x + knot_r, fall_y1 + knot_r], fill=ACENTO + (255,))

    return img


def render(out_size, path):
    big = build_logo(SS)
    small = big.resize((out_size, out_size), Image.LANCZOS)
    small.save(path)
    return small


def main():
    os.makedirs("tools/logo_concepts", exist_ok=True)
    p512 = "tools/logo_concepts/concept_5_birrete-malla.png"
    p32 = "tools/logo_concepts/concept_5_birrete-malla_32.png"
    render(512, p512)
    render(32, p32)
    print("OK", p512, p32)


if __name__ == "__main__":
    main()
