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
├─ build.spec           PyInstaller (onefile → dist/EduFEM.exe)
├─ requirements.txt     dependencias de runtime
├─ requirements-dev.txt dependencias de desarrollo
│
├─ config/              constantes, paleta, fuentes, decimales, unidades, colormaps
├─ models/              ProjectModel, Node/Element/Material/Load/BC, undo, salud, mesh_utils
├─ fem/                 motor NumPy/SciPy puro — sin GUI, corre headless
├─ file_io/             .edufem (JSON), CSV/ZIP, DXF, memoria PDF, figuras Pillow
├─ gui/                 tkinter + ttkbootstrap
│  ├─ preprocessing/    spreadsheet de 5 tablas + MeshCanvas
│  ├─ processing/       fase de proceso
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
│  ├─ build_all.ps1     icono → .exe → instalador
│  ├─ make_icon.py      genera resources/icons/edufem.ico
│  ├─ render_q4q9_manim/     escena Manim → cantilever_q4_q9.webp
│  └─ render_tp_dp_manim/    escena Manim → tension_deformacion_plana.webp
│
├─ installer/
│  ├─ EduFEM.iss        Inno Setup → EduFEM-Setup.exe
│  └─ dist_extra/       lanzadores .bat + LEEME.txt que acompañan al .exe
│
├─ docs/                ver §2
└─ tesis/               fuente LaTeX de la tesis — ver tesis/README.md
```

**Generado, no versionado** (`.gitignore`): `build/`, `dist/`, `installer/Output/`,
`.venv/`, `__pycache__/`, `tools/**/media/`, artefactos LaTeX de `tesis/`.

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
| `tools/make_icon.py`, `tools/build_all.ps1` | `build_all.ps1` invoca a `make_icon.py` por ruta relativa a `$PSScriptRoot` | Deben quedar hermanos en `tools/` |
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
| Diálogo (pop-up) | `gui/dialogs/` | Firma `(parent, project, main_window=None)` + `center_dialog` |
| Constante, color, tolerancia, decimales | `config/settings.py` | **Nunca** un literal en el sitio de uso |
| Script de test / validación | `tests/test_*.py` o `tests/vv_*.py` | Tipo printout, se corre con `python -m tests.X` |
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
pyinstaller --noconfirm build.spec  # dist/EduFEM.exe
powershell -File tools/build_all.ps1  # icono + .exe + instalador
```

La lista completa está en [../CLAUDE.md](../CLAUDE.md) (sección *Running*).
