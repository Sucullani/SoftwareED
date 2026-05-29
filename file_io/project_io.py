"""
Funciones de entrada/salida para proyectos EduFEM.
Guardar/abrir proyectos en formato JSON.
"""

import json
import os
import tempfile
from models.project import ProjectModel


def save_project(project, filepath):
    """
    Guarda el proyecto en formato JSON de forma ATÓMICA.

    Escribe a un archivo temporal en el mismo directorio, hace fsync para
    forzar el flush a disco, y luego `os.replace` (rename atómico). Así un
    fallo a mitad de escritura (cierre forzado, disco lleno, corte de luz)
    nunca deja el archivo original corrupto o truncado: o queda el contenido
    viejo intacto, o el nuevo completo.

    Parámetros:
        project: ProjectModel a guardar.
        filepath: ruta del archivo.
    """
    data = project.to_dict()
    directory = os.path.dirname(os.path.abspath(filepath)) or "."
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, filepath)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
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
