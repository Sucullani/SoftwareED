"""
Launcher compartido para los modulos educativos M0..M9.

Modos de presentación (propuesta UX 2026):
    - Toplevel (legacy): el modulo abre una ventana propia, hereda de
      `BaseEducationalModule`. Apropiado para modulos amplios o con
      comparacion lado-a-lado independiente del modelo (M1, M4, M5,
      M7, M9).
    - Overlay: el modulo se posa sobre el MeshCanvas compartido como un
      panel flotante. Hereda de `CanvasOverlayModule`. Apropiado para
      modulos que operan sobre la malla real (M0, M2, M3, M6, M8).

El launcher detecta automáticamente el modo inspeccionando la clase:
    - Si tiene método de clase `activate(main_window, project, elem_id)`
      → modo Overlay (singleton suave).
    - Si no → modo Toplevel: instancia normal `cls(parent, project, elem_id)`.

Modulos organizados por fase del flujo FEM:
- pre  : M0 (calidad de malla, Overlay)
- proc : M1..M6 (mapeo, B, D, K, ensamblaje, fuerzas equivalentes)
- post : M7 (discontinuidad/promediado), M8 (principales, Overlay), M9
"""

import importlib
from tkinter import messagebox, simpledialog


MODULE_MAP = {
    "mod00": ("education.mod00_mesh_quality",        "MeshQualityModule"),
    "mod01": ("education.mod01_iso_mapping",         "IsoMappingModule"),
    "mod02": ("education.mod02_b_matrix",            "BMatrixModule"),
    "mod03": ("education.mod03_constitutive",        "ConstitutiveModule"),
    "mod04": ("education.mod04_stiffness_gauss",     "StiffnessGaussModule"),
    "mod05": ("education.mod05_assembly",            "AssemblyModule"),
    "mod06": ("education.mod06_equivalent_forces",   "EquivalentForcesModule"),
    "mod07": ("education.mod07_stress_discontinuity","StressDiscontinuityModule"),
    "mod08": ("education.mod08_principal_stresses",  "PrincipalStressesModule"),
    "mod09": ("education.mod09_q4_vs_q9_comparison", "Q4vsQ9ComparisonModule"),
}

# Agrupacion pedagogica por fase del flujo FEM. M3 (Matriz constitutiva D)
# vive en proc porque la matriz D depende del material asignado a CADA
# elemento — en un modelo con varios materiales, cada elemento tiene su
# propia D. Por eso la exploración por-elemento es natural en la fase de
# Proceso (donde se calcula B, D, K para cada elemento). El submenú
# Modelo > Tipo de Análisis solo muestra videos didácticos de TP/DP.
MODULE_PHASE = {
    "pre":  ["mod00"],
    "proc": ["mod01", "mod02", "mod03", "mod04", "mod05", "mod06"],
    "post": ["mod07", "mod08", "mod09"],
}

# Etiquetas y descripciones para el launcher_panel (UI homogenea entre fases)
MODULE_META = {
    "mod00": ("Ⓜ Calidad de malla",
              "Jacobiano · aspect ratio · Robinson"),
    "mod01": ("① Coordenadas, N y Jacobiano",
              "Mapeo isoparametrico, det J"),
    "mod02": ("② Matriz B (Deformacion)",
              "∂N/∂x con J⁻¹, snap a Gauss"),
    "mod03": ("③ Matriz constitutiva D",
              "D(E,ν, caso) por material del elemento"),
    "mod04": ("④ Rigidez e integracion Gauss",
              "Integrando + cuadratura"),
    "mod05": ("⑤ Ensamblaje K, F + BCs",
              "Flying elements"),
    "mod06": ("⑥ Fuerzas equivalentes",
              "Carga arista / peso propio"),
    "mod07": ("⑦ Discontinuidad σ",
              "Crudo vs promediado · 3D toggle"),
    "mod08": ("⑧ Direcciones σ1/σ2",
              "Cruces principales + Mohr"),
    "mod09": ("⑨ Comparacion Q4 vs Q9",
              "Sandbox: h/p-refinement · convergencia"),
}

