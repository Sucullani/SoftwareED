# PyMuPDF retirado: la Teoría se abre con el visor del sistema (2026-09-25)

Pedido del autor: resolver la decisión abierta sobre la licencia reemplazando PyMuPDF por algo
libre, y poner al día la tesis, la distribución y el instalador. Cerró la decisión «Elegir la
licencia con que se publica EduFEM» de `ESTADO.md`: **EduFEM sigue siendo MIT, y ahora el
paquete binario también lo permite**.

## Por qué

- `importlib.metadata` de PyMuPDF 1.27.2.3: *«Dual Licensed - GNU AFFERO GPL 3.0 or Artifex
  Commercial License»*. El instalador lo metía en `_internal/pymupdf` (**38,1 MB de 225,0**),
  así que redistribuir el paquete quedaba sujeto a la AGPL, contra el MIT de `LICENSE`, del
  asistente y de la tesis.
- Se usaba en un solo lugar del programa: `education/components/theory_viewer.py`, unas 20
  líneas que pasaban cada página del PDF de Teoría a imagen para un Toplevel propio.
- Se cargaba **en cada arranque** aunque solo lo usa Ayuda ▸ Teoría MEF:
  `main_window → element_type_dialog → education.components.edu_plot_style →
  education.components → theory_viewer → fitz` (170 ms de los 2454 del import de
  `gui.main_window`).

## Alternativas (las comparó el autor antes de elegir)

| Opción | Resultado |
|---|---|
| Pillow o pylatex, que ya estaban | **No pueden**: Pillow solo *escribe* PDF, y su `PdfParser` ni siquiera abre un PDF de pdfTeX («trailer end not found»: son PDF 1.7 con tablas de referencias comprimidas); pylatex solo arma el `.tex` |
| `pypdfium2` (PDFium, BSD-3/Apache-2.0) | Viable, probado en un prototipo aislado sobre la Teoría real (13 páginas): mismas páginas y tamaño (893 × 1263 px a zoom 1,5), 0,25 s contra 0,28 s, diferencias solo en el suavizado del texto (media ≤ 5,6/255), ruta con tildes OK, 7,7 MB contra 37, *hooks* ya en `pyinstaller-hooks-contrib`. Suma una biblioteca y ~70 ms de import |
| **Visor de PDF del sistema** (`os.startfile`) | **Elegida por el autor.** Cero bibliotecas, −40 MB en el paquete, igual que la Memoria de Cálculo; el estudiante gana búsqueda, zoom e impresión. Se pierde la lectura *dentro* de EduFEM |
| pdf2image + Poppler, Ghostscript | Descartadas: GPL y AGPL, el mismo problema |
| Licencia comercial de Artifex / publicar EduFEM como AGPL | Descartadas: de pago / cambia la licencia del proyecto |

## Qué cambió en el software

- **`theory_viewer.py` reescrito** (conserva el nombre: lo nombran `.claude/rules/memoria-pdf.md`
  y los docs). `build_theory_pdf` compila solo si el PDF no está en el caché;
  `pdf_path_for` pone el hash en la carpeta y el título en el archivo
  (`~/.edufem/theory_cache/<hash>/Teoría MEF — EduFEM.pdf`: el visor muestra el nombre en su
  barra de título, y así un PDF abierto en Acrobat nunca se reescribe); `open_theory_pdf`
  compila en un hilo que **no toca Tk** (cola + `after` de sondeo), ignora el doble clic
  mientras compila, informa en la barra de estado (`on_status` ← `main_window.set_status`) y
  cubre los tres fallos: sin pdflatex (el diálogo de la Memoria), error de compilación
  (`showerror` con la primera línea del `.log`) y Windows sin visor de PDF (aviso con la ruta).
  Cerró la mitad de la Teoría del BACKLOG [9]. Un «no se generó el PDF» ahora es
  `RuntimeError`: como `FileNotFoundError` abría el diálogo de pdflatex faltante.
