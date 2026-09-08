"""
latex_runtime: localiza el compilador LaTeX (``pdflatex``) y compila
documentos de pylatex de forma determinista, sin diálogos ni ventanas de
consola.

Motivación (2026-09-08): la Memoria de Cálculo y el Theory Hub dependían del
``pdflatex`` que hubiera en el PATH. Con un MiKTeX básico, cada paquete que
falta (booktabs, tcolorbox, pgf, babel-spanish, listings...) abre un diálogo
de instalación, y sin internet la compilación falla. EduFEM ahora lleva un
**TeX Live recortado** propio (carpeta ``texlive/`` hermana del ejecutable,
producida por ``tools/build_texlive.py``) y solo cae al PATH si no lo tiene.

Orden de resolución (:func:`find_latex_runtime`):

1. ``EDUFEM_TEXLIVE_DIR`` — variable de entorno (desarrollo, tests, build).
2. TeX Live embebido — ``<carpeta del .exe>/texlive`` en el programa
   instalado o portable; ``<repo>/vendor/texlive`` corriendo desde el código.
3. ``pdflatex`` del PATH (MiKTeX o TeX Live del sistema). Si es MiKTeX se
   agrega ``-enable-installer``: instala los paquetes faltantes sin preguntar
   (necesita internet), en vez de un diálogo por paquete.
4. Nada → ``None``. El caller eleva ``FileNotFoundError`` y la GUI muestra el
   diálogo con botón de descarga (``gui/dialogs/pdflatex_missing_dialog``).

:func:`compile_document` escribe el ``.tex`` en un directorio de trabajo con
ruta ASCII (TeX Live en Windows falla si la ruta lleva tildes), corre
``pdflatex`` dos veces (índice y referencias) y mueve el PDF al destino, que
sí puede tener cualquier nombre. No usa ``Document.generate_pdf`` de pylatex:
aquel no permite ocultar la ventana de consola ni elegir el directorio de
trabajo, y prefiere ``latexmk`` (que en MiKTeX exige un Perl externo).
"""

from __future__ import annotations

import functools
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional

from config.settings import BASE_DIR

# Carpeta del TeX embebido, hermana del ejecutable (instalador / portable).
BUNDLE_DIRNAME = "texlive"
# Carpeta del TeX embebido en desarrollo (gitignored; la genera
# tools/build_texlive.py).
DEV_BUNDLE_RELPATH = os.path.join("vendor", "texlive")
# Variable de entorno que fuerza una distribución (tests, build, depuración).
ENV_TEXLIVE_DIR = "EDUFEM_TEXLIVE_DIR"

# Flag de MiKTeX: instalar paquetes faltantes sin preguntar.
MIKTEX_AUTOINSTALL_FLAG = "-enable-installer"

# Pasadas de pdflatex: la primera escribe .toc/.aux, la segunda los inserta.
DEFAULT_PASSES = 2
# Tiempo máximo por pasada (MiKTeX puede quedarse descargando paquetes).
PASS_TIMEOUT_S = 600
# Nombre fijo del trabajo dentro del directorio ASCII de compilación.
JOBNAME = "documento"

_EXE = ".exe" if sys.platform.startswith("win") else ""


class LatexCompileError(RuntimeError):
    """``pdflatex`` corrió pero no produjo el PDF. ``log_tail`` trae las
    últimas líneas del ``.log`` (o de la salida) para diagnosticar."""

    def __init__(self, message: str, log_tail: str = ""):
        super().__init__(message)
        self.log_tail = log_tail


@dataclass(frozen=True)
class LatexRuntime:
    """Compilador resuelto: ruta absoluta, origen y flags extra."""

    pdflatex: str
    kind: str  # "bundle" | "miktex" | "texlive" | "unknown"
    extra_args: tuple[str, ...] = ()

    @property
    def is_bundle(self) -> bool:
        return self.kind == "bundle"


# ---------------------------------------------------------------------------
# Resolución del compilador
# ---------------------------------------------------------------------------

def _pdflatex_in_texlive_dir(root: str) -> Optional[str]:
    """Ruta a ``pdflatex`` dentro de una raíz TeX Live (``bin/<plataforma>``),
    o None si no está."""
    if not root or not os.path.isdir(root):
        return None
    candidates = [os.path.join(root, "bin", "windows", "pdflatex" + _EXE)]
    candidates += sorted(glob.glob(os.path.join(root, "bin", "*", "pdflatex" + _EXE)))
    for exe in candidates:
        if os.path.isfile(exe):
            return os.path.abspath(exe)
    return None


