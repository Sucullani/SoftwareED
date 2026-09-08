"""
Test del runtime LaTeX (education/components/latex_runtime.py).

Estilo printout (sin pytest): `python -m tests.test_latex_runtime`.

Cobertura:
  - test_env_override_bundle: EDUFEM_TEXLIVE_DIR gana y se clasifica como bundle.
  - test_clasificacion_por_ruta: MiKTeX recibe -enable-installer; TeX Live no.
  - test_safe_workdir_ascii: el directorio de compilacion es ASCII y se limpia.
  - test_sin_compilador: sin bundle ni PATH -> None / FileNotFoundError.
  - test_compila_en_ruta_con_tilde: PDF (y .tex con keep_tex) en un destino con
    tilde y espacio (skip si no hay compilador).
  - test_error_con_log_tail: un .tex roto eleva LatexCompileError con la linea
    '!' del log (skip si no hay compilador).
  - test_bundle_presente: informa si vendor/texlive esta y se usa.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education.components import latex_runtime as lr  # noqa: E402
from education.components.theory_builder import TheoryDoc  # noqa: E402


def _restore_env(snapshot: dict) -> None:
    for k in (lr.ENV_TEXLIVE_DIR, "PATH"):
        if k in snapshot:
            os.environ[k] = snapshot[k]
        else:
            os.environ.pop(k, None)


def _env_snapshot() -> dict:
    return {k: os.environ[k] for k in (lr.ENV_TEXLIVE_DIR, "PATH") if k in os.environ}


def test_env_override_bundle() -> bool:
    print("test_env_override_bundle ...")
    snap = _env_snapshot()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            binw = Path(tmp) / "bin" / "windows"
            binw.mkdir(parents=True)
            fake = binw / ("pdflatex" + lr._EXE)
            fake.write_bytes(b"")
            os.environ[lr.ENV_TEXLIVE_DIR] = tmp
            rt = lr.find_latex_runtime()
            if rt is None or rt.kind != "bundle":
                print(f"  FAIL: se esperaba bundle, vino {rt}")
                return False
            if os.path.normcase(rt.pdflatex) != os.path.normcase(str(fake)):
                print(f"  FAIL: ruta inesperada {rt.pdflatex}")
                return False
            if rt.extra_args:
                print(f"  FAIL: el bundle no lleva flags extra: {rt.extra_args}")
                return False
            if os.path.normcase(lr.bundled_texlive_dir() or "") != os.path.normcase(tmp):
                print("  FAIL: bundled_texlive_dir no devuelve la raiz del env")
                return False
        print("  OK: EDUFEM_TEXLIVE_DIR se resuelve como bundle, sin flags")
        return True
    finally:
        _restore_env(snap)


def test_clasificacion_por_ruta() -> bool:
    print("test_clasificacion_por_ruta ...")
    mik = lr.runtime_for_executable(r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe")
    tl = lr.runtime_for_executable(r"C:\texlive\2026\bin\windows\pdflatex.exe")
    if mik.kind != "miktex" or mik.extra_args != (lr.MIKTEX_AUTOINSTALL_FLAG,):
        print(f"  FAIL: MiKTeX -> {mik}")
        return False
    if tl.kind != "texlive" or tl.extra_args:
        print(f"  FAIL: TeX Live -> {tl}")
        return False
    print("  OK: MiKTeX lleva -enable-installer; TeX Live no")
    return True


def test_safe_workdir_ascii() -> bool:
    print("test_safe_workdir_ascii ...")
    root = lr.safe_workdir_root()
    if not root.isascii() or not os.path.isdir(root):
        print(f"  FAIL: raiz no ASCII o inexistente: {root!r}")
        return False
    wd = lr.make_workdir("edufem_test_")
    path = wd.name
    if not os.path.isdir(path) or not path.isascii():
        print(f"  FAIL: workdir invalido: {path!r}")
        return False
    wd.cleanup()
    if os.path.exists(path):
        print("  FAIL: cleanup no borro el workdir")
        return False
    print(f"  OK: workdir ASCII bajo {root}")
    return True


def test_sin_compilador() -> bool:
    print("test_sin_compilador ...")
    snap = _env_snapshot()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ[lr.ENV_TEXLIVE_DIR] = os.path.join(tmp, "no_existe")
            os.environ["PATH"] = tmp  # sin pdflatex
            # Simula el .exe sin carpeta texlive: el candidato de desarrollo
            # (vendor/texlive) podria existir, asi que se compara con el.
            rt = lr.find_latex_runtime()
            if rt is not None and rt.kind == "bundle" and "vendor" in rt.pdflatex.lower():
                print("  SKIP: vendor/texlive presente (el fallback no se puede aislar)")
                return True
            if rt is not None:
                print(f"  FAIL: se esperaba None, vino {rt}")
                return False
            td = TheoryDoc(title="x")
            try:
                lr.compile_document(td.document(), os.path.join(tmp, "x.pdf"))
            except FileNotFoundError:
                print("  OK: sin compilador -> None y FileNotFoundError")
                return True
            print("  FAIL: compile_document no elevo FileNotFoundError")
            return False
    finally:
        _restore_env(snap)


def _has_runtime() -> bool:
    return lr.find_latex_runtime() is not None


def test_compila_en_ruta_con_tilde() -> bool:
    print("test_compila_en_ruta_con_tilde ...")
    if not _has_runtime():
        print("  SKIP: sin compilador LaTeX")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        dest_dir = os.path.join(tmp, "José Pérez")
        os.makedirs(dest_dir)
        td = TheoryDoc(title="Prueba de ruta", subtitle="con tilde y espacio")
        td.section_numbered("Sección")
        td.para("Texto con acentos: áéíóú ñ.")
        td.equation(r"\sigma = \mathbf{D}\,\boldsymbol{\varepsilon}")
        base = os.path.join(dest_dir, "salida")
        td.compile_to(base, keep_tex=True)
        pdf, tex = base + ".pdf", base + ".tex"
        if not os.path.isfile(pdf) or os.path.getsize(pdf) < 1000:
            print("  FAIL: no se genero el PDF en la ruta con tilde")
            return False
        if not os.path.isfile(tex):
            print("  FAIL: keep_tex no dejo el .tex junto al PDF")
            return False
        rt = lr.find_latex_runtime()
        print(f"  OK: PDF de {os.path.getsize(pdf)} bytes en ruta con tilde ({rt.kind})")
        return True


def test_error_con_log_tail() -> bool:
    print("test_error_con_log_tail ...")
    if not _has_runtime():
        print("  SKIP: sin compilador LaTeX")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        td = TheoryDoc(title="Roto")
        td.raw(r"\comandoInexistente")
        try:
            td.compile_to(os.path.join(tmp, "roto"))
        except lr.LatexCompileError as e:
            if "!" not in e.log_tail:
                print(f"  FAIL: log_tail sin linea de error: {e.log_tail[:200]!r}")
                return False
            print("  OK: LatexCompileError con la linea '!' del log")
            return True
        print("  FAIL: un .tex roto no elevo LatexCompileError")
        return False


def test_bundle_presente() -> bool:
    print("test_bundle_presente ...")
    rt = lr.find_latex_runtime()
    if rt is None:
        print("  INFO: sin compilador (ni vendor/texlive ni PATH)")
    elif rt.is_bundle:
        print(f"  OK: TeX Live embebido en uso: {rt.pdflatex}")
    else:
        print(f"  INFO: sin vendor/texlive; se usa {rt.kind}: {rt.pdflatex}")
    return True


if __name__ == "__main__":
    tests = [
        test_env_override_bundle,
        test_clasificacion_por_ruta,
        test_safe_workdir_ascii,
        test_sin_compilador,
        test_compila_en_ruta_con_tilde,
        test_error_con_log_tail,
        test_bundle_presente,
    ]
    results = [t() for t in tests]
    ok = sum(1 for r in results if r)
    print("=" * 60)
    print(f"Resultado: {ok}/{len(results)} OK")
    sys.exit(0 if ok == len(results) else 1)
