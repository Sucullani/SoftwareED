"""Tests headless de la logica de visualizacion del canvas (auditoria UX
2026-05). NO requieren Tk: validan funciones puras (LOD, culling, politica
de etiquetas, silueta del dominio, focus, colormaps).

Run:  python -m tests.test_canvas_visualization
"""

import sys

from config.settings import ELEMENT_Q4, ELEMENT_Q9
from config import colormaps as cm
from models.mesh_utils import (
    median_edge_length, boundary_edges, focus_keep_sets,
    generate_structured_quad_mesh,
)
from gui.preprocessing.canvas_logic import (
    lod_level, bbox_visible, point_visible,
    label_globally_visible, label_visible_for_item,
)

_fail = 0


def check(name, cond):
    global _fail
    status = "OK  " if cond else "FAIL"
    if not cond:
        _fail += 1
    print(f"  [{status}] {name}")


def _mesh(nx, ny, w=4.0, h=2.0, etype=ELEMENT_Q4):
    return generate_structured_quad_mesh(
        [(0, 0), (w, 0), (w, h), (0, h)], nx, ny,
        element_type=etype, material_name="Acero",
        thickness=1.0, analysis_type="Tensión plana",
    )


def test_lod_level():
    print("test_lod_level")
    # Malla chica: siempre near (no gating), aunque edge_px sea minusculo.
    check("malla chica -> near", lod_level(2.0, 4) == "near")
    check("malla chica grande zoom -> near", lod_level(200.0, 4) == "near")
    # Malla grande: gating segun edge_px.
    check("grande far", lod_level(8.0, 200) == "far")
    check("grande mid", lod_level(30.0, 200) == "mid")
    check("grande near", lod_level(80.0, 200) == "near")
    # Limites exactos.
    check("frontera far/mid", lod_level(14.0, 200) == "mid")
    check("frontera mid/near", lod_level(55.0, 200) == "near")
    # edge_px None o <=0 -> near (sin info de escala).
    check("edge None -> near", lod_level(None, 200) == "near")
    check("edge 0 -> near", lod_level(0.0, 200) == "near")


def test_bbox_visible():
    print("test_bbox_visible")
    W, H, M = 800, 600, 100
    check("dentro", bbox_visible(100, 100, 200, 200, W, H, M))
    check("fuera derecha", not bbox_visible(950, 100, 980, 200, W, H, M))
    check("fuera arriba", not bbox_visible(100, -300, 200, -250, W, H, M))
    check("borde con margen", bbox_visible(-50, 100, 10, 200, W, H, M))
    check("punto dentro", point_visible(400, 300, W, H, M))
    check("punto fuera", not point_visible(-300, 300, W, H, M))


def test_label_policy():
    print("test_label_policy")
    # always: visible salvo ghost.
    check("always near", label_globally_visible("always", "far", ghost=False))
    check("always ghost off", not label_globally_visible("always", "near", ghost=True))
    # never: nunca.
    check("never", not label_globally_visible("never", "near", ghost=False))
    # auto: solo near.
    check("auto near", label_globally_visible("auto", "near", ghost=False))
    check("auto mid no", not label_globally_visible("auto", "mid", ghost=False))
    # Realce por seleccion: item seleccionado muestra id aun en far/auto.
    check("auto far selected -> visible",
          label_visible_for_item("auto", "far", ghost=False, selected=True))
    check("auto far no-selected -> oculto",
          not label_visible_for_item("auto", "far", ghost=False, selected=False))
    # never gana sobre seleccion.
    check("never selected -> oculto",
          not label_visible_for_item("never", "near", ghost=False, selected=True))


def test_median_edge():
    print("test_median_edge")
    m = _mesh(4, 2)  # celdas de 1.0 x 1.0
    med = median_edge_length(m)
    check("mediana ~1.0", abs(med - 1.0) < 1e-9)
    empty = generate_structured_quad_mesh(
        [(0, 0), (1, 0), (1, 1), (0, 1)], 1, 1,
        element_type=ELEMENT_Q4, material_name="Acero",
        thickness=1.0, analysis_type="Tensión plana")
    # 1 elemento: mediana de su primera arista = 1.0
    check("1 elem mediana", abs(median_edge_length(empty) - 1.0) < 1e-9)