def bundle_candidates() -> list[str]:
    """Raíces donde puede vivir el TeX embebido, en orden de prioridad."""
    roots: list[str] = []
    env_dir = os.environ.get(ENV_TEXLIVE_DIR)
    if env_dir:
        roots.append(env_dir)
    if getattr(sys, "frozen", False):
        # .exe empaquetado: la carpeta texlive/ va junto al ejecutable, NO
        # dentro del onefile (se re-extraería en cada arranque).
        roots.append(os.path.join(os.path.dirname(sys.executable), BUNDLE_DIRNAME))
    else:
        roots.append(os.path.join(BASE_DIR, DEV_BUNDLE_RELPATH))
    return roots


def bundled_texlive_dir() -> Optional[str]:
    """Raíz del TeX embebido disponible, o None."""
    for root in bundle_candidates():
        if _pdflatex_in_texlive_dir(root):
            return os.path.abspath(root)
    return None


def _run_quiet(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """``subprocess.run`` sin ventana de consola (la app es ``console=False``;
    cada pdflatex abriría una consola negra)."""
    if sys.platform.startswith("win"):
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    kwargs.setdefault("stdout", subprocess.PIPE)
    kwargs.setdefault("stderr", subprocess.STDOUT)
    return subprocess.run(cmd, **kwargs)


@functools.lru_cache(maxsize=8)
def _probe_kind(exe: str) -> str:
    """Clasifica un ``pdflatex`` del PATH: ``miktex`` / ``texlive`` /
    ``unknown``. Primero por la ruta (barato); si no alcanza, por
    ``--version`` (cacheado por ruta)."""
    low = exe.lower()
    if "miktex" in low:
        return "miktex"
    if "texlive" in low or "tinytex" in low:
        return "texlive"
    try:
        out = _run_quiet([exe, "--version"], timeout=20).stdout
        text = out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out)
    except Exception:
        return "unknown"
    if "miktex" in text.lower():
        return "miktex"
    if "tex live" in text.lower():
        return "texlive"
    return "unknown"


def runtime_for_executable(exe: str, *, kind: Optional[str] = None) -> LatexRuntime:
    """Construye el runtime para un ejecutable concreto (bundle o PATH)."""
    kind = kind or _probe_kind(exe)
    extra: tuple[str, ...] = ()
    if kind == "miktex":
        extra = (MIKTEX_AUTOINSTALL_FLAG,)
    return LatexRuntime(pdflatex=os.path.abspath(exe), kind=kind, extra_args=extra)


def find_latex_runtime() -> Optional[LatexRuntime]:
    """Resuelve el compilador según el orden documentado en el módulo.

    No se cachea: son unos pocos ``isfile`` + ``which``, y así instalar
    MiKTeX o copiar la carpeta ``texlive/`` surte efecto sin reiniciar EduFEM.
    """
    for root in bundle_candidates():
        exe = _pdflatex_in_texlive_dir(root)
        if exe:
            return LatexRuntime(pdflatex=exe, kind="bundle")
    exe = shutil.which("pdflatex")
    if exe:
        return runtime_for_executable(exe)
    return None


# ---------------------------------------------------------------------------
# Directorio de trabajo con ruta ASCII
# ---------------------------------------------------------------------------

def _short_path(path: str) -> str:
    """Nombre corto 8.3 de Windows (sin tildes ni espacios) si el volumen lo
    tiene habilitado; si no, devuelve ``path`` tal cual."""
    if not sys.platform.startswith("win"):
        return path
    try:
        import ctypes
        from ctypes import wintypes

        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW  # type: ignore[attr-defined]
        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        GetShortPathNameW.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(1024)
        n = GetShortPathNameW(path, buf, len(buf))
        if 0 < n < len(buf):
            return buf.value
    except Exception:
        pass
    return path


def safe_workdir_root() -> str:
    """Directorio base para compilar, con ruta ASCII.

    TeX Live en Windows no resuelve rutas con caracteres fuera de ASCII y
    ``%TEMP%`` lleva el nombre del usuario (``C:\\Users\\José\\...``). Orden:
    ``%TEMP%`` si ya es ASCII → su nombre corto 8.3 → ``%PUBLIC%\\EduFEM\\tmp``
    (siempre ASCII y escribible por todos los usuarios) → ``%TEMP%`` como
    último recurso.
    """
    tmp = tempfile.gettempdir()
    if tmp.isascii():
        return tmp
    short = _short_path(tmp)
    if short.isascii() and os.path.isdir(short):
        return short
    public = os.environ.get("PUBLIC") or os.path.join(
        os.environ.get("SystemDrive", "C:"), os.sep, "Users", "Public")
    fallback = os.path.join(public, "EduFEM", "tmp")
    try:
        os.makedirs(fallback, exist_ok=True)
        if fallback.isascii():
            return fallback
    except OSError:
        pass
    return tmp


