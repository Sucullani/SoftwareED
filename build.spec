# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para EduFEM.

Uso:
    pyinstaller --noconfirm build.spec

Modo ONEFILE: produce un unico `dist/EduFEM.exe` autoextraible (no una
carpeta). En cada arranque PyInstaller descomprime los binarios + resources
a una carpeta temporal (sys._MEIPASS) -> el primer arranque es mas lento que
en onedir, pero el entregable es un solo archivo. Las rutas a recursos van
SIEMPRE via config.settings.resource_path (resuelve sys._MEIPASS) — nunca
rutas relativas al CWD.

Incluye:
    - resources/ entera (videos, fuentes, ejemplos, iconos)
    - hidden imports de pylatex / fitz / pylatex.utils (no detectados
      por autodiscover de PyInstaller en algunas versiones)

NO bundlea MiKTeX. Si el usuario lo tiene instalado, las formulas se
renderizan con calidad documento. Sin MiKTeX, EduFEM detecta y cae al
fallback mathtext con un banner one-shot (ver MainWindow._init_latex_pipeline).
"""

import os
import glob as _glob
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ─── Datos a bundlear ──────────────────────────────────────────────────────
# Carpeta `resources/` entera (videos webp, fuentes TTF, ejemplos DXF, icons).
# El path es relativo al spec; el destino dentro del bundle preserva la
# estructura para que sys._MEIPASS + ruta relativa funcione (ver
# config.settings.resource_path / gui.fonts_loader._resources_root).
datas = [
    ("resources/videos/*.webp", "resources/videos"),
    ("resources/examples/*", "resources/examples"),
    ("resources/icons/*.ico", "resources/icons"),  # icono de ventana (iconbitmap)
    ("config/*.py", "config"),  # por si algun importlib.resources lo busca
]
# Las TTF son opcionales (CMU para LaTeX). Solo se incluyen si estan presentes;
# un glob vacio aborta el Analysis en PyInstaller 6.x con "Unable to find ...".
if _glob.glob("resources/fonts/*.ttf"):
    datas.append(("resources/fonts/*.ttf", "resources/fonts"))

# ─── Hidden imports ────────────────────────────────────────────────────────
hiddenimports = [
    # pylatex tiene submodulos no detectados por autodiscover.
    *collect_submodules("pylatex"),
    # fitz / PyMuPDF
    "fitz",
    # PIL plugins
    "PIL._tkinter_finder",
    # scipy.sparse linalg backend
    "scipy.sparse.linalg",
    "scipy.sparse.csgraph",
    # matplotlib embebido en Tk (FigureCanvasTkAgg en modulos educativos)
    "matplotlib.backends.backend_tkagg",
    "mpl_toolkits.mplot3d",
    # ezdxf
    *collect_submodules("ezdxf"),
]

# Datos adicionales de paquetes terceros (matplotlib fonts, etc.)
datas += collect_data_files("matplotlib")

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Reducir tamaño excluyendo dependencias no usadas:
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "IPython", "jupyter",
        "pytest", "pytest_cov",
        "av",  # PyAV: decidido NO usar (ver CLAUDE.md)
        "tkvideoplayer",  # idem
        "manim",  # solo se usa offline para prerender videos
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── ONEFILE ───────────────────────────────────────────────────────────────
# Binarios, zipfiles y datas van DENTRO del EXE (no hay COLLECT) -> un solo
# archivo. exclude_binaries se omite (default False).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="EduFEM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/icons/edufem.ico" if os.path.exists("resources/icons/edufem.ico") else None,
)
