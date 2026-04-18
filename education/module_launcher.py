"""
Launcher compartido para los módulos educativos M1..M6.
Usado tanto desde el menú Educación de MainWindow como desde la sub-pestaña
"Módulos Educativos" de ProcessTab.
"""

import importlib
from tkinter import messagebox, simpledialog


MODULE_MAP = {
    "mod01": ("education.mod01_iso_mapping",      "IsoMappingModule"),
    "mod02": ("education.mod02_b_matrix",         "BMatrixModule"),
    "mod03": ("education.mod03_constitutive",     "ConstitutiveModule"),
    "mod04": ("education.mod04_stiffness_gauss",  "StiffnessGaussModule"),
    "mod05": ("education.mod05_assembly",         "AssemblyModule"),
    "mod06": ("education.mod06_equivalent_forces","EquivalentForcesModule"),
}


def open_module(parent_tk, project, mod_key, mesh_canvas=None, elem_id=None):
    """
    Abre el módulo educativo identificado por mod_key (p.ej. 'mod01').

    Parámetros:
        parent_tk: widget Tk padre (ventana principal o frame).
        project: ProjectModel activo.
        mod_key: 'mod01'..'mod06'.
        mesh_canvas: opcional, para resaltar el elemento seleccionado.
        elem_id: opcional, si ya se conoce el elemento a analizar.

    Retorna True si abrió el módulo; False si se canceló o falló la validación.
    """
    if mod_key not in MODULE_MAP:
        messagebox.showerror("Error", f"Módulo desconocido: {mod_key}")
        return False

    if not project.elements:
        messagebox.showwarning(
            "Aviso",
            "Cargue un modelo primero (Archivo ▸ Cargar Ejemplo)."
        )
        return False

    # Seleccionar elemento
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
                messagebox.showerror("Error", f"El elemento {elem_id} no existe.")
                return False

    if mesh_canvas is not None:
        try:
            mesh_canvas.highlight_element(elem_id)
        except Exception:
            pass

    try:
        module_name, class_name = MODULE_MAP[mod_key]
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        cls(parent_tk, project, elem_id)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error al abrir módulo:\n{e}")
        return False