def make_workdir(prefix: str = "edufem_latex_") -> tempfile.TemporaryDirectory:
    """``TemporaryDirectory`` bajo :func:`safe_workdir_root`. El caller lo
    limpia con ``.cleanup()`` (o lo usa como context manager)."""
    return tempfile.TemporaryDirectory(prefix=prefix, dir=safe_workdir_root())


# ---------------------------------------------------------------------------
# Compilación
# ---------------------------------------------------------------------------

def _log_tail(workdir: str, fallback_output: str = "", max_lines: int = 40) -> str:
    """Últimas líneas del ``.log`` (o de la salida de pdflatex), priorizando
    la primera línea de error ``!`` para que el mensaje sea accionable."""
    text = fallback_output
    log_path = os.path.join(workdir, JOBNAME + ".log")
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        pass
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    # Con -file-line-error los errores salen como `archivo:linea: mensaje`;
    # sin ese flag (o en errores fatales) empiezan con `!`.
    error_re = re.compile(r"^(?:!|[^\s].*?:\d+: )")
    first_error = next((i for i, ln in enumerate(lines) if error_re.match(ln)), None)
    if first_error is not None:
        chunk = lines[first_error:first_error + max_lines]
    else:
        chunk = lines[-max_lines:]
    return "\n".join(chunk)


def compile_document(doc, out_pdf: str, *, workdir: Optional[str] = None,
                     passes: int = DEFAULT_PASSES, keep_tex: bool = False,
                     runtime: Optional[LatexRuntime] = None) -> str:
    """Compila un ``pylatex.Document`` a ``out_pdf``.

    Parameters
    ----------
    doc : pylatex.Document
    out_pdf : ruta de destino del PDF (se crea la carpeta si no existe; se
        sobreescribe si ya hay uno).
    workdir : directorio donde compilar. Si el documento incluye figuras por
        ruta relativa, deben estar ahí. ``None`` → uno temporal ASCII propio.
    passes : pasadas de pdflatex (2 para que el índice quede completo).
    keep_tex : conserva ``<out_pdf sin .pdf>.tex`` junto al PDF.
    runtime : compilador ya resuelto; por defecto :func:`find_latex_runtime`.

    Raises
    ------
    FileNotFoundError : no hay compilador (ni embebido ni en el PATH).
    LatexCompileError : pdflatex falló o no produjo el PDF.
    """
    rt = runtime or find_latex_runtime()
    if rt is None:
        raise FileNotFoundError(
            "pdflatex no encontrado: falta la carpeta 'texlive' que acompaña "
            "a EduFEM y no hay una distribución TeX en el PATH."
        )
    if not out_pdf.lower().endswith(".pdf"):
        out_pdf = out_pdf + ".pdf"

    owned: Optional[tempfile.TemporaryDirectory] = None
    if workdir is None:
        owned = make_workdir()
        workdir = owned.name
    try:
        base = os.path.join(workdir, JOBNAME)
        doc.generate_tex(base)  # UTF-8, coherente con inputenc utf8
        cmd = [rt.pdflatex, "-interaction=nonstopmode", "-halt-on-error",
               "-file-line-error", *rt.extra_args, JOBNAME + ".tex"]
        output = ""
        for _ in range(max(1, passes)):
            try:
                proc = _run_quiet(cmd, cwd=workdir, timeout=PASS_TIMEOUT_S)
            except subprocess.TimeoutExpired as e:
                raise LatexCompileError(
                    f"pdflatex superó los {PASS_TIMEOUT_S} s de compilación "
                    f"({rt.kind}).", _log_tail(workdir)) from e
            raw = proc.stdout or b""
            output = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
            if proc.returncode != 0:
                tail = _log_tail(workdir, output)
                raise LatexCompileError(
                    f"pdflatex terminó con código {proc.returncode} "
                    f"({rt.kind}: {rt.pdflatex}).", tail)
        pdf_tmp = base + ".pdf"
        if not os.path.isfile(pdf_tmp):
            raise LatexCompileError(
                f"pdflatex no produjo el PDF ({rt.kind}: {rt.pdflatex}).",
                _log_tail(workdir, output))
        out_dir = os.path.dirname(os.path.abspath(out_pdf))
        os.makedirs(out_dir, exist_ok=True)
        if os.path.exists(out_pdf):
            os.remove(out_pdf)
        shutil.move(pdf_tmp, out_pdf)
        if keep_tex:
            shutil.copyfile(base + ".tex", out_pdf[:-4] + ".tex")
        return out_pdf
    finally:
        if owned is not None:
            try:
                owned.cleanup()
            except Exception:
                # Windows puede negar el borrado si un visor abrió el .log.
                pass
