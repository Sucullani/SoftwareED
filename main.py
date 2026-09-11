"""
EduFEM - Software Educativo de Elementos Finitos
Punto de entrada principal de la aplicación.

Ejecutar con:
    python main.py                    # ventana vacía
    python main.py modelo.edufem      # abre ese proyecto al arrancar

Además de crear la ventana, acá va la integración con Windows que el
instalador necesita y que tiene que ocurrir ANTES de que exista la ventana:

- **Identidad en la barra de tareas** (`AppUserModelID`): el instalador
  escribe el mismo identificador en los accesos directos; sin él, Windows
  agrupa el proceso por el nombre del ejecutable y el icono que el alumno
  ancla a la barra se desprende del acceso directo.
- **Mutex nombrado**: le permite al instalador (directiva `AppMutex` de
  `installer/EduFEM.iss`) detectar que EduFEM está abierto y ofrecer cerrarlo,
  en vez de copiar sobre un `.exe` en uso y dejar la instalación a medias.
- **Archivo por línea de comandos**: es lo que recibe la app cuando el alumno
  hace doble clic en un `.edufem` (la asociación la registra el instalador).

Nada de esto es obligatorio: en Linux o macOS, o si la llamada a la API falla,
la app arranca igual.
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto está en el PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import APP_MUTEX_NAME, APP_USER_MODEL_ID
from gui.main_window import MainWindow

_IS_WINDOWS = sys.platform.startswith("win")


def _set_windows_app_identity() -> None:
    """Declara el AppUserModelID del proceso. Silencioso si no es Windows."""
    if not _IS_WINDOWS:
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID)
    except Exception:
        pass


def _hold_app_mutex():
    """Crea el mutex nombrado que el instalador consulta.

    Devuelve el handle, que el llamador debe mantener vivo mientras corra la
    app: Windows libera el mutex al cerrarse el proceso. No se comprueba si ya
    existía — EduFEM permite varias ventanas abiertas a la vez, el mutex solo
    señala "hay al menos una".
    """
    if not _IS_WINDOWS:
        return None
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL,
                                          wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        return kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
    except Exception:
        return None


def _project_path_from_argv(argv) -> str | None:
    """Primer argumento que sea un archivo existente, o None.

    Se ignoran las opciones (`-algo`) y las rutas inexistentes: un argumento
    raro no debe impedir que la app abra.
    """
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        if os.path.isfile(arg):
            return os.path.abspath(arg)
        print(f"EduFEM: no existe el archivo '{arg}'; se ignora.",
              file=sys.stderr)
    return None


def main():
    """Inicia la aplicación EduFEM."""
    _set_windows_app_identity()
    _app_mutex = _hold_app_mutex()          # vive hasta que termina el proceso
    app = MainWindow(project_path=_project_path_from_argv(sys.argv))
    app.run()


if __name__ == "__main__":
    main()