def test_boundary_edges():
    print("test_boundary_edges")
    m = _mesh(3, 2)  # 6 elementos, contorno = 2*(3+2)=10 aristas
    be = boundary_edges(m)
    check("contorno = 10 aristas", len(be) == 10)
    # Ninguna arista interna (compartida) esta en el contorno.
    # La malla 3x2 tiene 3-1 internas verticales * 2 filas + 2-1 horizontales
    # * 3 columnas = 4 + 3 = 7 internas. Total aristas unicas = 10 + 7 = 17.
    # Verificamos que el contorno son exactamente las de un solo elemento.
    counts = {}
    for elem in m.elements.values():
        ids = elem.node_ids[:4]
        for k in range(4):
            e = frozenset((ids[k], ids[(k + 1) % 4]))
            counts[e] = counts.get(e, 0) + 1
    expected = {e for e, c in counts.items() if c == 1}
    check("contorno == aristas de 1 solo elem", be == expected)
    check("contorno Q9 igual que Q4", boundary_edges(_mesh(3, 2, etype=ELEMENT_Q9)) == be
          or len(boundary_edges(_mesh(3, 2, etype=ELEMENT_Q9))) == 10)


def test_focus_keep():
    print("test_focus_keep")
    m = _mesh(4, 4)  # 16 elementos
    eids = sorted(m.elements.keys())
    center = eids[5]  # un elemento interior
    keep_e, keep_n = focus_keep_sets(m, set(), {center})
    # El elemento seleccionado y al menos un vecino deben estar.
    check("selecto en keep", center in keep_e)
    check("vecinos incluidos (>1 elem)", len(keep_e) > 1)
    # No deben estar TODOS (en una malla 4x4 un interior no toca las esquinas).
    check("no son todos", len(keep_e) < len(m.elements))
    # Seleccion vacia -> keep vacio.
    ek, nk = focus_keep_sets(m, set(), set())
    check("sin seleccion -> vacio", len(ek) == 0 and len(nk) == 0)


def test_colormaps():
    print("test_colormaps")
    check("viridis LUT shape", cm.VIRIDIS_LUT.shape == (256, 3))
    check("coolwarm LUT shape", cm.COOLWARM_LUT.shape == (256, 3))
    # Extremos viridis: morado oscuro -> amarillo.
    r0, g0, b0 = cm.t_to_rgb(0.0, cm.VIRIDIS_LUT)
    r1, g1, b1 = cm.t_to_rgb(1.0, cm.VIRIDIS_LUT)
    check("viridis low = morado", b0 > r0 and b0 > 60)
    check("viridis high = amarillo", r1 > 200 and g1 > 200 and b1 < 100)
    # Coolwarm centro ~ gris claro; t=0 azul, t=1 rojo.
    rc, gc, bc = cm.t_to_rgb(0.5, cm.COOLWARM_LUT)
    check("coolwarm centro gris", abs(rc - gc) < 20 and abs(gc - bc) < 20 and rc > 180)
    rb, gb, bb = cm.t_to_rgb(0.0, cm.COOLWARM_LUT)
    rr, gr, br = cm.t_to_rgb(1.0, cm.COOLWARM_LUT)
    check("coolwarm low azul", bb > rb)
    check("coolwarm high rojo", rr > br)
    # normalized_t clamp.
    check("norm clamp low", cm.normalized_t(-5, 0, 10) == 0.0)
    check("norm clamp high", cm.normalized_t(50, 0, 10) == 1.0)
    check("norm degenerate", cm.normalized_t(5, 3, 3) == 0.5)
    # diverging detection + symmetric bounds.
    check("diverging detecta signo", cm.is_diverging_range(-2, 5))
    check("no diverging positivo", not cm.is_diverging_range(1, 5))
    # Ruido numerico: VM con -1e-9 NO debe clasificarse divergente (umbral
    # relativo) -> sigue en viridis.
    check("no diverging por ruido", not cm.is_diverging_range(-1e-9, 100.0))
    check("diverging real con rango grande", cm.is_diverging_range(-30.0, 100.0))
    lo, hi = cm.symmetric_bounds(-2, 5)
    check("symmetric centra cero", lo == -5 and hi == 5)
    # value_to_hex formato.
    h = cm.value_to_hex(5, 0, 10, cm.VIRIDIS_LUT)
    check("hex formato", h.startswith("#") and len(h) == 7)


def main():
    for fn in (test_lod_level, test_bbox_visible, test_label_policy,
               test_median_edge, test_boundary_edges, test_focus_keep,
               test_colormaps):
        fn()
    print()
    if _fail:
        print(f"FALLARON {_fail} checks")
        sys.exit(1)
    print("Todos los checks OK")


if __name__ == "__main__":
    main()
