"""
Tests de la fase Post-Proceso: grilla de la vista 3D, controles numericos
del panel y copiado del probe.

Sin display: `PostProcessTab` se instancia con `object.__new__` y se le
montan a mano los atributos que tocan las rutas bajo prueba (dobles de las
variables de Tk y de la ventana principal), igual que hicieron las sesiones
01, 02 y 03. La grilla del visor 3D se prueba contra el motor real.

Regresiones que cubre:

  - **Grilla cruda transpuesta en la vista 3D.** `compute_raw_grids` (y el
    rasterizador del lienzo 2D) indexan `G[i_ξ, j_η]`, pero el visor 3D
    armaba su geometria con `np.meshgrid(...)` por defecto (`indexing="xy"`,
    es decir `[j_η, i_ξ]`). En modo CRUDO la superficie se dibujaba con el
    campo transpuesto dentro de cada elemento: invisible en un campo
    simetrico, un error grosero en cualquier otro.

  - **`Factor de escala` y `Numero de niveles` reventaban el callback.** Un
    `DoubleVar`/`IntVar` con texto tipeado (`2,5`, `abc`, vacio) levanta
    `TclError` dentro del handler de Tk: el traceback iba a la consola, el
    alumno no veia nada y el control se quedaba mostrando lo que habia
    escrito aunque no se usara. Ahora se validan tolerando la coma decimal
    (misma regla que los editores de celda del Pre-Proceso) y avisando.

  - **Encabezados del TSV del probe en ingles y sin unidades** (`sigma_x`,
    `von_mises`), mientras la tabla de resultados —el otro `Ctrl+C` del
    Post— copiaba encabezados en español con la unidad del proyecto.

  - **`fmt_escala` como fuente unica** del formato de los ticks de las dos
    escalas de color (lienzo 2D y vista 3D).
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import tkinter                                   # noqa: F401
except ImportError:
    print("Tk no disponible — test omitido")
    sys.exit(0)

import numpy as np

from config.settings import (
    fmt_escala, ISOLINE_COUNT_MIN, ISOLINE_COUNT_MAX, ISOLINE_COUNT_DEFAULT,
)
from fem.probe_query import compute_raw, compute_raw_grids
from fem.shape_functions import get_shape_functions
from fem.solver import solve_system
from gui.postprocessing.post_tab import PostProcessTab
from gui.postprocessing.probe_overlay import ProbeOverlay
from gui.postprocessing.surface_3d_viewer import (
    element_grid_xy, natural_grid, shape_matrix_at_grid,
)
from models.example_library import load_example_cook_q4, load_example_project


# ── dobles minimos ───────────────────────────────────────────────────

class _VarStub:
    """Doble de `tk.StringVar`: guarda el texto crudo, como hace Tk."""

    def __init__(self, valor=""):
        self._valor = str(valor)

    def get(self):
        return self._valor

    def set(self, valor):
        self._valor = str(valor)


class _MainWindowStub:
    def __init__(self):
        self.status = []

    def set_status(self, msg):
        self.status.append(msg)


def _post_tab(escala="1", niveles=str(ISOLINE_COUNT_DEFAULT)):
    """PostProcessTab sin GUI, con solo lo que tocan los lectores."""
    pt = object.__new__(PostProcessTab)
    pt.main_window = _MainWindowStub()
    pt.scale_var = _VarStub(escala)
    pt.isoline_count_var = _VarStub(niveles)
    pt._ultimo_factor_escala = 1.0
    pt._ultimos_niveles = ISOLINE_COUNT_DEFAULT
    pt._aviso_pendiente = None
    return pt


# ═══════════════════════════════════════════════════════════════════════
# 1. Convencion de indices de la grilla (vista 3D vs motor)
# ═══════════════════════════════════════════════════════════════════════

def test_grilla_natural_indexa_xi_eta():
    n = 4
    XI, ETA = natural_grid(n)
    xs = np.linspace(-1, 1, n + 1)
    for i in range(n + 1):
        for j in range(n + 1):
            assert XI[i, j] == xs[i], "el primer indice debe ser ξ"
            assert ETA[i, j] == xs[j], "el segundo indice debe ser η"
    print("[OK] natural_grid indexa [i_ξ, j_η] (indexing='ij')")


def test_matriz_de_forma_en_la_grilla_coincide_punto_a_punto():
    n = 3
    for tipo in ("Q4 - Cuadrilátero 4 nodos", "Q9 - Cuadrilátero 9 nodos"):
        N_grid = shape_matrix_at_grid(tipo, n)
        N_func, _ = get_shape_functions(tipo)
        XI, ETA = natural_grid(n)
        planas_xi = XI.ravel()
        planas_eta = ETA.ravel()
        assert N_grid.shape[0] == (n + 1) ** 2
        for k in range(N_grid.shape[0]):
            esperado = N_func(float(planas_xi[k]), float(planas_eta[k]))
            assert np.allclose(N_grid[k], esperado, atol=1e-14), (
                f"{tipo}: N de la fila {k} no coincide con N(ξ,η)"
            )
    print("[OK] shape_matrix_at_grid reproduce N(ξ,η) fila por fila (Q4 y Q9)")


def test_geometria_y_campo_crudo_comparten_la_convencion():
    """El bug: X,Y venian de meshgrid 'xy' y Z de compute_raw_grids ('ij')."""
    p = load_example_cook_q4(N=4)     # malla distorsionada -> campo asimetrico
    sol = solve_system(p)
    n = 4
    xs = np.linspace(-1, 1, n + 1)
    grids = compute_raw_grids(p, sol, n=n)
    assert grids, "compute_raw_grids no devolvio datos"

    eid = sorted(p.elements.keys())[len(p.elements) // 2]
    elem = p.elements[eid]
    X, Y = element_grid_xy(p, elem, n)
    G = grids[eid]["sigma_x"]
    N_func, _ = get_shape_functions(p.element_type)
    pts = np.array([[p.nodes[i].x, p.nodes[i].y]
                    for i in elem.node_ids[:elem.num_nodes]])

    escala = max(abs(float(G.max())), abs(float(G.min())), 1e-12)
    peor_geo = peor_campo = 0.0
    for i, xi in enumerate(xs):
        for j, eta in enumerate(xs):
            Ns = N_func(xi, eta)
            peor_geo = max(peor_geo,
                           abs(X[i, j] - Ns @ pts[:, 0]),
                           abs(Y[i, j] - Ns @ pts[:, 1]))
            ref = compute_raw(p, sol, eid, xi, eta)["sigma_x"]
            peor_campo = max(peor_campo, abs(G[i, j] - ref))
    assert peor_geo < 1e-9, f"la geometria no cae en (ξ_i, η_j): {peor_geo:.2e}"
    assert peor_campo / escala < 1e-9, (
        f"el campo crudo no cae en (ξ_i, η_j): {peor_campo:.2e}"
    )

    # Y la transpuesta (lo que se dibujaba antes) SI difiere: si esta
    # comprobacion fallara, el test no distinguiria el bug de su arreglo.
    peor_transpuesto = max(
        abs(G[i, j] - compute_raw(p, sol, eid, xs[j], xs[i])["sigma_x"])
        for i in range(n + 1) for j in range(n + 1)
    )
    assert peor_transpuesto / escala > 1e-3, (
        "campo demasiado simetrico: el test no detectaria la transposicion"
    )
    print("[OK] geometria y campo crudo de la vista 3D comparten [i_ξ, j_η]")


def test_grilla_xy_no_depende_del_orden_de_llamada():
    """La matriz N esta cacheada por (tipo, n): el cache no debe ensuciar
    la geometria de elementos con distinto numero de nodos."""
    p = load_example_project()
    n = 3
    elem = p.elements[sorted(p.elements.keys())[0]]
    X1, Y1 = element_grid_xy(p, elem, n)
    shape_matrix_at_grid("Q9 - Cuadrilátero 9 nodos", n)   # ensucia el cache
    X2, Y2 = element_grid_xy(p, elem, n)
    assert np.array_equal(X1, X2) and np.array_equal(Y1, Y2)
    print("[OK] el cache de N esta separado por tipo de elemento")


# ═══════════════════════════════════════════════════════════════════════
# 2. Controles numericos del panel
# ═══════════════════════════════════════════════════════════════════════

def test_factor_de_escala_acepta_la_coma_decimal():
    pt = _post_tab(escala="2,5")
    assert pt._leer_factor_escala() == 2.5
    assert not pt.main_window.status, "un valor valido no debe avisar nada"
    print("[OK] el factor de escala acepta 2,5 (coma decimal de Excel)")


def test_factor_de_escala_invalido_avisa_y_conserva_el_ultimo_bueno():
    pt = _post_tab(escala="3")
    assert pt._leer_factor_escala() == 3.0
    for texto in ("abc", "", "-1", "0", "x2"):
        pt.scale_var.set(texto)
        assert pt._leer_factor_escala() == 3.0, (
            f"«{texto}» no debe cambiar el factor en uso"
        )
        assert pt.main_window.status, f"«{texto}» debe avisar al alumno"
        aviso = pt.main_window.status[-1]
        assert "Factor de escala" in aviso and "inválido" in aviso, aviso
        # El control vuelve al valor que realmente se esta usando.
        assert pt.scale_var.get() == "3", (
            f"el campo quedo mostrando «{pt.scale_var.get()}», que no se usa"
        )
    print("[OK] un factor de escala invalido avisa, no rompe y revierte el campo")


def test_niveles_de_isolineas_se_acotan_al_rango_del_control():
    pt = _post_tab(niveles="12")
    assert pt._leer_niveles_isolineas() == 12
    pt.isoline_count_var.set("500")
    assert pt._leer_niveles_isolineas() == ISOLINE_COUNT_MAX
    assert pt.isoline_count_var.get() == str(ISOLINE_COUNT_MAX)
    pt.isoline_count_var.set("1")
    assert pt._leer_niveles_isolineas() == ISOLINE_COUNT_MIN
    assert "fuera de rango" in pt.main_window.status[-1]
    print("[OK] los niveles de isolineas se acotan a "
          f"[{ISOLINE_COUNT_MIN}, {ISOLINE_COUNT_MAX}] y lo dicen")


def test_niveles_de_isolineas_invalidos_conservan_el_ultimo_bueno():
    pt = _post_tab(niveles="8")
    assert pt._leer_niveles_isolineas() == 8
    for texto in ("abc", "", "  "):
        pt.isoline_count_var.set(texto)
        assert pt._leer_niveles_isolineas() == 8
        assert "Número de niveles" in pt.main_window.status[-1]
        assert pt.isoline_count_var.get() == "8"
    print("[OK] un numero de niveles invalido avisa y revierte el campo")


# ═══════════════════════════════════════════════════════════════════════
# 3. Copiado del probe y formato de las escalas
# ═══════════════════════════════════════════════════════════════════════

def test_el_aviso_sobrevive_al_mensaje_de_visualizacion():
    """Los lectores corren al PRINCIPIO del repintado y `_on_result_changed`
    termina siempre con un `Visualizando: …`: un `set_status` directo en el
    lector quedaba tapado en el mismo instante y el alumno nunca veia por
    que su valor no se habia aplicado."""
    pt = _post_tab(escala="1")
    pt.scale_var.set("abc")
    pt._leer_factor_escala()
    assert pt._aviso_pendiente, "el lector debe dejar el aviso pendiente"
    pt._estado_visualizacion("Visualizando: Von Mises")
    assert "Factor de escala" in pt.main_window.status[-1], (
        f"el aviso quedo tapado: {pt.main_window.status[-1]!r}"
    )
    # Y no se pega al repintado siguiente, que ya no tiene nada que avisar.
    pt._estado_visualizacion("Visualizando: σx")
    assert pt.main_window.status[-1] == "Visualizando: σx"
    print("[OK] el aviso de un control invalido gana al «Visualizando: …»")


def test_encabezados_tsv_en_espanol_con_unidades():
    po = object.__new__(ProbeOverlay)
    po.project = load_example_project()
    headers = po.tsv_headers("node")
    assert headers[0] == "Nodo"
    unido = " ".join(headers)
    for clave_interna in ("sigma_x", "tau_xy", "von_mises", "Elem\t"):
        assert clave_interna not in unido, (
            f"«{clave_interna}» es una clave interna, no un encabezado"
        )
    for visible in ("σx", "τxy", "Von Mises", "Elemento", "ξ", "η"):
        assert any(visible in h for h in headers), f"falta «{visible}»"
    # Toda columna con dimension fisica lleva su unidad entre corchetes.
    con_unidad = [h for h in headers if "[" in h]
    assert len(con_unidad) == 10, (
        f"esperaba 10 columnas con unidad, hay {len(con_unidad)}: {con_unidad}"
    )
    # Y el TSV del punto libre no lleva la columna Nodo.
    assert po.tsv_headers("free")[0].startswith("x ["), po.tsv_headers("free")
    print("[OK] el TSV del probe usa el vocabulario y las unidades del alumno")


def test_fmt_escala_es_la_fuente_unica_de_los_ticks():
    from gui.preprocessing.mesh_canvas import MeshCanvas

    casos = [0.0, 1.5, -2.5e7, 25_000_000.0, 1e-4, -3.333333]
    for v in casos:
        assert MeshCanvas._fmt_colorbar_value(v) == fmt_escala(v)
    # Notacion cientifica arriba de 1e5 y abajo de 1e-3, compacta en el medio.
    assert fmt_escala(25_000_000.0) == "2.50e+07"
    assert fmt_escala(1.5) == "1.5"
    assert fmt_escala(0.0) == "0"
    assert fmt_escala("no soy un numero") == "no soy un numero"
    print("[OK] la colorbar del lienzo y la de la vista 3D formatean igual")


if __name__ == "__main__":
    print("=" * 62)
    print("  TEST: Post-Proceso (grilla 3D, controles, copiado)")
    print("=" * 62)
    test_grilla_natural_indexa_xi_eta()
    test_matriz_de_forma_en_la_grilla_coincide_punto_a_punto()
    test_geometria_y_campo_crudo_comparten_la_convencion()
    test_grilla_xy_no_depende_del_orden_de_llamada()
    test_factor_de_escala_acepta_la_coma_decimal()
    test_factor_de_escala_invalido_avisa_y_conserva_el_ultimo_bueno()
    test_niveles_de_isolineas_se_acotan_al_rango_del_control()
    test_niveles_de_isolineas_invalidos_conservan_el_ultimo_bueno()
    test_el_aviso_sobrevive_al_mensaje_de_visualizacion()
    test_encabezados_tsv_en_espanol_con_unidades()
    test_fmt_escala_es_la_fuente_unica_de_los_ticks()
    print("=" * 62)
    print("  TODOS LOS TESTS PASARON [11/11]")
    print("=" * 62)
