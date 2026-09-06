# Estado consolidado de auditorías — EduFEM

> **Empezá acá** si buscás deuda técnica pendiente. Este documento reemplaza la lectura
> de los seis informes (≈ 160 KB): consolida qué se auditó, qué se implementó y **qué
> sigue abierto**, con el enlace al informe original de cada punto.
>
> **Actualizado el 2026-09-06**: se cerró la auditoría 2026-06-10 completa — el Top-10 y
> además los hallazgos *medios* y *bajos* de §1 (robustez), §2 (convenciones y código
> muerto), §5 (higiene) y §6 (rendimiento). Los P0/P1 se reprodujeron headless antes de
> corregirlos; batería (14/14) y V&V en verde después de cada tanda.
>
> Queda **una decisión de autor**: `TheoryDoc.margin_formula()` existe y funciona pero
> ningún capítulo de la memoria la llama. Cablearla cambia el layout del PDF (validación
> visual del autor); mientras tanto el capítulo ya no la documenta como si estuviera en uso.
>
> **Cómo leerlo**: el estado de cada ítem sale de (a) lo que el propio informe declara,
> (b) el historial de git y (c) los cambios de higiene aplicados en la reorganización del
> 2026-09-06. **No se re-verificó el código línea por línea en esta pasada** — un ítem
> marcado *abierto* puede haberse arreglado sin registrarlo; confirmalo antes de trabajarlo.

## Los informes

| Fecha | Informe | Alcance | Estado global |
|---|---|---|---|
| 2026-06-10 | [2026-06-10_auditoria_general.md](2026-06-10_auditoria_general.md) | Repo completo: correctitud, convenciones, dependencias, higiene, rendimiento | **Vigente — solo diagnóstico, sin fixes aplicados** |
| 2026-06-10 | [2026-06-10_revision_tesis.md](2026-06-10_revision_tesis.md) | Tesis, estilo tribunal | **Vigente — propuestas a decisión del autor** |
| 2026-06-03 | [historico/2026-06-03_auditoria_tesis.pdf](historico/2026-06-03_auditoria_tesis.pdf) | Tesis (pasada anterior) | Superado por el informe del 06-10 |
| 2026-05-31 | [historico/2026-05-31_auditoria_integral.md](historico/2026-05-31_auditoria_integral.md) | Integral (17 agentes + verificación adversarial) | Implementado P0–P2 el 2026-06-01; **P3 diferido** |
| 2026-05-30 | [historico/2026-05-30_auditoria_canvas_ux.md](historico/2026-05-30_auditoria_canvas_ux.md) | UX/UI del `MeshCanvas` | Implementado (ver su §*Estado de implementación*); 4 ítems diferidos |
| 2026-05-25 | [historico/2026-05-25_auditoria_tecnica.md](historico/2026-05-25_auditoria_tecnica.md) | Rendimiento, arquitectura, seguridad | *Quick wins* aplicados; el resto superado por el informe del 05-31 |
| 2026-05-03 | [historico/2026-05-03_propuesta_ux_modulos.pdf](historico/2026-05-03_propuesta_ux_modulos.pdf) | Propuesta UX de los módulos educativos | Ejecutada (los 8 módulos son overlays) |

## Abierto — auditoría general 2026-06-10

Su Top-10, con el estado a hoy. Fuente:
[2026-06-10_auditoria_general.md](2026-06-10_auditoria_general.md) (§*Top-10 priorizado*),
donde está la evidencia y la línea exacta de cada uno.

