"""
Launcher compartido para los modulos educativos M0..M9.

**Arquitectura 2026-05**: TODOS los modulos son Overlay (heredan de
`CanvasOverlayModule`). El patron Toplevel + `base_module.py` fue
descartado — cada modulo es unico en su overlay y no comparte una
clase base de jerarquia compleja. Los helpers reusables viven en
`education/components/`, no en una base abstracta.

El launcher dispatchea via duck typing: si la clase expone classmethod
`activate(main_window, project, elem_id)`, es Overlay. Caso contrario
caemos al modo Toplevel legacy (mantenido como fallback defensivo
por si en el futuro un modulo amerita Toplevel propio, sin compartir
infraestructura con otros).

Modulos organizados por fase del flujo FEM:
- pre  : M0 (calidad de malla, Overlay)
- proc : M1..M7 — orden canonico del calculo FEM
    M1 Mapeo iso + funciones de forma N (xy↔ξη)
    M2 Jacobiano det J (Overlay, surface 3D + toggle F/V)
    M3 Matriz B (Overlay, snap a Gauss)
    M4 Matriz constitutiva D (por material)
    M5 Rigidez K + integracion Gauss (fusion: integral imposible)
    M6 Fuerzas equivalentes nodales
    M7 Ensamblaje K, F + BCs (sparsity + vuelo Bezier)
- post : (sin modulos — el analisis vive en las herramientas nativas
          del Post: contorno, probe, Mohr, Vista 3D)

Nota: el ex-M7 (discontinuidad / vista 3D) y ex-M8 (estado tensional
puntual) fueron consolidados en el flujo nativo del Post-Proceso:
  - 3D del campo + slider Crudo↔Suavizado -> boton "🧊 Vista 3D" en
    toolbar Post (gui/postprocessing/surface_3d_viewer.py).
  - Circulo de Mohr -> panel "Detalles" del probe (clic derecho).
    (gui/postprocessing/details_panel.py).
Las cruces principales σ1/σ2 (toggle sobre la malla) fueron eliminadas
en 2026-05: el contorno + el circulo de Mohr del probe ya cubren el
estado principal sin la capa extra.
Esta consolidacion eliminada la fragmentacion pedagogica: las vistas
viven donde se usan, no como modulos aislados.
"""

import importlib
from tkinter import messagebox


MODULE_MAP = {
    "mod00":  ("education.mod00_mesh_quality",        "MeshQualityModule"),
    "mod01":  ("education.mod01_iso_mapping",         "IsoMappingModule"),
    "mod02":  ("education.mod02_jacobian",            "JacobianModule"),
    "mod03":  ("education.mod03_b_matrix",            "BMatrixModule"),
    "mod04":  ("education.mod04_constitutive",        "ConstitutiveModule"),
    # M5 fusionado (ex-M5 + ex-M5b): la rigidez analítica (integral
    # imposible, colapsable) Y la solución numérica (cuadratura de Gauss
    # interactiva) viven en UN solo overlay con la narrativa ∫ → Σ.
    "mod05":  ("education.mod05_stiffness",           "StiffnessElementModule"),
    "mod06":  ("education.mod06_equivalent_forces",   "EquivalentForcesModule"),
    "mod07":  ("education.mod07_assembly",            "AssemblyModule"),
}

# Agrupacion pedagogica por fase del flujo FEM, alineada con el ORDEN
# CANONICO del calculo FEM:
#   1. Mapeo iso + funciones de forma  (M1)
#   2. Jacobiano (det J, distorsion local)  (M2)
#   3. Matriz B (gradiente, J^-1)  (M3)
#   4. Matriz constitutiva D (E, nu, TP/DP)  (M4)
#   5. Rigidez K_e + cuadratura de Gauss (integral imposible → suma)  (M5)
#   6. Fuerzas equivalentes nodales  (M6)
#   7. Ensamblaje K, F + BCs (vuelo Bezier + sparsity)  (M7)
#
# Fusión 2026-05 de M5: el split previo (M5 integrando + M5b cuadratura)
# se reunió en UN solo overlay. La narrativa "la integral es imposible →
# por eso usamos Gauss" es un único argumento; partirlo en dos overlays
# obligaba al alumno a abrir/cerrar para conectar las mitades. Ahora el
# salto ∫ → Σ es el héroe visual, el "monstruo" simbólico queda en un
# expander colapsable, y la cuadratura interactiva es el acto principal.
MODULE_PHASE = {
    "pre":  ["mod00"],
    "proc": ["mod01", "mod02", "mod03", "mod04",
              "mod05", "mod06", "mod07"],
    # Post sin modulos educativos: el analisis de resultados vive en las
    # herramientas nativas del Post (contorno, probe, circulo de Mohr del
    # clic derecho, 🧊 Vista 3D). El ex-M9 (comparacion Q4 vs Q9) fue
    # eliminado en 2026-05 (lento: re-resolvia mallas refinadas en vivo;
    # la convergencia/shear-locking ya esta en docs/vyv/ y la Memoria).
    "post": [],
}

