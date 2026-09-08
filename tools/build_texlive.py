"""
build_texlive.py — arma el TeX Live recortado que EduFEM lleva embebido.

Por qué: la Memoria de Cálculo y el Theory Hub se compilan con pdflatex. Depender
del MiKTeX de cada usuario producía un diálogo de instalación por paquete faltante
(booktabs, tcolorbox, pgf, babel-spanish, listings...) y fallaba sin internet. Con
este bundle el instalador es autosuficiente: sin diálogos, sin red, mismo PDF en
toda PC.

Qué hace (cada paso se puede saltar con flags):
  1. Descarga TinyTeX-0 (TeX Live "infraonly" para Windows, ~24 MB, versión fijada
     en TINYTEX_URL) y lo extrae en --dest (por defecto vendor/texlive, gitignored).
  2. Instala con tlmgr la lista fija PACKAGES desde un snapshot fechado de tlnet
     (TLNET_SNAPSHOT) para que el build sea reproducible; regenera el formato
     pdflatex (con patrones de silabeo español) y los mapas de fuentes.
  3. Valida compilando los documentos reales de EduFEM (Memoria Q4 educativo y
     directo, Memoria Q9, Theory Hub) con el bundle SIN podar.
  4. Poda: Perl, Ghostscript, instalador, docs, fuentes OpenType, motores que no
     son pdfTeX. Regenera los ls-R (kpathsea exige la base de datos: TEXMFDBS
     lleva "!!").
  5. Vuelve a validar con el bundle podado y escribe EDUFEM-TEXLIVE.txt
     (procedencia, lista de paquetes, tamaños).

Uso (desde la raíz del repo, con el venv):
    python tools/build_texlive.py                      # build completo
    python tools/build_texlive.py --tinytex-exe X.exe  # sin descargar
    python tools/build_texlive.py --validate-only      # solo paso 3/5
    python tools/build_texlive.py --force              # rehace vendor/texlive

Requiere internet para los pasos 1 y 2 (una sola vez por versión). El resultado
lo consume `installer/EduFEM.iss` ({app}\\texlive) y, en desarrollo,
`education/components/latex_runtime.py` (vendor/texlive).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEST = ROOT / "vendor" / "texlive"
DOWNLOAD_DIR = ROOT / "vendor" / "_downloads"

# Versión fijada de TinyTeX-0 (TeX Live 2026). Cambiarla implica re-validar.
TINYTEX_VERSION = "v2026.09"
TINYTEX_URL = (
    "https://github.com/rstudio/tinytex-releases/releases/download/"
    f"{TINYTEX_VERSION}/TinyTeX-0-windows-{TINYTEX_VERSION}.exe"
)
# Snapshot diario de tlnet (texlive.info los conserva): mismo año que TinyTeX.
TLNET_SNAPSHOT = "https://texlive.info/tlnet-archive/2026/09/07/tlnet/"
TLNET_FALLBACK = "https://mirror.ctan.org/systems/texlive/tlnet/"

# Paquetes TeX Live que consumen la Memoria y el Theory Hub. Lista derivada de
# compilar los documentos reales con `pdflatex -recorder` (2026-09-08): 95 archivos
# de macros, 26 fuentes Type1 de Latin Modern. tlmgr agrega las dependencias
# declaradas; los auxiliares de hyperref se listan igual por si alguna falta.
PACKAGES = [
    # infraestructura del formato pdflatex
    # (l3backend-pdftex.def viene dentro de l3kernel en TeX Live 2026)
    "kpathsea", "pdftex", "latex-bin", "latex", "latex-fonts", "latexconfig",
    "l3kernel", "tex-ini-files", "unicode-data", "hyphen-base",
    "hyph-utf8", "cm", "amsfonts", "lm",
    # pylatex carga fontenc[T1] ANTES de lmodern: en ese instante LaTeX pide
    # ecrm1095.tfm (fuentes EC). Sin `ec` la compilación aborta en fontenc.sty.
    "ec",
    # idioma
    "babel", "babel-spanish", "hyphen-spanish",
    # documento
    "amsmath", "tools", "booktabs", "caption", "fancyhdr", "float", "geometry",
    "graphics", "graphics-cfg", "graphics-def", "mptopdf", "epstopdf-pkg",
    "xcolor", "hyperref", "url", "lastpage", "pdflscape",
    # cajas de la memoria (tcolorbox[most] arrastra pgf, listings, tikzfill)
    "tcolorbox", "pgf", "environ", "trimspaces", "etoolbox", "listings",
    "listingsutf8", "tikzfill", "pdfcol",
    # auxiliares de hyperref / kernel (ex oberdiek)
    "iftex", "infwarerr", "ltxcmds", "pdftexcmds", "pdfescape", "kvoptions",
    "kvsetkeys", "kvdefinekeys", "intcalc", "bigintcalc", "bitset", "stringenc",
    "uniquecounter", "refcount", "rerunfilecheck", "gettitlestring", "hycolor",
    "letltxmacro", "auxhook", "atbegshi", "atveryend", "etexcmds",
]
# longtable, bm y verbatim viven en `tools`; lscape, keyval y color en `graphics`.

# ─── Poda ──────────────────────────────────────────────────────────────────
# Binarios que quedan en bin/windows (el resto se borra). En TeX Live 2026
# para Windows pdftex.exe/pdflatex.exe son lanzadores de 6 KB que cargan
# pdftex.dll (2,3 MB): por eso se conservan las DLL (salvo las de Lua).
KEEP_BIN = {"pdftex.exe", "pdflatex.exe", "kpsewhich.exe"}
# DLLs que NO hacen falta para pdftex (motores Lua y runscript/texlua).
DROP_DLL = {"luatex.dll", "luahbtex.dll", "lua53w64.dll"}
# Carpetas de primer nivel de texmf-dist que sobreviven.
KEEP_TEXMF_DIST_TOP = {"tex", "fonts", "web2c", "ls-R"}
# Subcarpetas de texmf-dist/fonts que sobreviven.
KEEP_FONT_KINDS = {"tfm", "type1", "enc", "map", "vf"}
# Subcarpetas de texmf-dist/tex que se borran (motores que no son pdfTeX y
# archivos que solo se usan al construir el formato).
DROP_TEX_TOP = {"luatex", "lualatex", "xetex", "xelatex", "plain", "latex-dev"}
# En texmf-var/web2c solo queda el formato pdflatex.
KEEP_FMT = {os.path.join("pdftex", "pdflatex.fmt")}
# Raíz: archivos/carpetas que se borran.
DROP_ROOT = {"tlpkg", "tl-tray-menu.exe", "texmfcnf.lua", "install-tl-windows.bat"}


def log(msg: str) -> None:
    # La consola de Windows (cp1252) no puede con todo Unicode: nunca abortar
    # el build por un carácter en un mensaje.
    try:
        sys.stdout.reconfigure(errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass
    print(f"[texlive] {msg}", flush=True)


def human(nbytes: float) -> str:
    return f"{nbytes / 1e6:.1f} MB"


def dir_size(path: Path) -> tuple[int, int]:
    total, count = 0, 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
            count += 1
    return total, count


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True,
        env: dict | None = None, timeout: int = 3600) -> subprocess.CompletedProcess:
    log("$ " + " ".join(str(c) for c in cmd))
    proc = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace",
                          env=env, timeout=timeout)
    tail = "\n".join(proc.stdout.strip().splitlines()[-25:])
    if proc.returncode != 0:
        log(f"código {proc.returncode}; últimas líneas:\n{tail}")
        if check:
            raise SystemExit(f"falló: {cmd[0]}")
    return proc


# ─── Paso 1: descarga + extracción ─────────────────────────────────────────

def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000:
        log(f"ya descargado: {dest.name} ({human(dest.stat().st_size)})")
        return dest
    log(f"descargando {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.replace(dest)
    log(f"descargado: {human(dest.stat().st_size)}")
    return dest


def extract_tinytex(sfx: Path, dest: Path) -> None:
    """El .exe de TinyTeX es un autoextraíble 7-Zip: acepta -y -o<dir>."""
    if dest.exists():
        raise SystemExit(f"{dest} ya existe (usar --force para rehacerlo)")
    with tempfile.TemporaryDirectory(prefix="tinytex_") as tmp:
        run([sfx, "-y", f"-o{tmp}"])
        inner = Path(tmp) / "TinyTeX"
        if not (inner / "bin" / "windows").is_dir():
            raise SystemExit(f"extracción inesperada en {tmp}: {os.listdir(tmp)}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(inner), str(dest))
    log(f"extraído en {dest}")


# ─── Paso 2: tlmgr ─────────────────────────────────────────────────────────

def tl_env(dest: Path) -> dict:
    env = dict(os.environ)
    env["PATH"] = str(dest / "bin" / "windows") + os.pathsep + env.get("PATH", "")
    # Evitar que un TeX del sistema (MiKTeX) interfiera en los scripts.
    for k in ("TEXMFHOME", "TEXMFVAR", "TEXMFCONFIG", "TEXINPUTS"):
        env.pop(k, None)
    return env


def repo_reachable(url: str) -> bool:
    try:
        req = urllib.request.Request(url + "tlpkg/texlive.tlpdb.xz", method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def install_packages(dest: Path, repo: str) -> None:
    binw = dest / "bin" / "windows"
    tlmgr = binw / "tlmgr.bat"
    env = tl_env(dest)
    if not repo_reachable(repo):
        log(f"snapshot no accesible ({repo}); uso {TLNET_FALLBACK}")
        repo = TLNET_FALLBACK
    common = [tlmgr, "--repository", repo]
    # El tlmgr del bundle debe estar al día con el repositorio elegido.
    run(common + ["update", "--self"], env=env, check=False)
    run(common + ["option", "docfiles", "0"], env=env, check=False)
    run(common + ["option", "srcfiles", "0"], env=env, check=False)
    proc = run(common + ["install", *PACKAGES], env=env, check=False)
    missing = [ln for ln in proc.stdout.splitlines()
               if "not present in repository" in ln or "unknown package" in ln.lower()]
    for ln in missing:
        log("aviso tlmgr: " + ln.strip())
    # Formato pdflatex con los patrones de silabeo instalados + mapas de fuentes.
    run([binw / "fmtutil-sys.exe", "--byfmt", "pdflatex"], env=env)
    run([binw / "updmap-sys.exe"], env=env, check=False)
    run([binw / "mktexlsr.exe"], env=env)
    if not (binw / "pdflatex.exe").is_file():
        raise SystemExit("tlmgr no instaló pdflatex.exe (¿latex-bin/pdftex?)")
    fmt = dest / "texmf-var" / "web2c" / "pdftex" / "pdflatex.fmt"
    if not fmt.is_file():
        raise SystemExit(f"no se generó el formato {fmt}")
    log(f"pdflatex.fmt: {human(fmt.stat().st_size)}")


# ─── Paso 3/5: validación con los documentos reales ────────────────────────

def validate(dest: Path, label: str) -> bool:
    """Compila Memoria Q4 (educativo, directo), Memoria Q9 y Theory Hub con el
    bundle. Devuelve True si los cuatro PDF se generan."""
    sys.path.insert(0, str(ROOT))
    os.environ["EDUFEM_TEXLIVE_DIR"] = str(dest)
    from education.components.latex_runtime import find_latex_runtime  # noqa: E402
    rt = find_latex_runtime()
    if rt is None or not rt.is_bundle or not rt.pdflatex.lower().startswith(str(dest).lower()):
        log(f"validación {label}: el runtime no apunta al bundle ({rt})")
        return False
    from education.components.theory_builder import TheoryDoc  # noqa: E402
    from file_io.memoria_calculo import generate_memoria_calculo  # noqa: E402
    from file_io import figure_export  # noqa: E402
    from fem.solver import solve_system  # noqa: E402
    from fem.stress import compute_all_stresses  # noqa: E402
    from tests.example_data import load_example_project, load_example_project_q9  # noqa: E402
    from gui.dialogs.theory_hub_dialog import _build_full_theory_document  # noqa: E402

    ok = True
    with tempfile.TemporaryDirectory(prefix="edufem_texlive_val_") as tmp:
        cases = [("memoria_q4_educativo", load_example_project, "educativo"),
                 ("memoria_q4_directo", load_example_project, "directo"),
                 ("memoria_q9_educativo", load_example_project_q9, "educativo")]
        for name, loader, style in cases:
            t0 = time.perf_counter()
            project = loader()
            solution = solve_system(project)
            project.is_solved = True
            es, ns = compute_all_stresses(project, solution)
            mesh = figure_export.render_mesh_diagram(project)
            contours = {}
            for comp in ("von_mises", "sigma_x", "sigma_y", "tau_xy"):
                img = figure_export.render_contour(project, solution, ns, comp)
                if img is not None:
                    contours[comp] = img
            out = os.path.join(tmp, name + ".pdf")
            try:
                generate_memoria_calculo(project, solution, es, ns, out, style=style,
                                         mesh_diagram=mesh, contour_figures=contours)
                size = os.path.getsize(out)
                log(f"validación {label}: {name} OK ({human(size)}, "
                    f"{time.perf_counter() - t0:.1f} s)")
            except Exception as e:  # noqa: BLE001
                ok = False
                log(f"validación {label}: {name} FALLÓ: {e}")
                tail = getattr(e, "log_tail", "") or getattr(getattr(e, "__cause__", None), "log_tail", "")
                if tail:
                    log(tail)
        t0 = time.perf_counter()
        td = TheoryDoc(title="Teoria MEF - EduFEM", subtitle="Fundamentos clasicos")
        _build_full_theory_document(td)
        out_base = os.path.join(tmp, "theory_hub")
        try:
            td.compile_to(out_base)
            size = os.path.getsize(out_base + ".pdf")
            log(f"validación {label}: theory_hub OK ({human(size)}, "
                f"{time.perf_counter() - t0:.1f} s)")
        except Exception as e:  # noqa: BLE001
            ok = False
            log(f"validación {label}: theory_hub FALLÓ: {e}")
            tail = getattr(e, "log_tail", "")
            if tail:
                log(tail)
    return ok


# ─── Paso 4: poda + ls-R ───────────────────────────────────────────────────

def _rm(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def prune(dest: Path) -> None:
    before, nbefore = dir_size(dest)
    for name in DROP_ROOT:
        _rm(dest / name)
    # bin/windows: solo pdftex + kpsewhich + DLLs de runtime.
    binw = dest / "bin" / "windows"
    for p in binw.iterdir():
        keep = p.name in KEEP_BIN or (p.suffix.lower() == ".dll" and p.name not in DROP_DLL)
        if not keep:
            _rm(p)
    # texmf-dist: solo tex/, fonts/, web2c/.
    dist = dest / "texmf-dist"
    for p in dist.iterdir():
        if p.name not in KEEP_TEXMF_DIST_TOP:
            _rm(p)
    for p in (dist / "fonts").iterdir():
        if p.name not in KEEP_FONT_KINDS:
            _rm(p)
    for p in (dist / "tex").iterdir():
        if p.name in DROP_TEX_TOP:
            _rm(p)
    # texmf-var: formato pdflatex + mapa pdftex + configuración de idiomas.
    var = dest / "texmf-var"
    web2c = var / "web2c"
    if web2c.is_dir():
        for p in web2c.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(web2c))
                if rel not in KEEP_FMT and p.suffix.lower() in {".fmt", ".log", ".mem", ".base"}:
                    p.unlink()
        for p in list(web2c.iterdir()):
            if p.is_dir() and not any(p.rglob("*")):
                _rm(p)
    for sub in ("fonts/map/dvips", "fonts/map/dvipdfmx", "fonts/pk", "fonts/tfm",
                "xdvi", "tex/context"):
        _rm(var / sub)
    after, nafter = dir_size(dest)
    log(f"poda: {human(before)} ({nbefore} archivos) -> {human(after)} ({nafter} archivos)")


def write_ls_r(tree: Path) -> None:
    """ls-R con el formato de mktexlsr: cabecera mágica, un bloque por directorio
    (`./ruta:` + entradas) separados por línea en blanco."""
    if not tree.is_dir():
        return
    lines = ["% ls-R -- filename database for kpathsea; do not edit."]
    for dirpath, dirnames, filenames in os.walk(tree):
        dirnames.sort()
        rel = os.path.relpath(dirpath, tree).replace("\\", "/")
        header = "./:" if rel == "." else f"./{rel}:"
        entries = sorted(set(dirnames) | set(filenames))
        if rel == ".":
            entries = sorted(set(entries) | {"ls-R"})
        lines.append(header)
        lines.extend(entries)
        lines.append("")
    (tree / "ls-R").write_text("\n".join(lines) + "\n", encoding="ascii", errors="replace")


def regenerate_ls_r(dest: Path) -> None:
    for name in ("texmf-dist", "texmf-var", "texmf-config", "texmf-local"):
        tree = dest / name
        tree.mkdir(exist_ok=True)
        write_ls_r(tree)
    log("ls-R regenerados")


def write_manifest(dest: Path, repo: str, sfx: Path) -> None:
    total, count = dir_size(dest)
    lines = [
        "EduFEM - TeX Live recortado (solo pdflatex) para la Memoria de Calculo y la Teoria.",
        "Generado por tools/build_texlive.py.",
        f"Fecha de build: {time.strftime('%Y-%m-%d %H:%M')}",
        f"Base: TinyTeX-0 {TINYTEX_VERSION} ({sfx.name}) -> TeX Live 2026",
        f"Repositorio de paquetes: {repo}",
        f"Tamano: {human(total)} en {count} archivos",
        "",
        "Paquetes instalados con tlmgr (mas sus dependencias):",
        "  " + " ".join(PACKAGES),
        "",
        "Podado: tlpkg (Perl, Ghostscript, instalador), docs, fuentes OpenType,",
        "motores luatex/xetex, binarios distintos de pdftex/pdflatex/kpsewhich.",
        "Licencias: LICENSE.TL y LICENSE.CTAN (TeX Live es software libre).",
    ]
    (dest / "EDUFEM-TEXLIVE.txt").write_text("\n".join(lines) + "\n", encoding="ascii",
                                             errors="replace")


# ─── main ──────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--tinytex-exe", type=Path, default=None,
                    help="autoextraíble TinyTeX-0 ya descargado (evita la descarga)")
    ap.add_argument("--repo", default=TLNET_SNAPSHOT, help="repositorio tlnet")
    ap.add_argument("--force", action="store_true", help="borra --dest y rehace todo")
    ap.add_argument("--validate-only", action="store_true",
                    help="solo compila los documentos de referencia con --dest")
    ap.add_argument("--resume", action="store_true",
                    help="--dest ya tiene los paquetes instalados: retoma en la "
                         "validación, poda y manifiesto")
    ap.add_argument("--no-prune", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)
    dest: Path = args.dest.resolve()

    if args.validate_only:
        return 0 if validate(dest, "bundle") else 1

    if args.force and dest.exists():
        log(f"borrando {dest}")
        shutil.rmtree(dest)
    if dest.exists() and not args.resume:
        raise SystemExit(f"{dest} ya existe; usar --force, --resume o --validate-only")

    t0 = time.perf_counter()
    sfx = Path(args.tinytex_exe) if args.tinytex_exe else DOWNLOAD_DIR / TINYTEX_URL.rsplit("/", 1)[-1]
    if not args.resume:
        if not args.tinytex_exe:
            sfx = download(TINYTEX_URL, sfx)
        extract_tinytex(sfx, dest)
        install_packages(dest, args.repo)
    if not args.no_validate and not validate(dest, "sin podar"):
        raise SystemExit("la validación sin podar falló; se conserva el bundle para inspección")
    if not args.no_prune:
        prune(dest)
        regenerate_ls_r(dest)
        if not args.no_validate and not validate(dest, "podado"):
            raise SystemExit("la validación del bundle podado falló")
    write_manifest(dest, args.repo, Path(sfx))
    total, count = dir_size(dest)
    log(f"listo: {dest} — {human(total)} en {count} archivos, "
        f"{(time.perf_counter() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
