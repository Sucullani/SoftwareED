# -*- coding: utf-8 -*-
"""
generar_memoria_anexo.py — Genera la Memoria de Calculo del ejemplo canonico
para embeberla como Anexo de la tesis (via \\includepdf de pdfpages).

Replica el flujo de exportacion de la GUI (gui/main_window._on_export_memoria):
carga el ejemplo canonico Q4, resuelve, calcula tensiones y llama a
generate_memoria_calculo con estilo 'educativo' (el estilo distintivo, con
infografia, tarjetas ENTRA->SALE y glosario).

Salida: tesis/anexo_memoria_calculo.pdf

Ejecutar (Windows, con MiKTeX/pdflatex en el PATH):
    .venv\\Scripts\\python.exe tesis\\figuras\\generar_memoria_anexo.py
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)


def _progress(stage: str, pct: float) -> None:
    print(f"  [{pct*100:5.1f}%] {stage}")


def main() -> int:
    from models.example_library import load_example_project
    from fem.solver import solve_system
    from fem.stress import compute_all_stresses
    from file_io.memoria_calculo import generate_memoria_calculo

    out_pdf = os.path.join(os.path.dirname(_HERE), "anexo_memoria_calculo.pdf")

    print("Generando la Memoria de Calculo del ejemplo canonico (Q4)...")
    print("-" * 60)

    project = load_example_project()           # cuadrado de validacion Q4 (9 nodos)
    solution = solve_system(project)
    element_stresses, nodal_stresses = compute_all_stresses(project, solution)

    # Dejar el project en estado resuelto (la memoria asume is_solved).
    project.is_solved = True
    project.displacements = solution["u"]
    project.global_K = solution["K"]
    project.global_F = solution["F"]
    project.stresses = element_stresses

    path = generate_memoria_calculo(
        project, solution, element_stresses, nodal_stresses,
        out_pdf, style="educativo", progress_callback=_progress,
    )

    print("-" * 60)
    size_kb = os.path.getsize(path) / 1024.0
    print(f"[OK] {path}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
