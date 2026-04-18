"""
Persistencia de la lista de proyectos abiertos recientemente.
Archivo en ~/.edufem/recent.json. Máximo RECENT_FILES_MAX entradas, sin duplicados,
el más reciente al frente.
"""

import json
import os

from config.settings import USER_CONFIG_DIR, RECENT_FILES_PATH, RECENT_FILES_MAX


def _ensure_dir():
    if not os.path.exists(USER_CONFIG_DIR):
        try:
            os.makedirs(USER_CONFIG_DIR, exist_ok=True)
        except OSError:
            pass


def load():
    """Retorna la lista de paths recientes (puede contener archivos ya borrados)."""
    if not os.path.exists(RECENT_FILES_PATH):
        return []
    try:
        with open(RECENT_FILES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(p) for p in data][:RECENT_FILES_MAX]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def _save(paths):
    _ensure_dir()
    try:
        with open(RECENT_FILES_PATH, "w", encoding="utf-8") as f:
            json.dump(paths[:RECENT_FILES_MAX], f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def add(path):
    """Agrega o mueve un path al frente de la lista."""
    if not path:
        return
    path = os.path.abspath(path)
    paths = load()
    paths = [p for p in paths if os.path.abspath(p) != path]
    paths.insert(0, path)
    _save(paths)


def remove(path):
    """Remueve una entrada de la lista."""
    if not path:
        return
    path_abs = os.path.abspath(path)
    paths = [p for p in load() if os.path.abspath(p) != path_abs]
    _save(paths)


def clear():
    """Vacía completamente la lista."""
    _save([])
