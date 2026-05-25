"""
latex_cache: compilacion + cache persistente de fragmentos LaTeX a PNG.

Pipeline (cuando MiKTeX/pdflatex esta disponible):
    expr (str) -> .tex con \\documentclass{standalone} -> pdflatex
                  -> PDF -> fitz.get_pixmap -> PNG -> cache disco

Cache:
    Directorio `~/.edufem/latex_cache/{sha256}.png`. Persistente entre
    sesiones. Key = SHA256(latex_body + dpi + color + bg). Reabrir EduFEM
    con las mismas formulas = render instantaneo.

Fallback:
    Si `pdflatex` no esta en el PATH, las llamadas a `get_or_compile`
    retornan `None`. El caller (LatexBlock) cae al render mathtext del
    pipeline legacy (latex_image / latex_figure).

Concurrencia:
    `get_or_compile` es thread-safe via lock global; multiples threads
    pueden pedir la misma expresion sin doble compile. Usado por el
    warmup en background.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Iterable, Optional


# ─── Paths ──────────────────────────────────────────────────────────────────

def cache_dir() -> Path:
    """Directorio persistente de cache. Lo crea si no existe."""
    d = Path.home() / ".edufem" / "latex_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── Disponibilidad de pdflatex ─────────────────────────────────────────────

_PDFLATEX_PATH: Optional[str] = None
_PDFLATEX_CHECKED = False
_LOCK = threading.RLock()


def pdflatex_path() -> Optional[str]:
    """Retorna el path absoluto a pdflatex, o None si no esta instalado.

    Cacheado: la primera llamada hace `shutil.which`; las siguientes
    retornan el path cacheado. Si el usuario instala MiKTeX despues de
    arrancar EduFEM, debe reiniciar (decision deliberada: evitar checks
    constantes en hot path).
    """
    global _PDFLATEX_PATH, _PDFLATEX_CHECKED
    with _LOCK:
        if not _PDFLATEX_CHECKED:
            _PDFLATEX_PATH = shutil.which("pdflatex")
            _PDFLATEX_CHECKED = True
        return _PDFLATEX_PATH


def is_latex_available() -> bool:
    """True si pdflatex esta accesible. Usado por LatexBlock para
    decidir si compilar o caer al fallback mathtext."""
    return pdflatex_path() is not None


# ─── Compilacion ────────────────────────────────────────────────────────────

# Preambulo standalone. `varwidth` ajusta el bbox al contenido (sin
# margenes de pagina). `xcolor` permite pasar color de fuente y fondo.
# `amsmath/amssymb/bm` son los paquetes matematicos canonicos que ya usa
# `theory_builder.py` — misma identidad tipografica que Teoria y Memoria
# PDF.
_STANDALONE_PREAMBLE = r"""
\documentclass[border=2pt,varwidth=true]{standalone}
\usepackage{amsmath,amssymb,amsfonts,bm}
\usepackage{xcolor}
%COLORS%
\pagecolor{edufembg}
\color{edufemfg}
\begin{document}
$\displaystyle %BODY% $
\end{document}
""".strip()


# Preambulo "text mode" para LatexStatusLabel: el body es texto plano
# con `$...$` para math inline. Soporta `\\` para newlines y comandos
# de texto (`\textbf`, `\text`, etc.). Multiples lineas via `tabular`
# centradas verticalmente.
_STANDALONE_PREAMBLE_TEXT = r"""
\documentclass[border=2pt,varwidth=true]{standalone}
\usepackage{amsmath,amssymb,amsfonts,bm}
\usepackage{xcolor}
\usepackage{array}
%COLORS%
\pagecolor{edufembg}
\color{edufemfg}
\begin{document}
\begin{tabular}{c}
%BODY%
\end{tabular}
\end{document}
""".strip()


def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    """`#dcdcdc` -> (0.86, 0.86, 0.86). Maneja `#rgb` y `#rrggbb`."""
    s = hex_color.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return (1.0, 1.0, 1.0)
    try:
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return (1.0, 1.0, 1.0)


def build_tex(body: str, color: str, bg: str, *, text_mode: bool = False) -> str:
    """Construye el .tex completo con el preambulo standalone y los
    colores definidos.

    `text_mode=False` (default): body envuelto en `$\\displaystyle ... $`.
    Para formulas matematicas puras.

    `text_mode=True`: body envuelto en `\\begin{tabular}{c} ... \\end{tabular}`.
    Para textos con math inline (usar `$...$` para entrar a math mode
    dentro del texto). Soporta `\\\\` para newlines.
    """
    fr, fg, fb = _hex_to_rgb01(color)
    br, bg_, bb = _hex_to_rgb01(bg)
    color_block = (
        rf"\definecolor{{edufemfg}}{{rgb}}{{{fr:.3f},{fg:.3f},{fb:.3f}}}"
        rf"\definecolor{{edufembg}}{{rgb}}{{{br:.3f},{bg_:.3f},{bb:.3f}}}"
    )
    template = _STANDALONE_PREAMBLE_TEXT if text_mode else _STANDALONE_PREAMBLE
    return (
        template
        .replace("%COLORS%", color_block)
        .replace("%BODY%", body)
    )


# Alias retrocompat (uso interno historico). El nombre publico es `build_tex`.
_build_tex = build_tex


def _make_key(body: str, dpi: int, color: str, bg: str, *, text_mode: bool = False) -> str:
    """SHA256 de los inputs (truncado a 16 chars). El truncado preserva
    ~64 bits de entropia: colision practicamente imposible para nuestra
    biblioteca (< 10k formulas distintas).

    `text_mode` se incluye en el hash para que un mismo body compilado
    como math vs text genere PNGs distintos en cache (no se pisan)."""
    mode_tag = "T" if text_mode else "M"
    payload = f"v2|{mode_tag}|{body}|{dpi}|{color}|{bg}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


class LatexCompileError(RuntimeError):
    """Compilacion fallo (sintaxis LaTeX invalida, paquete faltante, etc.).
    El caller deberia caer al fallback mathtext."""


def _compile_latex_to_png(
    body: str, *, dpi: int, color: str, bg: str, out_png: Path,
    text_mode: bool = False,
) -> Path:
    """Compila el body LaTeX a PNG en `out_png`. Levanta LatexCompileError
    si pdflatex falla o si fitz no puede abrir el PDF resultante."""
    pdflatex = pdflatex_path()
    if pdflatex is None:
        raise LatexCompileError("pdflatex no disponible en PATH")

    tex_source = build_tex(body, color=color, bg=bg, text_mode=text_mode)

    with tempfile.TemporaryDirectory(prefix="edufem_latex_") as tmp_str:
        tmp = Path(tmp_str)
        tex_file = tmp / "frag.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    pdflatex,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory", str(tmp),
                    str(tex_file),
                ],
                capture_output=True,
                text=True,
                timeout=20,
                # Windows: evita ventanas de consola flash.
                creationflags=(
                    0x08000000  # CREATE_NO_WINDOW
                    if os.name == "nt" else 0
                ),
            )
        except subprocess.TimeoutExpired as e:
            raise LatexCompileError(f"pdflatex timeout (>20s): {body[:60]!r}") from e
        except FileNotFoundError as e:
            raise LatexCompileError(f"pdflatex no ejecutable: {e}") from e

        pdf_file = tmp / "frag.pdf"
        if proc.returncode != 0 or not pdf_file.exists():
            # log abreviado para diagnostico (sin contaminar stdout)
            log_excerpt = (proc.stdout or proc.stderr or "")[-400:]
            raise LatexCompileError(
                f"pdflatex fallo (rc={proc.returncode}): {log_excerpt}"
            )

        # PDF -> PNG via fitz. Import diferido para no pagar el costo si
        # el modulo es importado pero nunca se compila nada (caso
        # warmup-skipped + modo fallback).
        import fitz  # type: ignore
        from PIL import Image

        doc = fitz.open(str(pdf_file))
        try:
            page = doc[0]
            zoom = dpi / 72.0  # PDF unit = 1/72 inch
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        finally:
            doc.close()

        out_png.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_png, format="PNG", optimize=True)
        return out_png


# ─── API publica ────────────────────────────────────────────────────────────

# Lock por clave para evitar doble compile concurrente de la misma expr.
# Ligero: un solo dict global protegido por _LOCK; las claves se limpian
# al terminar el compile.
_INFLIGHT: dict[str, threading.Event] = {}


def get_or_compile(
    body: str,
    *,
    dpi: int = 200,
    color: str = "#dcdcdc",
    bg: str = "#222233",
    text_mode: bool = False,
) -> Optional[Path]:
    """Retorna el path al PNG cacheado; compila si falta. None si
    pdflatex no esta disponible o si la compilacion fallo.

    `body` debe ser LaTeX en modo matematico (se envuelve en `$...$`
    automaticamente). Para una matriz, pasar `\\begin{bmatrix}...
    \\end{bmatrix}` directamente.

    `text_mode=True` cambia el wrapper a `tabular` text-with-math-inline.
    Usa `$...$` para math dentro y `\\\\` para newlines.
    """
    if not is_latex_available():
        return None

    key = _make_key(body, dpi=dpi, color=color, bg=bg, text_mode=text_mode)
    out = cache_dir() / f"{key}.png"
    if out.exists() and out.stat().st_size > 0:
        return out

    # Concurrencia: si otro thread esta compilando la misma key, esperar.
    with _LOCK:
        evt = _INFLIGHT.get(key)
        if evt is None:
            evt = threading.Event()
            _INFLIGHT[key] = evt
            owner = True
        else:
            owner = False

    if not owner:
        evt.wait(timeout=25)
        return out if out.exists() else None

    try:
        try:
            _compile_latex_to_png(
                body, dpi=dpi, color=color, bg=bg,
                out_png=out, text_mode=text_mode,
            )
            return out
        except LatexCompileError:
            return None
    finally:
        with _LOCK:
            _INFLIGHT.pop(key, None)
        evt.set()


def warmup(
    expressions: Iterable[tuple[str, dict]],
    *,
    on_progress: Optional[callable] = None,
    cooldown_ms: int = 150,
) -> int:
    """Precompila una lista de expresiones en background. Cada item es
    `(body, kwargs)` donde kwargs son los mismos que `get_or_compile`
    (dpi, color, bg).

    `cooldown_ms` introduce un sleep entre compiles (default 150 ms) para
    bajar la presion sobre el main thread Tk. Sin esto, el warmup
    saturaba el CPU y la GUI se sentia bloqueada por varios segundos.
    Total warmup: ~2.5s per compile + 0.15s gap = ~80s para 30 expr,
    completamente en background y amable con la UI.

    Retorna el numero de expresiones cacheadas (incluye hits previos).
    """
    import time as _time
    exprs = list(expressions)
    total = len(exprs)
    done = 0
    for body, kwargs in exprs:
        try:
            png = get_or_compile(body, **kwargs)
        except Exception:
            png = None
        done += 1
        if on_progress is not None:
            try:
                on_progress(done, total)
            except Exception:
                pass
        # Yield CPU al main thread Tk para que la UI no se sienta atascada.
        # Skip si fue cache hit (no compilo nada → no hay nada a ceder).
        if png is not None and cooldown_ms > 0:
            _time.sleep(cooldown_ms / 1000.0)
    return done


def clear_cache() -> int:
    """Borra todo el cache en disco. Retorna cantidad de archivos
    eliminados. Util si la paleta cambia o para liberar espacio."""
    d = cache_dir()
    n = 0
    for p in d.glob("*.png"):
        try:
            p.unlink()
            n += 1
        except OSError:
            pass
    return n


def cache_stats() -> dict:
    """Diagnostico: cantidad de archivos + tamaño total en disco."""
    d = cache_dir()
    files = list(d.glob("*.png"))
    size = sum(f.stat().st_size for f in files if f.is_file())
    return {
        "dir": str(d),
        "count": len(files),
        "bytes": size,
        "latex_available": is_latex_available(),
        "pdflatex_path": pdflatex_path(),
    }
