"""
Carpeta en la que se abren los diálogos de archivo del alumno.

Motivo (auditoría de distribución, 2026-09-10): ningún ``filedialog`` declaraba
``initialdir``, así que Tk los abría en el directorio de trabajo del proceso.
Corriendo desde el repositorio eso es la raíz del código —molesto pero
inofensivo—; en la **aplicación instalada** es la carpeta del programa, porque
los accesos directos que crea el instalador arrancan en ``{app}``. El primer
«Guardar Como» del alumno dejaba entonces su modelo dentro de
``AppData\\Local\\Programs\\EduFEM`` (o de ``C:\\ProgramData\\EduFEM``): una
carpeta que él no visita, que el Explorador ni siquiera muestra por defecto y
que la desinstalación deja huérfana con los trabajos adentro.

Orden de resolución de :func:`carpeta_inicial`:

1. La última carpeta que el alumno usó, si todavía existe. Se persiste en
   ``~/.edufem/paths.json``, al lado de la lista de recientes.
2. ``Documentos\\EduFEM``, creada la primera vez que hace falta.
3. ``Documentos``, o el perfil del usuario si tampoco está.

``Documentos`` se le pregunta a Windows por su *known folder* en lugar de
asumir ``~/Documents``: el nombre real depende del idioma del sistema y la
carpeta suele estar redirigida a OneDrive.
"""

import json
import os
import sys

from config.settings import USER_CONFIG_DIR

# Junto a recent.json: mismo directorio de configuración del usuario.
PATHS_FILE = os.path.join(USER_CONFIG_DIR, "paths.json")
# Subcarpeta propia dentro de Documentos, para que los modelos del alumno no
# queden sueltos entre el resto de sus archivos.
SUBCARPETA = "EduFEM"
# Clave dentro de paths.json. El archivo es un dict para poder crecer sin
# romper compatibilidad con las versiones que solo escribieron esta entrada.
_CLAVE_ULTIMA = "ultima_carpeta"


def _documentos():
    """Ruta real de «Documentos» según Windows, o None.

    Se usa ``SHGetFolderPathW`` con ``CSIDL_PERSONAL``: devuelve la ruta
    vigente aunque la carpeta esté redirigida (OneDrive) o el sistema esté en
    otro idioma. Fuera de Windows devuelve None y el llamador cae al perfil.
    """
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        ruta = buf.value
        return ruta if ruta and os.path.isdir(ruta) else None
    except Exception:
        return None


def _cargar():
    """Contenido de paths.json como dict; vacío si no existe o está corrupto."""
    try:
        with open(PATHS_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _guardar(datos):
    """Escribe paths.json. Silencioso ante errores de disco: recordar la
    carpeta es una comodidad, nunca un motivo para interrumpir al alumno."""
    try:
        os.makedirs(USER_CONFIG_DIR, exist_ok=True)
        with open(PATHS_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def carpeta_de_trabajo():
    """``Documentos\\EduFEM``, creada si hace falta.

    Si Documentos no existe o no se puede crear la subcarpeta, devuelve el
    mejor ancestro disponible; nunca falla ni devuelve una ruta inexistente.
    """
    docs = _documentos() or os.path.join(os.path.expanduser("~"), "Documents")
    if os.path.isdir(docs):
        destino = os.path.join(docs, SUBCARPETA)
        try:
            os.makedirs(destino, exist_ok=True)
            return destino
        except OSError:
            return docs
    return os.path.expanduser("~")


def carpeta_inicial():
    """Carpeta con la que abrir el próximo diálogo de archivo."""
    guardada = _cargar().get(_CLAVE_ULTIMA)
    if guardada and os.path.isdir(guardada):
        return guardada
    return carpeta_de_trabajo()


def recordar(path):
    """Registra la carpeta de ``path`` como punto de partida del próximo
    diálogo. Acepta la ruta del archivo, no la de la carpeta."""
    if not path:
        return
    carpeta = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(carpeta):
        return
    datos = _cargar()
    if datos.get(_CLAVE_ULTIMA) == carpeta:
        return          # sin escritura si no cambió nada
    datos[_CLAVE_ULTIMA] = carpeta
    _guardar(datos)


def nombre_sugerido(file_path, extension):
    """Nombre propuesto para un «Guardar Como» o una exportación.

    Reusa el nombre del proyecto abierto con otra extensión —así la Memoria de
    ``viga.edufem`` se propone como ``viga.pdf``— y cae a ``modelo`` cuando el
    proyecto todavía no se guardó nunca.
    """
    base = os.path.splitext(os.path.basename(file_path))[0] if file_path else ""
    return (base or "modelo") + extension
