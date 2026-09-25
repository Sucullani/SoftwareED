# -*- coding: utf-8 -*-
"""
licencias_terceros.py — arma installer/dist_extra/LICENCIAS-TERCEROS.txt.

El instalador redistribuye en binario las bibliotecas que usa EduFEM, y sus
licencias (BSD, MIT, Apache…) piden que el aviso de copyright acompañe a esa
copia. PyInstaller no copia los `dist-info` de los paquetes (en `_internal/`
solo quedaba el de NumPy), así que este guion los reúne en un archivo que
`installer/EduFEM.iss` instala junto a LICENCIA.txt.

De dónde sale la lista de paquetes:

  * del armado de PyInstaller, si existe (`build/build/*.toc`): son los
    archivos que de verdad entraron al paquete, y cada uno se asigna al
    paquete de pip que lo instaló. Así aparecen también los que PyInstaller
    arrastra porque están en el entorno y algún módulo los importa de forma
    opcional, que no figuran en `requirements.txt`;
  * si no, de la cadena de dependencias de `requirements.txt`, resuelta con
    `importlib.metadata` en el entorno en que corre.

Suma a mano lo que no es un paquete de pip: el intérprete de Python, Tcl/Tk,
el cargador de PyInstaller y el TeX Live embebido. No lleva fecha ni rutas de
este equipo: con el mismo entorno el archivo sale idéntico, y el diff de git
muestra solo lo que cambió de verdad.

Uso:
    python tools/licencias_terceros.py

`tools/build_all.ps1` lo corre entre el ejecutable (paso 3) y el instalador
(paso 4), cuando la lista del armado está recién hecha.
"""

from __future__ import annotations

import ast
import importlib.metadata as md
import os
import re
import sys
import textwrap
from pathlib import Path

from packaging.requirements import Requirement

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "installer" / "dist_extra" / "LICENCIAS-TERCEROS.txt"
TRABAJO_PYINSTALLER = RAIZ / "build" / "build"
TEXLIVE = RAIZ / "vendor" / "texlive"
ANCHO = 64

# Archivos de licencia dentro de un paquete: LICENSE, LICENCE, COPYING o
# NOTICE en cualquier parte del nombre (numpy trae `dragon4_LICENSE.txt`,
# scipy `COPYING_QHULL.txt`), y todo lo que viva en `*.dist-info/licenses/`.
_NOMBRE_LICENCIA = re.compile(r"(licen[cs]e|copying|notice)", re.IGNORECASE)

# Herramientas del armado: no viajan en el paquete. PyInstaller tiene su
# propia sección, porque de él sí va el cargador.
_SOLO_ARMADO = {"pyinstaller", "pyinstaller-hooks-contrib", "altgraph", "pefile",
                "pywin32-ctypes", "setuptools", "pip"}

# Texto de la licencia MIT, para el paquete que la declara en sus metadatos
# pero no trae el archivo (ordered-set).
_MIT = (
    "Permission is hereby granted, free of charge, to any person obtaining a "
    "copy of this software and associated documentation files (the "
    "\"Software\"), to deal in the Software without restriction, including "
    "without limitation the rights to use, copy, modify, merge, publish, "
    "distribute, sublicense, and/or sell copies of the Software, and to permit "
    "persons to whom the Software is furnished to do so, subject to the "
    "following conditions:",
    "The above copyright notice and this permission notice shall be included "
    "in all copies or substantial portions of the Software.",
    "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS "
    "OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF "
    "MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN "
    "NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, "
    "DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR "
    "OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE "
    "USE OR OTHER DEALINGS IN THE SOFTWARE.",
)


def _normal(nombre: str) -> str:
    return re.sub(r"[-_.]+", "-", nombre).lower()


# ─── Qué paquetes van dentro ───────────────────────────────────────────────

def _desde_requirements() -> dict[str, md.Distribution]:
    """Cadena de dependencias de requirements.txt en este entorno."""
    raices = []
    for linea in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if linea and not linea.startswith("-"):
            raices.append(Requirement(linea).name)
    vistos: dict[str, md.Distribution] = {}
    pila = list(raices)
    while pila:
        nombre = pila.pop()
        clave = _normal(nombre)
        if clave in vistos:
            continue
        try:
            dist = md.distribution(nombre)
        except md.PackageNotFoundError:
            if nombre in raices:
                raise SystemExit(
                    f"licencias_terceros: '{nombre}' (requirements.txt) no está "
                    "instalado: correr desde el .venv del build")
            continue
        vistos[clave] = dist
        for texto in dist.requires or []:
            req = Requirement(texto)
            if req.marker and not req.marker.evaluate({"extra": ""}):
                continue
            pila.append(req.name)
    return vistos


