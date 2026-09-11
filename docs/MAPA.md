# Mapa del repositorio EduFEM

> Orientación para cualquier agente o colaborador que llegue al repo.
> Reglas de trabajo: [../CLAUDE.md](../CLAUDE.md) · índice de documentación: [README.md](README.md).

## 1. Vista general

```
SoftwareED/
├─ CLAUDE.md            canon operativo: reglas duras + ruteo a los capítulos
├─ AGENTS.md            puntero para agentes que no leen CLAUDE.md
├─ README.md            qué es EduFEM, cómo instalarlo y correrlo (humanos)
├─ main.py              punto de entrada de la GUI
├─ build.spec           PyInstaller (onedir → dist/EduFEM/)
├─ requirements.txt     dependencias de runtime
├─ requirements-dev.txt dependencias de desarrollo
│
├─ config/              constantes, paleta, fuentes, decimales, unidades, colormaps
├─ models/              ProjectModel, Node/Element/Material/Load/BC, undo, salud, mesh_utils
├─ fem/                 motor NumPy/SciPy puro — sin GUI, corre headless
├─ file_io/             .edufem (JSON), CSV/ZIP, DXF, memoria PDF, figuras Pillow
├─ gui/                 tkinter + ttkbootstrap
│  ├─ preprocessing/    spreadsheet de 5 tablas + MeshCanvas
│  ├─ processing/       fase de proceso: tira del método + lanzador de módulos
│  ├─ postprocessing/   contornos, probe, vista 3D, panel de detalles
│  ├─ dialogs/          pop-ups del menú Modelo, DXF, salud, theory hub
│  └─ widgets/          tooltip, banner de fase, panel de módulos, WebpPlayer
├─ education/           módulos M0..M7 (overlays sobre el canvas real)
│  └─ components/       piezas reutilizables (LaTeX, expander, quality bar, estilo de plots)
├─ tests/               scripts printout: test_* (regresión) y vv_* (verificación y validación)
│
├─ resources/           ⚠ RUTAS DURAS — ver §3
│  ├─ examples/         DXF de ejemplo
│  ├─ fonts/            TTF opcionales
│  ├─ icons/            edufem.ico (ventana + instalador)
│  └─ videos/           .webp animados de los diálogos
│
├─ tools/               scripts de build y de generación de recursos
│  ├─ build_all.ps1     cadena completa: TeX → iconos/imágenes → .exe → instalador
│  ├─ build_texlive.py  genera vendor/texlive (TeX Live recortado para la Memoria/Teoría)
│  ├─ make_icon.py      genera resources/icons/edufem.ico y edufem_doc.ico (archivos .edufem)
│  ├─ make_installer_images.py  genera installer/assets/wizard*.bmp (asistente de Inno)
│  ├─ render_q4q9_manim/     escena Manim → cantilever_q4_q9.webp
│  └─ render_tp_dp_manim/    escena Manim → tension_deformacion_plana.webp
│
├─ vendor/              ⚠ generado, no versionado — texlive/ (lo embebe el instalador)
│
├─ installer/
│  ├─ EduFEM.iss        Inno Setup → EduFEM-Setup.exe (incluye vendor/texlive como {app}\texlive)
│  ├─ assets/           imágenes BMP del asistente (las genera make_installer_images.py)
│  └─ dist_extra/       LEEME.txt (lo instala el .iss) + lanzadores .bat de la carpeta portable
│
├─ docs/                ver §2
└─ tesis/               fuente LaTeX de la tesis — ver tesis/README.md
```

**Generado, no versionado** (`.gitignore`): `build/`, `dist/`, `installer/Output/`,
`vendor/`, `.venv/`, `__pycache__/`, `tools/**/media/`, artefactos LaTeX de `tesis/`.

Cuál es cuál, porque las cuatro primeras se parecen y solo una se entrega:

| Carpeta | Qué es | ¿Se puede borrar? |
|---|---|---|
| `installer/Output/EduFEM-Setup.exe` | **El entregable.** Lo único que se distribuye | No, es el producto |
| `dist/EduFEM/` | Salida de PyInstaller (onedir: lanzador + `_internal/`); el instalador la empaqueta adentro | Sí, la rehace PyInstaller (~5 min) |
| `vendor/texlive/` | TeX Live recortado que el instalador copia a `{app}` | Sí, pero rehacerlo pide internet y ~5 min |
| `build/` | Caché de trabajo de PyInstaller | Sí, en cualquier momento |

## 2. Qué hay en `docs/`

| Carpeta | Contenido | Quién la usa |
|---|---|---|
| `docs/convenciones/` | El canon del proyecto por capítulos (arquitectura, módulos, canvas, memoria, estilo, roadmap, prohibiciones) | Todo agente, **bajo demanda** según lo que vaya a tocar |
| `docs/notas/` | Espacio de trabajo: `ESTADO.md` (WIP vivo) + una nota por sesión | Todo agente, al empezar y al terminar |
| `docs/auditorias/` | Informes de auditoría. `ESTADO_AUDITORIAS.md` consolida qué sigue vigente; `historico/` guarda los informes superados | Quien busque deuda técnica pendiente |
| `docs/teoria/` | Documentos teóricos LaTeX (métricas de calidad de malla) | Quien toque `fem/mesh_quality.py` o el módulo M0 |
| `docs/vyv/` | **Verificación y validación**: capítulo LaTeX + `datos/*.csv` + `figuras/*.png` | ⚠ Los generan los scripts `tests/vv_*.py` y los consume la tesis |

## 3. Rutas frágiles — NO mover sin actualizar el consumidor

