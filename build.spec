# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para EduFEM.

Uso:
    pyinstaller --noconfirm build.spec

Modo ONEDIR: produce `dist/EduFEM/` con el lanzador `EduFEM.exe` y la
carpeta `_internal/`. El entregable NO cambia: sigue siendo un unico
`installer/Output/EduFEM-Setup.exe`, que copia esa carpeta a `{app}`.

Por que onedir y no onefile (medido el 2026-09-10 sobre este equipo):

    modo      arranque en frio   arranque habitual   restos en %TEMP%
    onefile        10,9 s           11,9 - 14,8 s     189 MB por cada
                                                      cierre anormal
    onedir          7,0 s            3,0 -  3,5 s     ninguno

El onefile es un autoextraible: en CADA arranque descomprime ~190 MB de
binarios a una carpeta temporal (sys._MEIPASS), la vuelve a escanear el
antivirus y arranca un segundo proceso. Nunca se acelera, y si el proceso
muere sin cerrar (crash, Administrador de tareas, apagon) la carpeta
temporal queda ahi. Su unica ventaja —un solo archivo— no aplicaba: el
entregable es el instalador, y la modalidad portable ya era una carpeta,
porque el TeX embebido va al lado del .exe.

Las rutas a recursos van SIEMPRE via config.settings.resource_path, que
resuelve sys._MEIPASS (en onedir, la carpeta `_internal`) — nunca rutas
relativas al CWD.

Incluye:
    - resources/ entera (videos, fuentes, ejemplos, iconos)
    - hidden imports de pylatex / fitz / pylatex.utils (no detectados
      por autodiscover de PyInstaller en algunas versiones)

NO mete el TeX dentro del bundle: el TeX Live recortado (vendor/texlive,
generado por tools/build_texlive.py) va como carpeta `texlive/` HERMANA del
.exe (la copia el instalador, o se copia a mano en la carpeta portable);
education/components/latex_runtime.py la resuelve en runtime contra
os.path.dirname(sys.executable). Son 4180 archivos y ~57 MB que no tienen
por que pasar por el analizador de PyInstaller. Las formulas in-app usan
mathtext, no LaTeX.
"""

import os
import glob as _glob
import re as _re
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ─── Datos de version del .exe ─────────────────────────────────────────────
# Sin este recurso, Windows muestra el ejecutable sin Descripcion, Version ni
# Empresa en Propiedades -> Detalles, y los filtros de reputacion penalizan a
# los binarios sin identificar. Los valores salen de config/settings.py, que
# es la unica fuente de la version (el instalador la lee del mismo archivo).
# Se parsea con regex en vez de importar el modulo para no meter la app en
# sys.modules durante el Analysis.
def _leer_constante(nombre, defecto=""):
    with open("config/settings.py", encoding="utf-8") as _f:
        m = _re.search(rf'^{nombre}\s*=\s*"([^"]*)"', _f.read(), _re.MULTILINE)
    return m.group(1) if m else defecto


_version = _leer_constante("APP_VERSION", "0.0.0")
_publisher = _leer_constante("APP_PUBLISHER", "EduFEM")
# El recurso VERSIONINFO exige cuatro numeros; APP_VERSION trae tres.
_vtuple = tuple((list(int(p) for p in _version.split(".")) + [0, 0, 0, 0])[:4])
_version_file = os.path.join("build", "edufem_version_info.txt")
os.makedirs("build", exist_ok=True)
with open(_version_file, "w", encoding="utf-8") as _f:
    _f.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={_vtuple}, prodvers={_vtuple},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('0c0a04b0', [
      StringStruct('CompanyName', {_publisher!r}),
      StringStruct('FileDescription', 'EduFEM - Software Educativo de Elementos Finitos'),
      StringStruct('FileVersion', {_version!r}),
      StringStruct('InternalName', 'EduFEM'),
      StringStruct('LegalCopyright', {f'Copyright (c) 2026 {_publisher} - Licencia MIT'!r}),
      StringStruct('OriginalFilename', 'EduFEM.exe'),
      StringStruct('ProductName', 'EduFEM'),
      StringStruct('ProductVersion', {_version!r}),
      StringStruct('Comments', 'Analisis por el Metodo de Elementos Finitos en 2D (Q4/Q9)'),
    ])]),
    VarFileInfo([VarStruct('Translation', [0x0c0a, 1200])])
  ]
)
""")

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
# Los modulos educativos M0..M7 se cargan por NOMBRE en runtime
# (`education.module_launcher.open_module` -> `importlib.import_module`), asi
# que el analizador estatico de PyInstaller NUNCA los ve y quedaban FUERA del
# bundle: la app abria, pero cada modulo fallaba con "No module named
# education.modXX_...". Se enumeran por glob (no lista fija) para que un modulo
# nuevo en education/ entre al bundle sin tocar este spec. Basta sembrar los
# modXX: sus dependencias estaticas (education.components.*, fem.*, gui.*) las
# arrastra el grafo de imports.
edu_modules = sorted(
    "education." + os.path.splitext(os.path.basename(_p))[0]
    for _p in _glob.glob("education/mod*.py")
)
if not edu_modules:  # fail-fast: mejor romper el build que shippear sin modulos
    raise SystemExit(
        "build.spec: no se encontro education/mod*.py — "
        "correr pyinstaller desde la raiz del repo."
    )

hiddenimports = [
    # Modulos educativos M0..M7 (import dinamico, ver nota de arriba).
    *edu_modules,
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
        # El motor es NumPy vectorizado por lotes: el JIT nunca entra al
        # bundle aunque alguien lo instale en el venv (+40 MB y recompila
        # en cada arranque porque onefile extrae a una carpeta aleatoria).
        "numba", "llvmlite",
        # lxml se cuela por `fontTools.misc.etree`, que lo prefiere si esta
        # instalado y si no cae a `xml.etree` (su comportamiento documentado).
        # No figura en requirements.txt y ningun modulo de EduFEM lo importa,
        # pero basta que aparezca en el venv para sumar 3,9 MB al entregable.
        # Mismo caso para BeautifulSoup.
        "lxml", "bs4", "soupsieve",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── ONEDIR ────────────────────────────────────────────────────────────────
# `exclude_binaries=True` deja el EXE como un lanzador chico; los binarios,
# zipfiles y datas los junta COLLECT en dist/EduFEM/_internal/. Para volver a
# onefile habria que borrar el COLLECT, pasar a=binaries/zipfiles/datas al EXE
# y quitar exclude_binaries — pero antes de hacerlo, releer la tabla de
# tiempos del docstring de arriba.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EduFEM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX apagado a proposito. Hoy no esta instalado en este equipo, asi que
    # `upx=True` no hacia nada; el dia que alguien lo instale, el build dejaria
    # de ser reproducible y empezaria a producir DLL empaquetadas, que es una
    # de las senales que mas peso tiene en los heuristicos de los antivirus.
    # EduFEM ya viaja sin firma de codigo: no conviene sumarle esa marca por
    # unos pocos MB, que ademas el instalador recomprime igual con LZMA2.
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/icons/edufem.ico" if os.path.exists("resources/icons/edufem.ico") else None,
    version=_version_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,              # ver la nota del EXE
    upx_exclude=[],
    name="EduFEM",          # -> dist/EduFEM/
)
