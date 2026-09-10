"""Tests headless (sin Tk) del rediseño de la capa visual del 2026-09-09:
cuadricula anclada al mundo, lente del sistema (marco local ξη, puntos de
Gauss fisicos), textos de la franja lectora y vista del sistema K·u = F.

Run:  python -m tests.test_canvas_lens
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np

from config.settings import ELEMENT_Q4, ELEMENT_Q9, GRID_TARGET_PX
from config.units import get_unit_labels
from models.example_library import load_example_project, load_example_cook_q9
from models.material import Material
from models.project import ProjectModel
from gui.preprocessing.canvas_logic import (
    grid_step, grid_range, is_major_line, grid_label,
    polygon_area, element_local_frame, gauss_physical_points,
    node_summary, element_summary, phase_hint, restraint_words, nearest_node,
)
from gui.preprocessing.canvas_glyphs import draw_natural_axes
from education.components.system_structure import (
    node_block_pairs, restrained_node_indices, system_summary,
    element_block_pairs, node_ordinal, render_pattern, block_rect, fingerprint,
)

_fail = 0


def check(name, cond):
    global _fail
    status = "OK  " if cond else "FAIL"
    if not cond:
        _fail += 1
    print(f"  [{status}] {name}")


# ── cuadricula ───────────────────────────────────────────────────────

def test_grid_step():
    print("test_grid_step")
    serie = {1.0, 2.0, 5.0}
    for scale in (0.001, 0.03, 0.7, 1.0, 7.0, 50.0, 333.0, 12345.0):
        step = grid_step(scale)
        mant = step / 10 ** np.floor(np.log10(step))
        check(f"scale={scale}: paso {step} es de la serie 1-2-5",
              any(abs(mant - m) < 1e-9 for m in serie))
        px = step * scale
        # El paso elegido mide entre 0,4x y 2,5x el objetivo: nunca muy
        # denso ni muy ralo.
        check(f"scale={scale}: {px:.1f} px cerca del objetivo",
              GRID_TARGET_PX * 0.4 <= px <= GRID_TARGET_PX * 2.5)
    check("escala 0 -> 1.0", grid_step(0) == 1.0)
    check("escala negativa -> 1.0", grid_step(-3) == 1.0)
    check("escala None -> 1.0", grid_step(None) == 1.0)


def test_grid_range_y_rotulos():
    print("test_grid_range_y_rotulos")
    vals = grid_range(-2.3, 11.2, 1.0)
    check("cubre el rango hacia afuera", vals[0] == -3.0 and vals[-1] == 12.0)
    check("paso entero", all(abs(v - round(v)) < 1e-12 for v in vals))
    check("rango absurdo -> vacio", grid_range(0, 1e9, 1.0) == [])
    check("paso 0 -> vacio", grid_range(0, 1, 0) == [])
    check("mayor cada 5", is_major_line(10.0, 2.0) and not is_major_line(4.0, 2.0))
    check("el 0 es mayor", is_major_line(0.0, 0.5))
    check("rotulo redondo sin decimales", grid_label(5.0) == "5")
    check("rotulo -0 -> 0", grid_label(-0.0) == "0")
    check("rotulo grande en cientifica", "e+" in grid_label(2.5e6))


# ── lente del elemento ───────────────────────────────────────────────

def test_marco_local_y_gauss():
    print("test_marco_local_y_gauss")
    sq = [(0, 0), (2, 0), (2, 2), (0, 2)]           # cuadrado, orden CCW
    check("area del cuadrado", abs(polygon_area(sq) - 4.0) < 1e-12)
    fr = element_local_frame(sq, reach=1.0)
    check("centroide", fr["centroid"] == (1.0, 1.0))
    # ξ apunta a la arista N2-N3 (x = 2), η a la N3-N4 (y = 2).
    check("xi hacia +x", abs(fr["xi_end"][0] - 2.0) < 1e-12
          and abs(fr["xi_end"][1] - 1.0) < 1e-12)
    check("eta hacia +y", abs(fr["eta_end"][0] - 1.0) < 1e-12
          and abs(fr["eta_end"][1] - 2.0) < 1e-12)
    check("menos de 4 vertices -> None", element_local_frame(sq[:3]) is None)

    # Glifo compartido de los ejes (lente del lienzo y capas de M1/M2/M3/M5):
    # 2 flechas + 2 rotulos, con los colores de settings, sobre un doble de
    # canvas sin Tk.
    class _CanvasSpy:
        def __init__(self):
            self.lines, self.texts = [], []

        def create_line(self, *coords, **kw):
            self.lines.append((coords, kw))

        def create_text(self, *coords, **kw):
            self.texts.append((coords, kw))

    from config.settings import CANVAS_XI_AXIS_COLOR, CANVAS_ETA_AXIS_COLOR
    spy = _CanvasSpy()
    n_items = draw_natural_axes(spy, lambda x, y: (10 * x, -10 * y), sq,
                                factor=1.0, tags=("t",))
    check("glifo: 4 items (2 flechas + 2 rotulos)", n_items == 4
          and len(spy.lines) == 2 and len(spy.texts) == 2)
    check("glifo: colores xi / eta de settings",
          spy.lines[0][1]["fill"] == CANVAS_XI_AXIS_COLOR
          and spy.lines[1][1]["fill"] == CANVAS_ETA_AXIS_COLOR)
    check("glifo: rotulos ξ y η", {t[1]["text"] for t in spy.texts} == {"ξ", "η"})
    check("glifo: xi apunta a +x en pantalla",
          spy.lines[0][0][2] > spy.lines[0][0][0]
          and abs(spy.lines[0][0][3] - spy.lines[0][0][1]) < 1e-9)
    check("glifo: sin 4 vertices no dibuja",
          draw_natural_axes(_CanvasSpy(), lambda x, y: (x, y), sq[:2]) == 0)

    gp = gauss_physical_points(sq, ELEMENT_Q4)
    check("Q4: 4 PG", gp.shape == (4, 2))
    a = 1.0 / np.sqrt(3.0)
    esperado = {(1 - a, 1 - a), (1 - a, 1 + a), (1 + a, 1 - a), (1 + a, 1 + a)}
    got = {(round(x, 9), round(y, 9)) for x, y in gp}
    check("Q4: PG en 1 ± 1/√3", got == {(round(x, 9), round(y, 9))
                                         for x, y in esperado})
    # Q9 sobre el mismo cuadrado con sus 9 nodos (medios + centro).
    q9 = sq + [(1, 0), (2, 1), (1, 2), (0, 1), (1, 1)]
    gp9 = gauss_physical_points(q9, ELEMENT_Q9)
    check("Q9: 9 PG", gp9.shape == (9, 2))
    check("Q9: el PG central es el centroide",
          any(abs(x - 1) < 1e-12 and abs(y - 1) < 1e-12 for x, y in gp9))
    check("Q9 con solo 4 nodos -> Q4", gauss_physical_points(sq, ELEMENT_Q9).shape == (4, 2))
    check("sin nodos -> vacio", gauss_physical_points([], ELEMENT_Q4).shape == (0, 2))
    # Elemento real del ejemplo canonico: todos los PG caen adentro.
    p = load_example_project(P=1000.0)
    for eid, e in p.elements.items():
        pts = [(p.nodes[n].x, p.nodes[n].y) for n in e.node_ids]
        for x, y in gauss_physical_points(pts, p.element_type):
            xs = [q[0] for q in pts[:4]]
            ys = [q[1] for q in pts[:4]]
            check(f"elem {eid}: PG dentro del bbox",
                  min(xs) < x < max(xs) and min(ys) < y < max(ys))


# ── franja lectora ───────────────────────────────────────────────────

def test_textos_del_lector():
    print("test_textos_del_lector")
    p = load_example_project(P=1000.0)
    u = get_unit_labels(p.unit_system)
    head, body = node_summary(p, 5, units=u)
    check("nodo: cabecera", head == "Nodo 5")
    check("nodo: coords con unidad", "(7.000, 4.000) mm" in body)
    check("nodo: GDL con indices globales (ordinal 4 -> 8, 9)",
          "u₅→8" in body and "v₅→9" in body)
    check("nodo: libre", "libre" in body)
    check("nodo: compartido", "compartido por 4 elementos" in body)
    _h, body1 = node_summary(p, 1, units=u)
    check("nodo empotrado", "empotrado" in body1)
    _h, body7 = node_summary(p, 7, units=u)
    check("nodo cargado muestra F con unidad", "F = (0.00, -1000.00) N" in body7)
    head, body = element_summary(p, 3, units=u)
    check("elemento: cabecera con tipo", head == "Elemento 3 · Q4")
    check("elemento: conectividad CCW", "nodos 4→5→8→7 (antihorario)" in body)
    check("elemento: espesor con unidad", "t = 0.800 mm" in body)
    check("elemento: area", "A = 15.000 mm²" in body)
    check("elemento: GDL y tamano de k_e",
          "GDL 6 7 8 9 14 15 12 13" in body and "kₑ 8×8" in body)
    # Q9: 18 GDL, se muestran 8 y el resto se resume.
    q = load_example_cook_q9(N=2)
    _h, bq = element_summary(q, sorted(q.elements)[0], units=u)
    check("Q9: kₑ 18×18 y resumen de GDL", "kₑ 18×18" in bq and "(+10)" in bq)
    check("Q9: nodos internos", "+ 5 internos" in bq)
    # Inexistentes.
    check("nodo inexistente", node_summary(p, 999)[1] == "ya no existe")
    check("elemento inexistente", element_summary(p, 999)[1] == "ya no existe")
    # Pistas por fase.
    for phase in ("pre", "proc", "post"):
        h, b = phase_hint(phase)
        check(f"pista {phase} no vacia", bool(h) and bool(b))
    check("pista dibujo", phase_hint("pre", draw_mode=True)[0] == "Dibujando")
    check("pista pre sin malla nombra la tecla D",
          "D" in phase_hint("pre", has_elements=False)[1])
    check("pista proc nombra k_e y K", "kₑ" in phase_hint("proc")[1])

    class _BC:
        def __init__(self, x, y):
            self.restrain_x, self.restrain_y = x, y
    check("rodillo y", restraint_words(_BC(False, True)) == "restringido en y (rodillo)")
    check("sin BC -> libre", restraint_words(None) == "libre")

    ids = [1, 2, 3]
    xy = np.array([[0, 0], [1, 0], [5, 5]], dtype=float)
    check("nodo mas cercano dentro de tol", nearest_node(xy, ids, 1.1, 0.1, 0.5) == 2)
    check("fuera de tol -> None", nearest_node(xy, ids, 3, 0, 0.5) is None)
    check("sin nodos -> None", nearest_node(np.zeros((0, 2)), [], 0, 0, 1) is None)


# ── vista del sistema K·u = F ────────────────────────────────────────

def test_sistema():
    print("test_sistema")
    p = load_example_project(P=1000.0)
    n, i, j = node_block_pairs(p)
    check("9 nodos", n == 9)
    check("pares simetricos", set(zip(i, j)) == set(zip(j, i)))
    check("diagonal completa", all((k, k) in set(zip(i, j)) for k in range(9)))
    # Los nodos 1 y 9 (ordinales 0 y 8) no comparten elemento: sin bloque.
    check("sin bloque entre nodos lejanos", (0, 8) not in set(zip(i, j)))
    # Nodo 5 (ordinal 4) esta en los 4 elementos: fila completa.
    check("nodo central toca a todos", {b for a, b in zip(i, j) if a == 4} == set(range(9)))
    s = system_summary(p)
    check("resumen: 18 GDL, 6 restringidos, 12 incognitas",
          s["n_dof"] == 18 and s["n_restrained"] == 6 and s["n_free"] == 12)
    check("resumen: bloques", s["n_blocks"] == len(i) and s["n_blocks_total"] == 81)
    check("resumen: semiancho positivo", s["half_bandwidth_dof"] >= 3)
    check("restringidos = nodos 1, 3, 6 (ordinales 0, 2, 5)",
          restrained_node_indices(p) == {0, 2, 5})
    pares = element_block_pairs(p, 1)
    check("elemento 1: 16 pares de sus 4 nodos", len(pares) == 16)
    check("elemento inexistente: sin pares", element_block_pairs(p, 99) == [])
    check("ordinal del nodo 5", node_ordinal(p, 5) == 4)

    img = render_pattern(n, i, j, 90, restrained=restrained_node_indices(p),
                         bg=(0, 0, 0), block=(100, 100, 100), diag=(200, 200, 200),
                         dim=0.5, grid=(30, 30, 30))
    check("imagen (size, size, 3)", img.shape == (90, 90, 3))
    check("bloque diagonal del nodo central (libre) al color diag",
          tuple(img[45, 45]) == (200, 200, 200))
    check("bloque vacio queda en bg", tuple(img[2, 87]) == (0, 0, 0))
    # Fila del nodo 1 (ordinal 0, restringido): atenuada.
    check("fila restringida atenuada", tuple(img[3, 3]) == (100, 100, 100))
    check("bloque libre-libre sin atenuar (nodos 5 y 8, ordinales 4 y 7)",
          tuple(img[45, 75]) == (100, 100, 100))
    x0, y0, x1, y1 = block_rect(2, 3, 9, 90)
    check("rect del bloque (2,3)", (x0, y0) == (30, 20) and (x1, y1) == (40, 30))
    check("rect minimo 2 px con n grande", block_rect(5, 5, 5000, 200)[2] - block_rect(5, 5, 5000, 200)[0] >= 2)
    vacio = render_pattern(0, [], [], 20)
    check("sin nodos: imagen de fondo", vacio.shape == (20, 20, 3))

    fp1 = fingerprint(p)
    p.set_boundary_condition(5, True, False)
    check("la firma cambia con una restriccion", fingerprint(p) != fp1)
    fp2 = fingerprint(p)
    p.remove_boundary_condition(5) if hasattr(p, "remove_boundary_condition") \
        else p.boundary_conditions.pop(5)
    check("y vuelve al quitarla", fingerprint(p) == fp1 and fp2 != fp1)

    # Malla grande: bineado sin explotar.
    q = load_example_cook_q9(N=16)
    n, i, j = node_block_pairs(q)
    img = render_pattern(n, i, j, 200, restrained=restrained_node_indices(q))
    check("Cook Q9 16x16: patron con contenido", img.shape == (200, 200, 3) and img.max() > 60)
    # Proyecto vacio.
    e = ProjectModel()
    e.materials["a"] = Material("a", 1.0, 0.3)
    s = system_summary(e)
    check("vacio: 0 GDL", s["n_dof"] == 0 and s["n_blocks"] == 0)


def main():
    for fn in (test_grid_step, test_grid_range_y_rotulos, test_marco_local_y_gauss,
               test_textos_del_lector, test_sistema):
        fn()
    print()
    if _fail:
        print(f"FALLARON {_fail} checks")
        sys.exit(1)
    print("Todos los checks OK")


if __name__ == "__main__":
    main()
