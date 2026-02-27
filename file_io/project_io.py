"""
Funciones de entrada/salida para proyectos EduFEM.
Guardar/abrir proyectos en formato JSON.
"""

import json
import os
from models.project import ProjectModel


def save_project(project, filepath):
    """
    Guarda el proyecto en formato JSON.

    Parámetros:
        project: ProjectModel a guardar.
        filepath: ruta del archivo.
    """
    data = project.to_dict()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    project.file_path = filepath
    project.is_modified = False


def load_project(filepath):
    """
    Carga un proyecto desde archivo JSON.

    Parámetros:
        filepath: ruta del archivo.

    Retorna:
        ProjectModel reconstruido.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    project = ProjectModel.from_dict(data)
    project.file_path = filepath
    project.is_modified = False
    return project