def _rutas_del_armado() -> list[str]:
    """Rutas de archivo que nombran los .toc del último armado de PyInstaller."""
    rutas: list[str] = []

    def recorrer(nodo):
        if isinstance(nodo, str):
            if "site-packages" in nodo:
                rutas.append(nodo)
        elif isinstance(nodo, (list, tuple)):
            for hijo in nodo:
                recorrer(hijo)

    for toc in sorted(TRABAJO_PYINSTALLER.glob("*.toc")):
        try:
            recorrer(ast.literal_eval(toc.read_text(encoding="utf-8")))
        except (ValueError, SyntaxError):
            continue
    return rutas


def _desde_el_armado() -> dict[str, md.Distribution]:
    """Paquetes de pip a los que pertenece cada archivo que entró al paquete."""
    rutas = _rutas_del_armado()
    if not rutas:
        return {}
    duenio: dict[str, md.Distribution] = {}
    for dist in md.distributions():
        for f in dist.files or []:
            duenio[os.path.normcase(os.path.abspath(dist.locate_file(f)))] = dist
    encontrados: dict[str, md.Distribution] = {}
    for ruta in rutas:
        dist = duenio.get(os.path.normcase(os.path.abspath(ruta)))
        if dist is not None:
            encontrados.setdefault(_normal(dist.metadata["Name"]), dist)
    return encontrados


# ─── Qué dice cada paquete ─────────────────────────────────────────────────

def _licencia(dist: md.Distribution) -> str:
    m = dist.metadata
    if m.get("License-Expression"):
        return m["License-Expression"].strip()
    clasificadores = [c.split("::")[-1].strip() for c in (m.get_all("Classifier") or [])
                      if c.startswith("License :: ")]
    if clasificadores:
        return ", ".join(dict.fromkeys(clasificadores))
    texto = (m.get("License") or "").strip()
    if texto and "\n" not in texto and len(texto) <= 60:
        return texto
    return "ver el texto"


def _textos(dist: md.Distribution) -> list[tuple[str, str]]:
    textos, vistos = [], set()
    for f in dist.files or []:
        rel = str(f).replace("\\", "/")
        base = rel.rsplit("/", 1)[-1]
        if base.endswith((".py", ".pyc", ".pyi")) or "__pycache__" in rel:
            continue
        en_dist_info = ".dist-info/licenses/" in rel or ".dist-info/LICENSE" in rel
        if not (en_dist_info or _NOMBRE_LICENCIA.search(base)):
            continue
        try:
            texto = Path(dist.locate_file(f)).read_text(encoding="utf-8",
                                                          errors="replace").strip()
        except OSError:
            continue
        if texto and texto not in vistos:
            vistos.add(texto)
            textos.append((rel, texto))
    return textos


# ─── Armado del archivo ────────────────────────────────────────────────────

def _titulo(texto: str, car: str = "=") -> str:
    return f"{car * ANCHO}\n  {texto}\n{car * ANCHO}\n"


def _parrafo(texto: str) -> str:
    # Sin cortar en guiones ni palabras largas: partida, una URL deja de
    # funcionar al copiarla.
    return textwrap.fill(" ".join(texto.split()), width=ANCHO,
                         break_on_hyphens=False, break_long_words=False) + "\n"


def _seccion_python() -> str:
    version = ".".join(str(n) for n in sys.version_info[:3])
    partes = [_titulo(f"Python {version} (intérprete y biblioteca estándar)", "-"),
              _parrafo("El ejecutable lleva el intérprete de CPython y los módulos "
                       "de su biblioteca estándar que usa EduFEM. Licencia: "
                       "PSF-2.0. El texto incluye además las condiciones de las "
                       "bibliotecas que trae la distribución de Windows (OpenSSL, "
                       "libffi, bzip2, zlib y otras).") + "\n"]
    lic = Path(sys.base_prefix) / "LICENSE.txt"
    partes.append(lic.read_text(encoding="utf-8", errors="replace").strip() + "\n")
    return "".join(partes)


def _seccion_tcltk() -> str:
    import tkinter
    terms = next(iter(sorted(Path(sys.base_prefix, "tcl").glob("tk*/license.terms"))), None)
    partes = [_titulo(f"Tcl/Tk {tkinter.TkVersion} (interfaz gráfica)", "-"),
              _parrafo("Tcl y Tk viajan con Python y dibujan todas las ventanas "
                       "de EduFEM. Comparten este texto de licencia, de estilo "
                       "BSD.") + "\n"]
    if terms is not None:
        partes.append(terms.read_text(encoding="utf-8", errors="replace").strip() + "\n")
    return "".join(partes)


def _seccion_pyinstaller() -> str:
    dist = md.distribution("pyinstaller")
    partes = [_titulo(f"PyInstaller {dist.version} (cargador del ejecutable)", "-"),
              _parrafo("EduFEM.exe es el cargador de PyInstaller, que arranca el "
                       "intérprete con los módulos de _internal. Se distribuye bajo "
                       "GPL-2.0 o posterior, con una excepción expresa que permite "
                       "distribuir los programas empaquetados bajo cualquier "
                       "licencia (ver el texto).") + "\n"]
    for _rel, texto in _textos(dist):
        partes.append(texto + "\n")
    return "".join(partes)