# Modulos que NO requieren un elemento especifico (operan sobre toda la malla)
_GLOBAL_MODULES = {"mod00", "mod07", "mod08", "mod09"}


def list_modules_for_phase(phase):
    """Devuelve [(mod_key, label, descripcion), ...] para la fase pedida."""
    out = []
    for k in MODULE_PHASE.get(phase, []):
        if k in MODULE_META:
            label, desc = MODULE_META[k]
            out.append((k, label, desc))
    return out


def _is_overlay_module(cls) -> bool:
    """Detecta si la clase implementa el patrón Overlay.

    Convención: las clases que heredan de `CanvasOverlayModule` exponen
    un método de clase `activate(main_window, project, elem_id)`. No
    importamos `CanvasOverlayModule` directamente para no acoplar el
    launcher al detalle de implementación — chequeamos por API (duck
    typing) lo cual mantiene el launcher robusto frente a refactors.
    """
    activate = getattr(cls, "activate", None)
    if activate is None:
        return False
    # Distinguir de cualquier `activate` legacy: el método debe ser una
    # classmethod que NO sea heredada de `object`. Conservador: verificamos
    # que esté definida en la clase o un ancestor distinto de object.
    return any(
        "activate" in vars(klass)
        for klass in cls.__mro__
        if klass is not object
    )


def open_module(parent_tk, project, mod_key, mesh_canvas=None, elem_id=None):
    """Abre el modulo educativo identificado por mod_key.

    Para modulos en _GLOBAL_MODULES (calidad, post-process) no se pide
    seleccionar elemento — pueden trabajar sobre la malla completa.

    Despacho automatico:
        - Modo Overlay (clase con `.activate()`): pasa el main_window
          como contexto; la singleton se gestiona internamente.
        - Modo Toplevel (legacy): instancia normal con `parent_tk` como
          parent Tk.

    Retorna True si abrio el modulo; False si se cancelo o fallo la
    validacion.
    """
    if mod_key not in MODULE_MAP:
        messagebox.showerror("Error", f"Modulo desconocido: {mod_key}")
        return False

    is_global = mod_key in _GLOBAL_MODULES

    if not project.elements:
        messagebox.showwarning(
            "Aviso",
            "Cargue un modelo primero (Archivo ▸ Cargar Ejemplo)."
        )
        return False

    if not is_global:
        # Modulos por elemento: pedir uno si no se proporciono.
        if elem_id is None:
            elem_ids = sorted(project.elements.keys())
            if len(elem_ids) == 1:
                elem_id = elem_ids[0]
            else:
                elem_id = simpledialog.askinteger(
                    "Seleccionar Elemento",
                    f"Ingrese el ID del elemento ({elem_ids[0]}-{elem_ids[-1]}):",
                    initialvalue=elem_ids[0],
                    minvalue=elem_ids[0],
                    maxvalue=elem_ids[-1],
                    parent=parent_tk,
                )
                if elem_id is None:
                    return False
                if elem_id not in project.elements:
                    messagebox.showerror("Error",
                                         f"El elemento {elem_id} no existe.")
                    return False

        if mesh_canvas is not None:
            try:
                mesh_canvas.highlight_element(elem_id)
            except Exception:
                pass
    else:
        # Modulos globales: no requieren elemento. Si no se paso uno, usar
        # el primero solo como contexto.
        if elem_id is None:
            elem_id = sorted(project.elements.keys())[0]

    try:
        module_name, class_name = MODULE_MAP[mod_key]
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)

        # Resolver main_window: necesario para overlay modules. Buscamos
        # el atributo en parent_tk; si no existe, asumimos que parent_tk
        # ES el main_window (caso típico cuando se invoca desde el menú).
        main_window = getattr(parent_tk, "main_window", None) or parent_tk

        if _is_overlay_module(cls):
            # Modo overlay: la clase gestiona su propio singleton.
            cls.activate(main_window, project, elem_id)
        else:
            # Modo toplevel: instancia con parent Tk estandar.
            cls(parent_tk, project, elem_id)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al abrir modulo:\n{e}")
        return False