- `config/settings.py`: fuera `THEORY_VIEWER_BG_COLOR` (sin consumidor).
- Pruebas: `test_edu_components` [1]-[4] reescritas (sin biblioteca de PDF, el hilo no toca Tk
  por AST, nombre legible, caché, y el flujo entero con Tk, visor y messagebox reemplazados por
  dobles); `test_dpi_layout` sin la ventana; `test_memoria_calculo` cuenta hojas con el `.log`
  («Output written on … (N pages») y busca apaisadas en el `.tex`; `test_distribucion` +2
  (PyMuPDF bloqueado en `sys.modules` mientras se importan todos los módulos; `requirements` y
  `build.spec`; los avisos de terceros).
- `tesis/figuras/gui_capture.py`: fuera la captura del visor, que ya no existe.

## Qué cambió en la distribución

- `requirements.txt` sin PyMuPDF. `build.spec`: fuera el hiddenimport `fitz`, y `excludes`
  suma `fitz`/`pymupdf` (**PyMuPDF sigue en el `.venv`**: lo usan
  `tesis/respaldo_citas/resaltar.py` y `paginas.py`, que no se distribuyen y ahora lo dicen en
  su cabecera; no desinstalarlo).
- **Hallazgo**: al armar sin PyMuPDF aparecieron en el paquete cinco que EduFEM no usa, que
  PyInstaller arrastraba por importaciones opcionales de las dependencias porque están en el
  `.venv` (las pidieron `moderngl-window`, `edge-tts`, `reportlab` y `manim`): `pyglet` (208
  módulos, vía `sympy.plotting`), **`certifi` (MPL-2.0, la única licencia no permisiva que
  quedaba)**, `charset_normalizer` (vía `numpy.f2py`), `pathops` (3,8 MB, vía
  `fontTools.ttLib.removeOverlaps`) y `win32pdh`/`pywintypes` (vía `numpy.testing`). Todas son
  importaciones perezosas o protegidas: se excluyeron como ya se hacía con `lxml`.
- `tools/licencias_terceros.py` (nuevo) → `installer/dist_extra/LICENCIAS-TERCEROS.txt`
  (versionado, 476 KB, UTF-8 con BOM): Python (su `LICENSE.txt` trae OpenSSL, libffi…),
  Tcl/Tk, el cargador de PyInstaller, TeX Live (remite a `texlive\LICENSE.TL`, `LICENSE.CTAN`,
  `EDUFEM-TEXLIVE.txt` y al snapshot de tlnet) y las 19 bibliotecas con sus textos. La lista
  sale de `build/build/*.toc` —lo que de verdad entró—, no de `requirements.txt` (que queda de
  respaldo): así se vio lo de arriba. `build_all.ps1` lo corre tras PyInstaller y frena el
  build si `_internal\` trae `pymupdf` o `fitz`. El `.iss` lo instala en `{app}`, `-Portable`
  lo copia, y el LEEME lo nombra (§11), explica que la Teoría y la Memoria se abren con el
  visor de Windows (§7) y qué hacer si no hay visor (§9).
- Versión: **sigue 1.0.0** (decisión del autor).

| Medición | Antes | Sin PyMuPDF | + sin los cinco extras |
|---|---|---|---|
| `dist/EduFEM/` | 225,0 MB · 1469 archivos | 185,0 MB · 1465 | **178,7 MB · 1455** |
| `EduFEM-Setup.exe` | 95,6 MB | 82,0 MB | **78,7 MB** (−18 %) |

El `.exe` armado abre su ventana principal en ~4 s (prueba de humo: título correcto, sin el
cuadro de «Unhandled exception»). El instalador anterior quedó copiado en el *scratchpad* de la
sesión, no en el repo.

## Tesis (sobre `final2`, en el lugar, por decisión del autor)

Tabla 2.5 sin la fila de PyMuPDF y nota sin la AGPL; el párrafo siguiente; el Anexo A; y la
«Versión evaluada», que decía que la 1.0.0 (`91e3df0`) «es la que se distribuye»: ahora dice que
el instalador sale de una revisión posterior que solo retira PyMuPDF y que la V&V da los mismos
datos. **Verificado**: sumas de control de `docs/vyv/datos/` y `docs/vyv/figuras/` antes y
después de correr `vv_mms`, `vv_timoshenko` y `vv_cook`: CSV idénticos; dos PNG de Cook
cambiaron solo el metadato «Software: Matplotlib version» (3.10.7 → 3.10.9), con 0 píxeles
distintos, y se restauraron. Queda un `% DATO PENDIENTE` para el hash de la revisión (sin
commit). Registro: `tesis/auditoria_final/IMPLEMENTACION-FINAL2.md`, «Cambio posterior».

## Lo que quedó para el autor

- **Material de defensa sin actualizar** (decisión del autor, «que quede»): la lista está en
  `ESTADO.md`.
- **Validación visual**: instalar el `EduFEM-Setup.exe` nuevo, abrir Ayuda ▸ Teoría MEF (se
  abre en Edge u otro visor; la primera vez tarda unos 3 s) y exportar una Memoria.
- **`capitulos_final3/`**, que otra sesión abrió a las 05:46 copiando final2 antes de las
  ediciones R2-Z (05:50–05:53), ya las lleva: esa sesión las copió con la misma redacción tras
  el aviso (verificado con Grep en 02b, 03 y 06).
- **Al commitear**: `tools/licencias_terceros.py` e `installer/dist_extra/LICENCIAS-TERCEROS.txt`
  son archivos nuevos (sin versionar): `git add -u` no los toma, y sin el segundo el `.iss` no
  compila. Después, completar el `% DATO PENDIENTE` de 02b con el hash del commit.
- **Gate verde** con `--con-latex --con-gui`: 102/102 módulos, 34 módulos de tests. El test de
  maquetación de la Memoria, ya sin PyMuPDF, mide 16 hojas (Q4 educativo) y 14 (Q9 directo).

## Trampas encontradas

- El Bash tool manda los heredoc y los `sed` con acentos en cp1252: un `sed` con «Teoría» dejó
  un byte `0xED` suelto en un `.md` UTF-8. Texto con acentos, solo por Edit/Write.
- Los `.toc` de PyInstaller (`build/build/`) son literales de Python salvo `EXE-00.toc`; las
  rutas vienen absolutas, y el dueño de cada archivo sale del `RECORD` de cada paquete.