def _seccion_texlive() -> str:
    repositorio = ""
    procedencia = TEXLIVE / "EDUFEM-TEXLIVE.txt"
    if procedencia.exists():
        m = re.search(r"Repositorio de paquetes:\s*(\S+)",
                      procedencia.read_text(encoding="utf-8", errors="replace"))
        if m:
            repositorio = m.group(1)
    texto = (
        "EduFEM usa pdflatex como programa aparte para compilar la Memoria de "
        "Cálculo y la Teoría MEF. TeX Live es una colección de paquetes "
        "independientes, cada uno con su propia licencia libre: entre ellos, "
        "el motor pdfTeX (GPL) y la biblioteca kpathsea (LGPL), los paquetes "
        "de LaTeX (LPPL) y las fuentes Latin Modern (GUST Font License). Esas "
        "licencias rigen los programas de la carpeta texlive y no se "
        "extienden a EduFEM, que los invoca como procesos separados. Las "
        "condiciones de copia de la distribución están en "
        "texlive\\LICENSE.TL y texlive\\LICENSE.CTAN, y qué se tomó y cómo se "
        "recortó, en texlive\\EDUFEM-TEXLIVE.txt. Código fuente: el de TeX "
        "Live, en https://tug.org/texlive/, y el de cada paquete, en "
        "https://ctan.org/pkg"
    )
    if repositorio:
        texto += (f"; la copia exacta de la que salió este subconjunto es "
                  f"{repositorio}")
    return _titulo("TeX Live (carpeta texlive)", "-") + _parrafo(texto + ".")


def _seccion_paquete(dist: md.Distribution) -> str:
    nombre, version, licencia = dist.metadata["Name"], dist.version, _licencia(dist)
    partes = [_titulo(f"{nombre} {version} — {licencia}", "-")]
    textos = _textos(dist)
    if textos:
        for rel, texto in textos:
            if len(textos) > 1:
                partes.append(f"[{rel}]\n")
            partes.append(texto + "\n\n")
    elif "MIT" in licencia:
        autor = dist.metadata.get("Author") or dist.metadata.get("Author-email") or ""
        autor = re.sub(r"\s*<[^>]*>", "", autor).strip()
        partes.append(_parrafo("El paquete no incluye su archivo de licencia. Va el "
                               "texto estándar de la licencia MIT que declaran sus "
                               "metadatos, con el autor que figura en ellos:") + "\n")
        if autor:
            partes.append(f"Copyright (c) {autor}\n\n")
        partes.append("\n\n".join(textwrap.fill(p, ANCHO) for p in _MIT) + "\n\n")
    else:
        partes.append(_parrafo("El paquete no incluye su archivo de licencia. "
                               f"Licencia declarada en sus metadatos: {licencia}.")
                      + "\n")
    return "".join(partes)


def main() -> int:
    paquetes = _desde_el_armado()
    origen = "del último armado de PyInstaller (build/build/*.toc)"
    if not paquetes:
        paquetes = _desde_requirements()
        origen = "de la cadena de dependencias de requirements.txt"
    for clave in list(paquetes):
        if clave in _SOLO_ARMADO:
            del paquetes[clave]
    orden = sorted(paquetes.values(), key=lambda d: d.metadata["Name"].lower())

    cab = [
        _titulo("EduFEM - Avisos de licencia de terceros"),
        "\n",
        _parrafo("EduFEM se publica bajo la licencia MIT (LICENCIA.txt, en esta "
                 "misma carpeta). El instalador incluye además componentes de "
                 "terceros que conservan sus propias licencias. Todas son "
                 "licencias libres que permiten redistribuirlos junto con "
                 "EduFEM, y las de las bibliotecas piden que su aviso de "
                 "copyright acompañe a la copia: eso es este archivo."),
        "\n",
        _parrafo(f"Lista generada por tools/licencias_terceros.py a partir "
                 f"{origen}."),
        "\n",
        "CONTENIDO\n",
        "  - Python, Tcl/Tk y PyInstaller (el intérprete y el cargador)\n",
        "  - TeX Live (carpeta texlive)\n",
        f"  - Bibliotecas de Python ({len(orden)} paquetes):\n",
    ]
    for dist in orden:
        cab.append(f"      {dist.metadata['Name']} {dist.version}: {_licencia(dist)}\n")
    cuerpo = [_seccion_python(), "\n", _seccion_tcltk(), "\n", _seccion_pyinstaller(),
              "\n", _seccion_texlive(), "\n"]
    for dist in orden:
        cuerpo.append(_seccion_paquete(dist))

    texto = "".join(cab) + "\n" + "".join(cuerpo)
    texto = re.sub(r"\n{3,}", "\n\n", texto).rstrip() + "\n"
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 con BOM, como el LEEME: el Bloc de notas lo abre sin adivinar la
    # codificación.
    SALIDA.write_text(texto, encoding="utf-8-sig", newline="\r\n")
    print(f"licencias_terceros: {len(orden)} paquetes, a partir {origen}")
    print(f"  -> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
