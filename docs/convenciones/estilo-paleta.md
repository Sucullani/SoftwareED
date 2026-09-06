# Estilo: paleta congelada, tipografia y decimales

> Capitulo del canon de EduFEM. Indice: [../../CLAUDE.md](../../CLAUDE.md) - mapa del repo: [../MAPA.md](../MAPA.md) - prohibiciones: [no-reintroducir.md](no-reintroducir.md).

**Leelo antes de tocar** cualquier archivo de `gui/` o `education/` que dibuje, coloree o formatee numeros.

---

## Tipografía y decimales

Fonts en [config/settings.py](../../config/settings.py) — **importar siempre, no hardcodear**:

| Constante | Valor | Uso |
|---|---|---|
| `FONT_UI` | Segoe UI 9 | Default UI |
| `FONT_UI_LARGE` | Segoe UI 10 | Treeview body + editor flotante |
| `FONT_UI_BOLD` | Segoe UI Semibold 9 | Headings, labels |
| `FONT_MONO` / `FONT_MONO_SMALL` | Consolas 10/9 | Código, coords canvas |
| `TREE_ROW_HEIGHT` | 22 | Compacto |

Decimales por magnitud — usar siempre `fmt(value, kind)`, no `f"{x:.4f}"`:

| Constante | Default | Uso |
|---|---|---|
| `DECIMALS_LENGTH` | 3 | X, Y, espesor |
| `DECIMALS_FORCE` | 2 | Fx, Fy, q, reacciones |
| `DECIMALS_STRESS` | 2 | σ, τ, von Mises |
| `DECIMALS_DISPLACEMENT` | 5 | u, v (científico `:.5e`) |
| `DECIMALS_ANGLE` | 1 | θ° |

**Trampa**: el editor flotante debe pre-llenar con el mismo string que la celda muestra (`current=fmt(raw, kind)`), no el float crudo — sino "salta" perdiendo decimales al abrir.
## Lineamientos de calidad

### Paleta congelada

Todos los colores viven en [config/settings.py](../../config/settings.py). Familias:
- Fases: `PHASE_PRE/PROC/POST_COLOR` y bootstyles asociados.
- Canvas geometría: `CANVAS_BG`, `CANVAS_GRID`, `CANVAS_NODE` (+ MID/CENTER/ORPHAN), `CANVAS_ELEMENT`.
- Canvas propiedades: `CANVAS_LOAD/CONSTRAINT/SELECTED_COLOR`.
- Sombras y labels: `SHADOW_*`, `LABEL_BG/FG`.
- Salud del modelo: `HEALTH_OK/WARNING/ERROR/INFO_COLOR`.

**Reglas no negociables**:
1. **Cero hex literales fuera de `config/settings.py`**. Nuevos colores → constante nombrada → import.
2. Naming `<DOMINIO>_<USO>_COLOR`. Agregar en sección comentada existente, no al final.
3. Mapas de color para resultados: `jet` (arcoíris clásico ANSYS/SAP2000) para **TODOS** los campos — no negativos Y con signo (los con signo, centrados en 0). **Excepción del usuario a la ex-regla "no jet"**: el usuario pidió "cambia todo a JET" (2026-05-31) y prioriza ese reconocimiento de ingeniería sobre la uniformidad perceptual — `jet` es la única paleta de resultado. `hsv` sigue prohibido. Aplica a TODO render de campo: canvas interactivo (`config/colormaps.py`, LUTs numpy), vista 3D y Memoria PDF (`figure_export.py`). `coolwarm`/`turbo`/`viridis` quedan definidos pero NO se usan en resultados (`viridis`/`coolwarm` solo en superficies pedagógicas de módulos educativos como M2). **No reintroducir** `coolwarm`/`turbo`/`viridis` para los campos de resultado sin pedido del usuario.
4. Estados de validación: verde = `PHASE_POST_COLOR` o `HEALTH_OK_COLOR`, naranja = warning, rojo = error.
5. Highlight: `CANVAS_SELECTED_COLOR` amarillo es el único color de selección — no reemplazar por color de propiedad. Lo **acompañan** (no reemplazan) `CANVAS_SELECTED_FILL_COLOR` (relleno punteado `stipple="gray12"` dentro del elemento seleccionado — señal primaria, color suave que llena área sin tapar los datos), `CANVAS_SELECTED_HALO_COLOR` (anillo glow fino bajo nodos/aristas seleccionados — **el halo grueso del elemento fue eliminado** 2026-05-31) y `CANVAS_HOVER_COLOR` (cian, pre-selección bajo el cursor) — ver "Render del canvas".
6. Bootstyles dentro de pestañas de fase: heredar `PHASE_*_BOOTSTYLE`.
7. **Auditoría pre-merge**: `Grep` `#[0-9a-fA-F]{3,8}` sobre `gui/**` + `education/**` (excluir `config/`). Esperado: 0 hits.

La paleta cumple WCAG AA contra fondo `darkly` (#212529); azul/naranja/verde tiene significado pedagógico (modelado → análisis → resultado).

## Alcance de la traducción al español

La tabla de terminología canónica vive en [CLAUDE.md](../../CLAUDE.md). Este es el detalle de
dónde aplica y dónde no.

**Sí se traduce**:
- Strings literales en `text=`, `label=`, `title=`, `subtitle=`, captions de plots, mensajes de
  la status bar, verdict labels en `Text(...)` / `MathTex(...)` de Manim, `messagebox.askyesno`
  y `showerror`.
- Documentos LaTeX/PDF generados ([memoria_calculo.py](../../file_io/memoria_calculo.py),
  [theory_hub_dialog.py](../../gui/dialogs/theory_hub_dialog.py)).
- Tooltips, hints y banners de fase.

**No se traduce**:
- Nombres de variables, funciones, clases y atributos (`n_dof`, `total_restrained_dofs`).
- Magic strings internos que sirven de key (`"stress"`, `"vm"` en los dicts de resultados).
- El *nombre* de las constantes de módulo, aunque su *valor* sí vaya en español:
  `ELEMENT_Q4 = "Q4 - Cuadrilátero 4 nodos"` está bien así.
- Nombres de archivo, paths y extensiones (`.edufem`, capa DXF `FEM_ELEMENTS`).
- Logs, `print(...)` de scripts de test y demás salida developer-facing.
- Comentarios y docstrings técnicos que usan la abreviatura inglesa por brevedad
  (`# Indice DOF global de Ux para node_id` es correcto).

Criterio de fondo: si la traducción española ya existe y un estudiante hispanohablante de
ingeniería la entiende, se usa. La marca **EduFEM** y la capa DXF `FEM_ELEMENTS` son las dos
excepciones fijas.
