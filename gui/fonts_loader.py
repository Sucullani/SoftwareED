"""
fonts_loader: registra fuentes TTF privadas del proceso al boot de EduFEM.

Plataforma-especifico:
    - Windows: AddFontResourceExW con FR_PRIVATE — la fuente queda
      disponible solo para el proceso actual, sin tocar el registry
      ni el folder Fonts\\ del sistema. No requiere admin.
    - Linux/macOS: no-op (Tk indexa via fontconfig; las fuentes en
      ~/.fonts/ o /usr/share/fonts/ se cargan automaticamente).

Uso:
    from gui.fonts_loader import register_bundled_fonts
    register_bundled_fonts()  # idempotente

Si las TTF no estan presentes en resources/fonts/, la funcion log-ea
silenciosamente y retorna — el fallback de LatexBlock (Tk serif italic)
sigue funcionando.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


# Lista de TTF que se intentan registrar. Los nombres siguen la
# convencion CMU oficial (cm-unicode). Si se agregan/quitan archivos en
# resources/fonts/, sincronizar aqui.
_BUNDLED_TTFS = (
    "cmunrm.ttf",  # Roman
    "cmunti.ttf",  # Italic
    "cmunbx.ttf",  # Bold
    "cmunbi.ttf",  # Bold Italic
)


def _resources_root() -> Path:
    """Carpeta raiz de `resources/`, resuelve tanto en dev (running desde
    repo) como en bundle PyInstaller (sys._MEIPASS).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Dev: este archivo vive en gui/. Subimos un nivel a la raiz del repo.
    return Path(__file__).resolve().parent.parent


def fonts_dir() -> Path:
    return _resources_root() / "resources" / "fonts"


def register_bundled_fonts() -> int:
    """Registra las fuentes bundleadas (Windows: privadas del proceso).
    Retorna la cantidad de TTF efectivamente registradas. Idempotente:
    llamadas repetidas no duplican el registro (Windows acepta sin error,
    pero conviene saltear).
    """
    if os.name != "nt":
        return 0  # Tk + fontconfig lo manejan.

    fdir = fonts_dir()
    if not fdir.is_dir():
        return 0

    registered = 0
    for name in _BUNDLED_TTFS:
        ttf = fdir / name
        if not ttf.is_file():
            continue
        if _register_one_windows(ttf):
            registered += 1
    return registered


def _register_one_windows(ttf_path: Path) -> bool:
    """AddFontResourceExW del path TTF con flag FR_PRIVATE. True si OK."""
    try:
        import ctypes
        from ctypes import wintypes  # noqa: F401 — fuerza import
    except Exception:
        return False

    try:
        gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        # AddFontResourceExW(LPCWSTR name, DWORD fl, PVOID pdv) -> int
        gdi32.AddFontResourceExW.restype = ctypes.c_int
        gdi32.AddFontResourceExW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_void_p,
        ]
        FR_PRIVATE = 0x10
        n = gdi32.AddFontResourceExW(str(ttf_path), FR_PRIVATE, 0)
        return n > 0
    except Exception:
        return False


def list_present_fonts() -> Iterable[str]:
    """Diagnostico: nombres de archivo presentes en resources/fonts/."""
    fdir = fonts_dir()
    if not fdir.is_dir():
        return ()
    return tuple(p.name for p in fdir.glob("*.ttf"))
