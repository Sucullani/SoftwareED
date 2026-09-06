# Notas de trabajo

Espacio compartido entre sesiones, agentes y el autor. Sirve para lo que **no** es una
regla permanente ni un informe formal: qué está a medias, qué se probó y no funcionó, qué
decisión quedó pendiente.

## Los tres lugares — no confundirlos

| Dónde | Qué va | Vida útil |
|---|---|---|
| [ESTADO.md](ESTADO.md) | Estado **actual** del trabajo: qué está en curso, qué quedó a medias, qué decisión espera al autor | Vivo — se edita, se borra lo que ya no aplica |
| `AAAA-MM-DD_slug.md` (acá) | Bitácora de una tarea concreta: qué se intentó, qué se descartó y por qué, dónde quedó | Permanente, pero histórico |
| [../convenciones/](../convenciones/) | **Reglas permanentes** del proyecto | Permanente y vinculante |

Regla simple: si otro agente **debe** obedecerlo → `convenciones/`.
Si solo **necesita saberlo** para no repetir trabajo → acá.

`CLAUDE.md` no es una bitácora: ahí solo van reglas duras y el ruteo.

## Al empezar una tarea

1. Leé [ESTADO.md](ESTADO.md).
2. Si tu tarea toca algo listado ahí como *en curso*, asumí que hay trabajo a medias y
   revisalo antes de reescribirlo.
3. Consultá [ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md) por si tu área ya
   tiene hallazgos abiertos: conviene resolverlos en el mismo pase.

## Al terminar

Actualizá `ESTADO.md` si cambió el panorama. Además, escribí una nota propia cuando se dé
alguna de estas condiciones:

- **Quedó algo a medias** o bloqueado esperando una decisión.
- **Descartaste un camino** (otro agente lo va a proponer de nuevo si no lo escribís).
- **Encontraste una trampa** no evidente (un `after` que hay que cancelar, un orden de
  inicialización, un comportamiento de Tk).
- La tarea fue larga y **el razonamiento no se deduce del diff**.

Si el cambio es autoexplicativo por el diff y el mensaje de commit, **no escribas nota**.
Este directorio pierde valor si se llena de ruido.

## Formato

Copiá [PLANTILLA.md](PLANTILLA.md) a `AAAA-MM-DD_slug-corto.md` (fecha del día,
`slug` en minúsculas con guiones: `2026-09-06_reorganizacion-repo.md`).

Fechas **absolutas** siempre — nunca "ayer" o "la semana pasada".

## Mantenimiento

Cuando una nota queda obsoleta, borrala. Cuando una nota describe algo que se volvió
permanente, movelo al capítulo de `convenciones/` que corresponda y borrá la nota. El
valor de este directorio es que sea corto y verdadero.