| # | Prio | Hallazgo | Estado |
|---|---|---|---|
| 1 | **P0** | `models/project.py` — `change_element_id` deja `_node_to_elements` stale: crash reproducible en flujo GUI común | **Resuelto 2026-09-06** — sincroniza el índice inverso; regresión en `test_node_cascade` |
| 2 | **P0** | `fem/assembly.py` — `KeyError` crudo por carga nodal huérfana; falta `.get()` + skip | **Resuelto 2026-09-06** — `idx_map.get()` + skip |
| 3 | P1 | `models/model_health.py` — el autofix de cargas superficiales borra por índice posicional (la carga equivocada) | **Resuelto 2026-09-06** — helper `_remove_surface_load` por identidad de objeto |
| 4 | P1 | Validador: falta el chequeo de nodos huérfanos libres (K singular con "modelo sano") + mensaje incorrecto de `load_orphan_node` | **Resuelto 2026-09-06** — `_check_orphan_free_nodes` (error + autofix + hint), mensaje corregido y `nodes_in_elements` deja de contar los sets vacíos de huérfanos preservados |
| 5 | P1 | Documentación desactualizada: orden B/D y chips `DOF` en vez de `GDL` | **Resuelto 2026-09-06** — corregido en `convenciones/` junto con otras 19 afirmaciones obsoletas (ver `notas/ESTADO.md`) |
| 6 | P2 | `health_report_dialog.py` — falta `capture()` antes de los autofixes (no son reversibles con Ctrl+Z) | **Resuelto 2026-09-06** |
| 7 | P2 | `main_window.py` — falta snapshot inmutable del project para el worker del PDF | **Resuelto 2026-09-06** — `ProjectModel.from_dict(to_dict())` antes de lanzar el thread |
| 8 | P2 | `pre_tab._paste_*` — no tolera la coma decimal de Excel español (regla explícita del canon sin implementar) | **Resuelto 2026-09-06** — helper `to_float_flex` en `_table_helpers` |
| 9 | P3 | `mod06` — usar `redraw_overlays_only()` en el loop de animación | **Resuelto 2026-09-06** |
| 10 | P3 | Higiene: `compile_*.txt` fuera de git · `README.md` en raíz · `.gitattributes` para EOL de `docs/vyv` · tests faltantes en la lista *Running* | **Resuelto 2026-09-06** — `.gitattributes` creado y lista *Running* completa |

**Falsos positivos ya descartados**: el informe del 06-10 cierra con una lista de ~10
hallazgos que **son decisiones documentadas y no deben "arreglarse"** (`K.toarray()`
gateado, `subdivide_q4_mesh` sin consumidor, LUTs sin uso, `tree.selection_set` fuera del
callback prohibido, det J lineal en Q9 de lados rectos…). Leerla antes de abrir un fix:
evita revertir decisiones. Complemento imprescindible:
[convenciones/no-reintroducir.md](../convenciones/no-reintroducir.md).

## Abierto — revisión de la tesis 2026-06-10

Requieren **decisión del autor**, no son fixes mecánicos. Los cinco bloqueantes según el
informe ([2026-06-10_revision_tesis.md](2026-06-10_revision_tesis.md), §*Top-15
consolidado*):

1. Error matemático en la ecuación central del marco teórico (cap. 02): el Jacobiano
   impreso es la transpuesta del producto al que se lo iguala.
2. Faltas de ortografía en la portada (nombre de la universidad y título).
3. Hipótesis circular + "variable independiente" con dos significados en el mismo capítulo.
4. Dos descripciones de comportamiento del software falsas en los anexos (fallback sin
   `pdflatex`; conversión Q9 del importador DXF).
5. El anexo de la memoria de cálculo dice "reproduce" cuando en realidad condensa.

Contexto y decisiones ya tomadas sobre la tesis: [../../tesis/README.md](../../tesis/README.md).

## Diferido con justificación — no reabrir sin plan

De la auditoría integral 2026-05-31 (P3) y de la de canvas 2026-05-30. Están diferidos
por ratio riesgo/beneficio, no por olvido:

| Ítem | Origen | Por qué está diferido |
|---|---|---|
| Descomponer los *god objects* (`mesh_canvas`, `pre_tab`, `memoria_calculo`, `main_window`) | 05-31 #15 | Alto riesgo; requiere tests de caracterización previos |
| Romper el ciclo `gui` ↔ `education` con una capa `ui_kit/` | 05-31 #16 | Refactor estructural amplio |
| Acotar `Pillow<14` y nota de `pdflatex` en requirements | 05-31 #17 | Bajo impacto |
| Restyle incremental de la selección (evitar `delete("all")`) | canvas E.3 | Imperceptible bajo 1000 elementos con culling + LOD; arriesga el sync canvas↔spreadsheet |
| Estados *Locked* / *Hidden* de entidades | canvas C.1 | El focus-and-context ya entrega el beneficio central |
| Etiquetas de valor sobre las isolíneas | canvas R3 | Obligaría a cambiar el contrato del kernel JIT; la colorbar ya comunica la escala |
| Validación con usuarios (sesiones presenciales) | canvas Fase 5 | Fuera del alcance del trabajo autónomo; el protocolo queda definido |

## Cómo agregar una auditoría nueva

1. El informe va en `docs/auditorias/AAAA-MM-DD_tema.md`.
2. Agregá su fila en *Los informes* y sus hallazgos abiertos en la tabla que corresponda.
3. Cuando un informe queda superado por otro más nuevo, movelo a `historico/` y marcá su
   fila como superado — **no lo borres**: la trazabilidad de decisiones es parte del valor.
4. El comando [`/schedule`](../../.claude/commands/schedule.md) corre esta auditoría de
   forma programada y deposita el informe acá.
