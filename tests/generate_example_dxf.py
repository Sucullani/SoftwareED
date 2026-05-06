"""
Genera un archivo DXF de ejemplo en resources/examples/ejemplo_geometria.dxf
con una viga rectangular de 4 m x 1 m subdividida en 6 cuadrilateros Q4
(3 columnas x 2 filas). Incluye capas FEM_ELEMENTS y OTROS (esta ultima como
decoracion — debe ser ignorada por el importador), y declara $INSUNITS = 6
(metros) para que el dialogo de import preseleccione un sistema metrico.

Ejecutar:
    python -m tests.generate_example_dxf
"""

from __future__ import annotations

import os

import ezdxf


_OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "resources", "examples",
)
_OUT_PATH = os.path.join(_OUT_DIR, "ejemplo_geometria.dxf")


def generate():
    os.makedirs(_OUT_DIR, exist_ok=True)

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = 6  # 6 = meters
    msp = doc.modelspace()

    doc.layers.add("FEM_ELEMENTS", color=5)  # azul AutoCAD
    doc.layers.add("OTROS", color=3)         # verde — no se importa

    # ── Viga 4 m x 1 m, malla 3 x 2 (6 cuadrilateros) ──────────────────
    # x va 0 -> 4 en 3 tramos: (0, 4/3, 8/3, 4)
    # y va 0 -> 1 en 2 tramos: (0, 0.5, 1)
    x_steps = [0.0, 4.0 / 3.0, 8.0 / 3.0, 4.0]
    y_steps = [0.0, 0.5, 1.0]

    for j in range(len(y_steps) - 1):         # 2 filas
        for i in range(len(x_steps) - 1):     # 3 columnas
            x0, x1 = x_steps[i], x_steps[i + 1]
            y0, y1 = y_steps[j], y_steps[j + 1]
            vertices = [
                (x0, y0),  # inferior izquierda
                (x1, y0),  # inferior derecha
                (x1, y1),  # superior derecha
                (x0, y1),  # superior izquierda
            ]
            msp.add_lwpolyline(
                vertices,
                close=True,
                dxfattribs={"layer": "FEM_ELEMENTS"},
            )

    # ── Decoracion en capa OTROS (debe ser ignorada) ───────────────────
    # Un marco alrededor que NO pertenece a FEM_ELEMENTS.
    frame = [(-0.5, -0.5), (4.5, -0.5), (4.5, 1.5), (-0.5, 1.5)]
    msp.add_lwpolyline(frame, close=True,
                        dxfattribs={"layer": "OTROS"})

    # Una anotacion de texto (no tiene efecto sobre el importador)
    msp.add_text(
        "Ejemplo EduFEM 4m x 1m",
        dxfattribs={"layer": "OTROS", "height": 0.15},
    ).set_placement((0.0, 1.25))

    doc.saveas(_OUT_PATH)
    print(f"OK - DXF escrito: {_OUT_PATH}")
    print(f"   Elementos en FEM_ELEMENTS: 6 (3 x 2)")
    print(f"   $INSUNITS = 6 (metros)")
    print(f"   Decoracion en capa OTROS (1 polilinea + 1 texto, ignorados)")


if __name__ == "__main__":
    generate()
