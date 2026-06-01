"""
Shim de compatibilidad: los loaders de ejemplo se movieron a la capa de
PRODUCTO en `models/example_library.py` (2026-05) — alimentan el menú
Ayuda ▸ Cargar Ejemplo, así que no deben vivir en `tests/` (el ejecutable
debe poder cargarlos aunque `tests/` no se empaquete).

Este módulo re-exporta los loaders para no romper los imports existentes en
`tests/` y en los scripts V&V. El código real vive en
`models.example_library`.
"""

from models.example_library import (  # noqa: F401
    load_example_project,
    load_example_project_q9,
    load_example_timoshenko,
    load_example_timoshenko_q4,
    load_example_timoshenko_q9,
    load_example_cook,
    load_example_cook_q4,
    load_example_cook_q9,
)

__all__ = [
    "load_example_project",
    "load_example_project_q9",
    "load_example_timoshenko",
    "load_example_timoshenko_q4",
    "load_example_timoshenko_q9",
    "load_example_cook",
    "load_example_cook_q4",
    "load_example_cook_q9",
]