# Etiquetas y descripciones para el launcher_panel (UI homogenea entre fases)
MODULE_META = {
    "mod00":  ("Ⓜ Calidad de malla",
               "Jacobiano escalado · Compacidad (Stretch)"),
    "mod01":  ("① Mapeo iso + funciones N",
               "Coordenadas naturales (ξ,η) ↔ (x,y)"),
    "mod02":  ("② Jacobiano  det J(ξ,η)",
               "Distorsion local, superficie 3D"),
    "mod03":  ("③ Matriz B (Deformacion)",
               "∂N/∂x con J⁻¹, snap a Gauss"),
    "mod04":  ("④ Matriz constitutiva D",
               "D(E,ν, caso) por material del elemento"),
    "mod05":  ("⑤ Rigidez K_e + Gauss",
               "Integral imposible → suma en PGs (cuadratura interactiva)"),
    "mod06":  ("⑥ Fuerzas equivalentes",
               "Carga arista / peso propio"),
    "mod07":  ("⑦ Ensamblaje K, F + BCs",
               "Vuelo Bezier · sparsity pattern"),
}

# Modulos que NO requieren un elemento especifico (operan sobre toda la malla)
# Publico: consumido por los paneles educativos para no desactivar visualmente
# los botones de modulos globales cuando no hay seleccion.
GLOBAL_MODULES = {"mod00"}
_GLOBAL_MODULES = GLOBAL_MODULES  # alias retrocompat interno


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

    # Resolvemos la clase ANTES de decidir el flujo de elem_id: los
    # overlays toleran abrir sin elemento (esperan el click del alumno
    # en el canvas con el módulo ya visible — UX "abrir y elegir", sin
    # diálogo intermedio). Los toplevels todavía requieren elemento al
    # construir.
    try:
        module_name, class_name = MODULE_MAP[mod_key]
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar modulo:\n{e}")
        return False

    is_overlay = _is_overlay_module(cls)

    if not is_global:
        if elem_id is None:
            elem_ids = sorted(project.elements.keys())
            if len(elem_ids) == 1:
                # Auto-pick si solo hay un elemento (UX óptima).
                elem_id = elem_ids[0]
            else:
                # **UX 2026 unificada**: el modulo se abre con `element_id
                # =None` y se actualiza apenas el alumno clickee un
                # elemento real (via `on_selection_changed` -> hook
                # `on_element_selected`). Eliminado el modal `askinteger`
                # porque rompe el flujo "click en canvas = single source
                # of truth" y obliga a tipear un numero antes de ver el
                # modulo.
                elem_id = None

        # Sincronizar selección del canvas SOLO si el elemento target no
        # está ya seleccionado como único. Antes usábamos
        # `highlight_element` que tiene semántica "second-click deselects"
        # — al abrir el módulo con el elemento ya seleccionado, lo
        # apagaba (visible como botón de módulo en gris). Usamos
        # `replace_element_selection({eid})` que es idempotente.
        if mesh_canvas is not None and elem_id is not None:
            try:
                already_unique = (
                    elem_id in mesh_canvas.selected_elements
                    and len(mesh_canvas.selected_elements) == 1
                )
                if not already_unique:
                    mesh_canvas.replace_element_selection({elem_id})
            except Exception:
                pass
    else:
        # Modulos globales: no requieren elemento. Si no se paso uno, usar
        # el primero solo como contexto.
        if elem_id is None:
            elem_id = sorted(project.elements.keys())[0]

    # Resolver main_window: necesario para overlay modules.
    main_window = _resolve_main_window(parent_tk, mesh_canvas)

    try:
        if is_overlay:
            if main_window is None or not hasattr(main_window, "mesh_canvas"):
                messagebox.showerror(
                    "Error",
                    "El modo Overlay requiere un MeshCanvas activo. "
                    "Volvé a abrir desde el menú Educación o desde la "
                    "sub-pestaña Educación de la fase actual.",
                )
                return False
            cls.activate(main_window, project, elem_id)
        else:
            # Modo toplevel: instancia con parent Tk estandar.
            cls(parent_tk, project, elem_id)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al abrir modulo:\n{e}")
        return False


def _resolve_main_window(parent_tk, mesh_canvas):
    """Resuelve el MainWindow a partir de los args del launcher.

    El menú principal pasa `parent_tk=self.root` (un Tk vacío) y el
    `mesh_canvas` real; las pestañas pasan `parent_tk=self` (que tiene
    `main_window` como atributo). Necesitamos cubrir ambos.
    """
    # 1. parent_tk tiene main_window (las pestañas: pre_tab/proc_tab/post_tab)
    cand = getattr(parent_tk, "main_window", None)
    if cand is not None and hasattr(cand, "mesh_canvas"):
        return cand
    # 2. mesh_canvas guarda main_window en __init__
    if mesh_canvas is not None:
        cand = getattr(mesh_canvas, "main_window", None)
        if cand is not None and hasattr(cand, "mesh_canvas"):
            return cand
    # 3. parent_tk tiene mesh_canvas directo (es el MainWindow)
    if hasattr(parent_tk, "mesh_canvas"):
        return parent_tk
    # 4. walk-up por widget tree desde parent_tk
    cur = parent_tk
    for _ in range(10):  # safety bound
        if cur is None:
            break
        if hasattr(cur, "mesh_canvas"):
            return cur
        cur = getattr(cur, "master", None)
    return None