| Ruta | Quién depende de ella | Cómo |
|---|---|---|
| `resources/**` | `config.settings.resource_path`, `gui/fonts_loader._resources_root`, `build.spec` (`datas`), `installer/EduFEM.iss` (`SetupIconFile`) | Rutas construidas en runtime y en el empaquetado |
| `resources/icons/edufem.ico` | `tools/make_icon.py` lo **escribe** (`../resources/icons`), `main_window` lo lee, el instalador lo usa | Salida fija del generador |
| `docs/vyv/datos/`, `docs/vyv/figuras/` | `tests/vv_mms.py`, `vv_timoshenko.py`, `vv_cook.py` **escriben** ahí; `tesis/figuras/generar_figuras.py` copia desde ahí; `tesis/capitulos/06_anexos.tex` las cita | Rutas literales en los scripts |
| `resources/examples/ejemplo_geometria.dxf` | `tests/generate_example_dxf.py` lo escribe | Ruta literal |
| `tools/make_icon.py`, `tools/make_installer_images.py`, `tools/build_texlive.py`, `tools/build_all.ps1` | `build_all.ps1` invoca a los `.py` por ruta relativa a `$PSScriptRoot` | Deben quedar hermanos en `tools/` |
| `vendor/texlive/` | `tools/build_texlive.py` lo **escribe**; `education/components/latex_runtime.py` (`DEV_BUNDLE_RELPATH`) lo lee en dev; `installer/EduFEM.iss` lo copia a `{app}\texlive`, que la app busca como carpeta `texlive` hermana del `.exe` | Rutas literales en los tres |
| `installer/assets/wizard*.bmp` | `tools/make_installer_images.py` los **escribe**; `installer/EduFEM.iss` los nombra uno por uno en `WizardImageFile` / `WizardSmallImageFile` | Los nombres llevan el tamaño: agregar uno obliga a listarlo en el `.iss` |
| `resources/icons/edufem_doc.ico` | `tools/make_icon.py` lo escribe; el `.iss` lo instala en `{app}` y el registro apunta ahí para el icono de los `.edufem` | El Explorador lee la ruta del registro: el archivo tiene que quedar instalado |
| `config/settings.py` → `APP_VERSION`, `APP_USER_MODEL_ID`, `APP_MUTEX_NAME` | `build.spec` (regex) y `installer/EduFEM.iss` (preprocesador y `#define`) los leen o los repiten | Única fuente de la versión; los otros dos están duplicados a mano en el `.iss` |
| `tools/render_q4q9_manim/`, `tools/render_tp_dp_manim/` | Mensajes de la GUI los nombran cuando falta el `.webp` (`analysis_type_dialog`, `element_type_dialog`) | Solo strings, pero visibles al usuario |
| `education/mod*.py` | `build.spec` los recoge por **glob** para `hiddenimports`; `module_launcher` los carga con `importlib` | Sin el prefijo `mod`, el `.exe` falla al abrir el módulo |
| `~/.edufem/recent.json` | `config/recent_files.py` | Fuera del repo (perfil del usuario) |

**Regla**: si movés algo de esta tabla, actualizá el consumidor en el mismo cambio.
Si movés un documento citado desde un comentario del código, actualizá también ese comentario.

## 4. Dónde va un archivo nuevo

| Qué estás creando | Dónde va | Nota |
|---|---|---|
| Módulo educativo | `education/modNN_nombre.py` | El prefijo `mod` es obligatorio (`build.spec`) + registrarlo en los 4 dicts de `module_launcher.py` |
| Widget reutilizable de GUI | `gui/widgets/` | |
| Pieza reutilizable de módulos educativos | `education/components/` | |
| Diálogo (pop-up) | `gui/dialogs/` | Firma `(parent, project, main_window=None)` + `size_dialog` (nunca `geometry` fija) |
| Constante, color, tolerancia, decimales | `config/settings.py` | **Nunca** un literal en el sitio de uso |
| Script de test / validación | `tests/test_*.py` o `tests/vv_*.py` | Tipo printout, se corre con `python -m tests.X` |
| Script de build / empaquetado | `tools/` | No se importa desde la app; `build_all.ps1` lo encadena |
| Paquete LaTeX nuevo en la Memoria o el Hub | `PACKAGES` de `tools/build_texlive.py` | Rehacer `vendor/texlive` (`--force`); si no, compila en dev y falla en el instalador |
| Video de un diálogo | Escena Manim en `tools/render_*_manim/` → `.webp` en `resources/videos/` | El `.webp` sí se versiona; `tools/**/media/` no |
| Informe de auditoría | `docs/auditorias/AAAA-MM-DD_tema.md` | Y una línea en `ESTADO_AUDITORIAS.md` |
| Documento teórico LaTeX | `docs/teoria/<tema>/` | `.tex` + `.pdf` compilado |
| Nota de trabajo / hallazgo | `docs/notas/` | Ver [notas/README.md](notas/README.md) |
| Regla permanente del proyecto | El capítulo que corresponda de `docs/convenciones/` | Si es una prohibición, además una fila en `no-reintroducir.md` |
| Contenido de la tesis | `tesis/capitulos/` | Ver `tesis/README.md` y las skills `tesis-*` |
| Archivo temporal, log, salida intermedia | **Fuera del repo** (directorio scratch de la sesión) | Nunca en la raíz |

## 5. Comandos habituales

```bash
python main.py                    # GUI
python -m tests.test_fem          # regresión numérica (obligatoria si tocás fem/)
python -m tests.vv_mms            # convergencia MMS
pyinstaller --noconfirm build.spec  # dist/EduFEM/
powershell -File tools/build_all.ps1  # icono + .exe + instalador
```

La lista completa está en [../CLAUDE.md](../CLAUDE.md) (sección *Running*).
