"""Genera resources/icons/edufem.ico — icono de la aplicacion EduFEM.

Concepto: BIRRETE ACADEMICO 3D cuyo tablero ES una malla de elementos finitos.
Fusiona la identidad educativa (Edu) con el MEF (FEM): el tablero del birrete
es un parche de elementos teñido con el colormap JET (la firma de resultados
del software, estilo ANSYS/SAP2000) con relleno continuo (Gouraud) y el
wireframe de la malla encima. Nodos blancos en las cuatro esquinas (que son a
la vez las esquinas del birrete) y un boton central dorado que es, a la vez, el
nodo centroide. Debajo, el casquete azul (color de la fase Pre) con sombreado
cilindrico, y una borla dorada (acento) con nudo y flecos.

Render realista, SIN baldosa cuadrada: fondo transparente, volumen 3D (espesor
del tablero, sombreado del casquete, cupula del boton) y sombra de contacto.
Multi-res 16..256.

(El concepto anterior — parche en voladizo con JET sobre baldosa — se conserva
como referencia en tools/logo_concepts/legacy_cantilever_icon.py.)

Regenerar:
    python tools/make_icon.py
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 1024            # supersampling; se reescala a 256 al guardar
N = 4                # NxN celdas del wireframe del tablero
M = 72               # subdivision fina para el relleno JET continuo (Gouraud)

# ── Birrete + malla ────────────────────────────────────────────────────
MESH = (245, 248, 252, 135)        # lineas de malla (translucido claro)
EDGE = (250, 252, 255, 210)        # rim claro del tablero (separa de JET/casquete)
SIDE_HI = (44, 50, 62, 255)        # canto del tablero (arriba, mas claro)
SIDE_LO = (16, 18, 23, 255)        # canto del tablero (abajo, mas oscuro)
NODE = (255, 255, 255, 255)
NODE_RING = (18, 20, 24, 255)
CAP_LO = np.array([14, 32, 78])    # casquete: azul navy (sombra)
CAP_HI = np.array([47, 116, 232])  # casquete: azul brillante (luz) — familia #0d6efd
CAP_RIM = (110, 170, 255, 235)     # realce del borde superior del casquete
TASSEL = (255, 235, 59)            # #ffeb3b — borla / boton (acento)
TASSEL_DK = (196, 150, 12)         # nucleo/sombra de la borla
TASSEL_RING = (18, 20, 24, 255)
SHADOW = (0, 0, 0, 130)            # sombra de contacto


def jet(t: float):
    """Mapa de color JET clasico para t en [0, 1] -> (r, g, b, a)."""
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)

    def ch(x: float) -> int:
        return int(max(0.0, min(1.0, x)) * 255)

    return (ch(1.5 - abs(4 * t - 3)),
            ch(1.5 - abs(4 * t - 2)),
            ch(1.5 - abs(4 * t - 1)), 255)


def _lerp(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(len(a)))


def _np_img(arr) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"), "RGBA")


def build_master() -> Image.Image:
    img = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))

    # ── Geometria del tablero (rombo en perspectiva) ───────────────────
    cx = SS / 2.0
    cy = SS * 0.42
    bx = SS * 0.325
    by = SS * 0.150
    th = SS * 0.050                 # espesor del tablero
    PL = (cx - bx, cy)              # izquierda
    PB = (cx, cy - by)              # atras (alta)
    PR = (cx + bx, cy)              # derecha
    PF = (cx, cy + by)              # frente (baja, mas cercana)

    def board(u: float, v: float):
        x = ((1 - u) * (1 - v) * PL[0] + u * (1 - v) * PB[0]
             + u * v * PR[0] + (1 - u) * v * PF[0])
        y = ((1 - u) * (1 - v) * PL[1] + u * (1 - v) * PB[1]
             + u * v * PR[1] + (1 - u) * v * PF[1])
        return (x, y)

    # ── Geometria del casquete ─────────────────────────────────────────
    cap_w = bx * 0.70               # semiancho del casquete (arriba)
    cap_bw = cap_w * 0.82           # semiancho abajo (leve estrechamiento -> cabeza)
    cap_top = cy + by * 0.10
    cap_side = cy + by * 1.30       # altura de los costados
    cap_dip = by * 0.45             # cuanto baja el centro (panza del casquete)
    cap_bot_full = cap_side + cap_dip
    bottom = []
    for s in range(49):
        t = s / 48.0
        x = cx - cap_bw + 2 * cap_bw * t
        y = cap_side + cap_dip * (1 - ((x - cx) / cap_bw) ** 2)
        bottom.append((x, y))
    cap_poly = ([(cx - cap_w, cap_top), (cx + cap_w, cap_top), (cx + cap_bw, cap_side)]
                + list(reversed(bottom)))

    ys, xs = np.mgrid[0:SS, 0:SS]

    # ── Sombra de contacto (blur) ──────────────────────────────────────
    shadow = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    syc = cap_bot_full + SS * 0.005
    sw, sh = cap_w * 1.65, by * 0.42
    sd.ellipse([cx - sw, syc - sh, cx + sw, syc + sh], fill=SHADOW)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SS * 0.022))
    img = Image.alpha_composite(img, shadow)

    # ── Casquete con sombreado cilindrico ──────────────────────────────
    cap_mask = Image.new("L", (SS, SS), 0)
    ImageDraw.Draw(cap_mask).polygon(cap_poly, fill=255)
    hx = np.cos(np.clip((xs - cx) / (cap_w * 1.08), -1, 1) * (np.pi / 2 * 0.95))
    hx = np.clip(hx, 0.30, 1.0)
    vt = np.clip((ys - cap_top) / (cap_bot_full - cap_top), 0, 1)
    shade = hx * (1.0 - 0.42 * vt)
    cap_rgb = CAP_LO[None, None, :] + (CAP_HI - CAP_LO)[None, None, :] * shade[..., None]
    cap_arr = np.dstack([cap_rgb, np.full((SS, SS), 255)])
    img.paste(_np_img(cap_arr), (0, 0), cap_mask)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(cx - cap_w, cap_top), (cx + cap_w, cap_top)], fill=CAP_RIM, width=int(SS * 0.010))

    # ── Canto (espesor) del tablero: aristas frontales extruidas ───────
    PLd = (PL[0], PL[1] + th)
    PFd = (PF[0], PF[1] + th)
    PRd = (PR[0], PR[1] + th)
    for poly in ([PL, PF, PFd, PLd], [PF, PR, PRd, PFd]):
        # gradiente vertical simple: claro arriba -> oscuro abajo
        seg = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
        sgm = Image.new("L", (SS, SS), 0)
        ImageDraw.Draw(sgm).polygon(poly, fill=255)
        ymin = min(p[1] for p in poly)
        ymax = max(p[1] for p in poly)
        tt = np.clip((ys - ymin) / max(1.0, (ymax - ymin)), 0, 1)
        edge_rgb = (np.array(SIDE_HI[:3])[None, None, :]
                    + (np.array(SIDE_LO[:3]) - np.array(SIDE_HI[:3]))[None, None, :] * tt[..., None])
        seg = _np_img(np.dstack([edge_rgb, np.full((SS, SS), 255)]))
        img.paste(seg, (0, 0), sgm)
    d = ImageDraw.Draw(img, "RGBA")

    # ── Tablero: relleno JET continuo (Gouraud), campo radial ──────────
    fills = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fills)
    for j in range(M):
        for i in range(M):
            uc, vc = (i + 0.5) / M, (j + 0.5) / M
            r = (((uc - 0.5) ** 2 + (vc - 0.5) ** 2) ** 0.5) / 0.7071
            field = 1.0 - r
            quad = [board(i / M, j / M), board((i + 1) / M, j / M),
                    board((i + 1) / M, (j + 1) / M), board(i / M, (j + 1) / M)]
            fd.polygon(quad, fill=jet(0.12 + 0.80 * field))
    img = Image.alpha_composite(img, fills)

    # ── Sombreado direccional del tablero (luz atras, sombra al frente) ─
    board_mask = Image.new("L", (SS, SS), 0)
    ImageDraw.Draw(board_mask).polygon([PL, PB, PR, PF], fill=255)
    bm = np.array(board_mask, dtype=float) / 255.0
    bt = np.clip((ys - PB[1]) / (PF[1] - PB[1]), 0, 1)
    hi_a = np.clip(0.42 - bt, 0, 1) / 0.42 * 60 * bm     # realce hacia atras
    lo_a = np.clip(bt - 0.55, 0, 1) / 0.45 * 80 * bm     # sombra hacia el frente
    img = Image.alpha_composite(img, _np_img(np.dstack(
        [np.full((SS, SS), 255), np.full((SS, SS), 255), np.full((SS, SS), 255), hi_a])))
    img = Image.alpha_composite(img, _np_img(np.dstack(
        [np.zeros((SS, SS)), np.zeros((SS, SS)), np.zeros((SS, SS)), lo_a])))
    d = ImageDraw.Draw(img, "RGBA")

    # ── Wireframe del tablero (encima del campo) ───────────────────────
    lw = int(SS * 0.0080)
    for k in range(N + 1):
        d.line([board(k / N, 0), board(k / N, 1)], fill=MESH, width=lw)
        d.line([board(0, k / N), board(1, k / N)], fill=MESH, width=lw)

    # ── Rim claro del contorno del tablero ─────────────────────────────
    d.line([PL, PB, PR, PF, PL], fill=EDGE, width=int(SS * 0.011), joint="curve")

    # ── Borla: cordon (boton -> vertice derecho) + nudo + flecos ───────
    btn = (cx, cy)
    hx0, hy0 = PR[0], PR[1]          # cuelga del vertice derecho
    bind_y = hy0 + SS * 0.052        # final del nudo (binding)
    tuft_y = hy0 + SS * 0.225        # largo de las hebras
    # cordon apoyado sobre el tablero (boton -> vertice)
    d.line([btn, PR], fill=TASSEL_DK, width=int(SS * 0.015), joint="curve")
    d.line([btn, PR], fill=TASSEL, width=int(SS * 0.009), joint="curve")
    # nudo / binding sobre el borde
    d.line([(hx0, hy0), (hx0, bind_y)], fill=TASSEL_DK, width=int(SS * 0.024))
    d.line([(hx0, hy0), (hx0, bind_y)], fill=TASSEL, width=int(SS * 0.015))
    # hebras colgando casi verticales, con leve apertura al final
    for k in range(-2, 3):
        topx = hx0 + k * SS * 0.007
        botx = hx0 + k * SS * 0.013
        col = TASSEL if k % 2 == 0 else TASSEL_DK
        d.line([(topx, bind_y), (botx, tuft_y)], fill=col, width=int(SS * 0.006))
    # borlon (tuft) al final
    d.ellipse([hx0 - SS * 0.020, tuft_y - SS * 0.010,
               hx0 + SS * 0.020, tuft_y + SS * 0.022], fill=TASSEL)
    d.ellipse([hx0 - SS * 0.012, tuft_y + SS * 0.001,
               hx0 + SS * 0.012, tuft_y + SS * 0.020], fill=TASSEL_DK)

    # ── Nodos en las 4 esquinas del tablero ────────────────────────────
    rN = int(SS * 0.023)
    for v in (PL, PB, PR, PF):
        d.ellipse([v[0] - rN, v[1] - rN, v[0] + rN, v[1] + rN], fill=NODE,
                  outline=NODE_RING, width=int(SS * 0.006))

    # ── Boton central = nodo centroide, como cupula dorada ─────────────
    rB = int(SS * 0.031)
    d.ellipse([btn[0] - rB, btn[1] - rB, btn[0] + rB, btn[1] + rB], fill=TASSEL_DK,
              outline=TASSEL_RING, width=int(SS * 0.006))
    d.ellipse([btn[0] - rB, btn[1] - rB, btn[0] + rB, btn[1] + rB], fill=None,
              outline=TASSEL_RING, width=int(SS * 0.006))
    # cupula: disco dorado + brillo arriba-izquierda
    d.ellipse([btn[0] - rB * 0.82, btn[1] - rB * 0.82,
               btn[0] + rB * 0.82, btn[1] + rB * 0.82], fill=TASSEL)
    hl = rB * 0.34
    d.ellipse([btn[0] - rB * 0.45 - hl, btn[1] - rB * 0.45 - hl,
               btn[0] - rB * 0.45 + hl, btn[1] - rB * 0.45 + hl], fill=(255, 252, 210, 255))

    return img


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.normpath(os.path.join(here, "..", "resources", "icons"))
    os.makedirs(out_dir, exist_ok=True)
    out_ico = os.path.join(out_dir, "edufem.ico")
    out_png = os.path.join(out_dir, "edufem_preview.png")

    base = build_master().resize((256, 256), Image.Resampling.LANCZOS)
    base.save(out_ico, format="ICO",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                     (64, 64), (128, 128), (256, 256)])
    base.save(out_png)
    print("Icono generado:", out_ico)
    print("Preview PNG:", out_png)


if __name__ == "__main__":
    main()
